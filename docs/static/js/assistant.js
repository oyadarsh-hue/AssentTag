/* The shared Assent launcher opens the full private workspace. */
(() => {
  'use strict';
  const script = document.querySelector('script[data-assent-assistant]');
  if (!script || document.querySelector('[data-at-assistant]')) return;
  let destination;
  try {
    destination = new URL(window.ASSENT_ASSISTANT_CONFIG?.workspace || 'http://127.0.0.1:8040/');
    const local = ['127.0.0.1', 'localhost', '[::1]'].includes(destination.hostname);
    if (destination.username || destination.password || (destination.protocol !== 'https:' && !(local && destination.protocol === 'http:'))) throw new Error('Invalid workspace address');
  } catch { destination = new URL('http://127.0.0.1:8040/'); }
  const host = document.createElement('div');
  host.dataset.atAssistant = '';
  if (script.dataset.siteMode === 'preview') host.dataset.preview = '';
  const root = host.attachShadow({mode: 'open'});
  const styles = document.createElement('link');
  styles.rel = 'stylesheet';
  styles.href = new URL('../css/assistant.css?v=3', script.src).href;
  const launcher = document.createElement('a');
  launcher.className = 'launcher';
  launcher.href = destination.href;
  launcher.rel = 'noreferrer';
  launcher.setAttribute('aria-label', 'Open Assent private workspace');
  launcher.title = 'Open your full private workspace on this computer';
  const orb = document.createElement('span');
  orb.className = 'orb'; orb.setAttribute('aria-hidden', 'true');
  for (let n = 0; n < 9; n++) orb.append(document.createElement('i'));
  const copy = document.createElement('span'); copy.className = 'launcher-copy';
  copy.append(document.createTextNode('Ask Assent'));
  const subtitle = document.createElement('small'); subtitle.textContent = 'Your personal space'; copy.append(subtitle);
  const arrow = document.createElement('span'); arrow.className = 'launcher-arrow'; arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true');
  launcher.append(orb, copy, arrow);
  root.append(styles, launcher);
  document.body.append(host);
})();
