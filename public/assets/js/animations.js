// ============================================
// FILE: public/assets/js/animations.js
// ============================================

/**
 * Finkele Animation Library
 * Handles all animations and visual effects
 */

class AnimationController {
    constructor() {
        this.observers = new Map();
        this.animations = new Map();
        this.particleSystem = null;
    }

    /**
     * Initialize all animations
     */
    init() {
        this.setupIntersectionObservers();
        this.initParticleSystem();
        this.initCounterAnimations();
        this.initScrollAnimations();
        this.initHoverEffects();
    }

    /**
     * Setup Intersection Observers for scroll animations
     */
    setupIntersectionObservers() {
        const options = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };

        // Fade in animation observer
        const fadeInObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                    fadeInObserver.unobserve(entry.target);
                }
            });
        }, options);

        // Slide in animation observer
        const slideInObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const direction = entry.target.dataset.slideDirection || 'up';
                    entry.target.classList.add(`animate-slide-${direction}`);
                    slideInObserver.unobserve(entry.target);
                }
            });
        }, options);

        // Store observers
        this.observers.set('fadeIn', fadeInObserver);
        this.observers.set('slideIn', slideInObserver);

        // Apply to elements
        document.querySelectorAll('[data-animate="fade"]').forEach(el => {
            fadeInObserver.observe(el);
        });

        document.querySelectorAll('[data-animate="slide"]').forEach(el => {
            slideInObserver.observe(el);
        });
    }

    /**
     * Initialize particle system for background effects
     */
    initParticleSystem() {
        const canvas = document.createElement('canvas');
        canvas.id = 'particle-canvas';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '-1';
        canvas.style.opacity = '0.3';

        const container = document.querySelector('.climate-particles');
        if (container) {
            container.appendChild(canvas);
            this.particleSystem = new ParticleSystem(canvas);
            this.particleSystem.start();
        }
    }

    /**
     * Initialize counter animations for numbers
     */
    initCounterAnimations() {
        const counters = document.querySelectorAll('[data-counter]');
        
        counters.forEach(counter => {
            const target = parseFloat(counter.dataset.counter);
            const duration = parseInt(counter.dataset.duration) || 2000;
            const format = counter.dataset.format || 'number';
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !counter.dataset.animated) {
                        this.animateCounter(counter, target, duration, format);
                        counter.dataset.animated = 'true';
                        observer.unobserve(counter);
                    }
                });
            }, { threshold: 0.5 });
            
            observer.observe(counter);
        });
    }

    /**
     * Animate counter from 0 to target value
     */
    animateCounter(element, target, duration, format) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const updateCounter = () => {
            current += increment;
            
            if (current < target) {
                element.textContent = this.formatNumber(current, format);
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = this.formatNumber(target, format);
            }
        };
        
        requestAnimationFrame(updateCounter);
    }

    /**
     * Format number based on type
     */
    formatNumber(value, format) {
        switch(format) {
            case 'currency':
                return '$' + value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            case 'percentage':
                return value.toFixed(1) + '%';
            case 'decimal':
                return value.toFixed(1);
            default:
                return Math.round(value).toLocaleString();
        }
    }

    /**
     * Initialize scroll-triggered animations
     */
    initScrollAnimations() {
        let lastScrollY = window.scrollY;
        let ticking = false;
        
        const updateScrollAnimations = () => {
            const scrollY = window.scrollY;
            const direction = scrollY > lastScrollY ? 'down' : 'up';
            
            // Parallax effects
            document.querySelectorAll('[data-parallax]').forEach(el => {
                const speed = parseFloat(el.dataset.parallax) || 0.5;
                const yPos = -(scrollY * speed);
                el.style.transform = `translateY(${yPos}px)`;
            });
            
            // Progress indicators
            const progress = (scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
            document.documentElement.style.setProperty('--scroll-progress', `${progress}%`);
            
            lastScrollY = scrollY;
            ticking = false;
        };
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollAnimations);
                ticking = true;
            }
        });
    }

    /**
     * Initialize hover effects
     */
    initHoverEffects() {
        // 3D card tilt effect
        document.querySelectorAll('[data-tilt]').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 20;
                const rotateY = (centerX - x) / 20;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
            });
        });

        // Magnetic button effect
        document.querySelectorAll('[data-magnetic]').forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translate(0, 0)';
            });
        });
    }

    /**
     * Ripple effect for buttons
     */
    createRipple(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    /**
     * Typewriter effect
     */
    typeWriter(element, text, speed = 50) {
        let i = 0;
        element.textContent = '';
        
        const type = () => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        };
        
        type();
    }

    /**
     * Smooth scroll to element
     */
    scrollToElement(selector, offset = 0) {
        const element = document.querySelector(selector);
        if (element) {
            const y = element.getBoundingClientRect().top + window.scrollY + offset;
            window.scrollTo({ top: y, behavior: 'smooth' });
        }
    }

    /**
     * Animate element on scroll
     */
    animateOnScroll(element, animation, options = {}) {
        const defaultOptions = {
            threshold: 0.5,
            rootMargin: '0px',
            once: true
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    element.style.animation = animation;
                    if (mergedOptions.once) {
                        observer.unobserve(element);
                    }
                }
            });
        }, {
            threshold: mergedOptions.threshold,
            rootMargin: mergedOptions.rootMargin
        });
        
        observer.observe(element);
    }
}

/**
 * Particle System for background effects
 */
class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 50;
        this.animationId = null;
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticle() {
        return {
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 2 + 1,
            opacity: Math.random() * 0.5 + 0.3,
            color: Math.random() > 0.5 ? '#038C50' : '#4FBF7F'
        };
    }
    
    start() {
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push(this.createParticle());
        }
        this.animate();
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = particle.color;
            this.ctx.globalAlpha = particle.opacity;
            this.ctx.fill();
        });
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// Initialize animations when DOM is ready
const animationController = new AnimationController();
document.addEventListener('DOMContentLoaded', () => {
    animationController.init();
});

// Export for use in other modules
window.AnimationController = AnimationController;
window.ParticleSystem = ParticleSystem;