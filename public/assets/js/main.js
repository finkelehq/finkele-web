/**
 * Finkele v2 — Main JS (lean)
 */
console.log('✅ main.js loaded');

const navbar = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navLinksEl = document.querySelector('.nav-links');
const navLinks = document.querySelectorAll('.nav-link');

/* ── Scroll: shrink nav ───────────────────── */
window.addEventListener('scroll', () => {
  navbar?.classList.toggle('scrolled', window.scrollY > 60);
});

/* ── Smooth scroll nav links ──────────────── */
navLinks.forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      navLinksEl?.classList.remove('mobile-active');
      hamburger?.classList.remove('active');
    }
  });
});

/* ── Active section highlight ─────────────── */
const sections = document.querySelectorAll('section[id]');
window.addEventListener('scroll', () => {
  const y = window.scrollY + 120;
  sections.forEach(sec => {
    if (y >= sec.offsetTop && y < sec.offsetTop + sec.offsetHeight) {
      navLinks.forEach(l => {
        l.classList.toggle('active', l.getAttribute('href') === '#' + sec.id);
      });
    }
  });
});

/* ── Mobile menu ──────────────────────────── */
hamburger?.addEventListener('click', () => {
  navLinksEl?.classList.toggle('mobile-active');
  hamburger.classList.toggle('active');
});

/* ── Scroll Reveal (IntersectionObserver) ── */
const revealEls = document.querySelectorAll('.reveal');
if (revealEls.length) {
  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        revealObs.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });
  revealEls.forEach(el => revealObs.observe(el));
}

/* ── Animated Counters ─────────────────────── */
function animateCounter(el) {
  const raw = el.dataset.count;
  if (!raw || el.dataset.animated) return;
  el.dataset.animated = '1';

  const prefix = raw.match(/^[^0-9]*/)[0];        // e.g. "$"
  const suffix = raw.match(/[^0-9.]*$/)[0];        // e.g. "B", "+", " min", "%"
  const numStr = raw.replace(prefix, '').replace(suffix, '').replace(/,/g, '');
  const target = parseFloat(numStr);
  const hasDecimal = numStr.includes('.');
  const decimals = hasDecimal ? numStr.split('.')[1].length : 0;
  const duration = 1800;
  const start = performance.now();

  function tick(now) {
    const elapsed = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - elapsed, 3); // ease-out cubic
    const current = target * eased;
    const formatted = hasDecimal
      ? current.toFixed(decimals)
      : Math.round(current).toLocaleString();
    el.textContent = prefix + formatted + suffix;
    if (elapsed < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

const counterEls = document.querySelectorAll('[data-count]');
if (counterEls.length) {
  const counterObs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCounter(e.target);
        counterObs.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  counterEls.forEach(el => counterObs.observe(el));
}
