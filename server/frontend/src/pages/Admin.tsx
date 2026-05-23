import { useEffect, useState } from "react";
import {
  Crown, Plus, Shield, Trash2, X, ChevronRight, Monitor,
  ShoppingBag, Key, Clock, Globe, Cpu, RefreshCw, UserCheck, UserX,
  Download, Activity, LogIn, Bot, RotateCcw,
} from "lucide-react";
import { api, type User, type UserDetail, type ActivityLog, type SiteStats, type AdminOrder } from "../lib/api";

const PLAN_COLORS: Record<string, string> = {
  free: "bg-gray-500/20 text-gray-300 border-gray-500/30",
  pro: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  agency: "bg-purple-500/20 text-purple-300 border-purple-500/30",
};

const ORDER_STATUS: Record<string, { label: string; cls: string }> = {
  pending: { label: "Bekliyor", cls: "text-yellow-400 bg-yellow-400/10" },
  success: { label: "Ödendi", cls: "text-green-400 bg-green-400/10" },
  failed: { label: "Başarısız", cls: "text-red-400 bg-red-400/10" },
};

const PRODUCT_LABELS: Record<string, string> = {
  license_pro_1m: "Pro Lisans — 1 Ay",
  license_pro_3m: "Pro Lisans — 3 Ay",
  license_pro_6m: "Pro Lisans — 6 Ay",
  license_agency_1m: "Agency Lisans — 1 Ay",
  device_reset: "Cihaz Sıfırlama",
};

const EVENT_META: Record<string, { label: string; icon: JSX.Element; cls: string }> = {
  login: { label: "Web Giriş", icon: <LogIn size={11} />, cls: "text-blue-300 bg-blue-400/10 border-blue-500/20" },
  register: { label: "Kayıt Oldu", icon: <UserCheck size={11} />, cls: "text-green-300 bg-green-400/10 border-green-500/20" },
  download: { label: "İndirdi", icon: <Download size={11} />, cls: "text-brand-300 bg-brand-400/10 border-brand-500/20" },
  bot_session: { label: "Bot Aktif", icon: <Bot size={11} />, cls: "text-purple-300 bg-purple-400/10 border-purple-500/20" },
  device_reset: { label: "Cihaz Sıfırladı", icon: <RotateCcw size={11} />, cls: "text-red-300 bg-red-400/10 border-red-500/20" },
};

