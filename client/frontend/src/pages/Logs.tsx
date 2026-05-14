import { useEffect, useRef, useState } from "react";
import { ScrollText, Trash2, WifiOff } from "lucide-react";
import { api, createLogWebSocket, type LogEntry } from "../lib/api";

const levelCls: Record<string, string> = {
  info: "text-gray-300",
  warning: "text-yellow-400",
  error: "text-red-400",
};

const levelBadge: Record<string, string> = {
  info: "bg-blue-500/10 text-blue-400",
  warning: "bg-yellow-500/10 text-yellow-400",
  error: "bg-red-500/10 text-red-400",
};

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    api.logs.list().then(setLogs).catch(() => { });

    const ws = createLogWebSocket((entry) => {
      setLogs((prev) => [...prev.slice(-499), entry]);
    });

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const formatTime = (iso: string) => {
    try {
      const utc = iso.endsWith("Z") ? iso : iso + "Z";
      return new Date(utc).toLocaleTimeString("tr-TR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="p-6 flex flex-col h-screen max-h-screen space-y-4">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white">Canlı Loglar</h1>
          <p className="text-gray-500 text-sm mt-1">{logs.length} kayıt</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {connected ? (
              <span className="flex items-center gap-1.5 text-green-400 text-xs">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                Canlı
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-red-400 text-xs">
                <WifiOff size={12} />
                Bağlantı yok
              </span>
            )}
          </div>
          <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="accent-brand-500"
            />
            Otomatik kaydır
          </label>
          <button
            onClick={() => setLogs([])}
            className="flex items-center gap-1.5 px-3 py-1.5 text-gray-500 hover:text-red-400 border border-gray-800 hover:border-red-500/30 rounded-lg text-xs transition-colors"
          >
            <Trash2 size={13} /> Temizle
          </button>
        </div>
      </div>

      <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl overflow-y-auto font-mono text-xs">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-700 gap-3">
            <ScrollText size={36} />
            <p>Henüz log yok. Bir kampanya başlatın.</p>
          </div>
        ) : (
          <div className="p-4 space-y-1">
            {logs.map((log, i) => (
              <div key={log.id ?? i} className="flex items-start gap-3 hover:bg-gray-800/30 px-2 py-0.5 rounded">
                <span className="text-gray-600 shrink-0 w-20">
                  {formatTime(log.created_at)}
                </span>
                <span
                  className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${levelBadge[log.level] ?? "bg-gray-700 text-gray-300"
                    }`}
                >
                  {log.level}
                </span>
                {log.campaign_id != null && (
                  <span className="text-gray-600 shrink-0">#{log.campaign_id}</span>
                )}
                <span className={`flex-1 break-all ${levelCls[log.level] ?? "text-gray-300"}`}>
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
