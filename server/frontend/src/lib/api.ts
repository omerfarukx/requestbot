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

export interface DownloadInfo {
  available: boolean;
  filename?: string;
  size_mb?: number;
  updated_at?: string;
}

export const api = {
  auth: {
    register: (email: string, username: string, password: string) =>
      http.post<AuthResponse>("/auth/register", { email, username, password }).then((r) => r.data),
    login: (username: string, password: string) =>
      http.post<AuthResponse>("/auth/login", { username, password }).then((r) => r.data),
    me: () => http.get<User>("/auth/me").then((r) => r.data),
  },
  license: {
    myDevice: () => http.get<Device | null>("/license/device").then((r) => r.data),
    resetDevice: () => http.post<{ ok: boolean; remaining_credits: number }>("/license/reset-device").then((r) => r.data),
  },
  download: {
    info: () => http.get<DownloadInfo>("/download/info").then((r) => r.data),
    url: () => "/api/download/latest", // browser direct download
  },
  admin: {
    listUsers: () => http.get<User[]>("/admin/users").then((r) => r.data),
    updateUser: (id: number, data: Partial<Pick<User, "plan" | "is_active" | "role" | "reset_credits"> & { license_expires_at: string | null }>) =>
      http.patch<User>(`/admin/users/${id}`, data).then((r) => r.data),
    extendLicense: (id: number, days: number) =>
      http.post<{ ok: boolean; new_expiry: string }>(`/admin/users/${id}/extend?days=${days}`).then((r) => r.data),
    grantReset: (id: number, count = 1) =>
      http.post<{ ok: boolean; reset_credits: number }>(`/admin/users/${id}/grant-reset?count=${count}`).then((r) => r.data),
    deleteUser: (id: number) => http.delete(`/admin/users/${id}`),
  },
};
