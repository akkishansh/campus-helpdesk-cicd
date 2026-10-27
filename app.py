"""A small, dependency-free campus helpdesk ticket tracker."""

import json
import os
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "data" / "tickets.db"))
STATUSES = {"Open", "In Progress", "Resolved"}


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
        route = urlparse(self.path).path
        if route == "/api/tickets":
            self.respond(200, list_tickets())
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
