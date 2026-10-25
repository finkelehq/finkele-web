/**
 * Finkele site showpieces: the platform loop on the laptop, and the drag-to-compare sliders.
 * Vanilla JS, no dependencies, and an enhancement only: without it the laptop shows its
 * poster and each comparison sits at its midpoint.
 */
(function () {
  'use strict';

  var reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- Platform loop ----------
     The video carries no src until it is near the screen (data-src on each <source>), so it
     costs nothing above the fold. Under reduced motion it is never loaded and the poster stays.
     Off screen it pauses; it resumes on return unless the viewer paused it. */
  Array.prototype.forEach.call(document.querySelectorAll('[data-devices]'), function (root) {
    var video = root.querySelector('video');
    var toggle = root.querySelector('.devices-toggle');
    if (!video || !toggle) return;
    var loaded = false;
    var userPaused = false;
    var visible = false;

    var label = toggle.querySelector('.devices-toggle-label');
    function sync() {
      // The label names the action, so the button needs no aria-pressed as well.
      toggle.classList.toggle('is-paused', video.paused);
      if (label) label.textContent = video.paused ? 'Play recording' : 'Pause recording';
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
      video.hidden = false;
      video.load();
    }
    function unload() {
      video.pause();
      video.hidden = true;
      toggle.parentElement.hidden = true;
    }

    if (reduceQuery.matches) { unload(); return; }

    video.addEventListener('play', sync);
    video.addEventListener('pause', sync);
    toggle.addEventListener('click', function () {
      if (video.paused) { userPaused = false; load(); tryPlay(); }
      else { userPaused = true; video.pause(); }
    });

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) load(); });
      }, { rootMargin: '300px 0px' }).observe(root);
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          visible = e.isIntersecting;
          if (!visible) video.pause();
          else if (!userPaused && loaded) tryPlay();
        });
      }, { threshold: 0.15 }).observe(video.parentElement);
    } else {
      load();
      tryPlay();
    }
    video.addEventListener('canplay', function () { if (visible && !userPaused) tryPlay(); });
    sync();

    reduceQuery.addEventListener('change', function (e) { if (e.matches) unload(); });
  });

  /* ---------- Drag to compare ----------
     The grip is a role="slider" (0 to 100, the share of the frame showing the first image).
     Pointer input on the whole frame moves the divider, mouse and touch alike; the frame keeps
     touch-action: pan-y so a vertical swipe still scrolls the page. Keys: arrows 2, Page Up and
     Page Down 10, Home and End to the ends. */
  Array.prototype.forEach.call(document.querySelectorAll('[data-compare]'), function (frame) {
    var grip = frame.querySelector('.compare-grip');
    if (!grip) return;
    var nameA = grip.getAttribute('data-a') || 'first image';
    var nameB = grip.getAttribute('data-b') || 'second image';
    var value = 50;

    function set(v) {
      value = Math.max(0, Math.min(100, Math.round(v)));
      frame.style.setProperty('--pos', value + '%');
      grip.setAttribute('aria-valuenow', String(value));
      grip.setAttribute('aria-valuetext', value + '% ' + nameA + ', ' + (100 - value) + '% ' + nameB);
    }
    function fromEvent(e) {
      var r = frame.getBoundingClientRect();
      return ((e.clientX - r.left) / r.width) * 100;
    }

    var dragging = null;
    var startX = 0;
    var startY = 0;
    frame.addEventListener('pointerdown', function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      dragging = e.pointerId;
      startX = e.clientX;
      startY = e.clientY;
      // A mouse or pen click moves the divider at once; a touch waits to see whether it is a
      // horizontal drag or a vertical scroll.
      if (e.pointerType !== 'touch' || e.target === grip) {
        set(fromEvent(e));
        try { frame.setPointerCapture(e.pointerId); } catch (err) { /* not capturable */ }
      }
      if (e.pointerType !== 'touch') grip.focus({ preventScroll: true });
    });
    frame.addEventListener('pointermove', function (e) {
      if (dragging !== e.pointerId) return;
      if (e.pointerType === 'touch' && !frame.hasPointerCapture(e.pointerId)) {
        var dx = Math.abs(e.clientX - startX);
        var dy = Math.abs(e.clientY - startY);
        if (dy > dx && dy > 6) { dragging = null; return; }   // a scroll: leave it to the page
        if (dx < 6) return;
        try { frame.setPointerCapture(e.pointerId); } catch (err) { /* not capturable */ }
      }
      set(fromEvent(e));
    });
    function end(e) {
      if (dragging !== e.pointerId) return;
      if (e.type === 'pointerup' && e.pointerType === 'touch' && !frame.hasPointerCapture(e.pointerId) &&
          Math.abs(e.clientX - startX) < 6 && Math.abs(e.clientY - startY) < 6) {
        set(fromEvent(e));                                     // a tap moves the divider there
      }
      dragging = null;
    }
    frame.addEventListener('pointerup', end);
    frame.addEventListener('pointercancel', end);

    grip.addEventListener('keydown', function (e) {
      var step = { ArrowLeft: -2, ArrowDown: -2, ArrowRight: 2, ArrowUp: 2, PageDown: -10, PageUp: 10 }[e.key];
      if (step !== undefined) set(value + step);
      else if (e.key === 'Home') set(0);
      else if (e.key === 'End') set(100);
      else return;
      e.preventDefault();
    });

    set(value);
  });
})();
