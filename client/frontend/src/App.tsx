import { BrowserRouter, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import {
  BarChart2,
  Crown,
  Globe,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Shield,
} from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Campaigns from "./pages/Campaigns";
import Proxies from "./pages/Proxies";
import Logs from "./pages/Logs";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Admin from "./pages/Admin";
import { AuthProvider, useAuth } from "./lib/auth";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/campaigns", icon: BarChart2, label: "Kampanyalar" },
  { to: "/proxies", icon: Shield, label: "Proxiler" },
  { to: "/logs", icon: ScrollText, label: "Canlı Loglar" },
];

const PLAN_BADGE: Record<string, string> = {
  free: "bg-gray-700 text-gray-300",
  pro: "bg-blue-500/30 text-blue-300",
  agency: "bg-purple-500/30 text-purple-300",
};

function Sidebar() {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";

  const fmtExpiry = (d: string | null) => {
    if (!d) return "—";
    const dt = new Date(d);
    const now = new Date();
    const diff = Math.floor((dt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diff < 0) return "Süresi dolmuş";
    if (diff === 0) return "Bugün biter";
    return `${diff} gün`;
  };

  return (
    <aside className="w-56 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="px-5 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Globe className="text-brand-500" size={22} />
          <span className="font-bold text-white tracking-wide text-sm">
            Request<span className="text-brand-500">Bot</span>
          </span>
        </div>
        <p className="text-gray-500 text-xs mt-1">SEO Trafik Botu</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive
                ? "bg-brand-500/10 text-brand-400 font-medium"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive
                ? "bg-yellow-500/10 text-yellow-400 font-medium"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`
            }
          >
            <Crown size={16} /> Admin
          </NavLink>
        )}
      </nav>

      {user && (
        <div className="px-4 py-4 border-t border-gray-800 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium truncate">{user.username}</div>
              <div className="text-gray-500 text-xs truncate">{user.email}</div>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className={`px-2 py-0.5 rounded-md font-medium capitalize ${PLAN_BADGE[user.plan]}`}>
              {user.plan}
            </span>
            <span className="text-gray-500" title={user.license_expires_at || ""}>
              {fmtExpiry(user.license_expires_at)}
            </span>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 mt-2 text-xs text-gray-500 hover:text-red-400 py-1.5 border border-gray-800 hover:border-red-500/30 rounded-md transition-colors"
          >
            <LogOut size={12} /> Çıkış
          </button>
        </div>
      )}
    </aside>
  );
}

function Protected({ children, adminOnly = false }: { children: JSX.Element; adminOnly?: boolean }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500 text-sm">Yükleniyor…</div>;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto bg-gray-950">{children}</main>
    </div>
  );
}

function SsoRedirect() {
  const navigate = useNavigate();
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get("t");
    if (t) {
      localStorage.setItem("token", t);
      localStorage.removeItem("user");
      window.location.replace("/");
    } else {
      navigate("/", { replace: true });
    }
  }, [navigate]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="text-center space-y-2">
        <div className="text-brand-500 text-xl font-bold">RequestBot</div>
        <div className="text-gray-400 text-sm">Giriş yapılıyor…</div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Protected><AppShell><Dashboard /></AppShell></Protected>} />
          <Route path="/campaigns" element={<Protected><AppShell><Campaigns /></AppShell></Protected>} />
          <Route path="/proxies" element={<Protected><AppShell><Proxies /></AppShell></Protected>} />
          <Route path="/logs" element={<Protected><AppShell><Logs /></AppShell></Protected>} />
          <Route path="/admin" element={<Protected adminOnly><AppShell><Admin /></AppShell></Protected>} />
          <Route path="/sso" element={<SsoRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
