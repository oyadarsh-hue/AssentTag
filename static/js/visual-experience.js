/* Progressive enhancement: all content is visible without this script. */
(() => {
  'use strict';
  const body = document.body;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  body.classList.add('at-experience');
  const pagePhoto = body.dataset.atPhoto;
  if (pagePhoto && /^\/static\/assets\/[\w-]+\.webp$/.test(pagePhoto)) {
    body.style.setProperty('--at-art', `url("${pagePhoto}")`);
  }
  const backdrop = document.createElement('div');
  backdrop.className = 'at-backdrop'; backdrop.setAttribute('aria-hidden', 'true');
  body.prepend(backdrop);
  if (body.dataset.atScene === 'index' || body.dataset.atScene === 'dashboard') {
    const layers = [0, 1].map(() => {
      const layer = document.createElement('div'); layer.className = 'at-scene-layer'; backdrop.append(layer); return layer;
    });
    let active = 0;
    let sequence = 0;
    let currentImage = '';
    const showScene = url => {
      if (url === currentImage) return;
      currentImage = url;
      const request = ++sequence;
      const photo = new Image();
      photo.onload = () => {
        if (request !== sequence) return;
        const next = 1 - active;
        layers[next].style.backgroundImage = `url("${url}")`;
        layers[next].classList.add('is-active'); layers[active].classList.remove('is-active'); active = next;
      };
      photo.src = url;
    };
    const initialPhoto = pagePhoto || document.querySelector('.hero-section')?.dataset.workflowImage || '/static/assets/photo-dashboard.webp';
    showScene(initialPhoto);
    if ('IntersectionObserver' in window) {
      const scenes = new IntersectionObserver(entries => {
        const visible = entries.filter(entry => entry.isIntersecting);
        if (!visible.length) return;
        visible.sort((a, b) => Math.abs(a.boundingClientRect.top - innerHeight / 3) - Math.abs(b.boundingClientRect.top - innerHeight / 3));
        const target = visible[0].target;
        showScene(target.dataset.workflowImage || initialPhoto);
      }, { rootMargin:'-20% 0px -35% 0px', threshold:0 });
      document.querySelectorAll('[data-workflow-image], .hero-section').forEach(el => scenes.observe(el));
    }
  }
  const progress = document.createElement('div');
  progress.className = 'at-page-progress'; progress.setAttribute('aria-hidden', 'true');
  body.append(progress);
  const visiblePhotos = new Set();
  let scheduled = false;
  const updateProgress = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.setProperty('--at-progress', max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0);
    if (!reducedMotion.matches) {
      backdrop.style.setProperty('--at-scroll-drift', `${Math.min(26, window.scrollY * .025)}px`);
      for (const card of visiblePhotos) {
        const rect = card.getBoundingClientRect();
        const position = (innerHeight / 2 - rect.top - rect.height / 2) / (innerHeight / 2 + rect.height / 2);
        card.style.setProperty('--at-photo-shift', `${Math.max(-20, Math.min(20, position * 20)).toFixed(2)}px`);
      }
    }
    scheduled = false;
  };
  window.addEventListener('scroll', () => {
    if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); }
  }, { passive: true });
  window.addEventListener('resize', updateProgress); updateProgress();
  if ('IntersectionObserver' in window) {
    const photoObserver = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) visiblePhotos.add(entry.target);
        else visiblePhotos.delete(entry.target);
      }
      if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); }
    }, { rootMargin:'100px 0px', threshold:0 });
    document.querySelectorAll('.at-dashboard-scene').forEach(card => photoObserver.observe(card));
  }
  const themeButton = document.querySelector('.toggle-btn');
  const syncThemeButton = () => {
    if (!themeButton) return;
    const light = body.classList.contains('light-mode');
    themeButton.setAttribute('aria-pressed', String(light));
    themeButton.setAttribute('aria-label', light ? 'Switch to dark theme' : 'Switch to light theme');
    themeButton.title = light ? 'Switch to dark theme' : 'Switch to light theme';
    const icon = themeButton.querySelector('i');
    if (icon) icon.className = light ? 'fas fa-sun' : 'fas fa-moon';
  };
  syncThemeButton();
  themeButton?.addEventListener('click', () => requestAnimationFrame(syncThemeButton));
  const headingSelector = 'h1,h2,h3,.panel-heading,.profile-name,.section-title,.cap-title,.universe-title';
  const selector = `section, .feature-box, .feature-card, .glass-panel, .post-card, .profile-card, .form-card, .otp-card, .auth-container, .stat-card, .cap-block, .notification-card, .contact-item, .at-pathway, .at-step, .at-workflow-chapter, ${headingSelector}, footer`;
  const prepareHeading = el => {
    if (reducedMotion.matches || !el.matches(headingSelector) || el.dataset.atWordsReady || el.matches('.ghost-text-content,[contenteditable]')) return;
    el.dataset.atWordsReady = 'true'; el.classList.add('at-heading-motion');
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: node => node.textContent.trim() && !node.parentElement.closest('.at-word,i,script,style,[aria-hidden="true"]') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
    });
    const nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
    let count = 0;
    for (const node of nodes) {
      const fragment = document.createDocumentFragment();
      for (const word of node.textContent.split(/(\s+)/)) {
        if (!word.trim()) { fragment.append(document.createTextNode(word)); continue; }
        const span = document.createElement('span'); span.className = 'at-word'; span.textContent = word;
        span.style.setProperty('--at-word-delay', `${Math.min(count++ * 55, 440)}ms`); fragment.append(span);
      }
      node.replaceWith(fragment);
    }
  };
  if ('IntersectionObserver' in window) {
    const observed = new WeakSet();
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        const heading = entry.target.matches(headingSelector);
        const replayPhoto = entry.target.matches('.at-dashboard-scene');
        if (!entry.isIntersecting) {
          if (heading) entry.target.classList.remove('at-text-visible');
          if (replayPhoto) entry.target.classList.remove('at-revealed');
          continue;
        }
        if (!reducedMotion.matches) {
          entry.target.classList.add('at-revealed');
          if (heading) entry.target.classList.add('at-text-visible');
        }
        // Headings remain observed so their word reveal replays on returning.
        if (!heading && !replayPhoto) observer.unobserve(entry.target);
      }
    }, { threshold: .08 });
    const watch = root => {
      const elements = [...(root.matches?.(selector) ? [root] : []), ...root.querySelectorAll(selector)];
      elements.forEach((el, index) => {
        if (observed.has(el)) return;
        observed.add(el); prepareHeading(el); el.style.setProperty('--at-delay', `${Math.min(index % 5 * 65, 260)}ms`); observer.observe(el);
      });
    };
    watch(body);
    new MutationObserver(records => {
      for (const record of records) for (const node of record.addedNodes) if (node.nodeType === 1) watch(node);
      updateProgress();
    }).observe(body, { childList:true, subtree:true });
  }
  const openComments = (panel, focus = true) => {
    panel.hidden = false;
    document.querySelector(`[data-comments="${panel.id}"]`)?.setAttribute('aria-expanded', 'true');
    panel.scrollIntoView({behavior: reducedMotion.matches ? 'instant' : 'smooth', block:'center'});
    if (focus) panel.querySelector('input[name="comment"]')?.focus({preventScroll:true});
  };
  document.querySelectorAll('[data-comments]').forEach(button => {
    button.addEventListener('click', () => {
      const panel = document.getElementById(button.dataset.comments);
      if (!panel) return;
      if (panel.hidden) openComments(panel);
      else { panel.hidden = true; button.setAttribute('aria-expanded','false'); }
    });
  });
  const followCommentLink = () => {
    if (!/^#comments-\d+$/.test(location.hash)) return;
    const panel = document.getElementById(location.hash.slice(1));
    if (panel) openComments(panel, false);
  };
  followCommentLink();
  window.addEventListener('hashchange', followCommentLink);
})();
