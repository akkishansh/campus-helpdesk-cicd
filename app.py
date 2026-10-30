"""TurfIt booking demo backend and legacy helpdesk API used by the CI pipeline."""

import json
import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import date, time, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "data" / "tickets.db"))
STATUSES = {"Open", "In Progress", "Resolved"}
DEMO_TURFS = (
    ("turf-central", "Turf Central", "Indiranagar, Bengaluru", "Bengaluru", "Football", "5-a-side", 1200, 4.8,
     "Floodlights, Parking, Changing room"),
    ("green-arena", "Green Arena", "Koramangala, Bengaluru", "Bengaluru", "Football", "7-a-side", 1800, 4.7,
     "Floodlights, Parking, Drinking water"),
    ("urban-playfield", "Urban Playfield", "Hitech City, Hyderabad", "Hyderabad", "Cricket", "Box cricket", 1500, 4.6,
     "Indoor, Equipment, Parking"),
)


def connect_db(path=None):
    database = Path(path or DB_PATH)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            requester TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS turfs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            city TEXT NOT NULL,
            sport TEXT NOT NULL,
            format TEXT NOT NULL,
            price_per_hour INTEGER NOT NULL,
            rating REAL NOT NULL,
            amenities TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )"""
    )
    turf_columns = {row["name"] for row in connection.execute("PRAGMA table_info(turfs)")}
    if "active" not in turf_columns:
        connection.execute("ALTER TABLE turfs ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL UNIQUE,
            turf_id TEXT NOT NULL REFERENCES turfs(id),
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            duration_hours INTEGER NOT NULL,
            total_amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS schedule_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turf_id TEXT NOT NULL REFERENCES turfs(id),
            block_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            duration_hours INTEGER NOT NULL,
            reason TEXT NOT NULL DEFAULT 'Unavailable',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            topic TEXT NOT NULL,
            body TEXT NOT NULL,
            likes INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS profiles (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            city TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    connection.executemany(
        """INSERT OR IGNORE INTO turfs
           (id, name, location, city, sport, format, price_per_hour, rating, amenities)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        DEMO_TURFS,
    )
    connection.commit()
    return connection


def list_tickets(path=None):
    with closing(connect_db(path)) as db:
        return [dict(row) for row in db.execute("SELECT * FROM tickets ORDER BY id DESC")]


