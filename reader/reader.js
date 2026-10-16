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

  // Free on-device/browser speech: no server, API key or audio upload.
  const ttsPanel = document.getElementById('ttsPanel');
  if (ttsPanel) {
    const synth = window.speechSynthesis;
    const supported = !!(synth && window.SpeechSynthesisUtterance);
    const toggle = document.getElementById('ttsToggle');
    const close = document.getElementById('ttsClose');
    const play = document.getElementById('ttsPlay');
    const pause = document.getElementById('ttsPause');
    const stop = document.getElementById('ttsStop');
    const status = document.getElementById('ttsStatus');
    const note = document.getElementById('ttsNote');
    const voicesSelect = document.getElementById('ttsVoice');
    const rateSelect = document.getElementById('ttsRate');
    const paragraphs = [...document.querySelectorAll('.reader article p, .reader article blockquote')]
      .filter(el => el.textContent.trim().length > 0);
    let thaiVoices = [], index = -1, part = 0, parts = [], active = false, paused = false, token = 0;
    const storedRate = localStorage.getItem(key+'tts-rate');
    if ([...rateSelect.options].some(option => option.value === storedRate)) rateSelect.value = storedRate;
    const statusText = text => { status.textContent = text; };
    const refreshButtons = () => {
      play.disabled = !supported || !paragraphs.length || (active && !paused);
      pause.disabled = !active;
      stop.disabled = !active;
      pause.textContent = paused ? '▶ ต่อ' : '⏸ พัก';
    };
    const clearHighlight = () => paragraphs.forEach(el => el.classList.remove('tts-active'));
    const setHighlight = () => {
      clearHighlight();
      if (paragraphs[index]) {
        paragraphs[index].classList.add('tts-active');
        paragraphs[index].scrollIntoView({behavior:'smooth',block:'center'});
      }
    };
    // Short utterances avoid engines stalling on long Thai paragraphs.
    const splitText = text => {
      const result = [];
      let rest = text.trim();
      while (rest.length > 220) {
        const windowText = rest.slice(0,220);
        const cut = Math.max(windowText.lastIndexOf(' '),windowText.lastIndexOf('।'),windowText.lastIndexOf('ฯ'),windowText.lastIndexOf('。'));
        const n = cut > 95 ? cut + 1 : 220;
        result.push(rest.slice(0,n).trim());
        rest = rest.slice(n).trim();
      }
      if (rest) result.push(rest);
      return result;
    };
    const reset = (message='หยุดอ่านแล้ว') => {
      token++;
      active = false; paused = false; index = -1; part = 0; parts = [];
      if (supported) synth.cancel();
      clearHighlight();
      statusText(message);
      refreshButtons();
    };
    const speakNext = myToken => {
      if (!active || myToken !== token) return;
      if (index >= paragraphs.length) { reset('อ่านจบตอนแล้ว'); return; }
      if (part >= parts.length) {
        index++; part = 0;
        if (index >= paragraphs.length) { reset('อ่านจบตอนแล้ว'); return; }
        parts = splitText(paragraphs[index].textContent);
        setHighlight();
      }
      const utterance = new SpeechSynthesisUtterance(parts[part]);
      utterance.lang = 'th-TH';
      utterance.rate = Number(rateSelect.value) || 1;
      const voice = thaiVoices.find(v => v.voiceURI === voicesSelect.value);
      if (voice) utterance.voice = voice;
      utterance.onstart = () => { if (myToken === token) statusText('กำลังอ่านย่อหน้า '+(index+1)+' / '+paragraphs.length); };
      utterance.onend = () => {
        if (!active || myToken !== token) return;
        part++;
        speakNext(myToken);
      };
      utterance.onerror = event => {
        if (myToken !== token) return;
        reset('เสียงอ่านขัดข้อง: '+(event.error || 'ไม่ทราบสาเหตุ'));
      };
      synth.speak(utterance);
    };
    const loadVoices = () => {
      if (!supported) return;
      const old = voicesSelect.value || localStorage.getItem(key+'tts-voice') || '';
      thaiVoices = synth.getVoices().filter(voice => /^th([_-]|$)/i.test(voice.lang)).slice(0,3);
      voicesSelect.replaceChildren(new Option('เสียงเริ่มต้นของอุปกรณ์',''));
      for (const voice of thaiVoices) voicesSelect.add(new Option(voice.name,voice.voiceURI));
      if (thaiVoices.some(v => v.voiceURI === old)) voicesSelect.value = old;
      note.textContent = thaiVoices.length
        ? 'พบเสียงภาษาไทย '+thaiVoices.length+' เสียง · ใช้เสียงของเบราว์เซอร์/อุปกรณ์'
        : 'ไม่พบเสียงภาษาไทยให้เลือก จะลองใช้เสียงเริ่มต้นของอุปกรณ์';
    };
    if (supported) {
      loadVoices();
      synth.addEventListener?.('voiceschanged',loadVoices);
      voicesSelect.addEventListener('change',() => localStorage.setItem(key+'tts-voice',voicesSelect.value));
      rateSelect.addEventListener('change',() => localStorage.setItem(key+'tts-rate',rateSelect.value));
    } else {
      note.textContent = 'เบราว์เซอร์นี้ไม่รองรับการอ่านออกเสียง กรุณาลอง Chrome, Edge หรือ Safari';
      statusText('ไม่รองรับการอ่านออกเสียง');
    }
    toggle?.addEventListener('click',() => {
      ttsPanel.hidden = !ttsPanel.hidden;
      toggle.setAttribute('aria-expanded',String(!ttsPanel.hidden));
    });
    close?.addEventListener('click',() => {
      ttsPanel.hidden = true;
      toggle?.setAttribute('aria-expanded','false');
    });
    play.addEventListener('click',() => {
      if (!supported || !paragraphs.length) return;
      if (active && paused) {
        paused = false; synth.resume(); statusText('กำลังอ่านต่อ'); refreshButtons(); return;
      }
      if (active) return;
      // Start at the paragraph currently visible, or the first paragraph.
      index = paragraphs.findIndex(el => el.getBoundingClientRect().bottom > 120);
      if (index < 0) index = 0;
      part = 0; parts = splitText(paragraphs[index].textContent);
      active = true; paused = false;
      const currentToken = ++token;
      setHighlight(); refreshButtons(); speakNext(currentToken);
    });
    pause.addEventListener('click',() => {
      if (!active || !supported) return;
      if (paused) { paused = false; synth.resume(); statusText('กำลังอ่านต่อ'); }
      else { paused = true; synth.pause(); statusText('พักการอ่าน'); }
      refreshButtons();
    });
    stop.addEventListener('click',() => reset());
    addEventListener('pagehide',() => { if (active) reset(); });
    refreshButtons();
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
