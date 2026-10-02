/* Page-local simulation: no network calls, accounts or saved messages. */
(() => {
  const body = document.querySelector('#cb');
  const dialog = document.querySelector('#timer-dialog');
  const labels = {0:'Off',60:'60 seconds',86400:'24 hours',604800:'7 days',7776000:'90 days'};
  if (new URLSearchParams(location.search).get('contact') === 'alex') {
    document.querySelector('.contact-details h1').textContent = 'Alex Stone';
    document.querySelector('.contact-avatar img').alt = "Alex's profile photo";
    document.title = 'Alex · AssentTag Chat';
  }
  let duration = 86400;
  const messages = [];
  body.replaceChildren();
  function add(text, mine, seconds = 0) {
    const row = document.createElement('div');
    row.style.cssText = `max-width:80%;width:fit-content;margin:14px ${mine ? '0 14px auto':'auto 14px 0'};padding:14px 18px;border-radius:18px;background:${mine?'#254b48':'#263148'};color:#f0f7ff;overflow-wrap:anywhere`;
    const content = document.createElement('p'); content.textContent = text; content.style.margin = '0 0 6px';
    const meta = document.createElement('small'); meta.style.color = '#bdccd9';
    row.append(content, meta); body.append(row);
    messages.push({row, meta, expires:seconds ? Date.now()+seconds*1000 : 0});
    body.scrollTop = body.scrollHeight; tick();
  }
  function tick() {
    for (const m of messages) {
      if (!m.expires) { m.meta.textContent = 'Sample conversation'; continue; }
      const left = Math.ceil((m.expires-Date.now())/1000);
      if (left <= 0) { m.row.remove(); continue; }
      m.meta.textContent = left < 60 ? `Disappears in ${left}s` : left < 3600 ? `Disappears in ${Math.ceil(left/60)}m` : `Disappears in ${Math.ceil(left/3600)}h`;
    }
  }
  add('Hey! Have you tried the privacy controls yet?', false);
  add('Yes! I like choosing how long my messages stay.', true);
  document.querySelectorAll('[data-open-timer]').forEach(b => b.onclick = () => dialog.showModal());
  document.querySelectorAll('[data-close-timer]').forEach(b => b.onclick = () => dialog.close());
  document.querySelector('#timer-form').onsubmit = e => {
    e.preventDefault(); duration = Number(new FormData(e.target).get('duration'));
    document.querySelectorAll('[data-timer-label]').forEach(el => el.textContent = labels[duration]);
    document.querySelector('[data-timer-description]').textContent = duration ? `New demo messages disappear ${labels[duration]} after sending.` : 'Disappearing messages are off. New demo messages stay until you leave this page.';
    dialog.close(); document.querySelector('#chat-status').textContent = 'Demo timer updated. Existing messages keep their original timer.';
  };
  document.querySelector('#message-form').onsubmit = e => {
    e.preventDefault(); const input = document.querySelector('#message-content');
    if (!input.value.trim()) return;
    add(input.value.trim(), true, duration); input.value='';
    document.querySelector('#chat-status').textContent = 'Demo only: this message stays in your browser and is not sent to anyone.';
  };
  setInterval(tick, 1000);
})();
