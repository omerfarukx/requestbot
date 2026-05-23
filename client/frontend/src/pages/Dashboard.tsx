import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle,
  Globe,
  Play,
  Shield,
  XCircle,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type Campaign, type Stats } from "../lib/api";

const PROXY_COLORS: Record<string, string> = {
  active: "#22c55e",
  dead: "#ef4444",
  unknown: "#64748b",
};

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  gradient,
  index = 0,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: string;
  gradient: string;
  index?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.5, ease: "easeOut" }}
      className="relative group overflow-hidden rounded-2xl p-5 border border-gray-800/60 cursor-default"
      style={{ background: "rgba(10,10,20,0.85)", backdropFilter: "blur(16px)" }}
      whileHover={{ scale: 1.02, borderColor: "rgba(99,102,241,0.4)" }}
    >
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${gradient} blur-3xl`} style={{ transform: "scale(1.5)" }} />
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <span className="text-gray-400 text-xs font-medium uppercase tracking-widest">{label}</span>
          <div className={`p-2.5 rounded-xl ${color}`}>
            <Icon size={15} />
          </div>
        </div>
        <p className="text-3xl font-bold text-white tabular-nums">{value}</p>
        <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${gradient} opacity-40 rounded-full`} />
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [hourly, setHourly] = useState<{ hour: string; total: number; success: number }[]>([]);
  const [proxyHealth, setProxyHealth] = useState<{ status: string; count: number }[]>([]);

  const load = async () => {
    try {
      const [s, c, h, p] = await Promise.all([
        api.stats.get(),
        api.campaigns.list(),
        api.analytics.hourly(24),
        api.analytics.proxies(),
      ]);
      setStats(s);
      setCampaigns(c);
      setHourly(h);
      setProxyHealth(p);
    } catch { }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const hourlyChart = hourly.map((h) => ({
    label: h.hour.slice(11, 16),
    Toplam: h.total,
    Başarılı: h.success,
  }));

  const chartData = campaigns.map((c) => ({
    name: c.name.length > 14 ? c.name.slice(0, 14) + "…" : c.name,
    Başarılı: c.successful_visits,
    Başarısız: c.failed_visits,
  }));

  const successRate =
    stats && stats.total_visits > 0
      ? Math.round((stats.successful_visits / stats.total_visits) * 100)
      : 0;

  return (
    <div className="p-6 space-y-6">
      <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Genel bakış ve istatistikler</p>
      </motion.div>

      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        <StatCard index={0} icon={Globe} label="Toplam Ziyaret" value={stats?.total_visits ?? 0}
          color="bg-blue-500/15 text-blue-400" gradient="bg-gradient-to-br from-blue-500/10 to-transparent" />
        <StatCard index={1} icon={CheckCircle} label="Başarılı" value={stats?.successful_visits ?? 0}
          color="bg-green-500/15 text-green-400" gradient="bg-gradient-to-br from-green-500/10 to-transparent" />
        <StatCard index={2} icon={XCircle} label="Başarısız" value={(stats?.total_visits ?? 0) - (stats?.successful_visits ?? 0)}
          color="bg-red-500/15 text-red-400" gradient="bg-gradient-to-br from-red-500/10 to-transparent" />
        <StatCard index={3} icon={Play} label="Çalışan Kampanya" value={stats?.running_campaigns ?? 0}
          color="bg-indigo-500/15 text-indigo-400" gradient="bg-gradient-to-br from-indigo-500/10 to-transparent" />
        <StatCard index={4} icon={Activity} label="Başarı Oranı" value={`%${successRate}`}
          color="bg-purple-500/15 text-purple-400" gradient="bg-gradient-to-br from-purple-500/10 to-transparent" />
        <StatCard index={5} icon={Shield} label="Aktif Proxy" value={`${stats?.active_proxies ?? 0} / ${stats?.total_proxies ?? 0}`}
          color="bg-cyan-500/15 text-cyan-400" gradient="bg-gradient-to-br from-cyan-500/10 to-transparent" />
      </div>

      {hourlyChart.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.5 }}
          className="rounded-2xl p-5 border border-gray-800/60" style={{ background: "rgba(10,10,20,0.85)" }}>
          <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-widest">Son 24 Saatlik Trafik</h2>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={hourlyChart}>
              <defs>
                <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gSuccess" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="label" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#0a0a14", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 12, color: "#f1f5f9", fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="Toplam" stroke="#6366f1" fill="url(#gTotal)" strokeWidth={2.5} dot={false} />
              <Area type="monotone" dataKey="Başarılı" stroke="#22c55e" fill="url(#gSuccess)" strokeWidth={2.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {proxyHealth.length > 0 && (
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.65, duration: 0.5 }}
            className="rounded-2xl p-5 border border-gray-800/60" style={{ background: "rgba(10,10,20,0.85)" }}>
            <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-widest">Proxy Sağlık</h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={proxyHealth}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  innerRadius={40}
                  paddingAngle={3}
                  label={(e: any) => `${e.status} (${e.count})`}
                >
                  {proxyHealth.map((p, i) => (
                    <Cell key={i} fill={PROXY_COLORS[p.status] || "#64748b"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0a0a14", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 12, color: "#f1f5f9", fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {chartData.length > 0 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.65, duration: 0.5 }}
            className="rounded-2xl p-5 border border-gray-800/60" style={{ background: "rgba(10,10,20,0.85)" }}>
            <h2 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-widest">Kampanya Bazında Ziyaretler</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "#111827",
                    border: "1px solid #374151",
                    borderRadius: 8,
                    color: "#f1f5f9",
                  }}
                />
                <Bar dataKey="Başarılı" fill="#22c55e" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Başarısız" fill="#ef4444" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </div>

      {campaigns.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
          className="rounded-2xl p-12 text-center border border-gray-800/60" style={{ background: "rgba(10,10,20,0.85)" }}>
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
            <Globe className="text-gray-600" size={28} />
          </div>
          <p className="text-gray-400 font-medium">Henüz kampanya yok.</p>
          <p className="text-gray-600 text-sm mt-1">Kampanyalar sayfasından bir tane oluşturun.</p>
        </motion.div>
      )}
    </div>
  );
}
