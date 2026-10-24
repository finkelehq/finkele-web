/**
 * Finkele site: menu, hero film control, section highlight and entrances.
 * Shared by the home page and the product pages.
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

  /* Hero film. The markup has no autoplay and preload="none", so nothing but the poster loads
     until this starts the film; it does not under reduced motion or when the browser asks to
     save data. The bar under the film is one button: it pauses and plays (aria-pressed is
     true while paused) and shows how far through the loop the film is. Off screen the film
     pauses, and it resumes on return unless the viewer paused it. The clock over the film
     follows the solver frame on screen, from data-times: [seconds into the film, "HH:MM"]. */
  var video = document.getElementById('hero-film');
  var filmToggle = document.getElementById('film-toggle');
  var filmBar = document.getElementById('film-bar');
  var filmFill = document.getElementById('film-fill');
  var filmClock = document.getElementById('film-clock');
  var userPaused = false;
  var saveData = !!(navigator.connection && navigator.connection.saveData);
  var filmTimes = [];
  var clockAtRest = filmClock ? filmClock.textContent : '';
  var frameRequest = 0;

  if (video) {
    try { filmTimes = JSON.parse(video.getAttribute('data-times') || '[]'); } catch (err) { filmTimes = []; }
  }

  function syncToggle() {
    if (filmToggle && video) filmToggle.setAttribute('aria-pressed', String(video.paused));
  }

  function drawProgress() {
    var t = video.currentTime;
    if (filmFill && video.duration) filmFill.style.transform = 'scaleX(' + (t / video.duration) + ')';
    if (filmClock && filmTimes.length) {
      var label = filmTimes[0][1];
      for (var i = 0; i < filmTimes.length && filmTimes[i][0] <= t; i++) label = filmTimes[i][1];
      if (filmClock.textContent !== label) filmClock.textContent = label;
    }
  }

  function followFilm() {
    drawProgress();
    frameRequest = video.paused ? 0 : window.requestAnimationFrame(followFilm);
  }

  function playFilm() {
    var p = video.play();
    if (p && p.catch) p.catch(syncToggle);
  }

  function stopFilm() {
    if (!video) return;
    video.pause();
    video.preload = 'none';
    Array.prototype.forEach.call(video.querySelectorAll('source'), function (s) { s.remove(); });
    video.load();
    if (filmBar) filmBar.hidden = true;
    if (filmClock) filmClock.textContent = clockAtRest;
  }

  if (video && filmToggle) {
    if (reduceQuery.matches || saveData) {
      stopFilm();
    } else {
      if (filmBar) filmBar.hidden = false;
      video.addEventListener('play', function () {
        syncToggle();
        if (!frameRequest) frameRequest = window.requestAnimationFrame(followFilm);
      });
      video.addEventListener('pause', function () { syncToggle(); drawProgress(); });
      filmToggle.addEventListener('click', function () {
        if (video.paused) {
          userPaused = false;
          playFilm();
        } else {
          userPaused = true;
          video.pause();
        }
      });
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (userPaused) return;
            if (entry.isIntersecting) playFilm();
            else video.pause();
          });
        }, { threshold: 0.1 }).observe(video);
      } else {
        playFilm();
      }
      syncToggle();
    }
    reduceQuery.addEventListener('change', function (e) {
      if (e.matches) stopFilm();
    });
  }

  /* Highlight the nav link of the section in view. */
  // Only in-page links (href="#id") take part; on a product page the nav points elsewhere.
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav-link[href^="#"]'));
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
