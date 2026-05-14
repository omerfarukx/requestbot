import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Bot,
  Check,
  ChevronDown,
  Cpu,
  Download,
  Globe,
  MessageSquare,
  Rocket,
  Send,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import BotIllustration from "../components/BotIllustration";

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

const PLANS = [
  {
    name: "Pro",
    price: "299",
    period: "ay",
    badge: "POPÜLER",
    badgeColor: "bg-blue-500",
    features: [
      "5 kampanya",
      "Sınırsız ziyaret",
      "Webshare proxy entegrasyonu",
      "Telegram bot komutları",
      "Saatlik istatistikler",
      "E-posta destek",
    ],
    cta: "Pro'yu Seç",
    highlight: false,
  },
  {
    name: "Agency",
    price: "799",
    period: "ay",
    badge: "EN İYİ DEĞER",
    badgeColor: "bg-purple-500",
    features: [
      "50 kampanya",
      "Sınırsız ziyaret + proxy",
      "Çoklu Webshare hesabı",
      "Öncelikli destek",
      "Beyaz etiket raporlar",
      "API erişimi",
    ],
    cta: "Agency'yi Seç",
    highlight: true,
  },
];

function AnimatedNumber({ value, suffix }: { value: number; suffix: string }) {
  const [n, setN] = useState(0);
  useEffect(() => {
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
  }, [value]);
  return (
    <span className="tabular-nums">
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

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-950 text-white relative overflow-hidden">
      {/* Background mesh + grid */}
      <div className="fixed inset-0 mesh-bg pointer-events-none" />
      <div className="fixed inset-0 bg-grid pointer-events-none opacity-50" />

      {/* Floating background orbs */}
      <div className="fixed top-1/4 -left-20 w-96 h-96 rounded-full bg-brand-500/20 blur-3xl animate-float-slow pointer-events-none" />
      <div className="fixed top-2/3 -right-20 w-96 h-96 rounded-full bg-purple-500/20 blur-3xl animate-float-slow pointer-events-none" style={{ animationDelay: "3s" }} />
      <div className="fixed bottom-1/4 left-1/3 w-72 h-72 rounded-full bg-pink-500/15 blur-3xl animate-float-slow pointer-events-none" style={{ animationDelay: "5s" }} />

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
            <div className="flex items-center gap-3">
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
          </div>
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

            {/* Right: Bot illustration */}
            <div className="relative animate-fade-up delay-200">
              <BotIllustration />
            </div>
          </div>
        </section>

        {/* Stats bar */}
        <section className="max-w-6xl mx-auto px-6 -mt-16 mb-20 relative z-20">
          <div className="glass border border-gray-800 rounded-2xl p-8 grid grid-cols-2 md:grid-cols-4 gap-6">
            {STATS.map((s, i) => (
              <div key={s.label} className="text-center animate-fade-up" style={{ animationDelay: `${i * 100}ms` }}>
                <div className="text-3xl md:text-4xl font-bold gradient-text">
                  <AnimatedNumber value={s.value} suffix={s.suffix} />
                </div>
                <p className="text-gray-500 text-xs mt-1 uppercase tracking-wide">{s.label}</p>
              </div>
            ))}
          </div>
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
            {/* Connecting line */}
            <div className="hidden md:block absolute top-12 left-1/3 right-1/3 h-px bg-gradient-to-r from-transparent via-brand-500/50 to-transparent" />

            {STEPS.map((s, i) => (
              <div
                key={s.title}
                className="relative glass border border-gray-800 rounded-2xl p-6 card-hover animate-fade-up"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <div className={`w-14 h-14 ${s.color} rounded-xl flex items-center justify-center mb-4 shadow-lg`}>
                  <s.icon className="text-white" size={26} />
                </div>
                <h3 className="text-xl font-bold mb-2">{s.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{s.desc}</p>
              </div>
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
              <div
                key={f.title}
                className="group relative glass border border-gray-800 rounded-2xl p-6 card-hover overflow-hidden animate-fade-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className={`absolute -top-12 -right-12 w-32 h-32 bg-gradient-to-br ${f.color} opacity-0 group-hover:opacity-20 blur-2xl transition-opacity`} />
                <div className={`relative w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
                  <f.icon className="text-white" size={22} />
                </div>
                <h3 className="font-bold text-lg text-white mb-2">{f.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
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
        <section id="pricing" className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-14">
            <span className="text-brand-400 text-sm font-semibold uppercase tracking-wider">Fiyatlandırma</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-2">Şeffaf Fiyat, Sürpriz Yok</h2>
            <p className="text-gray-500 mt-3">İhtiyacına göre plan seç. İstediğin zaman iptal et.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {PLANS.map((p) => (
              <div
                key={p.name}
                className={`relative glass border rounded-2xl p-8 card-hover ${p.highlight ? "border-purple-500/50" : "border-gray-800"
                  }`}
              >
                {p.highlight && (
                  <div className="absolute -inset-px rounded-2xl bg-gradient-to-r from-purple-500/30 via-pink-500/30 to-purple-500/30 -z-10 blur" />
                )}
                {p.badge && (
                  <span
                    className={`absolute -top-3 right-6 px-3 py-1 ${p.badgeColor} text-white text-xs font-semibold rounded-full shadow-lg`}
                  >
                    {p.badge}
                  </span>
                )}
                <h3 className="text-2xl font-bold mb-1">{p.name}</h3>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-5xl font-bold gradient-text">{p.price}</span>
                  <span className="text-gray-500 text-xl">₺</span>
                  <span className="text-gray-500 ml-1">/ {p.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                      <Check size={15} className="text-brand-400 flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/register"
                  className={`block text-center px-4 py-3.5 rounded-xl font-semibold transition-all hover:scale-[1.02] ${p.highlight
                    ? "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 text-white shadow-lg shadow-purple-500/40"
                    : "bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-400 hover:to-brand-500 text-white shadow-lg shadow-brand-500/40"
                    }`}
                >
                  {p.cta}
                </Link>
              </div>
            ))}
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
                  <li className="flex items-center gap-1.5"><MessageSquare size={12} /> Destek</li>
                  <li className="flex items-center gap-1.5"><Send size={12} /> @requestbot</li>
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
