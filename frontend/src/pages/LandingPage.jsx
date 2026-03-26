import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LandingPage.css';
import logo from '../assets/logo.png';

const LandingPage = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const canvasRef = useRef(null);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [videoModalOpen, setVideoModalOpen] = useState(false);

    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    const handleGetStarted = (e) => {
        if (e) e.preventDefault();
        if (user) {
            navigate('/dashboard');
        } else {
            navigate('/login');
        }
    };

    const openVideoModal = (e) => {
        if (e) e.preventDefault();
        setVideoModalOpen(true);
    };

    const closeVideoModal = (e) => {
        if (e && e.target !== e.currentTarget && !e.target.closest('.video-modal-close')) return;
        setVideoModalOpen(false);
    };

    // Aurora Canvas Animation
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        let W, H, blobs;
        const BLOBS = [
            { x: 0.2, y: 0.4, r: 0.5, hue: 108, alpha: 0.18 }, // sage green
            { x: 0.8, y: 0.55, r: 0.45, hue: 205, alpha: 0.14 }, // steel blue
            { x: 0.5, y: 0.25, r: 0.38, hue: 130, alpha: 0.10 }, // light green
            { x: 0.15, y: 0.75, r: 0.3, hue: 195, alpha: 0.10 }, // pale blue
            { x: 0.88, y: 0.3, r: 0.32, hue: 90, alpha: 0.09 }, // yellow-green
        ];

        function resize() {
            W = canvas.width = window.innerWidth;
            H = -200 + (canvas.parentElement.offsetHeight || window.innerHeight);
            canvas.height = H;
            blobs = BLOBS.map(b => ({
                ...b,
                cx: b.x * W, cy: b.y * H,
                rx: b.r * W, ry: b.r * H,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.2,
                phase: Math.random() * Math.PI * 2,
                speed: 0.0003 + Math.random() * 0.0004,
            }));
        }

        let animationFrameId;
        let t = 0;
        function draw() {
            ctx.clearRect(0, 0, W, H);
            t++;

            if (blobs) {
                for (const b of blobs) {
                    const ox = Math.sin(t * b.speed + b.phase) * W * 0.12;
                    const oy = Math.cos(t * b.speed * 0.7 + b.phase + 1) * H * 0.08;
                    const x = b.cx + ox;
                    const y = b.cy + oy;

                    const pulse = 1 + 0.08 * Math.sin(t * b.speed * 2 + b.phase);
                    const rx = b.rx * pulse;
                    const ry = b.ry * pulse;

                    const grad = ctx.createRadialGradient(x, y, 0, x, y, Math.max(rx, ry));
                    grad.addColorStop(0, `hsla(${b.hue}, 90%, 60%, ${b.alpha})`);
                    grad.addColorStop(0.4, `hsla(${b.hue}, 80%, 50%, ${b.alpha * 0.5})`);
                    grad.addColorStop(1, `hsla(${b.hue}, 70%, 40%, 0)`);

                    ctx.save();
                    ctx.filter = 'blur(60px)';
                    ctx.scale(rx / Math.max(rx, ry), ry / Math.max(rx, ry));
                    ctx.beginPath();
                    ctx.arc(x / (rx / Math.max(rx, ry)), y / (ry / Math.max(rx, ry)), Math.max(rx, ry), 0, Math.PI * 2);
                    ctx.fillStyle = grad;
                    ctx.fill();
                    ctx.restore();
                }
            }

            animationFrameId = requestAnimationFrame(draw);
        }

        resize();
        window.addEventListener('resize', resize);
        draw();

        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animationFrameId);
        }
    }, []);

    // Scroll Observer for Navbar, Reveal and Counter
    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 40);
        };
        window.addEventListener('scroll', handleScroll, { passive: true });

        // Reveal effect
        const revealEls = document.querySelectorAll('.reveal');
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
        revealEls.forEach(el => revealObserver.observe(el));

        // Counters
        const counters = document.querySelectorAll('.counter[data-target]');
        const easeOut = (t) => 1 - Math.pow(1 - t, 3);
        const animate = (el, target, duration = 1800) => {
            const start = performance.now();
            const update = (now) => {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                const value = Math.round(easeOut(progress) * target);
                el.textContent = value >= 1000 ? value.toLocaleString() : value;
                if (progress < 1) requestAnimationFrame(update);
            };
            requestAnimationFrame(update);
        };
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.dataset.target, 10);
                    animate(el, target, target > 1000 ? 2200 : 1200);
                    counterObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });
        counters.forEach(c => counterObserver.observe(c));

        // Card Hover Glow
        const cards = document.querySelectorAll('.feature-card, .model-card, .pricing-card, .stat-card');
        const handleMouseMove = (e) => {
            const card = e.currentTarget;
            const rect = card.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty('--mouse-x', `${x}%`);
            card.style.setProperty('--mouse-y', `${y}%`);
        };
        cards.forEach(card => card.addEventListener('mousemove', handleMouseMove));

        return () => {
            window.removeEventListener('scroll', handleScroll);
            revealObserver.disconnect();
            counterObserver.disconnect();
            cards.forEach(card => card.removeEventListener('mousemove', handleMouseMove));
        };
    }, []);

    return (
        <div className="landing-page-root">
            {/* Nav */}
            <nav className={`navbar ${scrolled ? 'scrolled' : ''}`} id="navbar">
                <div className="nav-container">
                    <a href="/" className="nav-logo">
                        <img src={logo} alt="Logo" className="logo-img" />
                        <span className="logo-text">AURORA <span className="logo-sentinel">SENTINEL</span></span>
                    </a>
                    <ul className={`nav-links ${mobileMenuOpen ? 'mobile-open' : ''}`} id="nav-links">
                        <li><a href="#features" className="nav-link">Features</a></li>
                        <li><a href="#how-it-works" className="nav-link">Architecture</a></li>
                        <li><a href="#accuracy" className="nav-link">Performance</a></li>
                        <li><a href="#comparison" className="nav-link">Compare</a></li>
                        <li><a href="#tech" className="nav-link">AI Models</a></li>
                        <li><a href="#pricing" className="nav-link">Pricing</a></li>
                    </ul>
                    <div className="nav-actions">
                        <button onClick={handleGetStarted} className="btn btn-primary">Get Started</button>
                    </div>
                    <button className={`hamburger ${mobileMenuOpen ? 'open' : ''}`} onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                        <span></span><span></span><span></span>
                    </button>
                </div>
            </nav>

            {/* Hero */}
            <section className="hero" id="home">
                <canvas ref={canvasRef} id="aurora-canvas"></canvas>
                <div className="hero-grid-overlay"></div>
                <div className="hero-content">
                    <div className="hero-badge reveal">
                        <span className="badge-dot"></span>
                        <span>Now Live — AURORA SENTINEL</span>
                    </div>
                    <h1 className="hero-title reveal reveal-delay-1">
                        The Future of <span className="accent-text">AI-Powered</span> <br />Threat Detection
                    </h1>
                    <p className="hero-subtitle reveal reveal-delay-2">
                        Revolutionary dual-brain intelligence that thinks like a human security expert. Detect real violence with <strong>97% accuracy</strong> in under <strong>100ms</strong> — distinguishing real fights from sports, drama, and everyday activity.
                    </p>
                    <div className="hero-stats reveal reveal-delay-3">
                        <div className="stat-pill"><span className="stat-value">97%</span><span className="stat-label">Accuracy</span></div>
                        <div className="stat-divider"></div>
                        <div className="stat-pill"><span className="stat-value">&lt;100ms</span><span className="stat-label">Latency</span></div>
                        <div className="stat-divider"></div>
                        <div className="stat-pill"><span className="stat-value">4</span><span className="stat-label">AI Models</span></div>
                        <div className="stat-divider"></div>
                        <div className="stat-pill"><span className="stat-value">0</span><span className="stat-label">False Positives on Sports</span></div>
                    </div>
                    <div className="hero-actions reveal reveal-delay-4">
                        <button onClick={handleGetStarted} className="btn btn-primary btn-lg">Get Started</button>
                        <button onClick={openVideoModal} className="btn btn-outline btn-lg">Demo Video</button>
                    </div>
                    <div className="hero-code reveal reveal-delay-4">
                        <div className="code-header">
                            <span className="code-dot red"></span><span className="code-dot yellow"></span><span className="code-dot green"></span>
                            <span className="code-filename">aurora_demo.py</span>
                        </div>
                        <pre className="code-body"><code>
                            <span className="code-comment"># 🚨 Real fight detected in real-time</span><br/>
                            ml_score  <span className="code-op">=</span> <span className="code-num">85</span>   <span className="code-comment"># Physical patterns detected</span><br/>
                            ai_score  <span className="code-op">=</span> <span className="code-num">90</span>   <span className="code-comment"># Context: real fight confirmed</span><br/>
                            final     <span className="code-op">=</span> <span className="code-num">88.5</span> <span className="code-comment"># → 🚨 ALERT TRIGGERED</span><br/><br/>
                            <span className="code-comment"># ✅ Boxing match — no false positive</span><br/>
                            ml_score  <span className="code-op">=</span> <span className="code-num">90</span>   <span className="code-comment"># Intense punching detected</span><br/>
                            ai_score  <span className="code-op">=</span> <span className="code-num">20</span>   <span className="code-comment"># Context: boxing with gloves</span><br/>
                            final     <span className="code-op">=</span> <span className="code-num">41.0</span> <span className="code-comment"># → ✅ No Alert (Correct!)</span>
                        </code></pre>
                    </div>
                </div>
            </section>

            {/* Trusted By */}
            <section className="trusted-section">
                <div className="container">
                    <p className="trusted-label">Powered by world-class AI technologies</p>
                    <div className="trusted-logos">
                        {[ 'Google Gemini', 'YOLOv8', 'MediaPipe', 'Qwen2-VL', 'FastAPI', 'Ollama' ].map(tech => (
                            <div key={tech} className="trust-logo"><span>{tech}</span></div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="features section" id="features">
                <div className="container">
                    <div className="section-header reveal">
                        <span className="section-tag">Core Capabilities</span>
                        <h2 className="section-title">Everything You Need to <span className="accent-text">Secure Your Space</span></h2>
                    </div>
                    <div className="features-grid">
                        <div className="feature-card reveal">
                            <div className="feature-icon feature-icon--teal">🚀</div>
                            <h3>Blazing Fast Performance</h3>
                            <p>Under 100ms latency for ML detection. Full AI analysis in 2–5 seconds with GPU acceleration.</p>
                        </div>
                        <div className="feature-card reveal reveal-delay-1">
                            <div className="feature-icon feature-icon--purple">🎯</div>
                            <h3>Unmatched Accuracy</h3>
                            <p>97% accuracy with Gemini API integration. Zero false positives on sports and boxing.</p>
                        </div>
                        <div className="feature-card reveal reveal-delay-2">
                            <div className="feature-icon feature-icon--blue">🧠</div>
                            <h3>Intelligent Differentiation</h3>
                            <p>Distinguishes real fights from boxing, drama, sports, and normal activity.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section className="how-it-works section" id="how-it-works">
                <div className="container">
                    <div className="section-header reveal">
                        <span className="section-tag">The Architecture</span>
                        <h2 className="section-title">Dual-Brain Intelligence <span className="accent-text">at Work</span></h2>
                    </div>
                    <div className="pipeline">
                        {[
                            { num: '01', title: 'Video Input', desc: 'Supports RTSP, webcams, and files. Smart buffering keeps 10s of history.' },
                            { num: '02', title: 'ML Detection Engine', desc: 'YOLOv8 and MediaPipe produced a physical risk score in 10-50ms.' },
                            { num: '03', title: 'AI Intelligence Layer', desc: 'Four VLMs operating in priority order deliver context and reasoning.' },
                            { num: '04', title: 'Weighted Fusion', desc: 'ML reflexes + AI context combined for the final decision.' },
                            { num: '05', title: 'Alert & Response', desc: 'Instant WebSocket broadcasts and clip extraction on detection.' }
                        ].map(step => (
                            <React.Fragment key={step.num}>
                                <div className="pipeline-step reveal">
                                    <div className="pipeline-step-num">{step.num}</div>
                                    <div className="pipeline-text">
                                        <h3>{step.title}</h3>
                                        <p>{step.desc}</p>
                                    </div>
                                </div>
                                {step.num !== '05' && <div className="pipeline-connector reveal"></div>}
                            </React.Fragment>
                        ))}
                    </div>
                </div>
            </section>

            {/* Performance Stats */}
            <section className="stats-section section" id="accuracy">
                <div className="container">
                    <div className="stats-grid">
                        {[
                            { val: '97', unit: '%', desc: 'Detection Accuracy' },
                            { val: '<100', unit: 'ms', desc: 'Detection Latency' },
                            { val: '10000', unit: '+', desc: 'Videos Tested' },
                            { val: '4', unit: '', desc: 'AI Providers' },
                            { val: '0', unit: '', desc: 'False Positives' },
                            { val: '99.9', unit: '%', desc: 'Service Uptime' }
                        ].map((stat, i) => (
                            <div key={i} className={`stat-card reveal reveal-delay-${i % 4}`}>
                                <div className="stat-number counter" data-target={stat.val.replace('<', '')}>{stat.val.includes('<') ? '<' : ''}0</div>
                                <div className="stat-unit">{stat.unit}</div>
                                <div className="stat-desc">{stat.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Comparison */}
            <section className="comparison section" id="comparison">
                <div className="container">
                    <div className="section-header reveal">
                        <h2 className="section-title">AURORA vs <span className="accent-text">Traditional</span></h2>
                    </div>
                    <div className="table-wrapper reveal">
                        <table className="compare-table">
                            <thead>
                                <tr><th>Feature</th><th>Traditional</th><th className="col-aurora">AURORA</th></tr>
                            </thead>
                            <tbody>
                                {[
                                    ['Detection', 'Motion based', 'Dual-tier ML+AI'],
                                    ['Context', 'None', 'Full Comprehension'],
                                    ['Accuracy', '60-70%', '97%'],
                                    ['Latency', '500ms+', '<100ms']
                                ].map(([feat, trad, aur], i) => (
                                    <tr key={i}><td>{feat}</td><td>{trad}</td><td className="col-aurora">{aur}</td></tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            {/* AI Models */}
            <section className="tech-section section" id="tech">
                <div className="container">
                    <div className="models-grid">
                        {[
                            { name: 'Qwen2-VL-2B', priority: '1', loc: 'Local', acc: '85%' },
                            { name: 'Ollama LLaVA', priority: '2', loc: 'Local', acc: '80%' },
                            { name: 'Gemini 1.5 Pro', priority: '3', loc: 'Cloud', acc: '97%' },
                            { name: 'HuggingFace', priority: '4', loc: 'Cloud', acc: 'Fallback' }
                        ].map((model, i) => (
                            <div key={i} className={`model-card reveal reveal-delay-${i}`}>
                                <div className="model-card-badge">P{model.priority} · {model.loc}</div>
                                <h3>{model.name}</h3>
                                <div className="metric"><span className="metric-val">{model.acc}</span><span className="metric-label">Accuracy</span></div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Pricing */}
            <section className="pricing section" id="pricing">
                <div className="container">
                    <div className="section-header reveal">
                        <h2 className="section-title">Choose Your <span className="accent-text">Level</span></h2>
                    </div>
                    <div className="pricing-grid">
                        {[
                            { name: 'Starter', price: 'Free', btn: 'Get Started Free', featured: false },
                            { name: 'Pro', price: 'Gemini API', btn: 'Activate Gemini API', featured: true },
                            { name: 'Enterprise', price: 'Custom', btn: 'Contact Sales', featured: false }
                        ].map(plan => (
                            <div key={plan.name} className={`pricing-card reveal ${plan.featured ? 'pricing-card--featured' : ''}`}>
                                <h3>{plan.name}</h3>
                                <div className="price">{plan.price}</div>
                                <button onClick={plan.btn.includes('Contact') ? null : handleGetStarted} className={`btn btn-full ${plan.featured ? 'btn-primary' : 'btn-outline'}`}>{plan.btn}</button>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="cta-section section" id="cta">
                <div className="container">
                    <div className="cta-card reveal">
                        <div className="cta-content">
                            <h2>Ready to Secure Your Space?</h2>
                            <p>Join the future of intelligence-led security. Deploy Aurora Sentinel today.</p>
                            <div className="cta-actions">
                                <button onClick={handleGetStarted} className="btn btn-primary btn-lg">Get Started Now</button>
                                <a href="https://github.com/KrishnaRajput07/AURORA-SENTINEL" target="_blank" rel="noreferrer" className="btn btn-outline btn-lg">View on GitHub</a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <div className="container">
                    <div className="footer-grid">
                        <div className="footer-brand">
                            <span className="logo-text">AURORA <span className="logo-sentinel">SENTINEL</span></span>
                            <p>AI-Powered Threat Detection. Built for safer communities.</p>
                        </div>
                        <div className="footer-links-col">
                            <h4>Product</h4>
                            <ul>
                                <li><a href="#features">Features</a></li>
                                <li><a href="#how-it-works">Architecture</a></li>
                                <li><a href="#tech">AI Models</a></li>
                            </ul>
                        </div>
                    </div>
                    <div className="footer-bottom">
                        <p>© 2026 AURORA AI Fight Detection.</p>
                    </div>
                </div>
            </footer>

            {/* Video Modal */}
            {videoModalOpen && (
                <div className="video-modal-overlay active" onClick={closeVideoModal}>
                    <div className="video-modal-content">
                        <button className="video-modal-close" onClick={closeVideoModal}>&times;</button>
                        <div className="video-modal-wrapper">
                            <iframe 
                                title="demo"
                                src="https://www.youtube-nocookie.com/embed/343zo4YIZ1M" 
                                frameBorder="0" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowFullScreen
                            ></iframe>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LandingPage;
