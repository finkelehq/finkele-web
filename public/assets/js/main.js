/**
 * Finkele home page: menu, hero film control, section highlight and entrances.
 * Vanilla JS, no dependencies. Everything here is an enhancement: the page reads
 * and works without it.
 */
(function () {
  'use strict';

  var reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* Mobile menu: a button with aria-expanded, closed by Escape, a link or a wider screen. */
  var toggle = document.getElementById('nav-toggle');
  var menu = document.getElementById('nav-menu');

  function setMenu(open) {
    if (!toggle || !menu) return;
    toggle.setAttribute('aria-expanded', String(open));
    menu.classList.toggle('is-open', open);
  }

  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      setMenu(toggle.getAttribute('aria-expanded') !== 'true');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) setMenu(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        toggle.focus();
      }
    });
    window.matchMedia('(min-width: 861px)').addEventListener('change', function (e) {
      if (e.matches) setMenu(false);
    });
  }

  /* Hero film: a pause/play toggle (aria-pressed is true while paused). Under reduced
     motion the film is not loaded and the poster stays. Off screen it pauses, and it
     resumes on return unless the viewer paused it. */
  var video = document.getElementById('hero-film');
  var filmToggle = document.getElementById('film-toggle');
  var userPaused = false;

  function syncToggle() {
    if (filmToggle && video) filmToggle.setAttribute('aria-pressed', String(video.paused));
  }

  function stopFilm() {
    if (!video) return;
    video.pause();
    video.removeAttribute('autoplay');
    video.preload = 'none';
    Array.prototype.forEach.call(video.querySelectorAll('source'), function (s) { s.remove(); });
    video.load();
  }

  if (video && filmToggle) {
    if (reduceQuery.matches) {
      stopFilm();
    } else {
      video.addEventListener('play', syncToggle);
      video.addEventListener('pause', syncToggle);
      filmToggle.addEventListener('click', function () {
        if (video.paused) {
          userPaused = false;
          var p = video.play();
          if (p && p.catch) p.catch(syncToggle);
        } else {
          userPaused = true;
          video.pause();
        }
      });
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (userPaused) return;
            if (entry.isIntersecting) {
              var p = video.play();
              if (p && p.catch) p.catch(syncToggle);
            } else {
              video.pause();
            }
          });
        }, { threshold: 0.1 }).observe(video);
      }
      syncToggle();
    }
    reduceQuery.addEventListener('change', function (e) {
      if (e.matches) stopFilm();
    });
  }

  /* Highlight the nav link of the section in view. */
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav-link'));
  var byId = {};
  links.forEach(function (l) { byId[l.getAttribute('href').slice(1)] = l; });
  if ('IntersectionObserver' in window) {
    var sectionObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var link = byId[entry.target.id];
        if (!link) return;
        links.forEach(function (l) { l.classList.toggle('is-active', l === link); });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) sectionObs.observe(el);
    });
  }

  /* Entrances: a short ease-out fade and rise, once, with a small stagger inside a
     group. Off entirely under reduced motion. */
  if (!reduceQuery.matches && 'IntersectionObserver' in window) {
    var reveals = document.querySelectorAll('.reveal');
    var groups = new Map();
    reveals.forEach(function (el) {
      var parent = el.parentElement;
      var i = groups.get(parent) || 0;
      el.style.setProperty('--stagger', Math.min(i, 4) * 60 + 'ms');
      groups.set(parent, i + 1);
    });
    var revealObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          revealObs.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    // Only elements below the first screen start hidden, so nothing visible on load flickers.
    var fold = window.innerHeight;
    reveals.forEach(function (el) {
      if (el.getBoundingClientRect().top < fold) {
        el.classList.add('is-in');
      } else {
        revealObs.observe(el);
      }
    });
    document.documentElement.classList.add('motion');
  }
})();
