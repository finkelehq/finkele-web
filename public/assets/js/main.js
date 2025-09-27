/**
 * Finkele Climate Platform - Main JavaScript
 * Version: 1.0.0
 * Author: Finkele Development Team
 */

console.log("✅ main.js loaded");

window.addEventListener("load", () => {
  console.log("✅ Page fully loaded");
  // Hide loader immediately after page load
  const loader = document.getElementById("loader");
  if (loader) {
    loader.style.opacity = "0";
    loader.style.transition = "opacity 0.5s ease-out";
    setTimeout(() => {
      loader.style.display = "none";
    }, 500);
  }
});

// Global Configuration
const CONFIG = {
  API_BASE_URL: 'https://api.open-meteo.com/v1',
  UPDATE_INTERVAL: 5000, // 5 seconds
  ANIMATION_DURATION: 800,
  SCROLL_THRESHOLD: 100
};

// DOM Elements
const elements = {
  navbar: document.getElementById('navbar'),
  loader: document.getElementById('loader'),
  hamburger: document.getElementById('hamburger'),
  navLinks: document.querySelectorAll('.nav-link'),
  servicesGrid: document.getElementById('services-grid'),
  impactMetrics: document.getElementById('impact-metrics'),
  dashboardContainer: document.getElementById('dashboard-container'),
  contactForm: document.getElementById('contact-form')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

function initializeApp() {
  // Hide loader after a short delay (failsafe)
  setTimeout(() => {
    elements.loader?.classList.add('hidden');
  }, 1000);

  // Initialize features
  initNavigation();
  loadServices();
  loadImpactMetrics();
  loadDashboardPreview();
  initScrollAnimations();
  initContactForm();

  console.log('🌍 Finkele Climate Platform Initialized');
}

// Navigation Functions
function initNavigation() {
  // Scroll effect
  window.addEventListener('scroll', () => {
    if (window.scrollY > CONFIG.SCROLL_THRESHOLD) {
      elements.navbar?.classList.add('scrolled');
    } else {
      elements.navbar?.classList.remove('scrolled');
    }
  });

  // Mobile menu toggle
  elements.hamburger?.addEventListener('click', toggleMobileMenu);

  // Smooth scroll for nav links
  elements.navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href');
      const targetSection = document.querySelector(targetId);

      if (targetSection) {
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Update active link
        elements.navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');

        // Close mobile menu
        closeMobileMenu();
      }
    });
  });

  updateActiveNav();
}

function toggleMobileMenu() {
  const navLinksContainer = document.querySelector('.nav-links');
  navLinksContainer?.classList.toggle('mobile-active');
  elements.hamburger?.classList.toggle('active');
}

function closeMobileMenu() {
  const navLinksContainer = document.querySelector('.nav-links');
  navLinksContainer?.classList.remove('mobile-active');
  elements.hamburger?.classList.remove('active');
}

function updateActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY + 100;
    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      const sectionId = section.getAttribute('id');

      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        elements.navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
          }
        });
      }
    });
  });
}

// Load Services
function loadServices() {
  const services = [
    { icon: '🌡️', title: 'Climate Risk Modeling', description: 'AI-driven physical climate modeling aligned with your double materiality reporting.' },
    { icon: '📊', title: 'ESG Integration', description: 'Real-time ESG metrics dashboard with automated TCFD/TNFD reporting.' },
    { icon: '🛡️', title: 'Asset Resilience', description: 'Comprehensive vulnerability assessments and adaptation roadmaps.' },
    { icon: '🔄', title: 'Transition Planning', description: 'Navigate the low-carbon transition with confidence and clarity.' },
    { icon: '🌍', title: 'Global Intelligence', description: 'Satellite monitoring and IoT sensor networks for real-time data.' },
    { icon: '💡', title: 'Innovation Advisory', description: 'Access cutting-edge climate technologies and solutions.' }
  ];

  if (elements.servicesGrid) {
    elements.servicesGrid.innerHTML = services.map((s, i) => `
      <div class="service-card" style="animation-delay: ${i * 0.1}s">
        <div class="service-icon">${s.icon}</div>
        <h3 class="service-title">${s.title}</h3>
        <p class="service-description">${s.description}</p>
      </div>
    `).join('');
  }
}

