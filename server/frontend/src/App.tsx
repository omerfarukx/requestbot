import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { AuthProvider, useAuth } from "./lib/auth";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Account from "./pages/Account";
import Admin from "./pages/Admin";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import PaymentResult from "./pages/PaymentResult";

function NoIndex() {
  useEffect(() => {
    let tag = document.querySelector<HTMLMetaElement>("meta[name='robots'][data-dynamic]");
    if (!tag) {
      tag = document.createElement("meta");
      tag.name = "robots";
      tag.setAttribute("data-dynamic", "true");
      document.head.appendChild(tag);
    }
    tag.content = "noindex, nofollow";
    return () => { tag?.remove(); };
  }, []);
  return null;
}

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
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/payment/result" element={<PaymentResult />} />
          <Route path="/account" element={<Protected><><NoIndex /><Account /></></Protected>} />
          <Route path="/admin" element={<Protected adminOnly><><NoIndex /><Admin /></></Protected>} />
          <Route path="*" element={
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 text-white gap-4">
              <span className="text-6xl font-black text-gray-700">404</span>
              <p className="text-gray-500">Sayfa bulunamadı</p>
              <a href="/" className="text-brand-400 hover:text-brand-300 text-sm">← Ana sayfaya dön</a>
            </div>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
