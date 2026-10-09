/* Backend-only adapter. Original templates, layout, inline animations and shared
   visual-experience.js remain intact. App actions are simulated. The assistant
   may connect to its separately configured real API with the user's chat text. */
(() => {
  'use strict';
  const page = location.pathname.split('/').pop() || 'index.html';
  const aliases={feed:'demo.html',login:'login.html',register:'register.html',profile:'profile.html',explore:'explore.html',notifications:'notifications.html',upload:'upload.html'};
  if(page==='demo.html' && aliases[location.hash.slice(1)] && location.hash!=='#feed') location.replace(aliases[location.hash.slice(1)]);
  const people=[{register_id:2,first_name:'Maya',last_name:'River',email:'maya@example.com',photo:'assets/user_icon.svg'}, {register_id:3,first_name:'Alex',last_name:'Stone',email:'alex@example.com',photo:'assets/user_icon.svg'}];
  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input, options) => {
    const url=String(input?.url || input);
    if(new URL(url, location.href).pathname.startsWith('/api/assistant/')) return nativeFetch(input, options);
    let data={status:'demo',message:'UI preview only. No server action was performed.'};
    if(url.includes('ajax_user_posts'))data={posts:[{url:'static/assets/photo-index-hero-v2.webp',caption:'A moment shared thoughtfully.'},{url:'static/assets/photo-consent.webp',caption:'Every face has a say.'},{url:'static/assets/page-stories.webp',caption:'Sample story'}]};
    if(url.includes('get_likers'))data={status:'success',likers:people};
    return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
  };
  if(navigator.mediaDevices) navigator.mediaDevices.getUserMedia=()=>Promise.reject(new Error('Camera is disabled in the static UI preview.'));
  const tell = text => {
    let el=document.querySelector('.demo-toast');
    if(!el){el=document.createElement('div');el.className='demo-toast';el.setAttribute('role','status');document.body.append(el);}
    el.textContent=text;clearTimeout(tell.timer);tell.timer=setTimeout(()=>el.remove(),4500);
  };
  document.addEventListener('click',e=>{
    const action=e.target.closest('a[href^="#demo-action"], [onclick*="deactivateAccount"], [onclick*="initiateScorchedEarth"], [onclick*="confirmDelete"]');
    const camera=e.target.closest('#start-camera-btn, #snap-btn, #verifyBtn');
    const file=e.target.closest('input[type=file]');
    if(camera||file){
      e.preventDefault();e.stopImmediatePropagation();
      if(camera?.id==='verifyBtn'){
        document.querySelector('#authActions').style.display='none';document.querySelector('#decisionActions').style.display='flex';
        document.querySelector('#statusMessage').textContent='Sample review screen · No identity verification performed.';
      } else tell('UI preview: camera and uploads are disabled. Explore the original layout using sample content.');
      return;
    }
    if(action){
      e.preventDefault();e.stopImmediatePropagation();
      if(action.matches('.interaction-btn.like')){
        const liked=action.classList.toggle('is-liked');action.querySelector('i').className=(liked?'fas':'far')+' fa-heart';
        action.setAttribute('aria-label',liked?'Unlike post':'Like post');
        const count=action.closest('.post-card').querySelector('.likes-count');
        count.textContent=(parseInt(count.textContent)+(liked?1:-1))+' likes';
      } else if(action.getAttribute('href')?.includes('approve-tag')||action.getAttribute('href')?.includes('reject-tag')) {
        tell('Sample consent decision selected. No real image was changed.');
      } else tell('UI preview only. No account, connection or photo was changed.');
    }
  },true);
  document.addEventListener('submit',e=>{
    if(e.target.matches('#message-form,#timer-form') || e.target.closest('[data-at-assistant]'))return;
    e.preventDefault();e.stopImmediatePropagation();
    if(page==='login.html'){location.href=e.target.querySelector('[name=role]')?.value==='admin'?'admin.html':'demo.html';return;}
    if(page==='register.html'){tell('Registration layout preview. Use Dashboard in the preview notice to explore.');return;}
    const input=e.target.querySelector('[name=comment]');
    if(input?.value.trim()){
      const p=document.createElement('p');p.textContent='Jamie: '+input.value.trim();p.style.cssText='color:inherit;padding:12px 25px;overflow-wrap:anywhere';
      e.target.before(p);input.value='';
      e.target.closest('.at-comments')?.querySelector('.at-comments-empty')?.remove();
    }
    tell('Preview only. Nothing was submitted to a server.');
  },true);
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelectorAll('input[type=file]').forEach(el=>el.removeAttribute('required'));
    if(page==='register.html')document.querySelector('#start-camera-btn')?.removeAttribute('disabled');
  });
})();
