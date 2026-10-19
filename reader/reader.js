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

  // Light deterrent for casual copying of chapter prose; not content access control.
  const prose = document.querySelector('.reader article');
  if (prose) {
    for (const type of ['copy','cut','contextmenu','dragstart']) {
      prose.addEventListener(type,(event)=>event.preventDefault());
    }
  }

  // Stream pre-generated MP3; no browser speech synthesis or TTS API.
  const audioPanel = document.getElementById('audioPanel');
  const audio = document.getElementById('chapterAudio');
  if (audioPanel && audio) {
    const toggle = document.getElementById('audioToggle');
    const close = document.getElementById('audioClose');
    const rate = document.getElementById('audioRate');
    const status = document.getElementById('audioStatus');
    const playButton = document.getElementById('audioPlay');
    const backButton = document.getElementById('audioBack');
    const forwardButton = document.getElementById('audioForward');
    const seek = document.getElementById('audioSeek');
    const currentLabel = document.getElementById('audioCurrent');
    const durationLabel = document.getElementById('audioDuration');
    const formatTime = seconds => {
      if (!Number.isFinite(seconds)) return '0:00';
      const value = Math.floor(seconds);
      return Math.floor(value / 60)+':'+String(value % 60).padStart(2,'0');
    };
    const syncPlayer = () => {
      const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
      seek.value = duration ? String(Math.round(audio.currentTime / duration * 1000)) : '0';
      currentLabel.textContent = formatTime(audio.currentTime);
      durationLabel.textContent = formatTime(duration);
      playButton.textContent = audio.paused ? '▶' : 'Ⅱ';
      playButton.setAttribute('aria-label',audio.paused ? 'เล่นเสียง' : 'พักเสียง');
    };
    playButton.addEventListener('click',()=> {
      if (audio.paused) audio.play().catch(()=>{status.textContent='ไม่สามารถเล่นเสียงได้';});
      else audio.pause();
    });
    backButton.addEventListener('click',()=> { audio.currentTime = Math.max(0,audio.currentTime-10); });
    forwardButton.addEventListener('click',()=> { if (Number.isFinite(audio.duration)) audio.currentTime=Math.min(audio.duration,audio.currentTime+10); });
    seek.addEventListener('input',()=> { if (Number.isFinite(audio.duration)) audio.currentTime=audio.duration*Number(seek.value)/1000; });
    for (const eventName of ['loadedmetadata','timeupdate','play','pause','seeking','ended']) audio.addEventListener(eventName,syncPlayer);
    audio.addEventListener('contextmenu',event=>event.preventDefault());
    const playbackKey = key+'audio:'+location.pathname.replace(/index\.html$/,'').replace(/\.html$/,'/');
    const saved = Number(localStorage.getItem(playbackKey) || 0);
    const storedRate = localStorage.getItem(key+'audio-rate') || '1';
    if ([...rate.options].some(option => option.value === storedRate)) rate.value = storedRate;
    audio.playbackRate = Number(rate.value);
    rate.addEventListener('change',()=> {
      audio.playbackRate = Number(rate.value);
      localStorage.setItem(key+'audio-rate',rate.value);
    });
    let restored = false;
    audio.addEventListener('loadedmetadata',()=> {
      if (!restored && Number.isFinite(saved) && saved > 0 && saved < audio.duration-3) audio.currentTime = saved;
      restored = true;
    });
    let lastSave = 0;
    audio.addEventListener('timeupdate',()=> {
      const now = Date.now();
      if (now-lastSave > 1500 && Number.isFinite(audio.currentTime)) {
        localStorage.setItem(playbackKey,String(audio.currentTime));
        lastSave = now;
      }
    });
    audio.addEventListener('ended',()=> {
      localStorage.removeItem(playbackKey);
      status.textContent = 'ฟังจบตอนแล้ว';
    });
    audio.addEventListener('error',()=> {status.textContent = 'ไม่สามารถโหลดไฟล์เสียงได้';});
    addEventListener('pagehide',()=> {
      if (audio.ended) return;
      if (Number.isFinite(audio.currentTime)) localStorage.setItem(playbackKey,String(audio.currentTime));
    });
    toggle?.addEventListener('click',()=> {
      audioPanel.hidden = !audioPanel.hidden;
      toggle.setAttribute('aria-expanded',String(!audioPanel.hidden));
    });
    close?.addEventListener('click',()=> {
      audioPanel.hidden = true;
      toggle?.setAttribute('aria-expanded','false');
    });
    if ('mediaSession' in navigator && typeof MediaMetadata !== 'undefined') {
      navigator.mediaSession.metadata = new MediaMetadata({title:document.title,artist:'Novel Reader'});
    }
  }

  const picker = document.getElementById('chapterPicker');
  const pickerButton = document.getElementById('openChapterPicker');
  const chapterSearch = document.getElementById('chapterSearch');
  const resultLinks = [...(document.querySelectorAll('#chapterResults .picker-chapter') || [])];
  const emptyMessage = document.getElementById('chapterEmpty');
  pickerButton?.addEventListener('click',()=>{
    if (!picker) return;
    picker.showModal();
    if (chapterSearch) {
      chapterSearch.value = '';
      chapterSearch.dispatchEvent(new Event('input'));
      chapterSearch.focus();
    }
    document.querySelector('.picker-chapter.current')?.scrollIntoView({block:'nearest'});
  });
  chapterSearch?.addEventListener('input',()=>{
    const term = chapterSearch.value.trim().toLocaleLowerCase('th');
    let visible = 0;
    for (const link of resultLinks) {
      const match = link.textContent.toLocaleLowerCase('th').includes(term);
      link.hidden = !match;
      if (match) visible++;
    }
    if (emptyMessage) emptyMessage.hidden = visible !== 0;
  });
  picker?.addEventListener('click',(event)=>{
    if (event.target === picker) picker.close();
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
