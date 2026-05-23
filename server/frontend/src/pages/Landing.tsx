import { Link } from "react-router-dom";
import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import { trackPageView } from "../lib/api";
import { motion, useInView } from "framer-motion";
import {
  ArrowRight, BarChart3, Bot, Check, ChevronDown, Cpu,
  Download, Globe, Menu, MessageSquare, Rocket, Send, Shield,
  Sparkles, Target, TrendingUp, X, Zap,
} from "lucide-react";

const FEATURES = [
  { icon: Target, title: "SerpAPI ile Sıralama Takibi", desc: "Anahtar kelimeleriniz Google'da kaçıncı sırada — gerçek zamanlı.", color: "from-blue-500 to-cyan-500" },
  { icon: Globe, title: "Çoklu Proxy Rotasyonu", desc: "Webshare entegrasyonu, otomatik test, sağlıklı proxy havuzu.", color: "from-purple-500 to-pink-500" },
  { icon: Zap, title: "Akıllı Trafik Simülasyonu", desc: "Bounce rate, mobil/desktop oranı, organik referrer karışımı.", color: "from-yellow-500 to-orange-500" },
  { icon: BarChart3, title: "Canlı Dashboard", desc: "Saatlik trafik grafikleri, kampanya performans analizi, Telegram raporları.", color: "from-green-500 to-emerald-500" },
  { icon: Shield, title: "Güvenli Lisans Sistemi", desc: "Tek cihaz kilidi, donanım parmak izi, anlık doğrulama.", color: "from-red-500 to-pink-500" },
  { icon: Rocket, title: "Hazır .exe", desc: "Kurulum yok — indir, giriş yap, çalıştır.", color: "from-indigo-500 to-purple-500" },
];

const STATS = [
  { value: 1247, suffix: "+", label: "Aktif Kullanıcı" },
  { value: 50, suffix: "M+", label: "Yapılan Ziyaret" },
  { value: 98, suffix: "%", label: "Başarı Oranı" },
  { value: 24, suffix: "/7", label: "Çalışma Süresi" },
];

const STEPS = [
  {
    icon: Download,
    title: "1. Programı İndir",
    desc: "Aktif lisans aldıktan sonra hesabından tek tıkla .exe dosyasını al.",
    color: "bg-blue-500",
  },
  {
    icon: Cpu,
    title: "2. Bilgisayarına Kur",
    desc: "Çift tıkla, hesabınla giriş yap. Tüm ayarlar otomatik hazır.",
    color: "bg-purple-500",
  },
  {
    icon: Rocket,
    title: "3. Botu Çalıştır",
    desc: "Kampanyanı oluştur, başlat. Telegram'dan canlı takip et.",
    color: "bg-pink-500",
  },
];

const TESTIMONIALS = [
  {
    name: "Mehmet K.",
    role: "Dijital Pazarlamacı",
    text: "3 ay içinde 'web tasarım' kelimesinde 2. sayfadan 1. sayfaya çıktım. Müşterilerime tavsiye ediyorum.",
    rating: 5,
  },
  {
    name: "Ayşe S.",
    role: "SEO Uzmanı",
    text: "10+ siteyi tek panelden yönetiyorum. Telegram raporları sayesinde uzaktayken bile takip ediyorum.",
    rating: 5,
  },
  {
    name: "Burak T.",
    role: "E-ticaret Sahibi",
    text: "Webshare entegrasyonu harika. Manuel proxy uğraşı bitti. Trafik realistik ve sıralamalar arttı.",
    rating: 5,
  },
];

