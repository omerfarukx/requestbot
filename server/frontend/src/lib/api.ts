import axios from "axios";

const http = axios.create({ baseURL: "/api" });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

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
  reset_credits: number;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface Device {
  id: number;
  machine_id: string;
  hostname: string | null;
  os_info: string | null;
  first_seen: string;
  last_seen: string;
  last_ip: string | null;
}

export interface Order {
  id: number;
  merchant_oid: string;
  product: string;
  amount_tl: number;
  currency: string;
  status: "pending" | "success" | "failed";
  paid_at: string | null;
  created_at: string;
}

export interface ActivityLog {
  id: number;
  event: string;
  ip: string | null;
  detail: string | null;
  created_at: string;
}

export interface UserDetail {
  user: User & { days_left: number | null };
  device: Device | null;
  activity: ActivityLog[];
  orders: Order[];
}

export interface DownloadInfo {
  available: boolean;
  filename?: string;
  size_mb?: number;
  updated_at?: string;
}

export interface AdminOrder {
  id: number;
  merchant_oid: string;
  product: string;
  amount_tl: number;
  status: string;
  user_id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface DeviceResetOrderResult {
  ok: boolean;
  order_id: number;
  merchant_oid: string;
  amount: string;
  bank: string;
  iban: string;
  name: string;
  note: string;
}

export interface SiteStats {
  page_views: { total: number; last_7d: number; last_30d: number; unique_ips_total: number; unique_ips_7d: number };
  events: { registrations_total: number; registrations_7d: number; logins_total: number; logins_7d: number; downloads_total: number; downloads_7d: number; bot_sessions_total: number; bot_sessions_7d: number };
  top_pages: { path: string; count: number }[];
  daily_views: { day: string; count: number }[];
}

export function trackPageView(path: string) {
  fetch("/api/stats/pageview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, referrer: document.referrer || null }),
  }).catch(() => { });
}

export const api = {
  auth: {
    register: (email: string, username: string, password: string) =>
      http.post<AuthResponse>("/auth/register", { email, username, password }).then((r) => r.data),
    login: (username: string, password: string) =>
      http.post<AuthResponse>("/auth/login", { username, password }).then((r) => r.data),
    me: () => http.get<User>("/auth/me").then((r) => r.data),
    forgotPassword: (email: string) =>
      http.post<{ ok: boolean; reset_url: string | null }>("/auth/forgot-password", { email }).then((r) => r.data),
    resetPassword: (token: string, new_password: string) =>
      http.post<{ ok: boolean }>("/auth/reset-password", { token, new_password }).then((r) => r.data),
  },
  license: {
    myDevice: () => http.get<Device | null>("/license/device").then((r) => r.data),
    resetDevice: () => http.post<{ ok: boolean; remaining_credits: number }>("/license/reset-device").then((r) => r.data),
    orderDeviceReset: () => http.post<DeviceResetOrderResult>("/license/order/device-reset").then((r) => r.data),
  },
  download: {
    info: () => http.get<DownloadInfo>("/download/info").then((r) => r.data),
    url: () => "/api/download/latest", // browser direct download
  },
  admin: {
    siteStats: () => http.get<SiteStats>("/admin/site-stats").then((r) => r.data),
    listUsers: () => http.get<User[]>("/admin/users").then((r) => r.data),
    updateUser: (id: number, data: Partial<Pick<User, "plan" | "is_active" | "role" | "reset_credits"> & { license_expires_at: string | null }>) =>
      http.patch<User>(`/admin/users/${id}`, data).then((r) => r.data),
    extendLicense: (id: number, days: number) =>
      http.post<{ ok: boolean; new_expiry: string }>(`/admin/users/${id}/extend?days=${days}`).then((r) => r.data),
    grantReset: (id: number, count = 1) =>
      http.post<{ ok: boolean; reset_credits: number }>(`/admin/users/${id}/grant-reset?count=${count}`).then((r) => r.data),
    deleteUser: (id: number) => http.delete(`/admin/users/${id}`),
    userDetail: (id: number) => http.get<UserDetail>(`/admin/users/${id}/detail`).then((r) => r.data),
    listOrders: (status = "pending") =>
      http.get<AdminOrder[]>(`/admin/orders?status=${status}`).then((r) => r.data),
  },
  payment: {
    start: (product: string) =>
      http.post<{ ok: boolean; token: string; merchant_oid: string }>("/payment/start", { product }).then((r) => r.data),
    products: () =>
      http.get<{ id: string; name: string; amount: number; amount_tl: number; plan: string | null; days: number }[]>("/payment/products").then((r) => r.data),
  },
};