// Load Impact Metrics
function loadImpactMetrics() {
  const metrics = [
    { value: '$3.2B', label: 'Assets Protected' },
    { value: '180+', label: 'Global Clients' },
    { value: '45%', label: 'Risk Reduction' },
    { value: '50M', label: 'CO₂ Avoided' }
  ];

  if (elements.impactMetrics) {
    elements.impactMetrics.innerHTML = metrics.map((m, i) => `
      <div class="impact-metric" style="animation-delay: ${i * 0.1}s">
        <div class="impact-number" data-target="${m.value}">${m.value}</div>
        <div class="impact-label">${m.label}</div>
      </div>
    `).join('');
  }
}

// Load Dashboard Preview
function loadDashboardPreview() {
  if (elements.dashboardContainer) {
    elements.dashboardContainer.innerHTML = `
      <div class="dashboard-preview">
        <div class="dashboard-header">
          <h3>Live Climate Monitoring</h3>
          <span class="live-indicator">
            <span class="live-dot"></span> LIVE
          </span>
        </div>
        <div class="metrics-grid">
          <div class="metric-card"><div class="metric-value">73.2</div><div class="metric-label">Risk Index</div></div>
          <div class="metric-card"><div class="metric-value">+1.8°C</div><div class="metric-label">Temperature</div></div>
          <div class="metric-card"><div class="metric-value">421 ppm</div><div class="metric-label">CO₂ Level</div></div>
          <div class="metric-card"><div class="metric-value">87%</div><div class="metric-label">Resilience</div></div>
        </div>
      </div>
    `;
  }
}

// Scroll Animations
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        if (entry.target.classList.contains('impact-metric')) {
          const num = entry.target.querySelector('.impact-number');
          animateNumber(num);
        }
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -100px 0px' });

  document.querySelectorAll('.service-card, .impact-metric').forEach(el => observer.observe(el));
}

// Number Animation
function animateNumber(element) {
  if (!element || element.dataset.animated) return;

  const target = element.dataset.target || element.textContent;
  const isPercentage = target.includes('%');
  const isCurrency = target.includes('$');
  const hasLetter = target.match(/[BMK+]/);

  let startValue = 0;
  let endValue = parseFloat(target.replace(/[^0-9.]/g, ''));
  const duration = 2000;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const currentValue = startValue + (endValue - startValue) * easeOutQuad(progress);

    let displayValue = currentValue.toFixed(0);
    if (isCurrency) displayValue = '$' + displayValue;
    if (hasLetter) displayValue += hasLetter[0];
    if (isPercentage) displayValue += '%';

    element.textContent = displayValue;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      element.textContent = target;
      element.dataset.animated = 'true';
    }
  }
  requestAnimationFrame(update);
}

function easeOutQuad(t) {
  return t * (2 - t);
}

// Contact Form
function initContactForm() {
  elements.contactForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'Sending...';
    btn.disabled = true;

    try {
      await new Promise(resolve => setTimeout(resolve, 1000)); // simulate API
      showNotification('Message sent successfully!', 'success');
      e.target.reset();
    } catch {
      showNotification('Failed to send message. Please try again.', 'error');
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
}

// Notification
function showNotification(msg, type = 'info') {
  const n = document.createElement('div');
  n.className = `notification notification-${type}`;
  n.textContent = msg;
  document.body.appendChild(n);

  setTimeout(() => n.classList.add('show'), 100);
  setTimeout(() => {
    n.classList.remove('show');
    setTimeout(() => n.remove(), 300);
  }, 3000);
}

// Utility
function debounce(fn, wait) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), wait);
  };
}

function throttle(fn, limit) {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Expose globals
window.FinkeleApp = { CONFIG, showNotification, debounce, throttle };
