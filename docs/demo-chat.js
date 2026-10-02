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
    const row = document.createElement('article'); row.className = 'msg-container '+(mine?'sent':'recv');
    const box = document.createElement('div'); box.className = 'msg-box';
    const content = document.createElement('span'); content.className = 'message-content'; content.textContent = text;
    const footer = document.createElement('footer'); footer.className = 'message-meta';
    const time = document.createElement('time'); time.textContent = new Date().toLocaleTimeString([], {hour:'numeric',minute:'2-digit'});
    const meta = document.createElement('span'); meta.className = 'message-countdown';
    footer.append(time,meta);box.append(content,footer);row.append(box);body.append(row);
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
