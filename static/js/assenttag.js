/* ==========================================================================
   ASSENTTAG MOTION ENGINE & INTERACTIVE SCRIPT ("THE VEIL")
   Target: Django Drop-in Static JS
   Dependencies: Lenis, GSAP, ScrollTrigger, Three.js, Vanilla-Tilt, KaTeX
   ========================================================================== */

(function () {
    'use strict';

    // --------------------------------------------------------------------------
    // 1. INITIALIZATION & UTILITIES
    // --------------------------------------------------------------------------
    const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isFinePointer = window.matchMedia('(pointer: fine)').matches;

    document.addEventListener('DOMContentLoaded', () => {
        initPreloader();
        initLenisScroll();
        initCustomCursor();
        initHero3DCloud();
        initConsentLens();
        initPinnedDemo();
        initCharacterBlurResolve();
        initMathSandbox();
        initScrollTriggers();
        initTiltCards();
    });

    // --------------------------------------------------------------------------
    // 2. PRELOADER SEQUENCE (1.4s)
    // --------------------------------------------------------------------------
    function initPreloader() {
        const preloader = document.getElementById('preloader');
        const counterEl = document.getElementById('preloader-counter');
        const wordmarkEl = document.getElementById('preloader-wordmark');
        if (!preloader || !counterEl) return;

        let count = 0;
        const duration = 1400; // 1.4s
        const interval = 14;   // Step interval ms

        setTimeout(() => {
            if (wordmarkEl) wordmarkEl.classList.add('loaded');
        }, 100);

        const timer = setInterval(() => {
            count += 1;
            counterEl.textContent = String(count).padStart(2, '0');

            if (count >= 100) {
                clearInterval(timer);
                gsap.to(preloader, {
                    opacity: 0,
                    duration: 0.6,
                    ease: 'power2.out',
                    onComplete: () => {
                        preloader.style.visibility = 'hidden';
                        gsap.fromTo('body', { scale: 0.96 }, { scale: 1, duration: 0.8, ease: 'cubic-bezier(0.16, 1, 0.3, 1)' });
                    }
                });
            }
        }, interval);
    }

    // --------------------------------------------------------------------------
    // 3. LENIS SMOOTH SCROLL & GSAP TICKER
    // --------------------------------------------------------------------------
    let lenis;
    function initLenisScroll() {
        if (isReducedMotion || typeof Lenis === 'undefined') return;

        lenis = new Lenis({
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            orientation: 'vertical',
            gestureOrientation: 'vertical',
            smoothWheel: true
        });

        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);

        // Sync GSAP ScrollTrigger with Lenis
        if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
            gsap.registerPlugin(ScrollTrigger);
            lenis.on('scroll', ScrollTrigger.update);
            gsap.ticker.add((time) => {
                lenis.raf(time * 1000);
            });
            gsap.ticker.lagSmoothing(0, 0);
        }

        // Navbar Scroll Pill Collapse & Progress Line
        const navbar = document.querySelector('.navbar-wrapper');
        const progressBar = document.querySelector('.scroll-progress-bar');

        lenis.on('scroll', (e) => {
            if (e.scroll > 50) {
                navbar?.classList.add('scrolled');
            } else {
                navbar?.classList.remove('scrolled');
            }

            const progress = (e.scroll / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
            if (progressBar) progressBar.style.width = `${progress}%`;
        });
    }

    // --------------------------------------------------------------------------
    // 4. CUSTOM CURSOR (FINE POINTER ONLY)
    // --------------------------------------------------------------------------
    function initCustomCursor() {
        if (!isFinePointer || isReducedMotion) return;

        const dot = document.querySelector('.cursor-dot');
        const ring = document.querySelector('.cursor-ring');
        if (!dot || !ring) return;

        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let ringX = mouseX;
        let ringY = mouseY;

        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            dot.style.transform = `translate(${mouseX}px, ${mouseY}px) translate(-50%, -50%)`;
        });

        function animateRing() {
            ringX += (mouseX - ringX) * 0.15;
            ringY += (mouseY - ringY) * 0.15;
            ring.style.transform = `translate(${ringX}px, ${ringY}px) translate(-50%, -50%)`;
            requestAnimationFrame(animateRing);
        }
        animateRing();

        // Interactive hover states
        const hoverTargets = document.querySelectorAll('a, button, input, .feature-tilt-card, .comparison-card');
        hoverTargets.forEach((target) => {
            target.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
            target.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
        });
    }

    // --------------------------------------------------------------------------
    // 5. THREE.JS 3D HERO PARTICLE MESH
    // --------------------------------------------------------------------------
    function initHero3DCloud() {
        const container = document.getElementById('hero-3d-canvas');
        if (!container || typeof THREE === 'undefined' || isReducedMotion) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.z = 220;

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // Generate ~2,000 points arranged into a loose 3D face-mesh topology
        const particleCount = 2000;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        const colorSignal = new THREE.Color('#2DE2E6');
        const colorAssent = new THREE.Color('#B14AED');

        for (let i = 0; i < particleCount; i++) {
            // Parametric face oval & nose/eye density distribution
            const u = Math.random() * Math.PI * 2;
            const v = (Math.random() - 0.5) * Math.PI;
            
            const rx = 65 * Math.cos(v) * Math.sin(u);
            const ry = 95 * Math.sin(v);
            const rz = 40 * Math.cos(v) * Math.cos(u) + Math.sin(u * 3) * 10;

            positions[i * 3] = rx + (Math.random() - 0.5) * 8;
            positions[i * 3 + 1] = ry + (Math.random() - 0.5) * 8;
            positions[i * 3 + 2] = rz + (Math.random() - 0.5) * 8;

            const mixFactor = Math.random();
            const pColor = colorSignal.clone().lerp(colorAssent, mixFactor);
            colors[i * 3] = pColor.r;
            colors[i * 3 + 1] = pColor.g;
            colors[i * 3 + 2] = pColor.b;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 1.8,
            vertexColors: true,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending
        });

        const points = new THREE.Points(geometry, material);
        scene.add(points);

        // Parallax mouse interaction
        let mouseX = 0;
        let mouseY = 0;
        window.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX / window.innerWidth - 0.5) * 0.5;
            mouseY = (e.clientY / window.innerHeight - 0.5) * 0.5;
        });

        function animate() {
            requestAnimationFrame(animate);
            points.rotation.y += 0.002;
            points.rotation.x += (mouseY - points.rotation.x) * 0.05;
            points.rotation.y += (mouseX - points.rotation.y) * 0.05;
            renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
            if (!container) return;
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });
    }

    // --------------------------------------------------------------------------
    // 6. RADIAL CONSENT LENS (CURSOR UNBLUR OVER HERO PORTRAIT)
    // --------------------------------------------------------------------------
    function initConsentLens() {
        const frame = document.querySelector('.hero-portrait-frame');
        const overlay = document.querySelector('.consent-lens-overlay');
        const portraitImg = document.querySelector('.hero-portrait-img');
        if (!frame || !overlay || !portraitImg) return;

        // Set the background source for lens overlay
        overlay.style.setProperty('--lens-src', `url('${portraitImg.src}')`);

        frame.addEventListener('mousemove', (e) => {
            const rect = frame.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            overlay.style.setProperty('--lens-x', `${x}%`);
            overlay.style.setProperty('--lens-y', `${y}%`);
        });
    }

    // --------------------------------------------------------------------------
    // 7. SIGNATURE PINNED SCROLL DEMO (§4.1 #3)
    // --------------------------------------------------------------------------
    function initPinnedDemo() {
        if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined' || isReducedMotion) return;

        const wrapper = document.querySelector('.pinned-demo-wrapper');
        const sticky = document.querySelector('.pinned-demo-sticky');
        if (!wrapper || !sticky) return;

        const railBar = document.querySelector('.demo-rail-bar');
        const railItems = document.querySelectorAll('.rail-stage-item');
        const faceBoxes = document.querySelectorAll('.face-box-target');
        const faceBlurs = document.querySelectorAll('.face-blur-cover');
        const notifyCard = document.querySelector('.demo-notify-card');

        // Create ScrollTrigger timeline for 400vh scroll pin
        const st = ScrollTrigger.create({
            trigger: wrapper,
            start: 'top top',
            end: 'bottom bottom',
            scrub: 0.5,
            onUpdate: (self) => {
                const progress = self.progress;

                // 1. Update rail progress bar height
                if (railBar) railBar.style.height = `${progress * 100}%`;

                // 2. Stage calculation (0.0 to 1.0 divided into 5 stages)
                let activeIndex = 0;
                if (progress > 0.8) activeIndex = 4;
                else if (progress > 0.6) activeIndex = 3;
                else if (progress > 0.4) activeIndex = 2;
                else if (progress > 0.2) activeIndex = 1;

                railItems.forEach((item, idx) => {
                    if (idx === activeIndex) item.classList.add('active');
                    else item.classList.remove('active');
                });

                // STAGE 01: DETECT (Draw bounding boxes)
                if (progress >= 0.1) {
                    faceBoxes.forEach(box => box.classList.add('detect-active'));
                } else {
                    faceBoxes.forEach(box => box.classList.remove('detect-active'));
                }

                // STAGE 02: MATCH (Readouts d = 0.41 / d = 0.77)
                if (progress >= 0.3) {
                    document.getElementById('readout-1').textContent = 'd = 0.41 ✓ MATCH';
                    document.getElementById('readout-2').textContent = 'd = 0.77 ✗ MISMATCH';
                    document.getElementById('readout-3').textContent = 'd = 0.82 ✗ MISMATCH';
                }

                // STAGE 03: BLUR (Gaussian blur all non-uploader faces)
                if (progress >= 0.5) {
                    faceBlurs.forEach((blur, idx) => {
                        // Skip uploader face (idx === 0)
                        if (idx !== 0) blur.classList.add('blurred');
                    });
                } else {
                    faceBlurs.forEach(blur => blur.classList.remove('blurred'));
                }

                // STAGE 04: NOTIFY (Slide in consent notification card)
                if (progress >= 0.7) {
                    notifyCard?.classList.add('visible');
                } else {
                    notifyCard?.classList.remove('visible');
                }

                // STAGE 05: REVEAL (Unblur approved target face)
                if (progress >= 0.9) {
                    const targetFaceBlur = document.getElementById('blur-target-reveal');
                    if (targetFaceBlur) targetFaceBlur.classList.remove('blurred');
                }
            }
        });
    }

    // --------------------------------------------------------------------------
    // 8. CHARACTER BLUR RESOLVE ANIMATION
    // --------------------------------------------------------------------------
    function initCharacterBlurResolve() {
        const blurHeadlines = document.querySelectorAll('.char-blur-resolve');
        blurHeadlines.forEach((headline) => {
            const text = headline.textContent.trim();
            headline.textContent = '';
            
            [...text].forEach((char, idx) => {
                const span = document.createElement('span');
                span.className = 'char-blur-wrap';
                span.textContent = char === ' ' ? '\u00A0' : char;
                span.style.transitionDelay = `${idx * 25}ms`;
                headline.appendChild(span);
            });

            // Trigger resolve on scroll enter
            if (typeof ScrollTrigger !== 'undefined') {
                ScrollTrigger.create({
                    trigger: headline,
                    start: 'top 85%',
                    onEnter: () => {
                        headline.querySelectorAll('.char-blur-wrap').forEach(span => span.classList.add('in-view'));
                    }
                });
            } else {
                headline.querySelectorAll('.char-blur-wrap').forEach(span => span.classList.add('in-view'));
            }
        });
    }

    // --------------------------------------------------------------------------
    // 9. KATEX MATH SANDBOX & LIVE SIGMA SLIDER (§4.1 #6)
    // --------------------------------------------------------------------------
    function initMathSandbox() {
        // Render KaTeX Formulas
        if (typeof katex !== 'undefined') {
            const eqEuclidean = document.getElementById('eq-euclidean');
            const eqGaussian = document.getElementById('eq-gaussian');

            if (eqEuclidean) {
                katex.render("d(p, q) = \\sqrt{\\sum_{i=1}^{128} (p_i - q_i)^2}", eqEuclidean, { displayMode: true });
            }
            if (eqGaussian) {
                katex.render("G(x, y) = \\frac{1}{2\\pi\\sigma^2} e^{-\\frac{x^2 + y^2}{2\\sigma^2}}", eqGaussian, { displayMode: true });
            }
        }

        // Live Sigma Slider Interaction
        const slider = document.getElementById('sigma-range-slider');
        const readout = document.getElementById('sigma-value-readout');
        const simImg = document.getElementById('sim-face-image');

        if (slider && readout && simImg) {
            slider.addEventListener('input', (e) => {
                const val = e.target.value;
                readout.textContent = `σ = ${val}`;
                simImg.style.filter = `blur(${val}px)`;
            });
        }
    }

    // --------------------------------------------------------------------------
    // 10. SCROLLTRIGGERS & ANIMATIONS
    // --------------------------------------------------------------------------
    function initScrollTriggers() {
        if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

        // Section Scanline Divider Sweep
        document.querySelectorAll('.section-scanline-divider').forEach((divider) => {
            ScrollTrigger.create({
                trigger: divider,
                start: 'top 80%',
                onEnter: () => {
                    divider.querySelector('.scanline-pulse')?.classList.add('sweep');
                }
            });
        });

        // 5-Step Process Rail Slide-in & SVG Line Draw
        const processNodes = document.querySelectorAll('.process-card-content');
        processNodes.forEach((node, idx) => {
            gsap.from(node, {
                scrollTrigger: {
                    trigger: node,
                    start: 'top 85%',
                },
                x: idx % 2 === 0 ? -50 : 50,
                opacity: 0,
                duration: 0.8,
                ease: 'cubic-bezier(0.16, 1, 0.3, 1)'
            });
        });

        // Metrics Count-up Band
        const metricNumbers = document.querySelectorAll('.metric-number');
        metricNumbers.forEach((el) => {
            const targetVal = parseFloat(el.getAttribute('data-target') || '0');
            const prefix = el.getAttribute('data-prefix') || '';
            const suffix = el.getAttribute('data-suffix') || '';

            ScrollTrigger.create({
                trigger: el,
                start: 'top 90%',
                onEnter: () => {
                    gsap.to({ val: 0 }, {
                        val: targetVal,
                        duration: 1.6,
                        ease: 'power2.out',
                        onUpdate: function () {
                            el.textContent = prefix + this.targets()[0].val.toFixed(targetVal % 1 === 0 ? 0 : 2) + suffix;
                        }
                    });
                }
            });
        });

        // Footer Wordmark Gradient Fill on Scroll-in
        const footerWordmark = document.querySelector('.footer-wordmark');
        if (footerWordmark) {
            ScrollTrigger.create({
                trigger: footerWordmark,
                start: 'top 85%',
                onEnter: () => footerWordmark.classList.add('filled')
            });
        }
    }

    // --------------------------------------------------------------------------
    // 11. VANILLA-TILT CARD EFFECT (§4.1 #7)
    // --------------------------------------------------------------------------
    function initTiltCards() {
        if (typeof VanillaTilt === 'undefined' || isReducedMotion) return;

        const tiltCards = document.querySelectorAll('.feature-tilt-card, .comparison-card');
        VanillaTilt.init(Array.from(tiltCards), {
            max: 6,
            speed: 400,
            glare: true,
            'max-glare': 0.15,
            scale: 1.02
        });
    }

})();
