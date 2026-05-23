import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  Calendar,
  CheckCircle,
  Cpu,
  CreditCard,
  Download,
  Monitor,
  RefreshCw,
  ShoppingCart,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { api, type Device, type DownloadInfo, type DeviceResetOrderResult } from "../lib/api";
import { useAuth } from "../lib/auth";

const PLAN_INFO: Record<string, { color: string; label: string }> = {
  free: { color: "bg-gray-700 text-gray-300", label: "Ücretsiz" },
  pro: { color: "bg-blue-500/30 text-blue-300", label: "Pro" },
  agency: { color: "bg-purple-500/30 text-purple-300", label: "Agency" },
};

export default function Account() {
  const { user, logout, refresh } = useAuth();
  const [device, setDevice] = useState<Device | null>(null);
  const [download, setDownload] = useState<DownloadInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [ordering, setOrdering] = useState(false);
  const [orderInfo, setOrderInfo] = useState<DeviceResetOrderResult | null>(null);
  const [paymentToken, setPaymentToken] = useState<string | null>(null);
  const [paymentProduct, setPaymentProduct] = useState("");
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{ msg: string; onConfirm: () => void } | null>(null);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const askConfirm = (msg: string) => new Promise<boolean>((resolve) => {
    setConfirmModal({
      msg,
      onConfirm: () => { setConfirmModal(null); resolve(true); },
    });
  });

  const load = async () => {
    setLoading(true);
    try {
      const [d, dl] = await Promise.all([
        api.license.myDevice().catch(() => null),
        api.download.info().catch(() => null),
      ]);
      setDevice(d);
      setDownload(dl);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const handler = (e: MessageEvent) => {
      if (e.data?.paytr === "success") {
        setPaymentToken(null);
        showToast("✅ Ödeme başarılı! Hesabınız güncellendi.");
        setTimeout(() => refresh(), 1500);
      } else if (e.data?.paytr === "failed") {
        setPaymentToken(null);
        showToast("Ödeme başarısız. Lütfen tekrar deneyin.", false);
      }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  const startPayment = async (product: string) => {
    setOrdering(true);
    setPaymentProduct(product);
    try {
      const r = await api.payment.start(product);
      setPaymentToken(r.token);
    } catch (e: any) {
      showToast(e?.response?.data?.detail || "Ödeme başlatılamadı", false);
    } finally {
      setOrdering(false);
    }
  };

  const orderDeviceReset = () => startPayment("device_reset");

  const resetDevice = async () => {
    const ok = await askConfirm("Cihaz kaydı silinecek. Sonra yeni cihazda giriş yapabilirsin. Devam?");
    if (!ok) return;
    setResetting(true);
    try {
      const r = await api.license.resetDevice();
      showToast(`✅ Cihaz sıfırlandı. Kalan hak: ${r.remaining_credits}`);
      await refresh();
      await load();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || "Sıfırlama başarısız", false);
    } finally {
      setResetting(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/download/latest", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showToast(err?.detail || "İndirme başarısız", false);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = download?.filename || "RequestBot.exe";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      showToast("İndirme hatası", false);
    } finally {
      setDownloading(false);
    }
  };

  if (!user) return null;

  const planInfo = PLAN_INFO[user.plan];
  const isExpired = user.license_expires_at && new Date(user.license_expires_at) < new Date();
  const daysLeft = user.license_expires_at
    ? Math.max(0, Math.floor((new Date(user.license_expires_at).getTime() - Date.now()) / 86400000))
    : 0;
  const hasActiveLicense = !isExpired && user.plan !== "free";

  const fmtDate = (d: string | null) =>
    d ? new Date(d).toLocaleDateString("tr-TR", { day: "2-digit", month: "long", year: "numeric" }) : "—";
  const fmtDateTime = (d: string) => new Date(d).toLocaleString("tr-TR");

  const PLAN_FEATURES = [
    "Sınırsız kampanya",
    "Çoklu proxy desteği",
    "SerpAPI sıralama takibi",
    "Telegram bildirimleri",
    "Cihaz sıfırlama hakkı",
  ];

  return (
    <div className="min-h-screen text-white relative overflow-hidden"
      style={{ background: "linear-gradient(135deg, #020817 0%, #0d0d1f 50%, #0a0520 100%)" }}>

      <style>{`
        @keyframes orb1 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(40px,-30px) scale(1.08)} 66%{transform:translate(-25px,20px) scale(0.93)} }
        @keyframes orb2 { 0%,100%{transform:translate(0,0) scale(1)} 40%{transform:translate(-30px,25px) scale(1.1)} 70%{transform:translate(25px,-15px) scale(0.9)} }
        @keyframes orb3 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(20px,30px)} }
        @keyframes shimmer { 0%{background-position:-200% center} 100%{background-position:200% center} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse-glow { 0%,100%{box-shadow:0 0 20px rgba(99,102,241,0.3)} 50%{box-shadow:0 0 40px rgba(99,102,241,0.6)} }
        .card-3d { transition: transform 0.35s cubic-bezier(.22,1,.36,1), box-shadow 0.35s ease; transform-style: preserve-3d; }
        .card-3d:hover { transform: perspective(900px) rotateX(-3deg) rotateY(4deg) translateZ(8px); }
        .plan-card-3d { transition: transform 0.4s cubic-bezier(.34,1.56,.64,1), box-shadow 0.4s ease; }
        .plan-card-3d:hover { transform: perspective(800px) rotateX(-5deg) rotateY(-3deg) translateY(-12px) scale(1.02); }
        .shimmer-text { background: linear-gradient(90deg, #f1f5f9 0%, #a5b4fc 40%, #f1f5f9 80%); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shimmer 3s linear infinite; }
        .glass { background: rgba(255,255,255,0.04); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.08); }
        .glass-hover:hover { background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.14); }
        .anim-fadein { animation: fadeUp 0.5s ease both; }
        .anim-fadein-2 { animation: fadeUp 0.5s ease 0.1s both; }
        .anim-fadein-3 { animation: fadeUp 0.5s ease 0.2s both; }
        .anim-fadein-4 { animation: fadeUp 0.5s ease 0.3s both; }
      `}</style>

      {/* Animated background orbs */}
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none", zIndex: 0 }}>
        <div style={{ position: "absolute", width: 700, height: 700, borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.13) 0%, transparent 70%)", top: -150, left: -200, animation: "orb1 14s ease-in-out infinite" }} />
        <div style={{ position: "absolute", width: 600, height: 600, borderRadius: "50%", background: "radial-gradient(circle, rgba(168,85,247,0.10) 0%, transparent 70%)", top: 100, right: -200, animation: "orb2 17s ease-in-out infinite" }} />
        <div style={{ position: "absolute", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)", bottom: -100, left: "35%", animation: "orb3 20s ease-in-out infinite" }} />
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(rgba(255,255,255,0.015) 1px, transparent 1px)", backgroundSize: "32px 32px" }} />
      </div>

      {/* Toast */}
      {toast && (
        <div className="toast-slide fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium shadow-2xl"
          style={{ background: toast.ok ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)", border: `1px solid ${toast.ok ? "rgba(16,185,129,0.4)" : "rgba(239,68,68,0.4)"}`, color: toast.ok ? "#6ee7b7" : "#fca5a5", backdropFilter: "blur(12px)" }}>
          <span>{toast.msg}</span>
          <button onClick={() => setToast(null)} className="opacity-60 hover:opacity-100 transition-opacity"><X size={14} /></button>
        </div>
      )}

      {/* Confirm Modal */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
          <div className="glass rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl" style={{ border: "1px solid rgba(255,255,255,0.12)" }}>
            <p className="text-white text-sm mb-5 leading-relaxed">{confirmModal.msg}</p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setConfirmModal(null)} className="px-4 py-2 text-sm text-gray-400 hover:text-white rounded-lg transition-colors" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>İptal</button>
              <button onClick={confirmModal.onConfirm} className="px-4 py-2 text-sm text-red-300 rounded-lg transition-colors" style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.35)" }}>Devam</button>
            </div>
          </div>
        </div>
      )}

      {/* PayTR iFrame Modal */}
      {paymentToken && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-lg p-4">
          <div className="relative w-full max-w-lg">
            <div className="flex items-center justify-between mb-3 px-1">
              <div className="flex items-center gap-2 text-white text-sm font-medium">
                <CreditCard size={15} style={{ color: "#a5b4fc" }} />
                Güvenli Ödeme
                <span className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>— 256-bit SSL</span>
              </div>
              <button onClick={() => setPaymentToken(null)} className="flex items-center gap-1 text-xs transition-colors hover:text-white" style={{ color: "rgba(255,255,255,0.4)" }}><X size={14} /> Kapat</button>
            </div>
            <iframe src={`https://www.paytr.com/odeme/guvenli/${paymentToken}`} className="w-full rounded-2xl" style={{ height: 600, border: "none" }} allowFullScreen title="PayTR Güvenli Ödeme" />
          </div>
        </div>
      )}

      {/* Ödeme Bilgileri Modali (manuel transfer) */}
      {orderInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
          <div className="glass rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-sm" style={{ color: "#a5b4fc" }}>
                <ShoppingCart size={16} /> Cihaz Sıfırlama — 15 ₺
              </div>
              <button onClick={() => setOrderInfo(null)} className="opacity-50 hover:opacity-100 transition-opacity"><X size={16} /></button>
            </div>
            <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>
              Aşağıdaki hesaba ödeme yapın. Açıklama alanına referans kodunuzu yazmayı unutmayın.
            </p>
            <div className="rounded-xl p-4 space-y-2 text-xs font-mono" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div className="flex justify-between"><span style={{ color: "rgba(255,255,255,0.4)" }}>Banka</span><span>{orderInfo.bank}</span></div>
              <div className="flex justify-between"><span style={{ color: "rgba(255,255,255,0.4)" }}>Ad</span><span>{orderInfo.name}</span></div>
              <div className="flex justify-between items-center gap-2"><span style={{ color: "rgba(255,255,255,0.4)" }} className="flex-shrink-0">IBAN</span><span className="text-right break-all">{orderInfo.iban}</span></div>
              <div className="flex justify-between"><span style={{ color: "rgba(255,255,255,0.4)" }}>Tutar</span><span style={{ color: "#a5b4fc", fontWeight: 700 }}>{orderInfo.amount}</span></div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Referans</span>
                <span className="text-yellow-400 font-bold tracking-wider">{orderInfo.note}</span>
              </div>
            </div>
            <p className="text-gray-600 text-xs text-center">
              Sipariş #{orderInfo.order_id} — Ödeme sonrası admin ile iletişime geçin.
            </p>
            <button
              onClick={() => setOrderInfo(null)}
              className="w-full py-2 bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 border border-brand-500/40 rounded-lg text-sm transition-colors"
            >
              Tamam
            </button>
          </div>
        </div>
      )}

      {/* Navbar */}
      <nav className="relative z-40 sticky top-0" style={{ background: "rgba(2,8,23,0.75)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div style={{ width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg,#6366f1,#7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700 }}>R</div>
            <span className="font-bold text-base">Request<span style={{ color: "#818cf8" }}>Bot</span></span>
          </Link>
          <div className="flex items-center gap-5">
            {user.role === "admin" && (
              <a href="/admin" className="text-xs font-medium flex items-center gap-1.5 transition-colors hover:opacity-80" style={{ color: "#fbbf24" }}>
                <Sparkles size={13} /> Admin Panel
              </a>
            )}
            <span className="text-sm" style={{ color: "rgba(255,255,255,0.5)" }}>{user.username}</span>
            <button onClick={logout} className="text-xs px-3 py-1.5 rounded-lg transition-colors hover:opacity-80" style={{ color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.1)" }}>Çıkış</button>
          </div>
        </div>
      </nav>

      <main className="relative z-10 max-w-6xl mx-auto px-6 py-10 space-y-8">

        {/* Hero */}
        <div className="anim-fadein flex items-center justify-between">
          <div>
            <p className="text-sm mb-1" style={{ color: "rgba(165,180,252,0.7)" }}>Hoş geldin,</p>
            <h1 className="text-3xl font-bold shimmer-text">{user.username}</h1>
          </div>
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <div className="w-2 h-2 rounded-full" style={{ background: hasActiveLicense ? "#10b981" : "#6b7280", boxShadow: hasActiveLicense ? "0 0 8px #10b981" : "none" }} />
            <span className="text-sm font-medium" style={{ color: hasActiveLicense ? "#6ee7b7" : "rgba(255,255,255,0.4)" }}>
              {hasActiveLicense ? `${planInfo.label} — ${daysLeft} gün kaldı` : "Aktif plan yok"}
            </span>
          </div>
        </div>

        {/* Info cards row */}
        <div className="grid md:grid-cols-3 gap-4 anim-fadein-2">
          {/* Lisans */}
          <div className="card-3d glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-lg" style={{ background: "rgba(99,102,241,0.15)" }}><Calendar size={16} style={{ color: "#a5b4fc" }} /></div>
              <span className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.8)" }}>Lisans</span>
            </div>
            {hasActiveLicense ? (
              <>
                <div className="text-3xl font-black mb-1" style={{ color: "#a5b4fc" }}>{daysLeft}</div>
                <div className="text-xs mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>gün kaldı · {fmtDate(user.license_expires_at)}</div>
                <div className="flex items-center gap-1.5 text-xs" style={{ color: "#6ee7b7" }}><CheckCircle size={12} /> Aktif</div>
              </>
            ) : isExpired ? (
              <div className="flex items-center gap-1.5 text-xs" style={{ color: "#fca5a5" }}><AlertCircle size={12} /> Süresi dolmuş</div>
            ) : (
              <div className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>Plan satın almadın</div>
            )}
          </div>

          {/* Cihaz */}
          <div className="card-3d glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-lg" style={{ background: "rgba(168,85,247,0.15)" }}><Monitor size={16} style={{ color: "#c084fc" }} /></div>
              <span className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.8)" }}>Cihaz</span>
            </div>
            {device ? (
              <>
                <div className="text-sm font-semibold mb-1 truncate">{device.hostname || "Bilinmiyor"}</div>
                <div className="text-xs mb-2 truncate" style={{ color: "rgba(255,255,255,0.3)" }}>{device.os_info || "—"}</div>
                <div className="text-xs font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>{device.last_ip}</div>
              </>
            ) : (
              <div className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>Henüz kayıtlı cihaz yok</div>
            )}
          </div>

          {/* İndir */}
          <div className="card-3d glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-lg" style={{ background: "rgba(59,130,246,0.15)" }}><Download size={16} style={{ color: "#93c5fd" }} /></div>
              <span className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.8)" }}>İndir</span>
            </div>
            {!hasActiveLicense ? (
              <div className="text-xs" style={{ color: "rgba(251,191,36,0.7)" }}>Aktif lisans gerekli</div>
            ) : !download?.available ? (
              <div className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>Yakında</div>
            ) : (
              <>
                <div className="text-xs mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>{download.size_mb} MB · Güncel</div>
                <button onClick={handleDownload} disabled={downloading}
                  className="w-full py-2 rounded-lg text-xs font-semibold transition-all hover:scale-105 disabled:opacity-50"
                  style={{ background: "linear-gradient(135deg,#6366f1,#7c3aed)", color: "#fff" }}>
                  {downloading ? "İndiriliyor…" : "İndir"}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Plan upgrade section */}
        {!hasActiveLicense && (
          <div className="anim-fadein-3">
            <div className="flex items-center gap-3 mb-6">
              <Sparkles size={18} style={{ color: "#a5b4fc" }} />
              <h2 className="text-lg font-bold">Lisans Satın Al</h2>
              <div className="h-px flex-1" style={{ background: "rgba(255,255,255,0.06)" }} />
            </div>
            <div className="plan-card-3d relative rounded-2xl p-8"
              style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(124,58,237,0.05) 100%)", border: "1px solid rgba(99,102,241,0.3)", boxShadow: "0 0 60px -15px rgba(99,102,241,0.3)" }}>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2.5 rounded-xl" style={{ background: "rgba(99,102,241,0.2)", color: "#818cf8" }}><Zap size={20} /></div>
                <div>
                  <div className="font-bold text-lg">RequestBot</div>
                  <div className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>Tam erişim lisansı</div>
                </div>
              </div>
              <ul className="grid sm:grid-cols-2 gap-2 mb-8">
                {PLAN_FEATURES.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm" style={{ color: "rgba(255,255,255,0.65)" }}>
                    <CheckCircle size={13} style={{ color: "#818cf8", flexShrink: 0 }} />{f}
                  </li>
                ))}
              </ul>
              <div className="grid sm:grid-cols-2 gap-4">
                <button onClick={() => startPayment("monthly")} disabled={ordering && paymentProduct === "monthly"}
                  className="rounded-2xl py-5 px-4 text-center transition-all hover:scale-105 disabled:opacity-50"
                  style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.35)" }}>
                  <div className="font-black text-3xl mb-1" style={{ color: "#a5b4fc" }}>299₺</div>
                  <div className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>/ ay</div>
                </button>
                <button onClick={() => startPayment("yearly")} disabled={ordering && paymentProduct === "yearly"}
                  className="relative rounded-2xl py-5 px-4 text-center transition-all hover:scale-105 disabled:opacity-50"
                  style={{ background: "rgba(99,102,241,0.25)", border: "1px solid rgba(99,102,241,0.6)", boxShadow: "0 0 30px -8px rgba(99,102,241,0.5)" }}>
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold"
                    style={{ background: "linear-gradient(90deg,#6366f1,#7c3aed)", color: "#fff", whiteSpace: "nowrap" }}>%44 tasarruf</div>
                  <div className="font-black text-3xl mb-1" style={{ color: "#fff" }}>1.990₺</div>
                  <div className="text-xs" style={{ color: "rgba(255,255,255,0.5)" }}>/ yıl</div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Device detail + reset */}
        {device && (
          <div className="card-3d glass rounded-2xl p-6 anim-fadein-4">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold flex items-center gap-2 text-sm">
                <Monitor size={16} style={{ color: "#c084fc" }} /> Kayıtlı Cihaz Detayı
              </h2>
              <span className="text-xs px-2.5 py-1 rounded-lg" style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.06)" }}>Tek cihaz kilidi</span>
            </div>
            <div className="grid sm:grid-cols-2 gap-4 mb-5">
              <Field icon={Cpu} label="Cihaz Adı" value={device.hostname || "—"} />
              <Field icon={Monitor} label="İşletim Sistemi" value={device.os_info || "—"} />
              <Field label="Son IP" value={device.last_ip || "—"} mono />
              <Field label="Son Görülme" value={fmtDateTime(device.last_seen)} />
            </div>
            <div className="pt-4 flex items-center justify-between gap-4" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
              <div>
                <p className="text-sm font-medium">Cihaz Sıfırlama</p>
                <p className="text-xs mt-1" style={{ color: "rgba(255,255,255,0.35)" }}>
                  Yeni bilgisayara geçiyor musun? &nbsp;Hakkın: <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{user.reset_credits}</span>
                </p>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button onClick={resetDevice} disabled={resetting || (user.reset_credits <= 0 && user.role !== "admin")}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:scale-105 disabled:opacity-40"
                  style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.35)", color: "#fca5a5" }}>
                  <RefreshCw size={11} className={`inline mr-1 ${resetting ? "animate-spin" : ""}`} />
                  {resetting ? "Sıfırlanıyor…" : "Sıfırla"}
                </button>
                {user.reset_credits <= 0 && user.role !== "admin" && (
                  <button onClick={orderDeviceReset} disabled={ordering}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:scale-105 disabled:opacity-50"
                    style={{ background: "rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.4)", color: "#a5b4fc" }}>
                    <ShoppingCart size={11} className={`inline mr-1 ${ordering ? "animate-pulse" : ""}`} />
                    {ordering ? "…" : "Hak Al — 15₺"}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Field({ icon: Icon, label, value, mono }: { icon?: any; label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-xs flex items-center gap-1 mb-1" style={{ color: "rgba(255,255,255,0.3)" }}>
        {Icon && <Icon size={10} />}{label}
      </div>
      <div className={`text-sm ${mono ? "font-mono" : "font-medium"}`} style={{ color: "rgba(255,255,255,0.85)" }}>{value}</div>
    </div>
  );
}
