(()=> {
  const root = document.documentElement;
  const themes = ['light','sepia','dark'];
  const key = 'novel-reader:';
  const minSize = 14, maxSize = 38, step = 3;
  const storedSize = Number(localStorage.getItem(key+'size'));
  let size = Number.isFinite(storedSize) && storedSize > 0 ? Math.min(maxSize,Math.max(minSize,storedSize)) : 19;
  const indicator = document.getElementById('fontSizeValue');
  const down = document.getElementById('fontDown'), up = document.getElementById('fontUp');
  function applySize() {
    root.style.setProperty('--font',size+'px');
    if (indicator) indicator.textContent = size+'px';
    if (down) down.disabled = size <= minSize;
    if (up) up.disabled = size >= maxSize;
  }
  applySize();
  let theme = localStorage.getItem(key+'theme') || 'light';
  if (!themes.includes(theme)) theme = 'light';
  document.body.dataset.theme = theme;
  function change(direction) {
    size = Math.min(maxSize,Math.max(minSize,size + direction*step));
    applySize();
    localStorage.setItem(key+'size',String(size));
  }
  down?.addEventListener('click',()=>change(-1));
  up?.addEventListener('click',()=>change(1));
  document.getElementById('theme')?.addEventListener('click',()=>{
    theme = themes[(themes.indexOf(theme)+1)%themes.length];
    document.body.dataset.theme = theme;
    localStorage.setItem(key+'theme',theme);
  });

  if (/\/chapter-\d{4}(?:\/|\.html$)/.test(location.pathname)) {
    // A single reading-progress key works for clean URLs and old .html bookmarks.
    const chapterPath = location.pathname.replace(/\.html$/,'/').replace(/\/index\.html$/,'/');
    const newKey = key+'scroll:'+chapterPath;
    const legacyKey = key+'scroll:'+chapterPath.replace(/\/$/,'.html');
    const stored = Number(localStorage.getItem(newKey) ?? localStorage.getItem(legacyKey) ?? 0);
    const saved = Number.isFinite(stored) && stored > 0 ? stored : 0;
    const banner = document.getElementById('resumePrompt');
    const resume = document.getElementById('resumeReading');
    const start = document.getElementById('startReading');
    let hasStartedReading = false;

    // Do not let native history restoration bypass the reader's opt-in choice.
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    function startAtTop() { window.scrollTo({top:0,behavior:'instant'}); }
    startAtTop();
    addEventListener('pageshow', startAtTop);

    if (banner && saved >= 150) banner.hidden = false;
    function dismiss() { if (banner) banner.hidden = true; }
    resume?.addEventListener('click',()=>{
      dismiss();
      hasStartedReading = true;
      const maxScroll = Math.max(0,root.scrollHeight-innerHeight);
      window.scrollTo({top:Math.min(saved,maxScroll),behavior:'smooth'});
    });
    start?.addEventListener('click',()=>{
      dismiss();
      // Keep the saved point until the user actually starts reading again.
    });
    let last = 0;
    addEventListener('scroll',()=>{
      if (scrollY > 80) {
        hasStartedReading = true;
        dismiss();
      }
      if (!hasStartedReading) return;
      const now = Date.now();
      if (now-last > 400) {
        localStorage.setItem(newKey,String(Math.round(scrollY)));
        last = now;
      }
    },{passive:true});
    addEventListener('pagehide',()=>{
      if (hasStartedReading) localStorage.setItem(newKey,String(Math.round(scrollY)));
    });
  }
})();
