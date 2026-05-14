import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/auth";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Account from "./pages/Account";
import Admin from "./pages/Admin";

function Protected({ children, adminOnly = false }: { children: JSX.Element; adminOnly?: boolean }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-gray-950 text-gray-500 text-sm">Yükleniyor…</div>;
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/account" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/account" element={<Protected><Account /></Protected>} />
          <Route path="/admin" element={<Protected adminOnly><Admin /></Protected>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