const FAQS = [
  {
    q: "Bot kullanmak Google tarafından cezalandırılır mı?",
    a: "Botumuz organik trafik kalıplarını taklit eder — gerçek tarayıcı parmak izleri, çeşitli referrer kaynakları, doğal session süreleri. Risk minimumdadır ama her SEO faaliyeti gibi dikkatli kullanılmalı.",
  },
  {
    q: "Lisansım kaç bilgisayarda çalışır?",
    a: "Lisansınız tek bir bilgisayara kilitlenir. Yeni cihaza geçmek için 'Cihaz Sıfırlama' paketi (15 ₺) satın alabilirsiniz.",
  },
  {
    q: "Botu çalıştırmak için bilgisayarımı sürekli açık tutmam gerekir mi?",
    a: "Evet — bot kullanıcının bilgisayarında çalışır. Bilgisayar kapalıysa bot duraklar. VPS veya sürekli açık bir bilgisayar tavsiye edilir.",
  },
  {
    q: "Proxyleri nereden alacağım?",
    a: "Webshare gibi proxy sağlayıcılarına kayıt ol. Hesabımız üzerinden Webshare API anahtarını gir, otomatik proxy yönetimi.",
  },
  {
    q: "İptal etmek istersem ne olur?",
    a: "İstediğin zaman iptal edebilirsin. Ödediğin döneme kadar kullanmaya devam edersin, otomatik yenilenmez.",
  },
  {
    q: "Telegram entegrasyonu nasıl çalışır?",
    a: "Bot başlangıcında /api/auth Telegram chat_id'i girersin. Anlık bildirimler ve /stats /rank gibi komutlarla uzaktan kontrol.",
  },
];

type PricePeriod = "daily" | "monthly" | "yearly";

const PRICING: Record<PricePeriod, { label: string; price: string; unit: string; saving: string | null; savingAmt: string | null; badge: string | null }> = {
  daily: { label: "Günlük Lisans", price: "300", unit: "gün", saving: null, savingAmt: null, badge: null },
  monthly: { label: "Aylık Lisans", price: "5.000", unit: "ay", saving: "%44", savingAmt: "4.000 ₺", badge: "EN POPÜLER" },
  yearly: { label: "Yıllık Lisans", price: "40.000", unit: "yıl", saving: "%63", savingAmt: "69.500 ₺", badge: "EN İYİ DEĞER" },
};

const PLAN_FEATURES = [
  "Sınırsız kampanya",
  "Sınırsız ziyaret simülasyonu",
  "Webshare & özel proxy desteği",
  "Telegram bot komutları",
  "Canlı istatistikler & raporlar",
  "Donanım parmak izi koruması",
  "7/24 destek",
];

// ── Three.js 3D Hero Visual ──────────────────────────────────────────────────

