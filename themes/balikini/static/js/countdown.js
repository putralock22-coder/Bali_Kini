// Countdown & Push Notification system — Bali Kini
(function(){

// ── EVENT DATA (diupdate agent setiap pagi) ──
const EVENTS = [
  { name:'Hari Raya Galungan', date:'2026-06-17', icon:'🙏', color:'#eab308' },
  { name:'Hari Raya Kuningan', date:'2026-06-27', icon:'🙏', color:'#f59e0b' },
  { name:'Pesta Kesenian Bali XLVIII', date:'2026-06-13', icon:'🎨', color:'#22c55e' },
  { name:'Bali Kite Festival', date:'2026-06-06', icon:'🪁', color:'#06b6d4' },
  { name:'Jatiluwih Festival', date:'2026-07-18', icon:'🌾', color:'#a78bfa' },
  { name:'Lovina Festival', date:'2026-07-24', icon:'🐬', color:'#3b82f6' },
];

// ── INJECT COUNTDOWN SECTION ──
function buildCountdownSection(){
  const now = new Date();
  const upcoming = EVENTS
    .map(e => ({ ...e, ms: new Date(e.date) - now }))
    .filter(e => e.ms > -86400000)
    .sort((a,b) => a.ms - b.ms)
    .slice(0, 4);

  if(!upcoming.length) return;

  const lang = document.documentElement.lang || 'id';
  const i18n = {
    tag:  lang === 'en' ? 'Upcoming Events' : lang === 'zh' ? '即将到来' : 'Pengingat Event',
    h2:   lang === 'en' ? 'Coming <em>Soon</em>' : lang === 'zh' ? '即将 <em>举行</em>' : 'Segera <em>Datang</em>',
    desc: lang === 'en' ? 'Countdown to Bali\'s most important events & holy days this month.'
         : lang === 'zh' ? '巴厘岛本月最重要活动与节日倒计时。'
         : 'Hitung mundur event & hari raya Bali terpenting bulan ini.',
    today: lang === 'en' ? '🎉 Today!' : lang === 'zh' ? '🎉 今天！' : '🎉 Hari ini!',
    days:  lang === 'en' ? 'days'  : lang === 'zh' ? '天' : 'hari',
    hours: lang === 'en' ? 'hrs'   : lang === 'zh' ? '时' : 'jam',
    mins:  lang === 'en' ? 'min'   : lang === 'zh' ? '分' : 'menit',
    secs:  lang === 'en' ? 'sec'   : lang === 'zh' ? '秒' : 'detik',
  };

  const section = document.createElement('div');
  section.className = 'section reveal';
  section.id = 'countdown';
  section.innerHTML = `
    <div class="section-header">
      <div class="sec-tag">⏳ ${i18n.tag}</div>
      <h2 class="sec-title">${i18n.h2}</h2>
      <div class="divider"></div>
      <p class="sec-desc">${i18n.desc}</p>
    </div>
    <div class="cd-grid" id="cd-grid"></div>
  `;

  // Insert before footer
  const footer = document.querySelector('.site-footer');
  if(footer) footer.parentNode.insertBefore(section, footer);

  renderCards(upcoming);
  setInterval(() => renderCards(
    EVENTS.map(e=>({...e,ms:new Date(e.date)-new Date()}))
          .filter(e=>e.ms>-86400000).sort((a,b)=>a.ms-b.ms).slice(0,4)
  ), 1000);
}

function renderCards(events){
  const grid = document.getElementById('cd-grid');
  if(!grid) return;
  const lang = document.documentElement.lang || 'id';
  const locale = lang === 'en' ? 'en-GB' : lang === 'zh' ? 'zh-CN' : 'id-ID';
  const lbl = {
    today: lang === 'en' ? '🎉 Today!' : lang === 'zh' ? '🎉 今天！' : '🎉 Hari ini!',
    d: lang === 'en' ? 'days' : lang === 'zh' ? '天' : 'hari',
    h: lang === 'en' ? 'hrs'  : lang === 'zh' ? '时' : 'jam',
    m: lang === 'en' ? 'min'  : lang === 'zh' ? '分' : 'menit',
    s: lang === 'en' ? 'sec'  : lang === 'zh' ? '秒' : 'detik',
  };
  grid.innerHTML = events.map(e => {
    const ms = Math.max(0, e.ms);
    const days  = Math.floor(ms / 86400000);
    const hours = Math.floor((ms % 86400000) / 3600000);
    const mins  = Math.floor((ms % 3600000) / 60000);
    const secs  = Math.floor((ms % 60000) / 1000);
    const done  = e.ms <= 0;
    return `
      <div class="cd-card" style="border-color:${e.color}22;">
        <div class="cd-top" style="background:${e.color}18;border-bottom:1px solid ${e.color}22;">
          <span class="cd-icon">${e.icon}</span>
          <span class="cd-name">${e.name}</span>
        </div>
        <div class="cd-body">
          ${done ? `<div class="cd-today" style="color:${e.color};">${lbl.today}</div>` : `
          <div class="cd-units">
            <div class="cd-unit"><div class="cd-num" style="color:${e.color};">${String(days).padStart(2,'0')}</div><div class="cd-lbl">${lbl.d}</div></div>
            <div class="cd-sep">:</div>
            <div class="cd-unit"><div class="cd-num" style="color:${e.color};">${String(hours).padStart(2,'0')}</div><div class="cd-lbl">${lbl.h}</div></div>
            <div class="cd-sep">:</div>
            <div class="cd-unit"><div class="cd-num" style="color:${e.color};">${String(mins).padStart(2,'0')}</div><div class="cd-lbl">${lbl.m}</div></div>
            <div class="cd-sep">:</div>
            <div class="cd-unit"><div class="cd-num" style="color:${e.color};">${String(secs).padStart(2,'0')}</div><div class="cd-lbl">${lbl.s}</div></div>
          </div>`}
          <div class="cd-date">${new Date(e.date).toLocaleDateString(locale,{weekday:'long',day:'numeric',month:'long',year:'numeric'})}</div>
        </div>
      </div>
    `;
  }).join('');
}

// ── STYLES ──
const style = document.createElement('style');
style.textContent = `
.cd-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}
@media(min-width:640px){.cd-grid{grid-template-columns:repeat(4,1fr);}}
.cd-card{background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden;transition:all 0.25s;}
.cd-card:hover{transform:translateY(-3px);background:var(--card-hover);}
.cd-top{display:flex;align-items:center;gap:8px;padding:10px 14px;}
.cd-icon{font-size:18px;}
.cd-name{font-size:10px;font-weight:700;color:var(--text);letter-spacing:0.3px;line-height:1.3;}
.cd-body{padding:14px;}
.cd-units{display:flex;align-items:center;gap:4px;margin-bottom:8px;}
.cd-unit{text-align:center;}
.cd-num{font-family:'Lora',serif;font-size:1.4rem;font-weight:600;line-height:1;}
.cd-lbl{font-size:8px;color:var(--text-3);text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;}
.cd-sep{font-family:'Lora',serif;font-size:1.2rem;color:var(--text-3);margin-bottom:10px;padding:0 1px;}
.cd-date{font-size:9px;color:var(--text-3);line-height:1.4;}
.cd-today{font-family:'Lora',serif;font-size:1.3rem;font-weight:600;margin-bottom:8px;}

/* PUSH NOTIFICATION BANNER */
#push-banner{
  position:fixed;bottom:24px;right:24px;z-index:500;
  background:rgba(15,25,18,0.97);
  border:1px solid rgba(34,197,94,0.3);
  border-radius:16px;padding:18px 20px;
  max-width:300px;width:calc(100vw - 48px);
  box-shadow:0 20px 60px rgba(0,0,0,0.5);
  animation:slideUp 0.4s cubic-bezier(0.4,0,0.2,1);
  display:none;
}
#push-banner.show{display:block;}
@keyframes slideUp{from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:translateY(0);}}
#push-banner h4{font-size:13px;font-weight:700;color:#fff;margin-bottom:4px;}
#push-banner p{font-size:11px;color:#a3b8a8;line-height:1.5;margin-bottom:14px;}
#push-banner .pb-btns{display:flex;gap:8px;}
#push-yes{background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.3);color:#22c55e;padding:8px 16px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;transition:all 0.2s;flex:1;}
#push-yes:hover{background:rgba(34,197,94,0.25);}
#push-no{background:transparent;border:1px solid rgba(255,255,255,0.08);color:#5e7563;padding:8px 12px;border-radius:100px;font-size:11px;cursor:pointer;transition:all 0.2s;}
#push-no:hover{border-color:rgba(255,255,255,0.15);color:#a3b8a8;}
#push-close{position:absolute;top:10px;right:10px;background:none;border:none;color:#5e7563;font-size:14px;cursor:pointer;}
`;
document.head.appendChild(style);

// ── PUSH NOTIFICATION BANNER ──
function showPushBanner(){
  if(localStorage.getItem('bk_push_decided')) return;
  if(!('Notification' in window) || !('serviceWorker' in navigator)) return;
  if(Notification.permission === 'granted') return;

  const banner = document.createElement('div');
  banner.id = 'push-banner';
  banner.className = 'show';
  banner.innerHTML = `
    <button id="push-close">✕</button>
    <h4>🔔 Ingin update harian?</h4>
    <p>Aktifkan notifikasi — setiap pagi jam 7 WITA kamu dapat ringkasan data Bali terbaru langsung di browser.</p>
    <div class="pb-btns">
      <button id="push-yes">✓ Aktifkan</button>
      <button id="push-no">Nanti saja</button>
    </div>
  `;
  document.body.appendChild(banner);

  document.getElementById('push-yes').onclick = () => {
    Notification.requestPermission().then(p => {
      localStorage.setItem('bk_push_decided', '1');
      banner.remove();
      if(p === 'granted') {
        // OneSignal handles subscription automatically after permission
        showToast('✅ Notifikasi aktif! Kamu akan dapat update setiap pagi.');
      }
    });
  };
  document.getElementById('push-no').onclick = () => {
    localStorage.setItem('bk_push_decided', 'skip');
    banner.remove();
  };
  document.getElementById('push-close').onclick = () => {
    banner.remove();
  };
}

function showToast(msg){
  const t = document.createElement('div');
  t.style.cssText = 'position:fixed;bottom:80px;right:24px;z-index:600;background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.3);color:#22c55e;padding:10px 16px;border-radius:12px;font-size:12px;font-weight:600;animation:slideUp 0.3s ease;';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(()=>t.remove(), 4000);
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  buildCountdownSection();
  // Show push banner after 8 seconds
  setTimeout(showPushBanner, 8000);

  // Observe new reveal elements
  const io = new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible');});
  },{threshold:0.08});
  document.querySelectorAll('#countdown.reveal').forEach(el=>io.observe(el));
});

})();
