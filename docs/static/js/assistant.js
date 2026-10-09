/* Assent lives in a shadow root so each page keeps its own styles and forms. */
(() => {
  'use strict';
  const script = document.querySelector('script[data-assent-assistant]');
  if (!script || document.querySelector('[data-at-assistant]')) return;
  const demo = script.dataset.siteMode === 'preview';
  const owner = script.dataset.owner || 'guest';
  const storageKey = `assent-v1:${demo ? 'preview' : owner}`;
  let storageWorks = true;
  const storeFor = name => { try { return window[name]; } catch { storageWorks = false; return { getItem: () => null, setItem: () => { throw new Error('Storage unavailable'); } }; } };
  const safeSession = storeFor('sessionStorage'), safeLocal = storeFor('localStorage');
  const read = (storage, key, fallback) => { try { return JSON.parse(storage.getItem(key)) ?? fallback; } catch { return fallback; } };
  const save = (storage, key, value) => { try { storage.setItem(key, JSON.stringify(value)); } catch { storageWorks = false; } };
  const host = document.createElement('div');
  host.dataset.atAssistant = '';
  if (demo) host.dataset.preview = '';
  document.body.append(host);
  const root = host.attachShadow({ mode: 'open' });
  // All HTML below is a static template. User and AI content always uses textContent.
  root.innerHTML = `
    <link rel="stylesheet" href="${new URL('../css/assistant.css?v=1', script.src).href}">
    <button class="launcher" aria-label="Open Assent personal assistant" aria-expanded="false" aria-controls="assent-panel">
      <span class="orb" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>
      <span class="launcher-copy">Ask Assent <small>Your personal space</small></span><span class="launcher-arrow" aria-hidden="true">↗</span>
    </button>
    <div class="panel" id="assent-panel" role="dialog" aria-label="Assent personal assistant" hidden>
      <header><div class="identity"><span class="mini-orb" aria-hidden="true">✦</span><div><strong>Assent<span> / </span>your sidekick</strong><p id="connection-status" role="status">Site guide · GPT-7+ connection pending</p></div></div><button class="icon close" aria-label="Close assistant">×</button></header>
      <div class="tabs" role="tablist" aria-label="Assistant tools"><button id="chat-tab" role="tab" aria-selected="true" aria-controls="chat-pane">✦ Chat</button><button id="tasks-tab" role="tab" aria-selected="false" aria-controls="tasks-pane" tabindex="-1">✓ My tasks <span id="task-count">0</span></button></div>
      <div id="chat-pane" class="pane" role="tabpanel" aria-labelledby="chat-tab">
        <div class="conversation" id="conversation" role="log" aria-label="Assistant conversation" aria-live="polite" aria-relevant="additions text"></div>
        <div class="thinking" role="status" hidden><span>● ● ●</span> Assent is thinking…</div>
        <div class="shortcuts" aria-label="Quick prompts"><button data-prompt="Help me write a cheerful photo caption.">Write a caption ↗</button><button data-prompt="Help me plan my day in three simple steps.">Plan my day ↗</button><button data-prompt="How do I share photos with consent on AssentTag?">Explore AssentTag ↗</button></div>
        <form id="chat-form"><label class="sr-only" for="assent-message">Message Assent</label><textarea id="assent-message" rows="2" maxlength="2000" placeholder="Ask, imagine, make a plan…" required></textarea><button class="send" type="submit" aria-label="Send message">↑</button><button class="stop" type="button" hidden>Stop</button></form>
        <p class="privacy">AI receives your chat text when connected. Avoid secrets. Replies can be mistaken.</p>
      </div>
      <div id="tasks-pane" class="pane tasks-pane" role="tabpanel" aria-labelledby="tasks-tab" hidden><div class="task-intro"><span class="eyebrow">A LITTLE MOMENTUM</span><h2>Make room for what matters.</h2><p>Add a small next step. Tick it off. Keep going.</p></div><form id="task-form"><label class="sr-only" for="task-input">New personal task</label><input id="task-input" maxlength="160" placeholder="One thing I want to do…" required><button type="submit" class="task-add">Add</button></form><ul id="task-list" aria-label="Personal tasks"></ul><p class="task-note" id="task-note">Tasks stay on this device. No notifications run while the site is closed.</p></div>
      <div class="connection" hidden><form id="connection-form"><strong>Your AI connection</strong><p>This assistant requires GPT-7 or higher. That model is not currently connected. A supported model, API credits, and a hosted backend are needed. Your OpenAI key stays on the server.</p><label for="backend-url">Backend URL</label><input id="backend-url" type="url" placeholder="https://your-assistant.example.com"><label for="access-code">Private assistant access code</label><input id="access-code" type="password" autocomplete="off" placeholder="For a hosted connection"><div class="connection-actions"><button type="submit">Save & connect</button><button class="reset-connection" type="button">Reset</button><button class="close-connection" type="button">Back</button></div><p id="connection-feedback" role="status"></p></form></div>
      <footer><span id="save-status">Chat kept in this tab</span><div><button class="clear-chat">New chat</button><button class="connection-toggle">Connection</button></div></footer>
    </div>`;
  const $ = selector => root.querySelector(selector);
  const conversation = $('#conversation'), panel = $('.panel'), input = $('#assent-message');
  const stored = read(safeSession, storageKey + ':chat', []);
  let transcript = Array.isArray(stored) ? stored.filter(x => x && ['user', 'assistant', 'error'].includes(x.role) && typeof x.content === 'string').slice(-30) : [];
  const storedTasks = read(safeLocal, storageKey + ':tasks', []);
  let tasks = Array.isArray(storedTasks) ? storedTasks.filter(x => x && typeof x.text === 'string' && typeof x.done === 'boolean').slice(0, 60) : [];
  let backend = read(safeLocal, 'assent:backend', '') || window.ASSENT_ASSISTANT_CONFIG?.backend || '';
  let accessCode = read(safeSession, 'assent:access', '');
  let mode = 'guide', busy = false, controller, lastFocus, connecting;
  const routeMap = {
    'Dashboard': ['demo.html', '/index/index3/'], 'Upload a photo': ['upload.html', '/image/image/'],
    'Notifications': ['notifications.html', '/index/index4/'], 'My profile': ['profile.html', '/register/profile/'],
    'Messages': ['messages.html', '/login/messages/']
  };
  const setStatus = (text, nextMode) => { $('#connection-status').textContent = text; if (nextMode) mode = nextMode; };
  function endpoint(path) {
    const origin = backend || location.origin;
    const url = new URL(origin);
    if (url.username || url.password || url.search || url.hash || (url.pathname !== '/' && url.pathname !== '')) throw new Error('Use only the backend origin, without a path, query, or login details.');
    if (url.protocol !== 'https:' && !(url.protocol === 'http:' && ['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname))) throw new Error('Use an HTTPS backend URL. Localhost also works for local testing.');
    return new URL('/api/assistant/' + path + '/', url).href;
  }
  async function connect() {
    connecting?.abort(); connecting = new AbortController();
    const active = connecting;
    if (!backend && (location.hostname.endsWith('.github.io') || location.protocol === 'file:')) {
      setStatus('Site guide · GPT-7+ connection pending', 'guide'); return;
    }
    setStatus('Checking AI connection…', 'guide');
    const timer = setTimeout(() => active.abort(), 7000);
    try {
      const res = await fetch(endpoint('status'), { signal: active.signal, credentials: 'omit' });
      const status = await res.json();
      if (status.service === 'assenttag-assistant' && status.model_pending) { setStatus('Site guide · GPT-7+ connection pending', 'guide'); return; }
      if (!res.ok || status.service !== 'assenttag-assistant' || !status.configured) throw new Error('AI backend is not configured.');
      if (status.requires_code && !accessCode) { setStatus('Add your private access code in Connection', 'locked'); return; }
      setStatus('AI server connected · send a message', 'ai');
    } catch {
      if (connecting === active) setStatus('Site guide · AI backend unavailable', 'guide');
    } finally { clearTimeout(timer); }
  }
  function persistChat() {
    transcript = transcript.slice(-30);
    save(safeSession, storageKey + ':chat', transcript);
    if (!storageWorks) $('#save-status').textContent = 'Storage unavailable · this page only';
  }
  function addBubble(role, text) {
    const bubble = document.createElement('div'); bubble.className = 'bubble ' + role;
    const label = document.createElement('span'); label.className = 'bubble-label'; label.textContent = role === 'user' ? 'YOU' : role === 'error' ? 'CONNECTION NOTICE' : 'ASSENT';
    const content = document.createElement('p'); content.textContent = text;
    bubble.append(label, content); conversation.append(bubble); conversation.scrollTop = conversation.scrollHeight;
  }
  function renderChat() {
    conversation.replaceChildren();
    if (!transcript.length) {
      const welcome = document.createElement('div'); welcome.className = 'welcome';
      const kicker = document.createElement('span'); kicker.className = 'eyebrow'; kicker.textContent = 'A SPARK FOR YOUR EVERYDAY';
      const title = document.createElement('h2'); title.textContent = 'Big ideas. Small steps. Your space.';
      const desc = document.createElement('p'); desc.textContent = 'I’m Assent. Bring a question, a half-formed thought, or a plan for the day.';
      const links = document.createElement('div'); links.className = 'site-links';
      for (const [name, paths] of Object.entries(routeMap)) { const link = document.createElement('a'); link.textContent = name + ' ↗'; link.href = demo ? new URL(paths[0], location.href).href : paths[1]; links.append(link); }
      welcome.append(kicker, title, desc, links); conversation.append(welcome);
    } else for (const item of transcript) addBubble(item.role, item.content);
  }
  function guide(message) {
    if (/consent|upload|photo|tag|share/i.test(message)) return 'To share with consent: open Upload a photo, choose a photo, and follow the tag review steps. Notifications contains consent requests. ' + (demo ? 'This public preview uses sample data; real uploads and approvals require the full AssentTag app.' : 'Only share photos you have permission to use.');
    if (/task|plan|remind|day/i.test(message)) return 'Open My tasks to add, complete, and remove your next steps. Tasks stay on this device. I can help make a personalized plan once an AI backend is connected. Notifications do not run when this page is closed.';
    if (/profile|message|notification|help|how/i.test(message)) return 'Use the site navigation for Profile, Messages, Upload, and Notifications. I can explain the site here. For general questions, writing, and personal planning, open Connection to connect your AI backend.';
    return 'I’m in site-guide mode right now. I can explain AssentTag and keep a personal task list. GPT-7 or higher is required for AI chat here, and is not connected yet. Open Connection for details.';
  }
  function setBusy(value) {
    busy = value; $('.thinking').hidden = !value; $('.send').hidden = value; $('.stop').hidden = !value;
    input.disabled = value; $('.clear-chat').disabled = value; $('.connection-toggle').disabled = value;
    root.querySelectorAll('[data-prompt]').forEach(button => { button.disabled = value; });
  }
  async function send(message) {
    if (busy || !message.trim()) return;
    message = message.trim().slice(0, 2000);
    const history = transcript.filter(x => x.role !== 'error' && !x.guide).slice(-6).map(({ role, content }) => ({ role, content: content.slice(0, 2300) }));
    transcript.push({ role: 'user', content: message }); input.value = ''; renderChat(); persistChat();
    if (mode !== 'ai') {
      const reply = mode === 'locked' ? 'Enter your private assistant access code in Connection to start AI chat. Site navigation and My tasks remain available.' : guide(message);
      transcript[transcript.length - 1].guide = true;
      transcript.push({ role: 'assistant', content: reply, guide: true }); addBubble('assistant', reply); persistChat(); return;
    }
    setBusy(true); controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 45000);
    try {
      const res = await fetch(endpoint('chat'), { method: 'POST', credentials: 'omit', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', ...(accessCode ? { Authorization: 'Bearer ' + accessCode } : {}) },
        body: JSON.stringify({ message, history, page: document.body.dataset.atScene || 'unknown' }) });
      const data = await res.json();
      if (!res.ok || typeof data.reply !== 'string') throw new Error(data.error || 'AI could not reply. Please try again.');
      transcript.push({ role: 'assistant', content: data.reply }); addBubble('assistant', data.reply);
      setStatus('AI connected · ready when you are', 'ai');
    } catch (error) {
      const text = error.name === 'AbortError' ? (timedOut ? 'That took too long. Please try again.' : 'Reply stopped. You can send another message.') : error.message;
      transcript.push({ role: 'error', content: text }); addBubble('error', text);
      if (error.name !== 'AbortError') setStatus('AI connection needs attention');
    } finally { clearTimeout(timer); setBusy(false); persistChat(); if (!panel.hidden) input.focus(); }
  }
  function renderTasks() {
    const list = $('#task-list'); list.replaceChildren();
    $('#task-count').textContent = String(tasks.filter(task => !task.done).length);
    if (!tasks.length) { const empty = document.createElement('li'); empty.className = 'empty-tasks'; empty.textContent = 'A fresh page. What’s your first step?'; list.append(empty); }
    tasks.forEach((task, index) => {
      const row = document.createElement('li'), label = document.createElement('label'), check = document.createElement('input'), text = document.createElement('span'), remove = document.createElement('button');
      check.type = 'checkbox'; check.checked = task.done; text.textContent = task.text; label.append(check, text);
      remove.type = 'button'; remove.textContent = '×'; remove.setAttribute('aria-label', 'Delete task: ' + task.text);
      check.addEventListener('change', () => { task.done = check.checked; storeTasks(); });
      remove.addEventListener('click', () => { tasks.splice(index, 1); storeTasks(); renderTasks(); $('#task-input').focus(); });
      row.append(label, remove); list.append(row);
    });
  }
  function storeTasks() { save(safeLocal, storageKey + ':tasks', tasks); $('#task-count').textContent = String(tasks.filter(task => !task.done).length); if (!storageWorks) $('#task-note').textContent = 'Browser storage is unavailable. Tasks last only on this page.'; }
  function openPanel() { lastFocus = root.activeElement || $('.launcher'); panel.hidden = false; $('.launcher').setAttribute('aria-expanded', 'true'); ($('#chat-pane').hidden ? $('#task-input') : input).focus(); connect(); }
  function closePanel() { panel.hidden = true; $('.launcher').setAttribute('aria-expanded', 'false'); (lastFocus || $('.launcher')).focus(); }
  $('.launcher').addEventListener('click', () => panel.hidden ? openPanel() : closePanel());
  $('.close').addEventListener('click', closePanel);
  root.addEventListener('keydown', event => { if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); closePanel(); } });
  function chooseTab(tab) {
    for (const button of root.querySelectorAll('[role=tab]')) { const selected = button === tab; button.setAttribute('aria-selected', String(selected)); button.tabIndex = selected ? 0 : -1; $('#' + button.getAttribute('aria-controls')).hidden = !selected; }
    $('.connection').hidden = true;
  }
  for (const tab of root.querySelectorAll('[role=tab]')) {
    tab.addEventListener('click', () => chooseTab(tab));
    tab.addEventListener('keydown', event => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) { event.preventDefault(); const next = event.key === 'Home' ? $('#chat-tab') : event.key === 'End' ? $('#tasks-tab') : tab === $('#chat-tab') ? $('#tasks-tab') : $('#chat-tab'); chooseTab(next); next.focus(); } });
  }
  $('#chat-form').addEventListener('submit', event => { event.preventDefault(); send(input.value); });
  input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(input.value); } });
  $('.stop').addEventListener('click', () => controller?.abort());
  root.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => send(button.dataset.prompt)));
  $('.clear-chat').addEventListener('click', () => { transcript = []; persistChat(); chooseTab($('#chat-tab')); renderChat(); input.focus(); });
  $('#task-form').addEventListener('submit', event => { event.preventDefault(); const text = $('#task-input').value.trim(); if (!text) return; if (tasks.length >= 60) { $('#task-note').textContent = 'Your list has 60 tasks. Delete a task before adding another.'; return; } tasks.push({ text: text.slice(0, 160), done: false }); $('#task-input').value = ''; storeTasks(); renderTasks(); $('#task-input').focus(); });
  $('.connection-toggle').addEventListener('click', () => { $('.connection').hidden = !$('.connection').hidden; $('#backend-url').value = backend; $('#access-code').value = accessCode; if (!$('.connection').hidden) $('#backend-url').focus(); });
  $('.close-connection').addEventListener('click', () => { $('.connection').hidden = true; $('.connection-toggle').focus(); });
  $('#connection-form').addEventListener('submit', async event => {
    event.preventDefault(); const previous = backend; backend = $('#backend-url').value.trim();
    try { endpoint('status'); } catch (error) { backend = previous; $('#connection-feedback').textContent = error.message; return; }
    accessCode = $('#access-code').value.trim(); save(safeLocal, 'assent:backend', backend); save(safeSession, 'assent:access', accessCode);
    await connect(); $('#connection-feedback').textContent = $('#connection-status').textContent;
  });
  $('.reset-connection').addEventListener('click', () => { backend = ''; accessCode = ''; save(safeLocal, 'assent:backend', ''); save(safeSession, 'assent:access', ''); $('#backend-url').value = ''; $('#access-code').value = ''; $('#connection-feedback').textContent = 'Custom connection cleared.'; connect(); });
  renderChat(); renderTasks();
})();
