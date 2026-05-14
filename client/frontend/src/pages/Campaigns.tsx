import { useEffect, useState } from "react";
import {
  Edit2,
  Pause,
  Play,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { api, type Campaign, type CampaignCreate, type RankCheck } from "../lib/api";

const ENGINES = [
  { value: "google", label: "Google" },
  { value: "yandex", label: "Yandex" },
  { value: "bing", label: "Bing" },
  { value: "direct", label: "Direkt (Referrer yok)" },
];

const defaultForm: CampaignCreate = {
  name: "",
  target_url: "",
  keyword: null,
  search_engine: "google",
  session_duration_min: 5,
  session_duration_max: 15,
  concurrent_workers: 3,
  daily_visit_target: null,
  pages_per_session_min: 2,
  pages_per_session_max: 8,
};

function Badge({ status }: { status: Campaign["status"] }) {
  const map = {
    idle: "bg-gray-700 text-gray-300",
    running: "bg-green-500/20 text-green-400 animate-pulse",
    stopped: "bg-red-500/20 text-red-400",
  };
  const labels = { idle: "Bekliyor", running: "Çalışıyor", stopped: "Durduruldu" };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[status]}`}>
      {labels[status]}
    </span>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-gray-400 text-xs mb-1 block">{label}</span>
      {children}
    </label>
  );
}

const inputCls =
  "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500";

interface ModalProps {
  editing: Campaign | null;
  onClose: () => void;
  onSave: () => void;
}

function CampaignModal({ editing, onClose, onSave }: ModalProps) {
  const [form, setForm] = useState<CampaignCreate>(
    editing
      ? {
        name: editing.name,
        target_url: editing.target_url,
        keyword: editing.keyword,
        search_engine: editing.search_engine,
        session_duration_min: editing.session_duration_min,
        session_duration_max: editing.session_duration_max,
        concurrent_workers: editing.concurrent_workers,
        daily_visit_target: editing.daily_visit_target,
        pages_per_session_min: editing.pages_per_session_min,
        pages_per_session_max: editing.pages_per_session_max,
      }
      : defaultForm
  );
  const [saving, setSaving] = useState(false);

  const set = (k: keyof CampaignCreate, v: unknown) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await api.campaigns.update(editing.id, form);
      } else {
        await api.campaigns.create(form);
      }
      onSave();
      onClose();
    } catch {
      alert("Kaydetme başarısız");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 className="font-semibold text-white">
            {editing ? "Kampanyayı Düzenle" : "Yeni Kampanya"}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          <Field label="Kampanya Adı *">
            <input
              className={inputCls}
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              required
              placeholder="Örn: Site1 Trafik"
            />
          </Field>
          <Field label="Hedef URL *">
            <input
              className={inputCls}
              value={form.target_url}
              onChange={(e) => set("target_url", e.target.value)}
              required
              placeholder="https://example.com"
              type="url"
            />
          </Field>
          <Field label="Anahtar Kelimeler (virgülle ayır)">
            <textarea
              className={`${inputCls} h-20 resize-none`}
              value={form.keyword ?? ""}
              onChange={(e) => set("keyword", e.target.value || null)}
              placeholder="adana evden eve nakliyat, adana nakliyat, adana taşımacılık"
            />
            <p className="text-gray-600 text-xs mt-1">Her oturumda rastgele biri seçilir</p>
          </Field>
          <Field label="Arama Motoru">
            <select
              className={inputCls}
              value={form.search_engine}
              onChange={(e) => set("search_engine", e.target.value)}
            >
              {ENGINES.map((e) => (
                <option key={e.value} value={e.value}>
                  {e.label}
                </option>
              ))}
            </select>
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Min Oturum Süresi (dk)">
              <input
                className={inputCls}
                type="number"
                min={1}
                max={60}
                value={form.session_duration_min}
                onChange={(e) => set("session_duration_min", +e.target.value)}
              />
            </Field>
            <Field label="Max Oturum Süresi (dk)">
              <input
                className={inputCls}
                type="number"
                min={1}
                max={60}
                value={form.session_duration_max}
                onChange={(e) => set("session_duration_max", +e.target.value)}
              />
            </Field>
            <Field label="Eşzamanlı İşçi">
              <input
                className={inputCls}
                type="number"
                min={1}
                max={50}
                value={form.concurrent_workers}
                onChange={(e) => set("concurrent_workers", +e.target.value)}
              />
            </Field>
            <Field label="Günlük Hedef (boş = sınırsız)">
              <input
                className={inputCls}
                type="number"
                min={1}
                value={form.daily_visit_target ?? ""}
                onChange={(e) =>
                  set("daily_visit_target", e.target.value ? +e.target.value : null)
                }
                placeholder="Sınırsız"
              />
            </Field>
            <Field label="Min Sayfa/Oturum">
              <input
                className={inputCls}
                type="number"
                min={1}
                max={30}
                value={form.pages_per_session_min}
                onChange={(e) => set("pages_per_session_min", +e.target.value)}
              />
            </Field>
            <Field label="Max Sayfa/Oturum">
              <input
                className={inputCls}
                type="number"
                min={1}
                max={30}
                value={form.pages_per_session_max}
                onChange={(e) => set("pages_per_session_max", +e.target.value)}
              />
            </Field>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-gray-700 text-gray-400 hover:text-white text-sm transition-colors"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-black font-semibold text-sm transition-colors disabled:opacity-50"
            >
              {saving ? "Kaydediliyor…" : "Kaydet"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RankChart({ data }: { data: RankCheck[] }) {
  if (data.length < 2) return null;

  // Her keyword için son 10 veriyi al
  const keywords = [...new Set(data.map((d) => d.keyword))];
  const colors = ["#f59e0b", "#3b82f6", "#10b981", "#ec4899", "#8b5cf6"];

  const timePoints = [...new Set(data.map((d) => d.checked_at))].slice(-15);
  const chartData = timePoints.map((t) => {
    const pt: Record<string, unknown> = {
      t: new Date(t).toLocaleDateString("tr-TR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }),
    };
    keywords.forEach((kw) => {
      const entry = data.find((d) => d.checked_at === t && d.keyword === kw);
      pt[kw] = entry?.rank ?? null;
    });
    return pt;
  });

  return (
    <div className="mt-3 border-t border-gray-800 pt-3">
      <p className="text-gray-500 text-xs mb-2">Sıralama Geçmişi</p>
      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={chartData}>
          <XAxis dataKey="t" hide />
          <YAxis reversed domain={[1, 100]} hide />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            formatter={(v: unknown, name: string) => [(v != null ? `${v}. sıra` : "Yok"), name]}
          />
          {keywords.map((kw, i) => (
            <Line
              key={kw}
              type="monotone"
              dataKey={kw}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [ranks, setRanks] = useState<Record<number, RankCheck[]>>({});
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Campaign | null>(null);

  const load = async () => {
    try {
      const list = await api.campaigns.list();
      setCampaigns(list);
      const rankMap: Record<number, RankCheck[]> = {};
      await Promise.all(
        list.map(async (c) => {
          try { rankMap[c.id] = await api.campaigns.ranks(c.id); } catch { }
        })
      );
      setRanks(rankMap);
    } catch { }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  const handleStart = async (id: number) => {
    await api.campaigns.start(id);
    load();
  };

  const handleStop = async (id: number) => {
    await api.campaigns.stop(id);
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Bu kampanyayı silmek istediğinize emin misiniz?")) return;
    await api.campaigns.delete(id);
    load();
  };

  const handleReset = async (c: Campaign) => {
    await api.campaigns.update(c.id, {
      ...c,
      total_visits: undefined,
      successful_visits: undefined,
      failed_visits: undefined,
    } as never);
    load();
  };

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Kampanyalar</h1>
          <p className="text-gray-500 text-sm mt-1">
            {campaigns.length} kampanya
          </p>
        </div>
        <button
          onClick={() => {
            setEditing(null);
            setShowModal(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm transition-colors"
        >
          <Plus size={16} /> Yeni Kampanya
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-gray-500">Henüz kampanya yok.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map((c) => (
            <div
              key={c.id}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-semibold text-white truncate">{c.name}</h3>
                    <Badge status={c.status} />
                  </div>
                  <p className="text-gray-500 text-xs truncate">{c.target_url}</p>
                  {c.keyword && (
                    <p className="text-gray-600 text-xs mt-0.5">
                      🔍 {c.keyword.split(",").map(k => k.trim()).join(" · ")} · {c.search_engine}
                    </p>
                  )}
                  <div className="flex gap-4 mt-3 text-xs">
                    <span className="text-gray-400">
                      Toplam:{" "}
                      <span className="text-white font-medium">{c.total_visits}</span>
                    </span>
                    <span className="text-green-400">✓ {c.successful_visits}</span>
                    <span className="text-red-400">✗ {c.failed_visits}</span>
                    <span className="text-gray-500">
                      ⏱ {c.session_duration_min}-{c.session_duration_max}dk
                    </span>
                    <span className="text-gray-500">👥 {c.concurrent_workers}x</span>
                  </div>
                  {ranks[c.id] && ranks[c.id].length > 0 && (
                    <RankChart data={ranks[c.id]} />
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {c.status === "running" ? (
                    <button
                      onClick={() => handleStop(c.id)}
                      className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                      title="Durdur"
                    >
                      <Pause size={16} />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStart(c.id)}
                      className="p-2 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors"
                      title="Başlat"
                    >
                      <Play size={16} />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setEditing(c);
                      setShowModal(true);
                    }}
                    className="p-2 rounded-lg bg-gray-800 text-gray-400 hover:text-white transition-colors"
                    title="Düzenle"
                  >
                    <Edit2 size={15} />
                  </button>
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="p-2 rounded-lg bg-gray-800 text-gray-400 hover:text-red-400 transition-colors"
                    title="Sil"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <CampaignModal
          editing={editing}
          onClose={() => setShowModal(false)}
          onSave={load}
        />
      )}
    </div>
  );
}
