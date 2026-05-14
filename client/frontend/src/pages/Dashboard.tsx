import { useEffect, useState } from "react";
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
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-gray-400 text-sm">{label}</span>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={16} />
        </div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
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
      <div>
        <h1 className="text-xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Genel bakış ve istatistikler</p>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        <StatCard
          icon={Globe}
          label="Toplam Ziyaret"
          value={stats?.total_visits ?? 0}
          color="bg-blue-500/10 text-blue-400"
        />
        <StatCard
          icon={CheckCircle}
          label="Başarılı"
          value={stats?.successful_visits ?? 0}
          color="bg-green-500/10 text-green-400"
        />
        <StatCard
          icon={XCircle}
          label="Başarısız"
          value={(stats?.total_visits ?? 0) - (stats?.successful_visits ?? 0)}
          color="bg-red-500/10 text-red-400"
        />
        <StatCard
          icon={Play}
          label="Çalışan Kampanya"
          value={stats?.running_campaigns ?? 0}
          color="bg-brand-500/10 text-brand-400"
        />
        <StatCard
          icon={Activity}
          label="Başarı Oranı"
          value={`%${successRate}`}
          color="bg-purple-500/10 text-purple-400"
        />
        <StatCard
          icon={Shield}
          label="Aktif Proxy"
          value={`${stats?.active_proxies ?? 0} / ${stats?.total_proxies ?? 0}`}
          color="bg-cyan-500/10 text-cyan-400"
        />
      </div>

      {hourlyChart.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">
            Son 24 Saatlik Trafik
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={hourlyChart}>
              <defs>
                <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gSuccess" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.7} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="label" tick={{ fill: "#9ca3af", fontSize: 11 }} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  color: "#f1f5f9",
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="Toplam" stroke="#6366f1" fill="url(#gTotal)" strokeWidth={2} />
              <Area type="monotone" dataKey="Başarılı" stroke="#22c55e" fill="url(#gSuccess)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {proxyHealth.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Proxy Sağlık Durumu</h2>
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
                <Tooltip
                  contentStyle={{
                    background: "#111827",
                    border: "1px solid #374151",
                    borderRadius: 8,
                    color: "#f1f5f9",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {chartData.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">
              Kampanya Bazında Ziyaretler
            </h2>
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
                <Bar dataKey="Başarılı" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Başarısız" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {campaigns.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-10 text-center">
          <Globe className="mx-auto text-gray-700 mb-3" size={40} />
          <p className="text-gray-500">Henüz kampanya yok.</p>
          <p className="text-gray-600 text-sm mt-1">
            Kampanyalar sayfasından bir tane oluşturun.
          </p>
        </div>
      )}
    </div>
  );
}
