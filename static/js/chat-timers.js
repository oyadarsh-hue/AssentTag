(() => {
  'use strict';
  const root = document.querySelector('.conversation');
  if (!root) return;
  const body = document.getElementById('cb');
  const dialog = document.getElementById('timer-dialog');
  const form = document.getElementById('timer-form');
  const status = document.getElementById('chat-status');
  const error = document.getElementById('timer-error');
  const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
  let timer = JSON.parse(document.getElementById('initial-chat-timer').textContent);
  let editRevision = timer.revision;
  let serverTime = Date.parse(root.dataset.serverNow);
  let syncedAt = performance.now();
  let polling = false;
  let stopped = false;
  let lastHtml = null;
  let opener;
  let saving = false;

  function syncClock(value) {
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) { serverTime = parsed; syncedAt = performance.now(); }
  }
  function now() { return serverTime + performance.now() - syncedAt; }
  function paintTimer(next) {
    // Ignore a slow poll response that predates a successful settings save.
    if (next.revision < timer.revision) return;
    timer = next;
    document.querySelectorAll('[data-timer-label]').forEach(el => { el.textContent = next.label; });
    document.querySelector('[data-timer-description]').textContent = next.duration
      ? `New messages disappear ${next.label} after sending.`
      : 'Disappearing messages are off. New messages stay in this chat.';
  }
  function countdown(seconds) {
    if (seconds >= 86400) return `${Math.floor(seconds / 86400)}d ${Math.floor(seconds % 86400 / 3600)}h left`;
    if (seconds >= 3600) return `${Math.floor(seconds / 3600)}h ${Math.floor(seconds % 3600 / 60)}m left`;
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')} left`;
  }
  function tick() {
    let removed = false;
    body.querySelectorAll('[data-expires-at]').forEach(message => {
      const remaining = Math.ceil((Date.parse(message.dataset.expiresAt) - now()) / 1000);
      if (remaining <= 0) { message.remove(); removed = true; return; }
      const label = message.querySelector('[data-countdown]');
      if (label) label.textContent = countdown(remaining);
      const ring = message.querySelector('.countdown-ring');
      if (ring) ring.style.setProperty('--progress', `${Math.min(100, remaining / Number(message.dataset.duration) * 100)}%`);
    });
    if (removed) { status.textContent = 'A timed message disappeared.'; lastHtml = null; }
  }
  function closeDialog() { dialog.close(); if (opener) opener.focus(); }
  document.querySelectorAll('[data-open-timer]').forEach(button => button.addEventListener('click', () => {
    opener = button;
    editRevision = timer.revision;
    form.elements.duration.value = String(timer.duration);
    error.textContent = '';
    dialog.showModal();
  }));
  document.querySelectorAll('[data-close-timer]').forEach(button => button.addEventListener('click', closeDialog));
  dialog.addEventListener('click', event => { if (event.target === dialog) closeDialog(); });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (saving) return;
    saving = true;
    const save = form.querySelector('[type=submit]');
    save.disabled = true;
    error.textContent = '';
    try {
      const response = await fetch(`${root.dataset.chatUrl}timer/`, {
        method: 'POST', credentials: 'same-origin',
        headers: {'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({duration: form.elements.duration.value, revision: editRevision}),
      });
      const result = await response.json();
      if (result.timer) { paintTimer(result.timer); syncClock(result.server_now); }
      if (!response.ok) {
        if (response.status === 409) {
          editRevision = timer.revision;
          form.elements.duration.value = String(timer.duration);
        }
        throw new Error(result.error || 'The timer could not be saved. Try again.');
      }
      closeDialog();
      status.textContent = timer.duration ? `Timer set to ${timer.label} for both people.` : 'Timer off. New messages will stay in the chat.';
    } catch (problem) {
      error.textContent = problem.message || 'Connection interrupted. Your timer was not changed.';
    } finally { save.disabled = false; saving = false; }
  });
  async function poll() {
    if (polling || stopped || document.hidden) return;
    polling = true;
    try {
      const response = await fetch(`${root.dataset.chatUrl}state/`, {cache:'no-store', credentials:'same-origin'});
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          stopped = true;
          body.replaceChildren();
          document.querySelectorAll('.composer-input input,.composer-input button,[data-open-timer]').forEach(el => { el.disabled = true; });
          if (dialog.open) dialog.close();
        }
        throw new Error(result.error || 'Messages could not refresh.');
      }
      const changed = result.timer.revision > timer.revision;
      paintTimer(result.timer);
      syncClock(result.server_now);
      if (changed) status.textContent = `The conversation timer is now ${timer.label.toLowerCase()}.`;
      else if (status.dataset.offline) { status.textContent = 'Connected. Messages are up to date.'; delete status.dataset.offline; }
      if (lastHtml !== result.html) {
        const atBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 90;
        const position = body.scrollTop;
        body.innerHTML = result.html; // Same-origin, server-escaped Django template.
        lastHtml = result.html;
        body.scrollTop = atBottom ? body.scrollHeight : position;
      }
      tick();
    } catch (problem) {
      status.dataset.offline = 'true';
      status.textContent = stopped ? problem.message : 'Reconnecting… Timers continue while messages refresh.';
    } finally { polling = false; }
  }
  body.scrollTop = body.scrollHeight;
  tick();
  poll();
  setInterval(tick, 1000);
  setInterval(poll, 5000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { tick(); poll(); } });
  window.addEventListener('online', poll);
})();
