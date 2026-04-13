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