function HeroVisual() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    const W = el.offsetWidth;
    const H = el.offsetHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 100);
    camera.position.z = 6;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0, 0);
    renderer.domElement.style.cssText = "position:absolute;inset:0;width:100%;height:100%;border-radius:1.5rem;";
    el.appendChild(renderer.domElement);

    // ── 1. Fibonacci dot-globe ──────────────────────────────────────────────
    const GLOBE_R = 1.7;
    const GLOBE_N = 2200;
    const gPos = new Float32Array(GLOBE_N * 3);
    const gCol = new Float32Array(GLOBE_N * 3);
    const PHI = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < GLOBE_N; i++) {
      const y = 1 - (i / (GLOBE_N - 1)) * 2;
      const r = Math.sqrt(1 - y * y);
      const theta = PHI * i;
      gPos[i * 3] = Math.cos(theta) * r * GLOBE_R;
      gPos[i * 3 + 1] = y * GLOBE_R;
      gPos[i * 3 + 2] = Math.sin(theta) * r * GLOBE_R;
      const t = (y + 1) / 2;
      gCol[i * 3] = 0.38 + t * 0.28;
      gCol[i * 3 + 1] = 0.28 + t * 0.12;
      gCol[i * 3 + 2] = 0.85 + t * 0.15;
    }
    const globeGeo = new THREE.BufferGeometry();
    globeGeo.setAttribute("position", new THREE.BufferAttribute(gPos, 3));
    globeGeo.setAttribute("color", new THREE.BufferAttribute(gCol, 3));
    const globe = new THREE.Points(globeGeo, new THREE.PointsMaterial({
      size: 0.022, vertexColors: true, transparent: true, opacity: 0.9, sizeAttenuation: true,
    }));
    scene.add(globe);

    // ── 2. Orbit rings (dot circles, each tilted) ───────────────────────────
    const makeRing = (rad: number, n: number, color: number, tiltX: number, tiltZ: number) => {
      const pos = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        pos[i * 3] = Math.cos(a) * rad;
        pos[i * 3 + 2] = Math.sin(a) * rad;
      }
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      const ring = new THREE.Points(g, new THREE.PointsMaterial({
        size: 0.045, color, transparent: true, opacity: 0.65, sizeAttenuation: true,
      }));
      ring.rotation.x = tiltX;
      ring.rotation.z = tiltZ;
      return ring;
    };
    const ring1 = makeRing(2.3, 140, 0x818cf8, 1.1, 0.2);
    const ring2 = makeRing(2.7, 90, 0xc084fc, 0.5, 0.8);
    const ring3 = makeRing(2.0, 70, 0x38bdf8, 1.9, 0.4);
    scene.add(ring1, ring2, ring3);

    // ── 3. Background nebula ────────────────────────────────────────────────
    const NEB_N = 600;
    const nPos = new Float32Array(NEB_N * 3);
    for (let i = 0; i < NEB_N; i++) {
      nPos[i * 3] = (Math.random() - 0.5) * 14;
      nPos[i * 3 + 1] = (Math.random() - 0.5) * 14;
      nPos[i * 3 + 2] = (Math.random() - 0.5) * 6 - 2;
    }
    const nebGeo = new THREE.BufferGeometry();
    nebGeo.setAttribute("position", new THREE.BufferAttribute(nPos, 3));
    const nebula = new THREE.Points(nebGeo, new THREE.PointsMaterial({
      size: 0.012, color: 0x6366f1, transparent: true, opacity: 0.35,
    }));
    scene.add(nebula);

    // ── Mouse parallax ──────────────────────────────────────────────────────
    let tgtX = 0, tgtY = 0, curX = 0, curY = 0;
    const onMouse = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      tgtX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      tgtY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMouse);

    // ── Render loop ─────────────────────────────────────────────────────────
    let raf: number;
    const clock = new THREE.Clock();
    const tick = () => {
      raf = requestAnimationFrame(tick);
      const t = clock.getElapsedTime();
      curX += (tgtX - curX) * 0.04;
      curY += (tgtY - curY) * 0.04;

      globe.rotation.y = t * 0.14 + curX * 0.35;
      globe.rotation.x = curY * 0.18;

      ring1.rotation.y = t * 0.28;
      ring2.rotation.y = -t * 0.18;
      ring3.rotation.y = t * 0.22;

      nebula.rotation.y = t * 0.018;
      renderer.render(scene, camera);
    };
    tick();

    // ── Resize ──────────────────────────────────────────────────────────────
    const onResize = () => {
      const w = el.offsetWidth, h = el.offsetHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMouse);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div ref={mountRef} className="relative h-[480px] lg:h-[560px]">
      {/* Three.js canvas injected here */}
      <motion.div animate={{ y: [-6, 6, -6] }} transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
        className="absolute bottom-8 left-4 z-10 bg-gray-900/90 backdrop-blur-md border border-indigo-500/40 rounded-2xl px-4 py-3 shadow-2xl">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-sm font-medium text-white">Bot aktif — 3 kampanya</span>
        </div>
      </motion.div>
      <motion.div animate={{ y: [6, -6, 6] }} transition={{ repeat: Infinity, duration: 3.5, ease: "easeInOut", delay: 1 }}
        className="absolute top-10 right-4 z-10 bg-gray-900/90 backdrop-blur-md border border-purple-500/40 rounded-2xl px-4 py-3 shadow-2xl">
        <div className="flex items-center gap-2">
          <TrendingUp size={14} className="text-green-400" />
          <span className="text-sm font-medium text-white">Sıralama: <span className="text-green-400">#3 → #1</span></span>
        </div>
      </motion.div>
    </div>
  );
}

function TiltCard({ children, className, style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  const ref = useRef<HTMLDivElement>(null);
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    ref.current.style.transform = `perspective(800px) rotateY(${x * 12}deg) rotateX(${-y * 12}deg) scale3d(1.02,1.02,1.02)`;
  }, []);
  const handleMouseLeave = useCallback(() => {
    if (!ref.current) return;
    ref.current.style.transform = "perspective(800px) rotateY(0deg) rotateX(0deg) scale3d(1,1,1)";
  }, []);
  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={className}
      style={{ ...style, transition: "transform 0.15s ease", transformStyle: "preserve-3d" }}
    >
      {children}
    </div>
  );
}

