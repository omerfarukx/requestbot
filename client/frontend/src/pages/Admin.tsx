import { useEffect, useState } from "react";
import { Calendar, Crown, Power, Shield, Trash2, UserPlus } from "lucide-react";
import { api, type User } from "../lib/api";

const PLAN_COLORS: Record<string, string> = {
  free: "bg-gray-500/20 text-gray-300 border-gray-500/30",
  pro: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  agency: "bg-purple-500/20 text-purple-300 border-purple-500/30",
};

export default function Admin() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  };

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
  };

  useEffect(() => {
    load();
  }, []);

  const extend = async (id: number, days: number) => {
    try {
      const r = await api.admin.extendLicense(id, days);
      showToast(`✅ Lisans uzatıldı: ${new Date(r.new_expiry).toLocaleDateString("tr-TR")}`);
      load();
    } catch {
      showToast("Uzatma başarısız", false);
    }
  };

  const togglePlan = async (u: User) => {
    const next = u.plan === "free" ? "pro" : u.plan === "pro" ? "agency" : "free";
    await api.admin.updateUser(u.id, { plan: next });
    showToast(`Plan değiştirildi: ${next}`);
    load();
  };

  const toggleActive = async (u: User) => {
    await api.admin.updateUser(u.id, { is_active: !u.is_active });
    showToast(u.is_active ? "Hesap pasifleştirildi" : "Hesap aktifleştirildi");
    load();
  };

  const del = async (id: number, username: string) => {
    if (!confirm(`${username} kullanıcısı silinsin mi?`)) return;
    try {
      await api.admin.deleteUser(id);
      showToast("Kullanıcı silindi");
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
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-xl
            ${toast.ok ? "bg-green-500/20 border border-green-500/40 text-green-300" : "bg-red-500/20 border border-red-500/40 text-red-300"}`}
        >
          {toast.msg}
        </div>
      )}

      <div className="flex items-center gap-3">
        <Crown className="text-yellow-400" size={22} />
        <div>
          <h1 className="text-xl font-bold text-white">Admin Paneli</h1>
          <p className="text-gray-500 text-sm">{users.length} kullanıcı</p>
        </div>
      </div>

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
                <th className="px-4 py-3 text-left">Kayıt</th>
                <th className="px-4 py-3 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-4 py-3">
                    <div className="text-white">{u.username}</div>
                    <div className="text-gray-500 text-xs">{u.email}</div>
                    {u.role === "admin" && (
                      <span className="text-xs text-yellow-400">👑 Admin</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => togglePlan(u)}
                      className={`px-2 py-0.5 rounded-md text-xs font-medium border capitalize ${PLAN_COLORS[u.plan]}`}
                    >
                      {u.plan}
                    </button>
                  </td>
                  <td className="px-4 py-3">
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
                  <td className="px-4 py-3">
                    <button onClick={() => toggleActive(u)} className="flex items-center gap-1.5">
                      <span
                        className={`inline-block w-2 h-2 rounded-full ${u.is_active ? "bg-green-400" : "bg-red-500"}`}
                      />
                      <span className="text-xs text-gray-400">{u.is_active ? "Aktif" : "Pasif"}</span>
                    </button>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => del(u.id, u.username)}
                      className="text-gray-600 hover:text-red-400 transition-colors"
                      title="Kullanıcıyı sil"
                    >
                      <Trash2 size={14} />
                    </button>
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
    </div>
  );
}
