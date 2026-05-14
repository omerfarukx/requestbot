import { useEffect, useState } from "react";
import {
  AlertCircle,
  Calendar,
  CheckCircle,
  Cpu,
  Crown,
  Download,
  Globe,
  Monitor,
  RefreshCw,
  ShoppingCart,
} from "lucide-react";
import { api, type Device, type DownloadInfo } from "../lib/api";
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
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

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

  const resetDevice = async () => {
    if (!confirm("Cihaz kaydı silinecek. Sonra yeni cihazda giriş yapabilirsin. Devam?")) return;
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

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-xl
            ${toast.ok ? "bg-green-500/20 border border-green-500/40 text-green-300" : "bg-red-500/20 border border-red-500/40 text-red-300"}`}
        >
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <header className="border-b border-gray-800">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="text-brand-500" size={22} />
            <span className="font-bold">
              Request<span className="text-brand-500">Bot</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            {user.role === "admin" && (
              <a href="/admin" className="text-yellow-400 text-sm hover:text-yellow-300">
                <Crown size={14} className="inline mr-1" /> Admin
              </a>
            )}
            <span className="text-gray-400 text-sm">{user.username}</span>
            <button onClick={logout} className="text-gray-500 hover:text-red-400 text-sm">
              Çıkış
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Hesabım</h1>
          <p className="text-gray-500 text-sm mt-1">Lisans, cihaz ve indirme bilgilerin</p>
        </div>

        <div className="grid md:grid-cols-2 gap-5">
          {/* Lisans kartı */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold flex items-center gap-2">
                <Calendar className="text-brand-400" size={18} /> Lisans Durumu
              </h2>
              <span className={`px-2.5 py-0.5 rounded-md text-xs font-semibold ${planInfo.color}`}>
                {planInfo.label}
              </span>
            </div>

            {hasActiveLicense ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-green-400 text-sm">
                  <CheckCircle size={16} /> Aktif lisans
                </div>
                <div className="text-gray-400 text-sm">
                  Bitiş: <span className="text-white font-medium">{fmtDate(user.license_expires_at)}</span>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="text-3xl font-bold text-brand-400">{daysLeft}</div>
                  <div className="text-xs text-gray-500">gün kaldı</div>
                </div>
              </div>
            ) : isExpired ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <AlertCircle size={16} /> Lisans süresi dolmuş
                </div>
                <a
                  href="/#pricing"
                  className="block w-full text-center px-4 py-2.5 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm"
                >
                  <ShoppingCart size={14} className="inline mr-1" /> Lisans Yenile
                </a>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-gray-400 text-sm">
                  Aktif lisansın yok. Botu kullanmak için bir plan satın al.
                </div>
                <a
                  href="/#pricing"
                  className="block w-full text-center px-4 py-2.5 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm"
                >
                  <ShoppingCart size={14} className="inline mr-1" /> Plan Seç
                </a>
              </div>
            )}
          </div>

          {/* İndirme kartı */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="font-semibold flex items-center gap-2 mb-4">
              <Download className="text-brand-400" size={18} /> Programı İndir
            </h2>

            {loading ? (
              <div className="text-gray-500 text-sm">Yükleniyor…</div>
            ) : !hasActiveLicense ? (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-yellow-300 text-xs">
                İndirme için aktif lisans gerekli.
              </div>
            ) : !download?.available ? (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-yellow-300 text-xs">
                Henüz dosya yüklenmedi. Yakında.
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-gray-400 text-xs">
                  Versiyon güncel · {download.size_mb} MB
                </div>
                <a
                  href={api.download.url()}
                  className="block w-full text-center px-4 py-3 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm transition-colors"
                  download
                >
                  <Download size={14} className="inline mr-1" /> {download.filename}
                </a>
                <p className="text-gray-600 text-xs leading-relaxed">
                  İndirdikten sonra çift tıkla, hesabınla giriş yap, kullanmaya başla.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Cihaz kartı */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold flex items-center gap-2">
              <Monitor className="text-brand-400" size={18} /> Kayıtlı Cihaz
            </h2>
            <span className="text-gray-500 text-xs">Tek cihaz kilidi</span>
          </div>

          {loading ? (
            <div className="text-gray-500 text-sm">Yükleniyor…</div>
          ) : !device ? (
            <div className="text-gray-500 text-sm">
              Henüz hiçbir cihazdan giriş yapmadın. Programı indir ve giriş yap.
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid sm:grid-cols-2 gap-3 text-sm">
                <Field icon={Cpu} label="Cihaz Adı" value={device.hostname || "—"} />
                <Field icon={Monitor} label="İşletim Sistemi" value={device.os_info || "—"} />
                <Field label="Son IP" value={device.last_ip || "—"} mono />
                <Field label="Son Görülme" value={fmtDateTime(device.last_seen)} />
              </div>

              <div className="border-t border-gray-800 pt-4 mt-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">Cihaz Sıfırlama</p>
                    <p className="text-gray-500 text-xs mt-1">
                      Yeni bilgisayara geçiyor musun? Cihaz kaydını sil, yenisinde giriş yap.
                      <br />
                      Hakkın: <span className="text-brand-400 font-semibold">{user.reset_credits}</span>
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 flex-shrink-0">
                    <button
                      onClick={resetDevice}
                      disabled={resetting || (user.reset_credits <= 0 && user.role !== "admin")}
                      className="px-3 py-1.5 bg-red-500/20 border border-red-500/40 text-red-300 hover:bg-red-500/30 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-xs font-medium transition-colors"
                    >
                      <RefreshCw size={12} className={`inline mr-1 ${resetting ? "animate-spin" : ""}`} />
                      {resetting ? "Sıfırlanıyor…" : "Cihazı Sıfırla"}
                    </button>
                    {user.reset_credits <= 0 && user.role !== "admin" && (
                      <button className="px-3 py-1.5 bg-brand-500/20 border border-brand-500/40 text-brand-300 hover:bg-brand-500/30 rounded-lg text-xs font-medium">
                        Sıfırlama Hakkı Al — 15 ₺
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function Field({
  icon: Icon,
  label,
  value,
  mono,
}: {
  icon?: any;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <div className="text-gray-500 text-xs flex items-center gap-1 mb-1">
        {Icon && <Icon size={11} />}
        {label}
      </div>
      <div className={`text-white text-sm ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}