function AnimatedNumber({ value, suffix }: { value: number; suffix: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!inView) return;
    const duration = 2000;
    const start = performance.now();
    let raf: number;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setN(Math.floor(eased * value));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value]);
  return (
    <span ref={ref} className="tabular-nums">
      {n.toLocaleString("tr-TR")}{suffix}
    </span>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden bg-gray-900/50 hover:border-brand-500/30 transition-colors">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full px-5 py-4 flex items-center justify-between text-left"
      >
        <span className="text-white font-medium text-sm">{q}</span>
        <ChevronDown
          size={18}
          className={`text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="px-5 pb-4 text-gray-400 text-sm leading-relaxed animate-fade-up">
          {a}
        </div>
      )}
    </div>
  );
}

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: (i: number = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.6, ease: "easeOut" as const } }),
};

export default function Landing() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pricePeriod, setPricePeriod] = useState<PricePeriod>("monthly");
  useEffect(() => { trackPageView("/"); }, []);

  return (
    <div className="min-h-screen bg-[#030712] text-white relative overflow-x-hidden">
      {/* Subtle grid overlay */}
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: "linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px)",
        backgroundSize: "60px 60px"
      }} />

      {/* Ambient glow orbs */}
      <div className="fixed top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
      <div className="fixed top-1/2 right-0 w-[500px] h-[500px] rounded-full bg-purple-600/10 blur-[120px] pointer-events-none" />

      <div className="relative z-10">
        {/* Nav */}
        <nav className="glass border-b border-gray-800/50 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2 group">
              <div className="relative">
                <Bot className="text-brand-400 group-hover:rotate-12 transition-transform" size={24} />
                <span className="absolute inset-0 bg-brand-400 rounded-full blur-md opacity-30 group-hover:opacity-60 transition-opacity" />
              </div>
              <span className="font-bold text-lg">
                Request<span className="gradient-text">Bot</span>
              </span>
            </div>
            <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
              <a href="#features" className="hover:text-white transition-colors">Özellikler</a>
              <a href="#how" className="hover:text-white transition-colors">Nasıl Çalışır</a>
              <a href="#pricing" className="hover:text-white transition-colors">Fiyatlar</a>
              <a href="#faq" className="hover:text-white transition-colors">SSS</a>
            </div>
            <div className="hidden md:flex items-center gap-3">
              <Link to="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                Giriş
              </Link>
              <Link
                to="/register"
                className="relative px-4 py-2 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-400 hover:to-purple-400 text-white font-semibold rounded-lg text-sm transition-all shadow-lg shadow-brand-500/30 hover:shadow-brand-500/50 hover:scale-105"
              >
                Ücretsiz Başla
              </Link>
            </div>
            {/* Mobile hamburger */}
            <button
              className="md:hidden p-2 text-gray-400 hover:text-white transition-colors"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Menüyü aç"
            >
              {mobileOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
          {/* Mobile dropdown */}
          {mobileOpen && (
            <div className="md:hidden border-t border-gray-800/50 px-6 py-4 space-y-4 animate-fade-up">
              <div className="flex flex-col gap-3 text-sm text-gray-400">
                <a href="#features" onClick={() => setMobileOpen(false)} className="hover:text-white transition-colors py-1">Özellikler</a>
                <a href="#how" onClick={() => setMobileOpen(false)} className="hover:text-white transition-colors py-1">Nasıl Çalışır</a>
                <a href="#pricing" onClick={() => setMobileOpen(false)} className="hover:text-white transition-colors py-1">Fiyatlar</a>
                <a href="#faq" onClick={() => setMobileOpen(false)} className="hover:text-white transition-colors py-1">SSS</a>
              </div>
              <div className="flex flex-col gap-2 pt-2 border-t border-gray-800">
                <Link to="/login" onClick={() => setMobileOpen(false)} className="text-sm text-gray-400 hover:text-white transition-colors py-1">
                  Giriş Yap
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileOpen(false)}
                  className="px-4 py-2 bg-gradient-to-r from-brand-500 to-purple-500 text-white font-semibold rounded-lg text-sm text-center transition-all"
                >
                  Ücretsiz Başla
                </Link>
              </div>
            </div>
          )}
        </nav>

        {/* Hero */}
        <section className="max-w-7xl mx-auto px-6 pt-20 pb-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-7">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-brand-500/10 border border-brand-500/30 rounded-full text-brand-300 text-xs font-medium animate-fade-up">
                <Sparkles size={12} className="animate-pulse" />
                Yapay Zeka Destekli SEO Trafik Botu
              </div>

              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-[1.05] animate-fade-up delay-100">
                Google'da{" "}
                <span className="gradient-text">üst sıralara</span>
                <br />
                yükselmek artık{" "}
                <span className="relative inline-block">
                  <span className="gradient-text">otomatik</span>
                  <svg className="absolute -bottom-2 left-0 w-full" height="14" viewBox="0 0 200 14">
                    <path
                      d="M2 8 Q 50 2, 100 7 T 198 6"
                      fill="none"
                      stroke="url(#underlineGrad)"
                      strokeWidth="3"
                      strokeLinecap="round"
                      style={{
                        strokeDasharray: 300,
                        strokeDashoffset: 300,
                        animation: "draw-line 1.5s 0.8s ease-out forwards",
                      }}
                    />
                    <defs>
                      <linearGradient id="underlineGrad">
                        <stop offset="0%" stopColor="#818cf8" />
                        <stop offset="100%" stopColor="#f472b6" />
                      </linearGradient>
                    </defs>
                  </svg>
                </span>
              </h1>

              <p className="text-gray-400 text-lg leading-relaxed max-w-xl animate-fade-up delay-200">
                SerpAPI ile gerçek sıralama takibi. Çoklu proxy üzerinden organik trafik simülasyonu.
                Telegram'dan tek komutla yönet. <span className="text-brand-400 font-medium">Kur, çalıştır, sıralanı izle.</span>
              </p>

              <div className="flex flex-wrap items-center gap-3 animate-fade-up delay-300">
                <Link
                  to="/register"
                  className="group relative inline-flex items-center gap-2 px-7 py-3.5 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-400 hover:to-purple-400 text-white font-semibold rounded-xl shadow-lg shadow-brand-500/40 hover:shadow-brand-500/60 transition-all hover:scale-105"
                >
                  <span className="absolute inset-0 rounded-xl shine opacity-30 group-hover:opacity-100 transition-opacity" />
                  Hemen Başla
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="#how"
                  className="inline-flex items-center gap-2 px-6 py-3.5 glass border border-gray-700 hover:border-brand-500/50 rounded-xl text-sm font-medium transition-colors"
                >
                  <span>Demo Gör</span>
                </a>
              </div>

              <div className="flex items-center gap-6 pt-4 animate-fade-up delay-500">
                <div className="flex -space-x-2">
                  {[...Array(4)].map((_, i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full border-2 border-gray-950"
                      style={{
                        background: `linear-gradient(${i * 90}deg, #818cf8, #c084fc)`,
                      }}
                    />
                  ))}
                </div>
                <div>
                  <div className="flex items-center gap-1 text-yellow-400">
                    {"★★★★★".split("").map((s, i) => <span key={i}>{s}</span>)}
                  </div>
                  <p className="text-gray-500 text-xs mt-0.5">1247+ memnun kullanıcı</p>
                </div>
              </div>
            </div>

            {/* Right: CSS 3D Hero Visual */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
            >
              <HeroVisual />
            </motion.div>
          </div>
        </section>

        {/* Stats bar */}
        <section className="max-w-6xl mx-auto px-6 -mt-16 mb-20 relative z-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.7 }}
            className="border border-indigo-500/20 rounded-2xl p-8 grid grid-cols-2 md:grid-cols-4 gap-6"
            style={{ background: "rgba(15,15,30,0.8)", backdropFilter: "blur(20px)" }}
          >
            {STATS.map((s, i) => (
              <div key={s.label} className="text-center">
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  <AnimatedNumber value={s.value} suffix={s.suffix} />
                </div>
                <p className="text-gray-500 text-xs mt-1 uppercase tracking-widest">{s.label}</p>
              </div>
            ))}
          </motion.div>
        </section>

        {/* How it works */}
        <section id="how" className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-14">
            <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">Nasıl Çalışır</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-2">3 Adımda Başla</h2>
            <p className="text-gray-500 mt-3 max-w-xl mx-auto">
              Karmaşık kurulum yok, kod yazmana gerek yok. Hesap aç, indir, çalıştır.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 relative">
            <div className="hidden md:block absolute top-14 left-[38%] right-[38%] h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
            {STEPS.map((s, i) => (
              <TiltCard
                key={s.title}
                className="relative rounded-2xl p-6 border border-gray-800/60 overflow-hidden"
                style={{ background: "rgba(10,10,20,0.8)", backdropFilter: "blur(16px)" } as React.CSSProperties}
              >
                <motion.div
                  variants={fadeUp}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  custom={i}
                >
                  <div className={`w-14 h-14 ${s.color} rounded-2xl flex items-center justify-center mb-5 shadow-xl`}>
                    <s.icon className="text-white" size={26} />
                  </div>
                  <h3 className="text-xl font-bold mb-2">{s.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{s.desc}</p>
                  <div className="absolute inset-0 rounded-2xl opacity-0 hover:opacity-100 transition-opacity"
                    style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.06), rgba(168,85,247,0.06))" }} />
                </motion.div>
              </TiltCard>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-14">
            <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">Özellikler</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-2">Profesyonel SEO Cephanesi</h2>
            <p className="text-gray-500 mt-3 max-w-xl mx-auto">
              Her şeyi tek panelde yönet — sıralama, trafik, proxy, raporlama.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <TiltCard
                key={f.title}
                className="group relative rounded-2xl p-6 border border-gray-800/60 overflow-hidden cursor-default"
                style={{ background: "rgba(8,8,20,0.9)", backdropFilter: "blur(16px)" } as React.CSSProperties}
              >
                <motion.div
                  variants={fadeUp}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  custom={i * 0.5}
                >
                  <div className={`absolute -top-16 -right-16 w-40 h-40 bg-gradient-to-br ${f.color} opacity-0 group-hover:opacity-15 blur-3xl transition-all duration-500`} />
                  <div className={`relative w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-300`}>
                    <f.icon className="text-white" size={22} />
                  </div>
                  <h3 className="font-bold text-lg text-white mb-2">{f.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
                </motion.div>
              </TiltCard>
            ))}
          </div>
        </section>

        {/* Demo / Mockup */}
        <section className="max-w-6xl mx-auto px-6 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">Canlı Panel</span>
              <h2 className="text-4xl md:text-5xl font-bold">
                Modern <span className="gradient-text">dashboard</span> ile her şey kontrolünde
              </h2>
              <p className="text-gray-400 text-lg leading-relaxed">
                Saatlik trafik grafikleri, proxy sağlık durumu, sıralama değişimleri — hepsi gözünün önünde.
              </p>
              <ul className="space-y-3">
                {[
                  "Recharts ile interaktif grafikler",
                  "Anlık WebSocket logları",
                  "Telegram'dan /stats /rank komutları",
                  "Her sabah 09:00'da otomatik rapor",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-gray-300">
                    <div className="w-6 h-6 rounded-full bg-brand-500/20 flex items-center justify-center flex-shrink-0">
                      <Check size={14} className="text-brand-400" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Mockup browser */}
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-brand-500 to-purple-500 rounded-3xl blur-2xl opacity-20 animate-pulse-glow" />
              <div className="relative glass border border-gray-700 rounded-2xl overflow-hidden shadow-2xl">
                {/* Browser bar */}
                <div className="bg-gray-800/80 px-4 py-3 flex items-center gap-2 border-b border-gray-700">
                  <div className="flex gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500" />
                    <span className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <div className="flex-1 mx-4 bg-gray-900 rounded px-3 py-1 text-xs text-gray-500 font-mono">
                    requestbot.io/dashboard
                  </div>
                </div>

                {/* Mock dashboard */}
                <div className="p-5 space-y-3 bg-gray-950/80">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-sm">📊 Dashboard</h3>
                    <span className="text-xs text-green-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      Canlı
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "Ziyaret", val: "12,847", color: "text-brand-400" },
                      { label: "Sıra", val: "#3", color: "text-green-400" },
                      { label: "Proxy", val: "47", color: "text-purple-400" },
                    ].map((s) => (
                      <div key={s.label} className="bg-gray-900/60 rounded-lg p-2 border border-gray-800">
                        <div className={`text-base font-bold ${s.color}`}>{s.val}</div>
                        <div className="text-[10px] text-gray-500">{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Mini chart */}
                  <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
                    <div className="flex items-end gap-1 h-20">
                      {[40, 65, 45, 80, 60, 90, 75, 100, 85, 95, 70, 90].map((h, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-gradient-to-t from-brand-600 to-brand-400 rounded-t opacity-80"
                          style={{
                            height: `${h}%`,
                            animation: `fade-up 0.5s ${i * 50}ms ease-out forwards`,
                            opacity: 0,
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <div className="flex-1 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2 text-xs">
                      <div className="text-green-300 font-medium">↑ %23 artış</div>
                      <div className="text-gray-500">Son 7 gün</div>
                    </div>
                    <div className="flex-1 bg-purple-500/10 border border-purple-500/30 rounded-lg px-3 py-2 text-xs">
                      <div className="text-purple-300 font-medium">3 kampanya</div>
                      <div className="text-gray-500">Aktif</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating notification */}
              <div className="absolute -bottom-6 -left-6 glass border border-brand-500/30 rounded-xl px-4 py-3 shadow-xl animate-bounce-slow">
                <div className="flex items-center gap-2 text-sm">
                  <Send size={14} className="text-brand-400" />
                  <span className="text-white font-medium">Telegram'a rapor gönderildi</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-14">
            <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">Yorumlar</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-2">Kullananlar Konuşuyor</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {TESTIMONIALS.map((t, i) => (
              <div
                key={t.name}
                className="glass border border-gray-800 rounded-2xl p-6 card-hover animate-fade-up"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="text-yellow-400 mb-3">{"★".repeat(t.rating)}</div>
                <p className="text-gray-300 text-sm leading-relaxed mb-4">"{t.text}"</p>
                <div className="flex items-center gap-3 pt-3 border-t border-gray-800">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                    {t.name[0]}
                  </div>
                  <div>
                    <p className="text-white text-sm font-medium">{t.name}</p>
                    <p className="text-gray-500 text-xs">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="max-w-3xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">Fiyatlandırma</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-2">Şeffaf Fiyat, Sürpriz Yok</h2>
            <p className="text-gray-500 mt-3">Süreyi seç, hemen başla. İstediğin zaman iptal et.</p>
          </div>

          {/* Period toggle */}
          <div className="flex justify-center mb-10">
            <div className="flex bg-gray-900 border border-gray-800 rounded-2xl p-1.5 gap-1">
              {(["daily", "monthly", "yearly"] as PricePeriod[]).map((p) => {
                const lbl = { daily: "Günlük", monthly: "Aylık", yearly: "Yıllık" };
                const sav = { daily: null, monthly: "%44", yearly: "%63" };
                return (
                  <button key={p} onClick={() => setPricePeriod(p)}
                    className={`relative px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${pricePeriod === p
                        ? "bg-brand-500 text-black shadow-lg shadow-brand-500/30"
                        : "text-gray-400 hover:text-white"
                      }`}>
                    {lbl[p]}
                    {sav[p] && (
                      <span className={`absolute -top-2.5 -right-1 text-[9px] font-bold px-1.5 py-0.5 rounded-full ${pricePeriod === p ? "bg-green-400 text-black" : "bg-green-500/20 text-green-400"
                        }`}>{sav[p]}</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Single card */}
          <div className="relative max-w-lg mx-auto">
            <div className="absolute -inset-px rounded-3xl bg-gradient-to-br from-brand-500/40 via-purple-500/30 to-brand-500/20 -z-10 blur" />
            <div className="relative glass border border-brand-500/30 rounded-3xl p-10 text-center">

              {/* Badge */}
              {PRICING[pricePeriod].badge && (
                <span className="inline-block mb-4 px-3 py-1 bg-brand-500/20 border border-brand-500/40 text-brand-400 text-xs font-bold rounded-full uppercase tracking-wider">
                  {PRICING[pricePeriod].badge}
                </span>
              )}

              {/* Plan label */}
              <p className="text-gray-500 text-sm mb-4">{PRICING[pricePeriod].label}</p>

              {/* Price */}
              <div className="flex items-end justify-center gap-2 mb-2">
                <motion.span key={pricePeriod}
                  initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}
                  className="text-7xl font-black gradient-text tabular-nums leading-none">
                  {PRICING[pricePeriod].price}
                </motion.span>
                <div className="mb-2 text-left">
                  <div className="text-2xl font-bold text-gray-300">₺</div>
                  <div className="text-gray-500 text-sm">/ {PRICING[pricePeriod].unit}</div>
                </div>
              </div>

              {/* Savings */}
              {PRICING[pricePeriod].saving ? (
                <motion.p key={pricePeriod + "s"} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="text-green-400 text-sm font-medium mb-8">
                  Günlük fiyata göre <strong>{PRICING[pricePeriod].savingAmt}</strong> tasarruf
                  &nbsp;—&nbsp;<strong>{PRICING[pricePeriod].saving}</strong> indirim
                </motion.p>
              ) : (
                <p className="text-gray-600 text-sm mb-8">Bağlılık yok — özgürce dene.</p>
              )}

              {/* Features */}
              <ul className="space-y-3 mb-8 text-left">
                {PLAN_FEATURES.map((f) => (
                  <li key={f} className="flex items-center gap-3 text-sm text-gray-300">
                    <Check size={15} className="text-brand-400 flex-shrink-0" />{f}
                  </li>
                ))}
              </ul>

              <Link to="/register"
                className="block text-center px-4 py-4 rounded-xl font-bold text-base bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-400 hover:to-brand-500 text-white shadow-lg shadow-brand-500/40 transition-all hover:scale-[1.02]">
                Hemen Başla →
              </Link>
            </div>
          </div>

          <div className="text-center mt-8 p-4 glass border border-gray-800 rounded-xl max-w-md mx-auto">
            <p className="text-gray-400 text-sm">
              <span className="text-yellow-400">⚡</span> Cihaz değişikliği için <strong className="text-white">"Cihaz Sıfırlama Paketi"</strong> — 15 ₺
            </p>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="max-w-3xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">SSS</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-2">Aklındaki Sorular</h2>
          </div>
          <div className="space-y-3">
            {FAQS.map((f, i) => (
              <div key={i} className="animate-fade-up" style={{ animationDelay: `${i * 50}ms` }}>
                <FAQItem q={f.q} a={f.a} />
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-5xl mx-auto px-6 py-20">
          <div className="relative glass border border-brand-500/30 rounded-3xl p-12 text-center overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500/20 via-purple-500/20 to-pink-500/20 animate-gradient" />
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-brand-500/30 blur-3xl" />
            <div className="relative">
              <Rocket className="mx-auto text-brand-400 mb-4 animate-bounce-slow" size={40} />
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                Hazır mısın <span className="gradient-text">üst sıralara</span> çıkmaya?
              </h2>
              <p className="text-gray-300 max-w-xl mx-auto mb-8">
                Ücretsiz hesap aç, 5 dakikada kurulumu tamamla, sonuçları görmeye başla.
              </p>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-400 hover:to-purple-400 text-white font-bold rounded-xl shadow-2xl shadow-brand-500/40 transition-all hover:scale-105"
              >
                Şimdi Başla — Ücretsiz
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-gray-800/50 mt-12">
          <div className="max-w-6xl mx-auto px-6 py-10">
            <div className="grid md:grid-cols-4 gap-8 mb-8">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Bot className="text-brand-400" size={20} />
                  <span className="font-bold">Request<span className="gradient-text">Bot</span></span>
                </div>
                <p className="text-gray-500 text-xs leading-relaxed">
                  SEO trafik otomasyon aracı. Sıralama yükselt, trafik üret, raporla.
                </p>
              </div>
              <div>
                <h4 className="text-white text-sm font-semibold mb-3">Ürün</h4>
                <ul className="space-y-2 text-xs text-gray-500">
                  <li><a href="#features" className="hover:text-white">Özellikler</a></li>
                  <li><a href="#pricing" className="hover:text-white">Fiyatlandırma</a></li>
                  <li><a href="#faq" className="hover:text-white">SSS</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-white text-sm font-semibold mb-3">Hesap</h4>
                <ul className="space-y-2 text-xs text-gray-500">
                  <li><Link to="/login" className="hover:text-white">Giriş Yap</Link></li>
                  <li><Link to="/register" className="hover:text-white">Kayıt Ol</Link></li>
                  <li><Link to="/account" className="hover:text-white">Hesabım</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="text-white text-sm font-semibold mb-3">İletişim</h4>
                <ul className="space-y-2 text-xs text-gray-500">
                  <li>
                    <a href="https://t.me/requestbotdestek" target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1.5 hover:text-white transition-colors">
                      <MessageSquare size={12} /> Destek (Telegram)
                    </a>
                  </li>
                  <li>
                    <a href="https://t.me/requestbot" target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1.5 hover:text-white transition-colors">
                      <Send size={12} /> @requestbot
                    </a>
                  </li>
                </ul>
              </div>
            </div>
            <div className="text-center pt-6 border-t border-gray-800/50 text-gray-600 text-xs">
              © 2026 RequestBot · Tüm hakları saklıdır
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
