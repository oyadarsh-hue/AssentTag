/* Local, accessible success feedback survives server redirects without a CDN. */
(() => {
  'use strict';
  const queue = [];
  let showing = false;
  const titles = { login:'Login successful', 'admin-login':'Admin login successful', registration:'Registration successful', profile:'Profile updated', upload:'Photo shared', post:'Post published', feedback:'Feedback received', complaint:'Report submitted', verification:'Verified successfully' };
  const showNext = () => {
    if (showing || !queue.length) return;
    showing = true;
    const item = queue.shift();
    const dialog = document.createElement('dialog');
    dialog.className = 'at-success-dialog';
    dialog.setAttribute('aria-labelledby','at-success-title');
    dialog.setAttribute('aria-describedby','at-success-message');
    dialog.innerHTML = '<button type="button" class="at-success-close" aria-label="Close success notification">×</button><div class="at-success-brand"><img src="static/assets/assenttag-logo.png" alt="" width="30" height="30"><span>AssentTag</span></div><div class="at-success-symbol" aria-hidden="true"><svg viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="19" stroke="currentColor" stroke-width="2"/><path d="m14 24 7 7 14-15" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></div><p class="at-success-eyebrow">All set</p><h2 id="at-success-title"></h2><p id="at-success-message"></p><button type="button" class="at-success-confirm" autofocus>Continue</button>';
    dialog.querySelector('#at-success-title').textContent = item.title;
    dialog.querySelector('#at-success-message').textContent = item.message;
    if (item.tags.includes('registration')) dialog.querySelector('.at-success-confirm').textContent = 'Continue to login';
    const finish = () => dialog.close();
    dialog.querySelector('.at-success-close').addEventListener('click',finish);
    dialog.querySelector('.at-success-confirm').addEventListener('click',finish);
    dialog.addEventListener('click',event => {
      const rect = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) finish();
    });
    dialog.addEventListener('close',() => {
      document.body.classList.remove('at-success-open');
      dialog.remove(); showing = false;
      if (item.redirect.startsWith('/') && !item.redirect.startsWith('//')) location.assign(item.redirect);
      else showNext();
    },{once:true});
    document.body.append(dialog);
    document.body.classList.add('at-success-open');
    dialog.showModal();
  };
  const success = (message, options = {}) => {
    const tags = String(options.tags || '').split(/\s+/);
    const title = options.title || tags.map(tag => titles[tag]).find(Boolean) || 'Completed successfully';
    queue.push({message:String(message),title:String(title),tags,redirect:String(options.redirect || '')});
    showNext();
  };
  window.AssentTagNotice = Object.freeze({success});
  document.querySelectorAll('.at-success-data').forEach(data => {
    success(data.dataset.message, {title:data.dataset.title,tags:data.dataset.tags,redirect:data.dataset.redirect});
    data.remove();
  });
})();
