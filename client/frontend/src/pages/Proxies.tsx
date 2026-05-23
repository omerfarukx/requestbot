import { useEffect, useState } from "react";
import { RefreshCw, Shield, Trash2, Upload, Zap, Activity } from "lucide-react";
import { api, type Proxy } from "../lib/api";

function StatusDot({ status }: { status: Proxy["status"] }) {
  const map: Record<string, string> = {
    unknown: "bg-gray-500",
    active: "bg-green-400",
    dead: "bg-red-500",
    cooldown: "bg-orange-400",
  };
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${map[status] ?? "bg-gray-500"}`}
      title={status}
    />
  );
}

export default function Proxies() {
  const [proxies, setProxies] = useState<Proxy[]>([]);
  const [text, setText] = useState("");
  const [adding, setAdding] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [testing, setTesting] = useState(false);
  const [wsKey, setWsKey] = useState("");
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [stats, setStats] = useState({ active: 0, dead: 0, unknown: 0, cooldown: 0 });
  const [usage, setUsage] = useState<Record<number, { visits: number; estimated_mb: number }>>({});

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const TOTAL_MB = 10240; // 10 GB proxy paketi

  const load = async () => {
    try {
      const [list, usageList] = await Promise.all([api.proxies.list(), api.proxies.usage()]);
      setProxies(list);
      setStats({
        active: list.filter((p) => p.status === "active").length,
        dead: list.filter((p) => p.status === "dead").length,
        unknown: list.filter((p) => p.status === "unknown").length,
        cooldown: list.filter((p) => p.status === "cooldown").length,
      });
      const usageMap: Record<number, { visits: number; estimated_mb: number }> = {};
      usageList.forEach((u) => { usageMap[u.proxy_id] = u; });
      setUsage(usageMap);
    } catch { }
  };

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async () => {
    if (!text.trim()) return;
    setAdding(true);
    try {
      const res = await api.proxies.addBulk(text);
      showToast(`${res.added} proxy eklendi`);
      setText("");
      load();
    } catch {
      showToast("Proxy eklenemedi", false);
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: number) => {
    await api.proxies.delete(id);
    load();
  };

  const handleDeleteAll = async () => {
    if (!confirm(`${proxies.length} proxyi silmek istediğinize emin misiniz?`))
      return;
    await api.proxies.deleteAll();
    load();
  };

  const handleWebshareRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await api.proxies.webshareRefresh(wsKey || undefined);
      showToast(`✅ ${res.added} proxy Webshare'den yüklendi`);
      load();
    } catch (e: any) {
      const msg = e?.response?.data?.detail || "Webshare yenilemesi başarısız";
      showToast(`❌ ${msg}`, false);
    } finally {
      setRefreshing(false);
    }
  };

  const handleTestAll = async () => {
    setTesting(true);
    try {
      const res = await api.proxies.testAll();
      showToast(`🔍 ${res.tested} test edildi — ${res.active} aktif, ${res.dead} ölü`);
      load();
    } catch {
      showToast("Test başarısız", false);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="p-6 space-y-5">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-xl transition-all
            ${toast.ok ? "bg-green-500/20 border border-green-500/40 text-green-300" : "bg-red-500/20 border border-red-500/40 text-red-300"}`}
        >
          {toast.msg}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Proxy Listesi</h1>
          <p className="text-gray-500 text-sm mt-1">
            {proxies.length} proxy ·{" "}
            <span className="text-green-400">{stats.active} aktif</span> ·{" "}
            <span className="text-orange-400">{stats.cooldown} cooldown</span> ·{" "}
            <span className="text-red-400">{stats.dead} ölü</span> ·{" "}
            <span className="text-gray-400">{stats.unknown} bilinmiyor</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {proxies.length > 0 && (
            <button
              onClick={handleTestAll}
              disabled={testing}
              className="flex items-center gap-2 px-3 py-2 text-yellow-400 hover:text-yellow-300 border border-yellow-500/30 hover:border-yellow-500/60 rounded-lg text-sm transition-colors disabled:opacity-40"
            >
              <Zap size={14} /> {testing ? "Test ediliyor…" : "Tümünü Test Et"}
            </button>
          )}
          {proxies.length > 0 && (
            <button
              onClick={handleDeleteAll}
              className="flex items-center gap-2 px-3 py-2 text-red-400 hover:text-red-300 border border-red-500/30 hover:border-red-500/60 rounded-lg text-sm transition-colors"
            >
              <Trash2 size={15} /> Tümünü Sil
            </button>
          )}
        </div>
      </div>

      {/* Proxy Kullanım Özeti */}
      {Object.keys(usage).length > 0 && (() => {
        const totalMb = Object.values(usage).reduce((s, u) => s + u.estimated_mb, 0);
        const totalVisits = Object.values(usage).reduce((s, u) => s + u.visits, 0);
        const pct = Math.min((totalMb / TOTAL_MB) * 100, 100);
        const remaining = Math.max(TOTAL_MB - totalMb, 0);
        return (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
                <Activity size={15} />
                Tahmini Proxy Kullanımı
              </div>
              <span className="text-xs text-gray-500">{totalVisits} ziyaret</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${pct > 80 ? "bg-red-500" : pct > 50 ? "bg-yellow-500" : "bg-green-500"
                    }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-xs font-mono text-gray-400 whitespace-nowrap">
                {totalMb >= 1024 ? `${(totalMb / 1024).toFixed(2)} GB` : `${totalMb.toFixed(0)} MB`}
                {" / 10 GB"}
              </span>
            </div>
            <p className="text-xs text-gray-600">
              Kalan: <span className="text-gray-400 font-medium">
                {remaining >= 1024 ? `~${(remaining / 1024).toFixed(2)} GB` : `~${remaining.toFixed(0)} MB`}
              </span>
              {" "} · Her browser session ≈ 2 MB (tahmini)
            </p>
          </div>
        );
      })()}

      {/* Webshare hızlı yenileme kartı */}
      <div className="bg-gray-900 border border-indigo-500/30 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-indigo-300">
          <RefreshCw size={15} />
          Webshare'den Otomatik Yenile
        </div>
        <p className="text-gray-500 text-xs">
          Webshare API anahtarınızı girin — mevcut proxyler silinir, yenileri eklenir.
          Daha önce kaydettiyseniz boş bırakın.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Webshare API key (ör: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-indigo-500"
            value={wsKey}
            onChange={(e) => setWsKey(e.target.value)}
          />
          <button
            onClick={handleWebshareRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-sm transition-colors disabled:opacity-40 whitespace-nowrap"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Yükleniyor…" : "Yenile"}
          </button>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Upload size={15} />
          Proxy Ekle (Manuel)
        </div>
        <p className="text-gray-600 text-xs">
          Desteklenen formatlar: <code className="text-gray-400">host:port</code> ·{" "}
          <code className="text-gray-400">host:port:user:pass</code> ·{" "}
          <code className="text-gray-400">user:pass@host:port</code> ·{" "}
          <code className="text-gray-400">http://host:port</code> ·{" "}
          <code className="text-gray-400">socks5://user:pass@host:port</code>
        </p>
        <textarea
          className="w-full h-36 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-brand-500 resize-none"
          placeholder={"192.168.1.1:8080\n192.168.1.2:8080:user:pass\nuser:pass@192.168.1.3:8080"}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          onClick={handleAdd}
          disabled={adding || !text.trim()}
          className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm transition-colors disabled:opacity-40"
        >
          {adding ? "Ekleniyor…" : "Proxileri Ekle"}
        </button>
      </div>

      {proxies.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs">
                <th className="px-4 py-3 text-left">Proxy</th>
                <th className="px-4 py-3 text-left">Protokol</th>
                <th className="px-4 py-3 text-left">Durum</th>
                <th className="px-4 py-3 text-left">Kullanım</th>
                <th className="px-4 py-3 text-left">Son Kontrol</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {proxies.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-gray-300">
                    {p.host}:{p.port}
                    {p.username && (
                      <span className="text-gray-600"> [{p.username}]</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-gray-800 rounded text-gray-400 text-xs">
                      {p.protocol.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <StatusDot status={p.status} />
                      <span className="text-gray-400 text-xs capitalize">
                        {p.status === "unknown" ? "Bilinmiyor" : p.status === "active" ? "Aktif" : p.status === "cooldown" ? "Cooldown" : "Ölü"}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">
                    {usage[p.id]
                      ? `${usage[p.id].estimated_mb >= 1024
                        ? (usage[p.id].estimated_mb / 1024).toFixed(2) + " GB"
                        : usage[p.id].estimated_mb + " MB"} (${usage[p.id].visits} ziyaret)`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs">
                    {p.last_checked
                      ? new Date(p.last_checked).toLocaleString("tr-TR")
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(p.id)}
                      className="text-gray-600 hover:text-red-400 transition-colors"
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

      {proxies.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <Shield className="mx-auto text-gray-700 mb-3" size={36} />
          <p className="text-gray-500 text-sm">
            Proxy listesi boş. Yukarıdan ekleyebilirsiniz.
          </p>
          <p className="text-gray-600 text-xs mt-1">
            Proxy olmadan da çalışır — direkt bağlantı kullanılır.
          </p>
        </div>
      )}
    </div>
  );
}
