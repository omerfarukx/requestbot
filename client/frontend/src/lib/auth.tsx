import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type User } from "./api";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.auth.me()
      .then((u) => {
        setUser(u);
        localStorage.setItem("user", JSON.stringify(u));
      })
      .catch(() => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const r = await api.auth.login(username, password);
    localStorage.setItem("token", r.access_token);
    localStorage.setItem("user", JSON.stringify(r.user));
    setUser(r.user);
  };

  const register = async (email: string, username: string, password: string) => {
    const r = await api.auth.register(email, username, password);
    localStorage.setItem("token", r.access_token);
    localStorage.setItem("user", JSON.stringify(r.user));
    setUser(r.user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    window.location.href = "/login";
  };

  const refresh = async () => {
    const u = await api.auth.me();
    setUser(u);
    localStorage.setItem("user", JSON.stringify(u));
  };

  return (
    <Ctx.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
