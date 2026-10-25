/**
 * Finkele site: the research loops on the home page and on research.html.
 * Vanilla JS, no dependencies, and an enhancement only: without it each figure shows its
 * poster image. Same pattern as the platform loop in showpieces.js, for several figures.
 *
 * Each [data-research-loop] holds a poster <img>, a hidden muted <video> whose <source>s carry
 * data-src, and a hidden pause button. The video gets its src only when the figure comes within
 * 300 px of the screen, plays only while at least 40% of it is on screen, and pauses off screen;
 * it resumes on return unless the viewer paused it. Under prefers-reduced-motion the video is
 * never loaded and the poster stays.
 */
(function () {
  'use strict';

  var roots = document.querySelectorAll('[data-research-loop]');
  if (!roots.length) return;
  var reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  Array.prototype.forEach.call(roots, function (root) {
    var video = root.querySelector('video');
    var toggle = root.querySelector('.research-toggle');
    if (!video || !toggle) return;
    var label = toggle.querySelector('.visually-hidden');
    var loaded = false;
    var userPaused = false;
    var visible = false;

    function sync() {
      // The label names the action, so the button needs no aria-pressed as well.
      toggle.classList.toggle('is-paused', video.paused);
      if (label) label.textContent = video.paused ? 'Play animation' : 'Pause animation';
    }
    function tryPlay() {
      var p = video.play();
      if (p && p.catch) p.catch(sync);
    }
    function load() {
      if (loaded || reduceQuery.matches) return;
      loaded = true;
      Array.prototype.forEach.call(video.querySelectorAll('source[data-src]'), function (s) {
        s.src = s.getAttribute('data-src');
      });
      video.load();
    }
    function unload() {
      video.pause();
      video.hidden = true;
      toggle.hidden = true;
    }

    if (reduceQuery.matches) { unload(); return; }

    video.addEventListener('play', sync);
    video.addEventListener('pause', sync);
    // Show the video over its poster only once it has a frame, so the poster never blinks out.
    video.addEventListener('loadeddata', function () {
      if (reduceQuery.matches) return;
      video.hidden = false;
      toggle.hidden = false;
    });
    video.addEventListener('canplay', function () { if (visible && !userPaused) tryPlay(); });
    toggle.addEventListener('click', function () {
      if (video.paused) { userPaused = false; load(); tryPlay(); }
      else { userPaused = true; video.pause(); }
    });

    if ('IntersectionObserver' in window) {
      var near = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { load(); near.unobserve(root); }
        });
      }, { rootMargin: '300px 0px' });
      near.observe(root);
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          visible = e.isIntersecting;
          if (!visible) video.pause();
          else if (!userPaused && loaded) tryPlay();
        });
      }, { threshold: 0.4 }).observe(video.parentElement);
    } else {
      load();
      visible = true;
    }
    sync();

    reduceQuery.addEventListener('change', function (e) { if (e.matches) unload(); });
  });
})();
