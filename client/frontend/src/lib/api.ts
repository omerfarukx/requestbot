import axios from "axios";

const http = axios.create({ baseURL: "/api" });

// JWT token interceptor — her istekte Authorization header ekle
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 401 -> login sayfasına yönlendir
http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export interface User {
  id: number;
  email: string;
  username: string;
  role: "user" | "admin";
  plan: "free" | "pro" | "agency";
  is_active: boolean;
  license_expires_at: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Campaign {
  id: number;
  name: string;
  target_url: string;
  keyword: string | null;
  search_engine: string;
  session_duration_min: number;
  session_duration_max: number;
  concurrent_workers: number;
  daily_visit_target: number | null;
  pages_per_session_min: number;
  pages_per_session_max: number;
  mode: "http" | "browser";
  status: "idle" | "running" | "stopped";
  total_visits: number;
  successful_visits: number;
  failed_visits: number;
  created_at: string;
  updated_at: string;
}

export interface Proxy {
  id: number;
  host: string;
  port: number;
  username: string | null;
  password: string | null;
  protocol: string;
  status: "unknown" | "active" | "dead" | "cooldown";
  last_checked: string | null;
  created_at: string;
}

export interface RankCheck {
  id: number;
  campaign_id: number;
  keyword: string;
  rank: number | null;
  checked_at: string;
}

export interface LogEntry {
  id: number;
  campaign_id: number | null;
  level: "info" | "warning" | "error";
  message: string;
  created_at: string;
}

export interface Stats {
  total_campaigns: number;
  running_campaigns: number;
  total_visits: number;
  successful_visits: number;
  total_proxies: number;
  active_proxies: number;
}

export type CampaignCreate = Omit<Campaign, "id" | "status" | "total_visits" | "successful_visits" | "failed_visits" | "created_at" | "updated_at">;
export type CampaignUpdate = Partial<CampaignCreate>;

export const api = {
  auth: {
    register: (email: string, username: string, password: string) =>
      http.post<AuthResponse>("/auth/register", { email, username, password }).then((r) => r.data),
    login: (username: string, password: string) =>
      http.post<AuthResponse>("/auth/login", { username, password }).then((r) => r.data),
    me: () => http.get<User>("/auth/me").then((r) => r.data),
  },
  admin: {
    listUsers: () => http.get<User[]>("/auth/admin/users").then((r) => r.data),
    updateUser: (id: number, data: Partial<Pick<User, "plan" | "is_active" | "role"> & { license_expires_at: string | null }>) =>
      http.patch<User>(`/auth/admin/users/${id}`, data).then((r) => r.data),
    extendLicense: (id: number, days: number) =>
      http.post<{ ok: boolean; new_expiry: string }>(`/auth/admin/users/${id}/extend?days=${days}`).then((r) => r.data),
    deleteUser: (id: number) => http.delete(`/auth/admin/users/${id}`),
  },
  campaigns: {
    list: () => http.get<Campaign[]>("/campaigns").then((r) => r.data),
    create: (d: CampaignCreate) => http.post<Campaign>("/campaigns", d).then((r) => r.data),
    update: (id: number, d: CampaignUpdate) => http.put<Campaign>(`/campaigns/${id}`, d).then((r) => r.data),
    delete: (id: number) => http.delete(`/campaigns/${id}`),
    start: (id: number) => http.post(`/campaigns/${id}/start`),
    stop: (id: number) => http.post(`/campaigns/${id}/stop`),
    ranks: (id: number) => http.get<RankCheck[]>(`/campaigns/${id}/ranks`).then((r) => r.data),
  },
  proxies: {
    list: () => http.get<Proxy[]>("/proxies").then((r) => r.data),
    addBulk: (text: string) => http.post("/proxies/bulk", { text }).then((r) => r.data),
    delete: (id: number) => http.delete(`/proxies/${id}`),
    deleteAll: () => http.delete("/proxies/all"),
    webshareRefresh: (api_key?: string) =>
      http.post<{ added: number; total: number }>("/proxies/webshare-refresh", { api_key: api_key ?? "" }).then((r) => r.data),
    testAll: () =>
      http.post<{ tested: number; active: number; dead: number }>("/proxies/test-all").then((r) => r.data),
    usage: () =>
      http.get<{ proxy_id: number; visits: number; estimated_mb: number }[]>("/proxies/usage").then((r) => r.data),
  },
  logs: {
    list: (campaign_id?: number) =>
      http.get<LogEntry[]>("/logs", { params: campaign_id ? { campaign_id } : {} }).then((r) => r.data),
  },
  stats: {
    get: () => http.get<Stats>("/stats").then((r) => r.data),
  },
  analytics: {
    hourly: (hours = 24) =>
      http.get<{ hour: string; total: number; success: number }[]>(`/analytics/hourly`, { params: { hours } }).then((r) => r.data),
    proxies: () =>
      http.get<{ status: string; count: number }[]>("/analytics/proxies").then((r) => r.data),
    referrers: () =>
      http.get<{ status: string; count: number }[]>("/analytics/referrers").then((r) => r.data),
  },
};

export function createLogWebSocket(onMessage: (log: LogEntry) => void): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${window.location.host}/ws/logs`);
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch { }
  };
  return ws;
}