def create_ticket(values, path=None):
    required = ("title", "category", "priority", "requester", "description")
    cleaned = {key: str(values.get(key, "")).strip() for key in required}
    if any(not value for value in cleaned.values()):
        raise ValueError("Please complete every field before submitting.")
    if len(cleaned["title"]) > 90 or len(cleaned["description"]) > 1000:
        raise ValueError("Title must be under 90 characters and description under 1000.")
    if cleaned["priority"] not in {"Low", "Medium", "High"}:
        raise ValueError("Choose a valid priority.")
    with closing(connect_db(path)) as db, db:
        cursor = db.execute(
            "INSERT INTO tickets (title, category, priority, requester, description) VALUES (?, ?, ?, ?, ?)",
            tuple(cleaned[key] for key in required),
        )
        row = db.execute("SELECT * FROM tickets WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def set_ticket_status(ticket_id, status, path=None):
    if status not in STATUSES:
        raise ValueError("Choose a valid ticket status.")
    with closing(connect_db(path)) as db, db:
        cursor = db.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        if cursor.rowcount == 0:
            return None
        return dict(db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())


def list_turfs(filters=None, path=None):
    filters = filters or {}
    query = "SELECT * FROM turfs WHERE active = 1"
    params = []
    for key in ("city", "sport"):
        value = str(filters.get(key, "")).strip()
        if value:
            query += f" AND lower({key}) = lower(?)"
            params.append(value)
    search = str(filters.get("q", "")).strip()
    if search:
        query += " AND (lower(name) LIKE lower(?) OR lower(location) LIKE lower(?) OR lower(city) LIKE lower(?))"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY rating DESC, name"
    with closing(connect_db(path)) as db:
        turfs = [dict(row) for row in db.execute(query, params)]
    for turf in turfs:
        turf["amenities"] = [item.strip() for item in turf["amenities"].split(",") if item.strip()]
    return turfs


def list_owner_turfs(path=None):
    with closing(connect_db(path)) as db:
        turfs = [dict(row) for row in db.execute("SELECT * FROM turfs ORDER BY name")]
    for turf in turfs:
        turf["amenities"] = [item.strip() for item in turf["amenities"].split(",") if item.strip()]
    return turfs


def get_turf(turf_id, path=None):
    with closing(connect_db(path)) as db:
        row = db.execute("SELECT * FROM turfs WHERE id = ?", (turf_id,)).fetchone()
    if row is None:
        return None
    turf = dict(row)
    turf["amenities"] = [item.strip() for item in turf["amenities"].split(",") if item.strip()]
    return turf


def _valid_booking_date(value):
    try:
        parsed = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError("Choose a valid booking date in YYYY-MM-DD format.")
    if parsed < date.today():
        raise ValueError("Choose today or a future date.")
    if parsed > date.today() + timedelta(days=90):
        raise ValueError("Bookings can be made up to 90 days ahead.")
    return parsed


def _valid_start_time(value):
    try:
        parsed = time.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError("Choose a valid start time.")
    if parsed.minute or parsed.second or parsed.hour < 6 or parsed.hour > 22:
        raise ValueError("Choose an hourly slot between 06:00 and 22:00.")
    return parsed


def list_availability(turf_id, booking_date, path=None):
    _valid_booking_date(booking_date)
    turf = get_turf(turf_id, path)
    if turf is None:
        return None
    with closing(connect_db(path)) as db:
        bookings = db.execute(
            """SELECT start_time, duration_hours FROM bookings
               WHERE turf_id = ? AND booking_date = ? AND status = 'Confirmed'""",
            (turf_id, booking_date),
        ).fetchall()
        blocks = db.execute(
            """SELECT start_time, duration_hours FROM schedule_blocks
               WHERE turf_id = ? AND block_date = ?""",
            (turf_id, booking_date),
        ).fetchall()
    occupied = [(time.fromisoformat(row["start_time"]), row["duration_hours"]) for row in (*bookings, *blocks)]
    slots = []
    for hour in range(6, 23):
        start = time(hour)
        end = start.hour + 1
        available = all(
            not (start.hour < existing.hour + duration and end > existing.hour)
            for existing, duration in occupied
        )
        slots.append({
            "start_time": start.strftime("%H:%M"),
            "available": available,
            "price": turf["price_per_hour"],
        })
    return slots


def create_booking(values, path=None):
    required = ("turf_id", "date", "start_time", "duration_hours", "customer_name", "email", "phone")
    cleaned = {key: str(values.get(key, "")).strip() for key in required}
    if any(not value for value in cleaned.values()):
        raise ValueError("Please complete all booking details.")
    booking_date = _valid_booking_date(cleaned["date"])
    start = _valid_start_time(cleaned["start_time"])
    try:
        duration = int(cleaned["duration_hours"])
    except ValueError:
        raise ValueError("Choose a booking duration of 1, 2, or 3 hours.")
    if duration not in {1, 2, 3} or start.hour + duration > 23:
        raise ValueError("Choose a booking duration of 1, 2, or 3 hours within opening hours.")
    if len(cleaned["customer_name"]) > 100:
        raise ValueError("Name must be under 100 characters.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", cleaned["email"]):
        raise ValueError("Enter a valid email address.")
    digits = re.sub(r"\D", "", cleaned["phone"])
    if len(digits) < 7 or len(digits) > 15:
        raise ValueError("Enter a phone number with 7 to 15 digits.")

    reference = f"TFT-{secrets.token_hex(4).upper()}"
    with closing(connect_db(path)) as db:
        db.execute("BEGIN IMMEDIATE")
        turf = db.execute("SELECT * FROM turfs WHERE id = ?", (cleaned["turf_id"],)).fetchone()
        if turf is None:
            raise ValueError("Choose a valid turf.")
        if not turf["active"]:
            raise ValueError("This turf is not accepting bookings right now.")
        new_start = start.hour
        new_end = new_start + duration
        existing = db.execute(
            """SELECT start_time, duration_hours FROM bookings
               WHERE turf_id = ? AND booking_date = ? AND status = 'Confirmed'""",
            (cleaned["turf_id"], booking_date.isoformat()),
        ).fetchall()
        blocks = db.execute(
            """SELECT start_time, duration_hours FROM schedule_blocks
               WHERE turf_id = ? AND block_date = ?""",
            (cleaned["turf_id"], booking_date.isoformat()),
        ).fetchall()
        for row in (*existing, *blocks):
            old_start = time.fromisoformat(row["start_time"]).hour
            old_end = old_start + row["duration_hours"]
            if new_start < old_end and new_end > old_start:
                raise ValueError("That time is no longer available. Please choose another slot.")
        cursor = db.execute(
            """INSERT INTO bookings
               (reference, turf_id, customer_name, email, phone, booking_date, start_time,
                duration_hours, total_amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (reference, cleaned["turf_id"], cleaned["customer_name"], cleaned["email"].lower(),
             cleaned["phone"], booking_date.isoformat(), start.strftime("%H:%M"), duration,
             turf["price_per_hour"] * duration),
        )
        booking = db.execute(
            """SELECT bookings.*, turfs.name AS turf_name, turfs.location
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id WHERE bookings.id = ?""",
            (cursor.lastrowid,),
        ).fetchone()
        db.commit()
        return dict(booking)


def list_bookings(email, path=None):
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        raise ValueError("Enter the email address used for the booking.")
    with closing(connect_db(path)) as db:
        rows = db.execute(
            """SELECT bookings.*, turfs.name AS turf_name, turfs.location
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id
               WHERE lower(bookings.email) = ? ORDER BY bookings.booking_date DESC, bookings.start_time""",
            (normalized_email,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_booking(booking_id, email, path=None):
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        raise ValueError("Enter the email address used for the booking.")
    with closing(connect_db(path)) as db:
        row = db.execute(
            """SELECT bookings.*, turfs.name AS turf_name, turfs.location
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id
               WHERE bookings.id = ? AND lower(bookings.email) = ?""",
            (booking_id, normalized_email),
        ).fetchone()
    return dict(row) if row else None


def cancel_booking(booking_id, email, path=None):
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        raise ValueError("Enter the email address used for the booking.")
    with closing(connect_db(path)) as db, db:
        cursor = db.execute(
            """UPDATE bookings SET status = 'Cancelled'
               WHERE id = ? AND lower(email) = ? AND status = 'Confirmed'""",
            (booking_id, normalized_email),
        )
        if cursor.rowcount == 0:
            return None
        row = db.execute(
            """SELECT bookings.*, turfs.name AS turf_name, turfs.location
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id WHERE bookings.id = ?""",
            (booking_id,),
        ).fetchone()
        return dict(row)


def owner_bookings(filters=None, path=None):
    filters = filters or {}
    query = """SELECT bookings.*, turfs.name AS turf_name, turfs.location
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id WHERE 1 = 1"""
    params = []
    for key, column in (("status", "bookings.status"), ("date", "bookings.booking_date"), ("turf_id", "bookings.turf_id")):
        value = str(filters.get(key, "")).strip()
        if value:
            query += f" AND {column} = ?"
            params.append(value)
    query += " ORDER BY bookings.booking_date DESC, bookings.start_time DESC"
    with closing(connect_db(path)) as db:
        return [dict(row) for row in db.execute(query, params)]


def owner_dashboard(path=None):
    with closing(connect_db(path)) as db:
        totals = db.execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN status = 'Confirmed' THEN 1 ELSE 0 END) AS confirmed,
                      SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                      SUM(CASE WHEN status = 'Confirmed' THEN total_amount ELSE 0 END) AS revenue
               FROM bookings"""
        ).fetchone()
        turf_count = db.execute("SELECT COUNT(*) FROM turfs WHERE active = 1").fetchone()[0]
        recent = db.execute(
            """SELECT bookings.*, turfs.name AS turf_name
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id
               ORDER BY bookings.id DESC LIMIT 8"""
        ).fetchall()
        daily = db.execute(
            """SELECT booking_date AS date, SUM(total_amount) AS revenue, COUNT(*) AS bookings
               FROM bookings WHERE status = 'Confirmed' AND booking_date >= date('now', '-6 days')
               GROUP BY booking_date ORDER BY booking_date"""
        ).fetchall()
    return {
        "total_bookings": totals["total"] or 0,
        "confirmed_bookings": totals["confirmed"] or 0,
        "cancelled_bookings": totals["cancelled"] or 0,
        "revenue": totals["revenue"] or 0,
        "active_turfs": turf_count,
        "recent_bookings": [dict(row) for row in recent],
        "daily_performance": [dict(row) for row in daily],
    }


def update_owner_booking_status(booking_id, status, path=None):
    if status not in {"Confirmed", "Cancelled"}:
        raise ValueError("Choose Confirmed or Cancelled.")
    with closing(connect_db(path)) as db, db:
        cursor = db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        if cursor.rowcount == 0:
            return None
        row = db.execute(
            """SELECT bookings.*, turfs.name AS turf_name, turfs.location
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id WHERE bookings.id = ?""",
            (booking_id,),
        ).fetchone()
        return dict(row)


def save_turf(values, path=None):
    required = ("name", "location", "city", "sport", "format", "price_per_hour")
    cleaned = {key: str(values.get(key, "")).strip() for key in required}
    if any(not value for value in cleaned.values()):
        raise ValueError("Complete all required turf details.")
    try:
        price = int(cleaned["price_per_hour"])
        rating = float(values.get("rating", 4.8))
    except ValueError:
        raise ValueError("Price and rating must be numbers.")
    if price < 1 or price > 100000:
        raise ValueError("Set an hourly price between ₹1 and ₹100,000.")
    if rating < 0 or rating > 5:
        raise ValueError("Rating must be between 0 and 5.")
    turf_id = str(values.get("id", "")).strip()
    if not turf_id:
        slug = re.sub(r"[^a-z0-9]+", "-", cleaned["name"].lower()).strip("-")[:40] or "new-turf"
        turf_id = f"{slug}-{secrets.token_hex(2)}"
    amenities = values.get("amenities", [])
    if isinstance(amenities, str):
        amenities = [item.strip() for item in amenities.split(",") if item.strip()]
    if not isinstance(amenities, list):
        raise ValueError("Amenities must be a list of text values.")
    active = 1 if str(values.get("active", "1")).lower() not in {"false", "0", "inactive"} else 0
    with closing(connect_db(path)) as db, db:
        db.execute(
            """INSERT INTO turfs (id, name, location, city, sport, format, price_per_hour, rating, amenities, active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name = excluded.name, location = excluded.location,
                 city = excluded.city, sport = excluded.sport, format = excluded.format,
                 price_per_hour = excluded.price_per_hour, rating = excluded.rating,
                 amenities = excluded.amenities, active = excluded.active""",
            (turf_id, cleaned["name"], cleaned["location"], cleaned["city"], cleaned["sport"], cleaned["format"],
             price, rating, ", ".join(str(item).strip() for item in amenities if str(item).strip()), active),
        )
        row = db.execute("SELECT * FROM turfs WHERE id = ?", (turf_id,)).fetchone()
    turf = dict(row)
    turf["amenities"] = [item.strip() for item in turf["amenities"].split(",") if item.strip()]
    return turf


def list_schedule_blocks(booking_date="", path=None):
    query = """SELECT schedule_blocks.*, turfs.name AS turf_name
               FROM schedule_blocks JOIN turfs ON turfs.id = schedule_blocks.turf_id WHERE 1 = 1"""
    params = []
    if booking_date:
        _valid_booking_date(booking_date)
        query += " AND block_date = ?"
        params.append(booking_date)
    query += " ORDER BY block_date, start_time"
    with closing(connect_db(path)) as db:
        return [dict(row) for row in db.execute(query, params)]


def add_schedule_block(values, path=None):
    turf_id = str(values.get("turf_id", "")).strip()
    booking_date = _valid_booking_date(values.get("date", "")).isoformat()
    start = _valid_start_time(values.get("start_time", ""))
    try:
        duration = int(values.get("duration_hours", 1))
    except (TypeError, ValueError):
        raise ValueError("Choose a block duration of 1, 2, or 3 hours.")
    if duration not in {1, 2, 3} or start.hour + duration > 23:
        raise ValueError("Choose a block duration of 1, 2, or 3 hours within opening hours.")
    reason = str(values.get("reason", "Unavailable")).strip()[:100] or "Unavailable"
    with closing(connect_db(path)) as db:
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM turfs WHERE id = ?", (turf_id,)).fetchone():
            raise ValueError("Choose a valid turf.")
        existing = db.execute(
            """SELECT start_time, duration_hours FROM bookings
               WHERE turf_id = ? AND booking_date = ? AND status = 'Confirmed'""",
            (turf_id, booking_date),
        ).fetchall()
        for row in existing:
            old_start = time.fromisoformat(row["start_time"]).hour
            if start.hour < old_start + row["duration_hours"] and start.hour + duration > old_start:
                raise ValueError("This time has a confirmed booking and cannot be blocked.")
        cursor = db.execute(
            "INSERT INTO schedule_blocks (turf_id, block_date, start_time, duration_hours, reason) VALUES (?, ?, ?, ?, ?)",
            (turf_id, booking_date, start.strftime("%H:%M"), duration, reason),
        )
        row = db.execute(
            """SELECT schedule_blocks.*, turfs.name AS turf_name FROM schedule_blocks
               JOIN turfs ON turfs.id = schedule_blocks.turf_id WHERE schedule_blocks.id = ?""",
            (cursor.lastrowid,),
        ).fetchone()
        db.commit()
        return dict(row)


def remove_schedule_block(block_id, path=None):
    with closing(connect_db(path)) as db, db:
        cursor = db.execute("DELETE FROM schedule_blocks WHERE id = ?", (block_id,))
        return cursor.rowcount > 0


def owner_notifications(path=None):
    with closing(connect_db(path)) as db:
        rows = db.execute(
            """SELECT bookings.id, bookings.reference, bookings.customer_name, bookings.booking_date,
                      bookings.start_time, bookings.status, bookings.created_at, turfs.name AS turf_name
               FROM bookings JOIN turfs ON turfs.id = bookings.turf_id
               ORDER BY bookings.id DESC LIMIT 20"""
        ).fetchall()
    return [dict(row) for row in rows]


def list_community_posts(path=None):
    with closing(connect_db(path)) as db:
        return [dict(row) for row in db.execute("SELECT * FROM community_posts ORDER BY id DESC LIMIT 50")]


def create_community_post(values, path=None):
    author = str(values.get("author", "")).strip() or "TurfIt Player"
    topic = str(values.get("topic", "General")).strip() or "General"
    body = str(values.get("body", "")).strip()
    if not body:
        raise ValueError("Write a message before posting.")
    if len(author) > 80 or len(topic) > 40 or len(body) > 1000:
        raise ValueError("Keep your name under 80 characters, topic under 40, and message under 1,000.")
    with closing(connect_db(path)) as db, db:
        cursor = db.execute("INSERT INTO community_posts (author, topic, body) VALUES (?, ?, ?)", (author, topic, body))
        return dict(db.execute("SELECT * FROM community_posts WHERE id = ?", (cursor.lastrowid,)).fetchone())


def like_community_post(post_id, path=None):
    with closing(connect_db(path)) as db, db:
        cursor = db.execute("UPDATE community_posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        if cursor.rowcount == 0:
            return None
        return dict(db.execute("SELECT * FROM community_posts WHERE id = ?", (post_id,)).fetchone())


def get_profile(email, path=None):
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        raise ValueError("Enter your email address.")
    with closing(connect_db(path)) as db:
        row = db.execute("SELECT * FROM profiles WHERE email = ?", (normalized_email,)).fetchone()
    return dict(row) if row else None


def save_profile(values, path=None):
    email = str(values.get("email", "")).strip().lower()
    name = str(values.get("name", "")).strip()
    phone = str(values.get("phone", "")).strip()[:30]
    city = str(values.get("city", "")).strip()[:80]
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Enter a valid email address.")
    if not name or len(name) > 100:
        raise ValueError("Enter your name (up to 100 characters).")
    with closing(connect_db(path)) as db, db:
        db.execute(
            """INSERT INTO profiles (email, name, phone, city, updated_at) VALUES (?, ?, ?, ?, datetime('now'))
               ON CONFLICT(email) DO UPDATE SET name = excluded.name, phone = excluded.phone,
                 city = excluded.city, updated_at = datetime('now')""",
            (email, name, phone, city),
        )
        return dict(db.execute("SELECT * FROM profiles WHERE email = ?", (email,)).fetchone())


def rewards_summary(email, path=None):
    bookings = list_bookings(email, path)
    earned = sum(booking["total_amount"] // 100 for booking in bookings if booking["status"] == "Confirmed")
    next_tier = 500 if earned < 500 else 1000 if earned < 1000 else earned + 500
    return {
        "points": earned,
        "tier": "Rookie" if earned < 500 else "Pro" if earned < 1000 else "Legend",
        "next_reward_at": next_tier,
        "points_to_next_reward": max(0, next_tier - earned),
        "confirmed_bookings": sum(booking["status"] == "Confirmed" for booking in bookings),
    }


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, payload, content_type="application/json; charset=utf-8"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        query = parse_qs(parsed_url.query)
        if route == "/api/tickets":
            self.respond(200, list_tickets())
        elif route == "/api/turfs":
            self.respond(200, list_turfs({key: query.get(key, [""])[0] for key in ("city", "sport", "q")}))
        elif route.startswith("/api/turfs/") and route.endswith("/availability"):
            try:
                turf_id = route.split("/")[3]
                booking_date = query.get("date", [""])[0]
                slots = list_availability(turf_id, booking_date)
                self.respond(200, {"turf_id": turf_id, "date": booking_date, "slots": slots}) if slots is not None else self.respond(404, {"error": "Turf not found"})
            except ValueError as exc:
                self.respond(400, {"error": str(exc)})
        elif route.startswith("/api/turfs/"):
            turf = get_turf(route.split("/")[3]) if len(route.split("/")) == 4 else None
            self.respond(200, turf) if turf else self.respond(404, {"error": "Turf not found"})
        elif route == "/api/bookings":
            try:
                self.respond(200, list_bookings(query.get("email", [""])[0]))
            except ValueError as exc:
                self.respond(400, {"error": str(exc)})
        elif route == "/api/owner/dashboard":
            self.respond(200, owner_dashboard())
        elif route == "/api/owner/turfs":
            self.respond(200, list_owner_turfs())
        elif route == "/api/owner/bookings":
            self.respond(200, owner_bookings({key: query.get(key, [""])[0] for key in ("status", "date", "turf_id")}))
        elif route == "/api/owner/schedule":
            try:
                self.respond(200, list_schedule_blocks(query.get("date", [""])[0]))
            except ValueError as exc:
                self.respond(400, {"error": str(exc)})
        elif route == "/api/owner/notifications":
            self.respond(200, owner_notifications())
        elif route == "/api/community/posts":
            self.respond(200, list_community_posts())
        elif route == "/api/profile":
            try:
                profile = get_profile(query.get("email", [""])[0])
                self.respond(200, profile) if profile else self.respond(404, {"error": "Profile not found"})
            except ValueError as exc:
                self.respond(400, {"error": str(exc)})
        elif route == "/api/rewards":
            try:
                self.respond(200, rewards_summary(query.get("email", [""])[0]))
            except ValueError as exc:
                self.respond(400, {"error": str(exc)})
        elif route.startswith("/api/bookings/"):
            try:
                booking_id = int(route.split("/")[3])
                booking = get_booking(booking_id, query.get("email", [""])[0])
                self.respond(200, booking) if booking else self.respond(404, {"error": "Booking not found"})
            except (ValueError, IndexError) as exc:
                self.respond(400, {"error": str(exc)})
        elif route == "/health":
            self.respond(200, {"status": "ok"})
        elif route == "/":
            self.respond(200, (ROOT / "static" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif route == "/styles.css":
            self.respond(200, (ROOT / "static" / "styles.css").read_bytes(), "text/css; charset=utf-8")
        elif route == "/app.js":
            self.respond(200, (ROOT / "static" / "app.js").read_bytes(), "text/javascript; charset=utf-8")
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        route = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            values = json.loads(self.rfile.read(length) or b"{}")
            if route == "/api/tickets":
                self.respond(201, create_ticket(values))
            elif route == "/api/bookings":
                self.respond(201, create_booking(values))
            elif route == "/api/owner/turfs":
                self.respond(201, save_turf(values))
            elif route.startswith("/api/owner/turfs/"):
                turf_id = route.split("/")[4] if len(route.split("/")) > 4 else ""
                values["id"] = turf_id
                self.respond(200, save_turf(values))
            elif route == "/api/owner/bookings/status":
                booking_id = int(values.get("booking_id", 0))
                booking = update_owner_booking_status(booking_id, values.get("status", ""))
                self.respond(200, booking) if booking else self.respond(404, {"error": "Booking not found"})
            elif route == "/api/owner/schedule":
                self.respond(201, add_schedule_block(values))
            elif route.startswith("/api/owner/schedule/") and route.endswith("/delete"):
                block_id = int(route.split("/")[4])
                self.respond(200, {"deleted": remove_schedule_block(block_id)})
            elif route == "/api/community/posts":
                self.respond(201, create_community_post(values))
            elif route.startswith("/api/community/posts/") and route.endswith("/like"):
                post_id = int(route.split("/")[4])
                post = like_community_post(post_id)
                self.respond(200, post) if post else self.respond(404, {"error": "Post not found"})
            elif route == "/api/profile":
                self.respond(200, save_profile(values))
            elif route.startswith("/api/bookings/") and route.endswith("/cancel"):
                booking_id = int(route.split("/")[3])
                booking = cancel_booking(booking_id, values.get("email", ""))
                self.respond(200, booking) if booking else self.respond(404, {"error": "Booking not found or already cancelled"})
            elif route.startswith("/api/tickets/") and route.endswith("/status"):
                ticket_id = int(route.split("/")[3])
                ticket = set_ticket_status(ticket_id, values.get("status", ""))
                self.respond(200, ticket) if ticket else self.respond(404, {"error": "Ticket not found"})
            else:
                self.respond(404, {"error": "Not found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self.respond(400, {"error": str(exc)})

    def log_message(self, _format, *_args):
        print("[http]", self.address_string(), self.command, self.path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    connect_db().close()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Campus Helpdesk is ready on port {port}")
    server.serve_forever()
