const rows = document.querySelector('#ticketRows');
const modal = document.querySelector('#modal');
const form = document.querySelector('#ticketForm');
const empty = document.querySelector('#empty');
let tickets = [];
let activeFilter = 'All';
let toastTimer;

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function statusClass(value) { return value.replaceAll(' ', '-'); }

function render() {
  const query = document.querySelector('#search').value.trim().toLowerCase();
  const visible = tickets.filter(ticket => (activeFilter === 'All' || ticket.status === activeFilter) &&
    `${ticket.title} ${ticket.category} ${ticket.requester}`.toLowerCase().includes(query));
  rows.innerHTML = visible.map(ticket => `<tr>
    <td><strong>${escapeHTML(ticket.title)}</strong><small>#${String(ticket.id).padStart(4, '0')} · ${new Date(`${ticket.created_at}Z`).toLocaleDateString()}</small></td>
    <td class="category">${escapeHTML(ticket.category)}</td>
    <td><span class="priority ${escapeHTML(ticket.priority)}">${escapeHTML(ticket.priority)}</span></td>
    <td><span class="status ${statusClass(ticket.status)}"><i></i></span><select class="status-select" data-id="${ticket.id}" aria-label="Update status for ${escapeHTML(ticket.title)}">${['Open','In Progress','Resolved'].map(s => `<option ${s === ticket.status ? 'selected' : ''}>${s}</option>`).join('')}</select></td>
    <td>${escapeHTML(ticket.requester)}</td><td><button class="row-menu" title="Request options">···</button></td></tr>`).join('');
  document.querySelector('#totalCount').textContent = tickets.length;
  document.querySelector('#openCount').textContent = tickets.filter(t => t.status === 'Open').length;
  document.querySelector('#progressCount').textContent = tickets.filter(t => t.status === 'In Progress').length;
  document.querySelector('#resolvedCount').textContent = tickets.filter(t => t.status === 'Resolved').length;
  document.querySelector('#allPill').textContent = tickets.length;
  document.querySelector('#showing').textContent = `Showing ${visible.length} request${visible.length === 1 ? '' : 's'}`;
  empty.classList.toggle('show', visible.length === 0);
}

async function loadTickets() {
  try {
    const response = await fetch('/api/tickets');
    if (!response.ok) throw new Error('Unable to load requests');
    tickets = await response.json();
    document.querySelector('#updated').textContent = `Updated ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`;
    render();
  } catch (error) { showToast(error.message); }
}

function showToast(message) {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
}

function openModal() { modal.hidden = false; setTimeout(() => form.elements.title.focus(), 0); }
function closeModal() { modal.hidden = true; form.reset(); document.querySelector('#formError').textContent = ''; }
document.querySelector('#newTicket').addEventListener('click', openModal);
document.querySelector('#emptyNew').addEventListener('click', openModal);
document.querySelector('#closeModal').addEventListener('click', closeModal);
document.querySelector('#cancelModal').addEventListener('click', closeModal);
modal.addEventListener('click', event => { if (event.target === modal) closeModal(); });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && !modal.hidden) closeModal(); });
document.querySelector('#search').addEventListener('input', render);
document.querySelector('#filters').addEventListener('click', event => {
  const button = event.target.closest('[data-filter]');
  if (!button) return;
  activeFilter = button.dataset.filter;
  document.querySelectorAll('.filter').forEach(item => item.classList.toggle('active', item === button));
  render();
});
rows.addEventListener('change', async event => {
  if (!event.target.matches('.status-select')) return;
  const response = await fetch(`/api/tickets/${event.target.dataset.id}/status`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:event.target.value})});
  if (!response.ok) { showToast('Could not update the request status.'); return loadTickets(); }
  showToast('Request status updated.');
  await loadTickets();
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  document.querySelector('#formError').textContent = '';
  try {
    const values = Object.fromEntries(new FormData(form));
    const response = await fetch('/api/tickets', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not submit request.');
    closeModal(); activeFilter = 'All';
    document.querySelectorAll('.filter').forEach(item => item.classList.toggle('active', item.dataset.filter === 'All'));
    await loadTickets(); showToast('Your request has been submitted.');
  } catch (error) { document.querySelector('#formError').textContent = error.message; }
  finally { submit.disabled = false; }
});
loadTickets();
