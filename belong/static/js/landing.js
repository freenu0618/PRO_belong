// static/js/landing.js
// Landing Page GSAP Animations

document.addEventListener("DOMContentLoaded", () => {
    if (typeof gsap === 'undefined') {
        console.warn('[landing.js] GSAP not loaded');
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Hero Animations (On Load)
    gsap.from(".gsap-hero", {
        y: 50,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        ease: "power3.out"
    });

    // Problem Section Animations (Scroll)
    gsap.utils.toArray(".gsap-reveal").forEach(elem => {
        gsap.to(elem, {
            scrollTrigger: {
                trigger: elem,
                start: "top 85%",
                toggleActions: "play none none reverse"
            },
            y: 0,
            opacity: 1,
            duration: 0.8,
            ease: "power2.out"
        });
    });

    // Solution Section Left/Right
    gsap.from(".gsap-reveal-left", {
        scrollTrigger: {
            trigger: ".solution-section",
            start: "top 70%"
        },
        x: -50,
        opacity: 0,
        duration: 1,
        ease: "power3.out"
    });

    gsap.utils.toArray(".gsap-reveal-right").forEach((elem, i) => {
        gsap.from(elem, {
            scrollTrigger: {
                trigger: elem,
                start: "top 90%",
            },
            x: 50,
            opacity: 0,
            duration: 0.8,
            delay: i * 0.1,
            ease: "power3.out"
        });
    });

    // Solution Steps Highlight Animation (Scroll-based)
    gsap.utils.toArray(".solution-step").forEach(step => {
        ScrollTrigger.create({
            trigger: step,
            start: "top 80%",
            end: "bottom 20%",
            onEnter: () => step.classList.add("active"),
            onLeaveBack: () => step.classList.remove("active"),
        });
    });

    // CTA Scale Up
    gsap.from(".gsap-scale-up", {
        scrollTrigger: {
            trigger: ".cta-section",
            start: "top 80%"
        },
        scale: 0.9,
        opacity: 0,
        duration: 0.8,
        stagger: 0.2,
        ease: "back.out(1.7)"
    });
});