export default function Admin() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{ msg: string; onConfirm: () => void } | null>(null);
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [stats, setStats] = useState<SiteStats | null>(null);
  const [pendingOrders, setPendingOrders] = useState<AdminOrder[]>([]);
  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
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
      const list = await api.admin.listUsers();
      setUsers(list);
    } catch {
      showToast("Kullanıcı listesi alınamadı", false);
    } finally {
      setLoading(false);
    }
    try {
      const s = await api.admin.siteStats();
      setStats(s);
    } catch {
      // istatistikler sessizce başarısız olabilir
    }
    try {
      const orders = await api.admin.listOrders("pending");
      setPendingOrders(orders);
    } catch {
      // siparişler sessizce başarısız olabilir
    }
  };

  const openDetail = async (id: number) => {
    setDetail(null);
    setDetailLoading(true);
    try {
      const d = await api.admin.userDetail(id);
      setDetail(d);
    } catch {
      showToast("Detay alınamadı", false);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setDetail(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const refreshBoth = (id?: number) => {
    load();
    if (id) openDetail(id);
  };

  const extend = async (id: number, days: number) => {
    try {
      const r = await api.admin.extendLicense(id, days);
      showToast(`✅ Lisans uzatıldı: ${new Date(r.new_expiry).toLocaleDateString("tr-TR")}`);
      refreshBoth(id);
    } catch {
      showToast("Uzatma başarısız", false);
    }
  };

  const togglePlan = async (u: User) => {
    const next = u.plan === "free" ? "pro" : u.plan === "pro" ? "agency" : "free";
    const ok = await askConfirm(`${u.username} planı "${next}" yapılsın mı?`);
    if (!ok) return;
    await api.admin.updateUser(u.id, { plan: next });
    showToast(`Plan değiştirildi: ${next}`);
    refreshBoth(u.id);
  };

  const toggleActive = async (u: User) => {
    await api.admin.updateUser(u.id, { is_active: !u.is_active });
    showToast(u.is_active ? "Hesap pasifleştirildi" : "Hesap aktifleştirildi");
    refreshBoth(u.id);
  };

  const grantReset = async (id: number) => {
    try {
      const r = await api.admin.grantReset(id, 1);
      showToast(`Reset hakkı verildi (toplam: ${r.reset_credits})`);
      refreshBoth(id);
    } catch {
      showToast("Verilemedi", false);
    }
  };

  const del = async (id: number, username: string) => {
    const ok = await askConfirm(`${username} kullanıcısı kalıcı olarak silinsin mi?`);
    if (!ok) return;
    try {
      await api.admin.deleteUser(id);
      showToast("Kullanıcı silindi");
      setDetail(null);
      load();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || "Silinemedi", false);
    }
  };

  const fmt = (d: string | null) => (d ? new Date(d).toLocaleDateString("tr-TR") : "—");
  const isExpired = (d: string | null) => d && new Date(d) < new Date();

  return (
    <div className="p-6 space-y-5">
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium shadow-xl
            ${toast.ok ? "bg-green-500/20 border border-green-500/40 text-green-300" : "bg-red-500/20 border border-red-500/40 text-red-300"}`}
        >
          <span>{toast.msg}</span>
          <button onClick={() => setToast(null)} className="opacity-60 hover:opacity-100"><X size={14} /></button>
        </div>
      )}

      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl">
            <p className="text-white text-sm mb-5">{confirmModal.msg}</p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setConfirmModal(null)} className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg">
                İptal
              </button>
              <button onClick={confirmModal.onConfirm} className="px-4 py-2 text-sm bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/40 rounded-lg">
                Onayla
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        <Crown className="text-yellow-400" size={22} />
        <div>
          <h1 className="text-xl font-bold text-white">Admin Paneli</h1>
          <p className="text-gray-500 text-sm">{users.length} kullanıcı</p>
        </div>
      </div>

      {/* ── Bekleyen Ödemeler ── */}
      {pendingOrders.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xs font-semibold text-yellow-400 uppercase tracking-wider flex items-center gap-2">
            <ShoppingBag size={12} /> Bekleyen Ödemeler ({pendingOrders.length})
          </h2>
          <div className="space-y-2">
            {pendingOrders.map((o) => (
              <div key={o.id} className="bg-gray-900 border border-yellow-500/20 rounded-xl px-4 py-3 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-white font-medium">{o.username}</span>
                    <span className="text-gray-500 text-xs">{o.email}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs">
                    <span className="text-yellow-400 font-mono">{o.merchant_oid}</span>
                    <span className="text-gray-400">{o.product === "device_reset" ? "Cihaz Sıfırlama" : o.product}</span>
                    <span className="text-brand-400 font-semibold">{o.amount_tl} ₺</span>
                  </div>
                </div>
                <span className="px-3 py-1.5 bg-yellow-500/20 text-yellow-300 border border-yellow-500/40 rounded-lg text-xs font-medium">
                  Bekliyor
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Site İstatistikleri ── */}
      {stats && (
        <div className="space-y-3">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Activity size={12} /> Site İstatistikleri
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Toplam Ziyaret", main: stats.page_views.total, sub: `7g: ${stats.page_views.last_7d}`, cls: "text-brand-400" },
              { label: "Tekil IP", main: stats.page_views.unique_ips_total, sub: `7g: ${stats.page_views.unique_ips_7d}`, cls: "text-blue-400" },
              { label: "Kayıt", main: stats.events.registrations_total, sub: `7g: +${stats.events.registrations_7d}`, cls: "text-green-400" },
              { label: "İndirme", main: stats.events.downloads_total, sub: `7g: ${stats.events.downloads_7d}`, cls: "text-yellow-400" },
              { label: "Web Giriş", main: stats.events.logins_total, sub: `7g: ${stats.events.logins_7d}`, cls: "text-purple-400" },
              { label: "Bot Oturumu", main: stats.events.bot_sessions_total, sub: `7g: ${stats.events.bot_sessions_7d}`, cls: "text-pink-400" },
            ].map(({ label, main, sub, cls }) => (
              <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-3">
                <div className="text-gray-500 text-[10px] uppercase mb-1">{label}</div>
                <div className={`text-2xl font-bold font-mono ${cls}`}>{main.toLocaleString()}</div>
                <div className="text-gray-600 text-[10px] mt-0.5">{sub}</div>
              </div>
            ))}
          </div>
          {stats.top_pages.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="text-gray-500 text-xs font-medium mb-3">En Çok Ziyaret Edilen Sayfalar</div>
              <div className="space-y-2">
                {stats.top_pages.map(({ path, count }) => {
                  const pct = Math.round((count / (stats.top_pages[0]?.count || 1)) * 100);
                  return (
                    <div key={path} className="flex items-center gap-3 text-xs">
                      <span className="text-gray-400 font-mono w-28 truncate shrink-0">{path}</span>
                      <div className="flex-1 bg-gray-800 rounded-full h-1.5">
                        <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-gray-400 font-mono w-10 text-right">{count.toLocaleString()}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="text-gray-500 text-sm">Yükleniyor…</div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs">
                <th className="px-4 py-3 text-left">Kullanıcı</th>
                <th className="px-4 py-3 text-left">Plan</th>
                <th className="px-4 py-3 text-left">Lisans</th>
                <th className="px-4 py-3 text-left">Durum</th>
                <th className="px-4 py-3 text-left">Reset</th>
                <th className="px-4 py-3 text-left">Kayıt</th>
                <th className="px-4 py-3 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 cursor-pointer"
                  onClick={() => openDetail(u.id)}
                >
                  <td className="px-4 py-3">
                    <div className="text-white">{u.username}</div>
                    <div className="text-gray-500 text-xs">{u.email}</div>
                    {u.role === "admin" && (
                      <span className="text-xs text-yellow-400">👑 Admin</span>
                    )}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => togglePlan(u)}
                      className={`px-2 py-0.5 rounded-md text-xs font-medium border capitalize ${PLAN_COLORS[u.plan]}`}
                    >
                      {u.plan}
                    </button>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className={`text-xs ${isExpired(u.license_expires_at) ? "text-red-400" : "text-gray-300"}`}>
                      {fmt(u.license_expires_at)}
                    </div>
                    <div className="flex gap-1 mt-1">
                      {[7, 30, 90, 365].map((d) => (
                        <button
                          key={d}
                          onClick={() => extend(u.id, d)}
                          className="text-[10px] px-1.5 py-0.5 bg-gray-800 hover:bg-brand-500 hover:text-black text-gray-400 rounded transition-colors"
                          title={`+${d} gün uzat`}
                        >
                          +{d}g
                        </button>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <button onClick={() => toggleActive(u)} className="flex items-center gap-1.5">
                      <span
                        className={`inline-block w-2 h-2 rounded-full ${u.is_active ? "bg-green-400" : "bg-red-500"}`}
                      />
                      <span className="text-xs text-gray-400">{u.is_active ? "Aktif" : "Pasif"}</span>
                    </button>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-brand-400 font-mono">{u.reset_credits}</span>
                      <button
                        onClick={() => grantReset(u.id)}
                        className="text-gray-600 hover:text-brand-400 transition-colors"
                        title="+1 reset hakkı ver"
                      >
                        <Plus size={12} />
                      </button>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => del(u.id, u.username)}
                        className="text-gray-600 hover:text-red-400 transition-colors"
                        title="Kullanıcıyı sil"
                      >
                        <Trash2 size={14} />
                      </button>
                      <ChevronRight size={14} className="text-gray-600" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-xs text-gray-500 space-y-1">
        <div className="flex items-center gap-2 text-gray-400 font-medium mb-2">
          <Shield size={14} /> Plan Limitleri
        </div>
        <div>• <span className="text-gray-300">Free:</span> 1 kampanya</div>
        <div>• <span className="text-blue-300">Pro:</span> 5 kampanya · gelişmiş özellikler</div>
        <div>• <span className="text-purple-300">Agency:</span> 50 kampanya · sınırsız erişim</div>
      </div>

      {/* Detail Drawer */}
      {(detail || detailLoading) && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            onClick={() => setDetail(null)}
          />
          <div className="fixed right-0 top-0 h-full w-full max-w-lg z-50 bg-gray-950 border-l border-gray-800 shadow-2xl flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 font-bold text-sm">
                  {detail?.user.username?.[0]?.toUpperCase() ?? "?"}
                </div>
                <div>
                  <div className="text-white font-semibold">{detail?.user.username ?? "Yükleniyor…"}</div>
                  <div className="text-gray-500 text-xs">{detail?.user.email}</div>
                </div>
              </div>
              <button onClick={() => setDetail(null)} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>

            {detailLoading && !detail ? (
              <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">Yükleniyor…</div>
            ) : detail ? (
              <div className="flex-1 overflow-y-auto p-6 space-y-6">

                {/* ── Hesap Özeti ── */}
                <section className="space-y-3">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <Key size={12} /> Hesap
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "ID", value: `#${detail.user.id}` },
                      { label: "Rol", value: detail.user.role === "admin" ? "👑 Admin" : "Kullanıcı" },
                      {
                        label: "Plan",
                        value: (
                          <span className={`px-2 py-0.5 rounded-md text-xs font-medium border capitalize ${PLAN_COLORS[detail.user.plan]}`}>
                            {detail.user.plan}
                          </span>
                        ),
                      },
                      {
                        label: "Durum",
                        value: (
                          <span className={`flex items-center gap-1.5 text-xs ${detail.user.is_active ? "text-green-400" : "text-red-400"}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${detail.user.is_active ? "bg-green-400" : "bg-red-500"}`} />
                            {detail.user.is_active ? "Aktif" : "Pasif"}
                          </span>
                        ),
                      },
                      {
                        label: "Lisans Bitiş",
                        value: (
                          <span className={detail.user.days_left === 0 ? "text-red-400" : "text-gray-200"}>
                            {detail.user.license_expires_at
                              ? `${fmt(detail.user.license_expires_at)} (${detail.user.days_left} gün)`
                              : "—"}
                          </span>
                        ),
                      },
                      { label: "Reset Hakkı", value: <span className="text-brand-400 font-mono">{detail.user.reset_credits}</span> },
                      { label: "Kayıt", value: fmt(detail.user.created_at) },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-gray-900 rounded-lg px-3 py-2">
                        <div className="text-gray-500 text-[10px] uppercase mb-0.5">{label}</div>
                        <div className="text-sm text-gray-200">{value}</div>
                      </div>
                    ))}
                  </div>
                </section>

                {/* ── Hızlı İşlemler ── */}
                <section className="space-y-3">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <RefreshCw size={12} /> Hızlı İşlemler
                  </h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-gray-500 text-xs mb-1.5">Lisans Uzat</p>
                      <div className="flex gap-2 flex-wrap">
                        {[7, 30, 90, 180, 365].map((d) => (
                          <button
                            key={d}
                            onClick={() => extend(detail.user.id, d)}
                            className="px-3 py-1.5 bg-gray-800 hover:bg-brand-500 hover:text-black text-gray-300 text-xs rounded-lg transition-colors font-medium"
                          >
                            +{d} gün
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2 flex-wrap pt-1">
                      <button
                        onClick={() => {
                          const fakeUser = users.find((u) => u.id === detail.user.id);
                          if (fakeUser) togglePlan(fakeUser);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 text-xs rounded-lg border border-blue-500/30 transition-colors"
                      >
                        <Crown size={11} /> Plan Değiştir
                      </button>
                      <button
                        onClick={() => {
                          const fakeUser = users.find((u) => u.id === detail.user.id);
                          if (fakeUser) toggleActive(fakeUser);
                        }}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-colors ${detail.user.is_active
                          ? "bg-red-500/10 hover:bg-red-500/20 text-red-300 border-red-500/30"
                          : "bg-green-500/10 hover:bg-green-500/20 text-green-300 border-green-500/30"
                          }`}
                      >
                        {detail.user.is_active ? <><UserX size={11} /> Pasifleştir</> : <><UserCheck size={11} /> Aktifleştir</>}
                      </button>
                      <button
                        onClick={() => grantReset(detail.user.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded-lg border border-gray-700 transition-colors"
                      >
                        <Plus size={11} /> Reset Hakkı Ver
                      </button>
                      <button
                        onClick={() => del(detail.user.id, detail.user.username)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs rounded-lg border border-red-500/30 transition-colors"
                      >
                        <Trash2 size={11} /> Sil
                      </button>
                    </div>
                  </div>
                </section>

                {/* ── Cihaz Bilgisi ── */}
                <section className="space-y-3">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <Monitor size={12} /> Kayıtlı Cihaz
                  </h3>
                  {detail.device ? (
                    <div className="bg-gray-900 rounded-xl p-4 space-y-2.5 border border-gray-800">
                      {[
                        { icon: <Cpu size={12} />, label: "Hostname", value: detail.device.hostname ?? "—" },
                        { icon: <Monitor size={12} />, label: "OS", value: detail.device.os_info ?? "—" },
                        { icon: <Globe size={12} />, label: "Son IP", value: detail.device.last_ip ?? "—" },
                        { icon: <Key size={12} />, label: "Machine ID", value: detail.device.machine_id, mono: true },
                        { icon: <Clock size={12} />, label: "İlk Görülme", value: fmt(detail.device.first_seen) },
                        { icon: <Clock size={12} />, label: "Son Görülme", value: fmt(detail.device.last_seen) },
                      ].map(({ icon, label, value, mono }) => (
                        <div key={label} className="flex items-start gap-2 text-sm">
                          <span className="text-gray-600 mt-0.5">{icon}</span>
                          <span className="text-gray-500 w-24 shrink-0">{label}</span>
                          <span className={`text-gray-200 break-all ${mono ? "font-mono text-xs text-gray-400" : ""}`}>{value}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-600 text-sm bg-gray-900 rounded-xl p-4 border border-gray-800">
                      Henüz cihaz kaydı yok — kullanıcı hiç giriş yapmamış.
                    </div>
                  )}
                </section>

                {/* ── Aktivite Geçmişi ── */}
                <section className="space-y-3">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <Activity size={12} /> Aktivite ({detail.activity?.length ?? 0})
                  </h3>
                  {!detail.activity?.length ? (
                    <div className="text-gray-600 text-sm bg-gray-900 rounded-xl p-4 border border-gray-800">
                      Henüz aktivite kaydı yok.
                    </div>
                  ) : (
                    <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                      {detail.activity.map((a: ActivityLog) => {
                        const meta = EVENT_META[a.event] ?? { label: a.event, icon: <Activity size={11} />, cls: "text-gray-400 bg-gray-700/30 border-gray-700" };
                        return (
                          <div key={a.id} className="flex items-start gap-2.5 py-1.5 px-2 rounded-lg hover:bg-gray-900 transition-colors">
                            <span className={`mt-0.5 flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-medium border whitespace-nowrap ${meta.cls}`}>
                              {meta.icon} {meta.label}
                            </span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                {a.ip && <span className="text-gray-500 text-[10px] font-mono">{a.ip}</span>}
                                {a.detail && <span className="text-gray-600 text-[10px]">{a.detail}</span>}
                              </div>
                              <div className="text-gray-600 text-[10px] mt-0.5">
                                {new Date(a.created_at).toLocaleString("tr-TR")}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>

                {/* ── Sipariş Geçmişi ── */}
                <section className="space-y-3">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    <ShoppingBag size={12} /> Sipariş Geçmişi
                  </h3>
                  {detail.orders.length === 0 ? (
                    <div className="text-gray-600 text-sm bg-gray-900 rounded-xl p-4 border border-gray-800">
                      Sipariş kaydı yok.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {detail.orders.map((o) => {
                        const st = ORDER_STATUS[o.status] ?? ORDER_STATUS.pending;
                        return (
                          <div key={o.id} className="bg-gray-900 border border-gray-800 rounded-xl p-3 flex items-center gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="text-gray-200 text-sm font-medium truncate">
                                {PRODUCT_LABELS[o.product] ?? o.product}
                              </div>
                              <div className="text-gray-500 text-xs mt-0.5 font-mono">{o.merchant_oid}</div>
                              <div className="text-gray-600 text-xs mt-0.5">
                                {o.paid_at ? `Ödeme: ${fmt(o.paid_at)}` : `Oluşturma: ${fmt(o.created_at)}`}
                              </div>
                            </div>
                            <div className="text-right shrink-0">
                              <div className="text-white font-semibold text-sm">
                                {o.amount_tl} {o.currency}
                              </div>
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${st.cls}`}>
                                {st.label}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
