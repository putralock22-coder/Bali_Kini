// Bali Kini — UX: mobile menu, active nav, share
(function(){

// ── MOBILE MENU ──
const menuBtn  = document.getElementById('menuBtn');
const mobileMenu = document.getElementById('mobileMenu');

if(menuBtn && mobileMenu){
  menuBtn.addEventListener('click', () => {
    const open = mobileMenu.classList.toggle('open');
    menuBtn.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', open);
    mobileMenu.setAttribute('aria-hidden', !open);
  });

  // Close on link click
  mobileMenu.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      mobileMenu.classList.remove('open');
      menuBtn.classList.remove('open');
      menuBtn.setAttribute('aria-expanded', false);
      mobileMenu.setAttribute('aria-hidden', true);
    });
  });

  // Close on outside click
  document.addEventListener('click', e => {
    if(!menuBtn.contains(e.target) && !mobileMenu.contains(e.target)){
      mobileMenu.classList.remove('open');
      menuBtn.classList.remove('open');
      menuBtn.setAttribute('aria-expanded', false);
    }
  });
}

// ── ACTIVE SECTION NAV HIGHLIGHT ──
const navLinks = document.querySelectorAll('.main-nav a[data-section]');

if(navLinks.length){
  const sectionIds = [...navLinks].map(a => a.dataset.section);
  const sections   = sectionIds.map(id => document.getElementById(id)).filter(Boolean);

  const setActive = id => {
    navLinks.forEach(a => a.classList.toggle('nav-active', a.dataset.section === id));
  };

  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if(entry.isIntersecting) setActive(entry.target.id);
    });
  }, { rootMargin: '-30% 0px -60% 0px', threshold: 0 });

  sections.forEach(s => io.observe(s));
}

// ── SHARE FUNCTIONALITY ──
function showToast(msg){
  const existing = document.querySelector('.share-toast');
  if(existing) existing.remove();
  const t = document.createElement('div');
  t.className = 'share-toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2800);
}

function shareSection(title, url){
  const text = `${title} — Bali Kini\n${url}`;
  if(navigator.share){
    navigator.share({ title, text, url }).catch(() => {});
  } else {
    // Fallback: copy link + open WhatsApp option
    navigator.clipboard.writeText(url).then(() => {
      showToast('🔗 Link disalin!');
    }).catch(() => {
      // Older browsers: open WhatsApp
      const wa = `https://wa.me/?text=${encodeURIComponent(text)}`;
      window.open(wa, '_blank');
    });
  }
}

// Attach to all share buttons
document.querySelectorAll('.share-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const section = btn.closest('[id]');
    const titleEl = btn.closest('.section-header')?.querySelector('.sec-title');
    const title   = (titleEl ? titleEl.textContent.trim() : document.title) + ' | Bali Kini';
    const hash    = section ? '#' + section.id : '';
    const url     = location.origin + location.pathname + hash;
    shareSection(title, url);
  });
});

// ── ARTIKEL SINGLE: SHARE ──
const artikelShare = document.getElementById('artikelShare');
if(artikelShare){
  artikelShare.addEventListener('click', () => {
    shareSection(document.title, location.href);
  });
}

})();
