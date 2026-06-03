// Modal & Chart system for Bali Kini
(function(){

// ── CREATE MODAL DOM ──
const overlay = document.createElement('div');
overlay.id = 'modal-overlay';
overlay.innerHTML = `
  <div id="modal-box">
    <button id="modal-close">✕</button>
    <div id="modal-title"></div>
    <div id="modal-sub"></div>
    <div id="modal-chart-wrap"><canvas id="modal-chart"></canvas></div>
    <div id="modal-stats"></div>
    <div id="modal-src"></div>
  </div>
`;
document.body.appendChild(overlay);

// ── STYLES ──
const style = document.createElement('style');
style.textContent = `
#modal-overlay{
  display:none;position:fixed;inset:0;z-index:999;
  background:rgba(7,12,9,0.85);backdrop-filter:blur(12px);
  align-items:center;justify-content:center;padding:20px;
}
#modal-overlay.open{display:flex;}
#modal-box{
  background:rgba(15,25,18,0.97);
  border:1px solid rgba(255,255,255,0.1);
  border-radius:20px;padding:32px;
  max-width:640px;width:100%;
  position:relative;
  box-shadow:0 40px 80px rgba(0,0,0,0.6),inset 0 1px 0 rgba(255,255,255,0.08);
  animation:modalIn 0.25s cubic-bezier(0.4,0,0.2,1);
}
@keyframes modalIn{from{opacity:0;transform:scale(0.95) translateY(16px);}to{opacity:1;transform:none;}}
#modal-close{
  position:absolute;top:16px;right:16px;
  background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
  color:#a3b8a8;font-size:14px;width:30px;height:30px;border-radius:50%;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all 0.2s;
}
#modal-close:hover{background:rgba(239,68,68,0.15);color:#ef4444;border-color:#ef4444;}
#modal-title{font-family:'Lora',serif;font-size:1.5rem;font-weight:600;color:#fff;margin-bottom:4px;}
#modal-sub{font-size:12px;color:#5e7563;margin-bottom:20px;}
#modal-chart-wrap{position:relative;height:220px;margin-bottom:20px;}
#modal-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;}
.ms{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:12px;}
.ms-val{font-family:'Lora',serif;font-size:1.2rem;font-weight:600;color:#fff;}
.ms-lbl{font-size:10px;color:#5e7563;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;}
#modal-src{font-size:10px;color:#5e7563;border-top:1px solid rgba(255,255,255,0.06);padding-top:12px;}
.kpi[data-modal]{cursor:pointer;}
.kpi[data-modal]:hover{border-color:rgba(34,197,94,0.3);}
.kpi[data-modal]::after{
  content:'📊 Lihat grafik';
  display:block;font-size:9px;color:#22c55e;margin-top:8px;
  font-weight:700;letter-spacing:0.5px;
}
`;
document.head.appendChild(style);

// ── CHART DATA ──
const charts = {
  wisman_jan_apr: {
    title: 'Wisman ke Bali — Tren Bulanan',
    sub: 'Perbandingan 2025 vs 2026 · Sumber: BPS Bali',
    type: 'line',
    data: {
      labels: ['Jan','Feb','Mar','Apr'],
      datasets: [
        {label:'2026',data:[484270,479160,502934,553328],borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,0.08)',tension:0.4,fill:true,pointRadius:5,pointBackgroundColor:'#22c55e'},
        {label:'2025',data:[536474,495232,506186,590253],borderColor:'rgba(255,255,255,0.2)',backgroundColor:'transparent',tension:0.4,borderDash:[4,4],pointRadius:4,pointBackgroundColor:'rgba(255,255,255,0.3)'}
      ]
    },
    stats:[
      {val:'2,02 Jt',lbl:'Total Jan–Apr 2026'},
      {val:'↓1,11%',lbl:'vs Jan–Apr 2025'},
      {val:'553K',lbl:'April 2026 (tertinggi)'}
    ],
    src:'BPS Bali, Mei 2026 · Antara Bali'
  },
  wisman_apr: {
    title: 'Asal Wisman — April 2026',
    sub: 'Top 5 negara asal wisatawan mancanegara · BPS Bali',
    type: 'bar',
    data: {
      labels: ['🇦🇺 Australia','🇮🇳 India','🇨🇳 Tiongkok','🇰🇷 Korea','🇬🇧 Inggris'],
      datasets: [{
        label:'Kunjungan April 2026',
        data:[146414,46513,44447,28000,22000],
        backgroundColor:['#22c55e','#f59e0b','#3b82f6','#a78bfa','#06b6d4'],
        borderRadius:8,borderSkipped:false
      }]
    },
    stats:[
      {val:'146K',lbl:'Australia (↑22,24%)'},
      {val:'46K',lbl:'India (↑9,55%)'},
      {val:'553K',lbl:'Total April 2026'}
    ],
    src:'BPS Bali, April 2026'
  },
  phr: {
    title: 'Pajak Hotel & Restoran (PHR) 2026',
    sub: 'Realisasi pendapatan PHR Bali Jan–Mei 2026',
    type: 'bar',
    data: {
      labels: ['Jan','Feb','Mar','Apr','Mei'],
      datasets: [
        {label:'2026 (Rp Miliar)',data:[480,510,620,590,700],backgroundColor:'rgba(34,197,94,0.7)',borderRadius:8,borderSkipped:false},
        {label:'2025 (Rp Miliar)',data:[450,480,580,560,630],backgroundColor:'rgba(255,255,255,0.08)',borderRadius:8,borderSkipped:false}
      ]
    },
    stats:[
      {val:'Rp2,9T',lbl:'Total Jan–Mei 2026'},
      {val:'↑Rp300M',lbl:'vs 2025'},
      {val:'Rp700M',lbl:'Mei (tertinggi)'}
    ],
    src:'Bisnis.com & Pemprov Bali, Jun 2026'
  },
  target_wisman: {
    title: 'Target vs Realisasi Wisman Bali',
    sub: 'Perbandingan target dan realisasi kunjungan tahunan',
    type: 'bar',
    data: {
      labels: ['2022','2023','2024','2025','2026 (target)'],
      datasets: [{
        label:'Realisasi / Target (Juta)',
        data:[2.9,5.27,6.29,6.9,6.625],
        backgroundColor:['rgba(34,197,94,0.6)','rgba(34,197,94,0.7)','rgba(34,197,94,0.8)','rgba(34,197,94,1)','rgba(234,179,8,0.6)'],
        borderRadius:10,borderSkipped:false
      }]
    },
    stats:[
      {val:'6,9 Jt',lbl:'Realisasi 2025'},
      {val:'6,625 Jt',lbl:'Target 2026'},
      {val:'↑5,6x',lbl:'vs 2022 (recovery)'}
    ],
    src:'Dispar Bali, BPS Bali 2022–2026'
  },
  pdrb: {
    title: 'Pertumbuhan PDRB Bali (yoy)',
    sub: 'Laju pertumbuhan ekonomi Bali per kuartal',
    type: 'line',
    data: {
      labels: ['Q1 2024','Q2 2024','Q3 2024','Q4 2024','Q1 2025','Q2 2025','Q3 2025','Q4 2025','Q1 2026'],
      datasets: [{
        label:'PDRB Growth (%)',
        data:[5.1,5.8,6.2,5.9,5.4,5.7,6.0,5.8,5.58],
        borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,0.08)',
        tension:0.4,fill:true,pointRadius:5,pointBackgroundColor:'#22c55e'
      }]
    },
    stats:[
      {val:'5,58%',lbl:'Q1 2026 (yoy)'},
      {val:'Rp44,28T',lbl:'Nilai PDRB Q1 2026'},
      {val:'>Nasional',lbl:'Di atas rata-rata RI'}
    ],
    src:'BPS Bali, Mei 2026'
  },
  inflasi_mtm: {
    title: 'Inflasi Bali Bulanan (mtm)',
    sub: 'Month-to-month · Mei 2026 anomali naik saat biasanya deflasi',
    type: 'bar',
    data: {
      labels: ['Jan','Feb','Mar','Apr','Mei'],
      datasets: [{
        label:'Inflasi mtm (%)',
        data:[0.21,-0.08,0.15,0.31,0.42],
        backgroundColor(ctx){
          return ctx.raw >= 0 ? 'rgba(239,68,68,0.7)' : 'rgba(34,197,94,0.7)';
        },
        borderRadius:8,borderSkipped:false
      }]
    },
    stats:[
      {val:'0,42%',lbl:'Mei 2026 (mtm)'},
      {val:'2,99%',lbl:'Mei 2026 (yoy)'},
      {val:'Anomali',lbl:'Biasanya Mei deflasi'}
    ],
    src:'BPS Bali, 2 Juni 2026'
  },
  inflasi_yoy: {
    title: 'Inflasi Bali Tahunan (yoy)',
    sub: 'Year-on-year · Dalam sasaran BI 2,5±1%',
    type: 'line',
    data: {
      labels: ['Jan','Feb','Mar','Apr','Mei'],
      datasets: [
        {label:'Inflasi yoy (%)',data:[2.41,2.28,2.15,2.67,2.99],borderColor:'#eab308',backgroundColor:'rgba(234,179,8,0.08)',tension:0.4,fill:true,pointRadius:5,pointBackgroundColor:'#eab308'},
        {label:'Batas atas BI (3,5%)',data:[3.5,3.5,3.5,3.5,3.5],borderColor:'rgba(239,68,68,0.4)',borderDash:[6,4],pointRadius:0,fill:false},
        {label:'Batas bawah BI (1,5%)',data:[1.5,1.5,1.5,1.5,1.5],borderColor:'rgba(34,197,94,0.4)',borderDash:[6,4],pointRadius:0,fill:false}
      ]
    },
    stats:[
      {val:'2,99%',lbl:'Mei 2026 (yoy)'},
      {val:'2,5±1%',lbl:'Sasaran BI 2026'},
      {val:'Aman',lbl:'Masih dalam target'}
    ],
    src:'BPS Bali & Bank Indonesia, Juni 2026'
  },
  gap_umr: {
    title: 'Kesenjangan UMR vs Kebutuhan Hidup Layak',
    sub: 'Bali 2026 — gap sebesar Rp1,95 juta per bulan',
    type: 'bar',
    data: {
      labels: ['Sewa','Makan','Transport','Adat/Banjar','Hari Raya','Lainnya','TOTAL KHL','UMR Bali'],
      datasets: [{
        label:'Rp (Juta/bulan)',
        data:[2.25,1.25,0.75,0.2,0.35,0.75,5.25,3.3],
        backgroundColor(ctx){
          const i=ctx.dataIndex;
          if(i===7) return '#22c55e';
          if(i===6) return '#ef4444';
          return 'rgba(255,255,255,0.12)';
        },
        borderRadius:8,borderSkipped:false
      }]
    },
    stats:[
      {val:'Rp3,3Jt',lbl:'UMR Bali 2026'},
      {val:'Rp5,25Jt',lbl:'KHL Bali 2026'},
      {val:'−Rp1,95Jt',lbl:'Defisit per bulan'}
    ],
    src:'Kemnaker, BPS, Balinewsweek 2026'
  }
};

// ── CHART OPTIONS ──
const baseOpts = {
  responsive:true,maintainAspectRatio:false,
  plugins:{legend:{labels:{color:'#a3b8a8',font:{size:11},boxWidth:12}},tooltip:{backgroundColor:'rgba(7,12,9,0.95)',titleColor:'#f0faf2',bodyColor:'#a3b8a8',borderColor:'rgba(255,255,255,0.1)',borderWidth:1}},
  scales:{x:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#5e7563',font:{size:10}}},y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#5e7563',font:{size:10}}}}
};

let activeChart = null;

function openModal(key){
  const d = charts[key];
  if(!d) return;
  document.getElementById('modal-title').textContent = d.title;
  document.getElementById('modal-sub').textContent = d.sub;
  document.getElementById('modal-src').textContent = '📌 Sumber: ' + d.src;
  document.getElementById('modal-stats').innerHTML = d.stats.map(s=>`<div class="ms"><div class="ms-val">${s.val}</div><div class="ms-lbl">${s.lbl}</div></div>`).join('');

  if(activeChart){activeChart.destroy();activeChart=null;}
  const canvas = document.getElementById('modal-chart');
  const ctx = canvas.getContext('2d');
  activeChart = new Chart(ctx, {type:d.type, data:d.data, options:{...baseOpts}});

  overlay.classList.add('open');
  document.body.style.overflow='hidden';
}

function closeModal(){
  overlay.classList.remove('open');
  document.body.style.overflow='';
  if(activeChart){activeChart.destroy();activeChart=null;}
}

document.getElementById('modal-close').addEventListener('click',closeModal);
overlay.addEventListener('click',e=>{if(e.target===overlay)closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});

// ── ATTACH TO KPI CARDS ──
document.querySelectorAll('.kpi[data-modal]').forEach(el=>{
  el.addEventListener('click',()=>openModal(el.dataset.modal));
});

})();
