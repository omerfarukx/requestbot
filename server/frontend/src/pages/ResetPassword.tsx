import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Globe, Lock, CheckCircle } from "lucide-react";
import { api } from "../lib/api";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const nav = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    if (password.length < 6) { setErr("Şifre en az 6 karakter olmalı."); return; }
    if (password !== confirm) { setErr("Şifreler eşleşmiyor."); return; }
    setLoading(true);
    try {
      await api.auth.resetPassword(token, password);
      setDone(true);
      setTimeout(() => nav("/login"), 2500);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Geçersiz veya süresi dolmuş bağlantı.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4 text-center">
        <div>
          <p className="text-red-400 text-sm mb-4">Geçersiz sıfırlama bağlantısı.</p>
          <Link to="/forgot-password" className="text-brand-400 hover:text-brand-300 text-sm">
            Yeni bağlantı talep et →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Globe className="mx-auto text-brand-500 mb-3" size={42} />
          <h1 className="text-2xl font-bold text-white">
            Request<span className="text-brand-500">Bot</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">Yeni Şifre Belirle</p>
        </div>

        {done ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center space-y-3">
            <CheckCircle className="mx-auto text-green-400" size={40} />
            <p className="text-white font-semibold">Şifreniz güncellendi!</p>
            <p className="text-gray-500 text-sm">Giriş sayfasına yönlendiriliyorsunuz…</p>
          </div>
        ) : (
          <form onSubmit={submit} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            {err && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-3 py-2">
                {err}
              </div>
            )}
            <div>
              <label className="block text-gray-400 text-xs mb-1.5">Yeni şifre</label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label className="block text-gray-400 text-xs mb-1.5">Şifre tekrar</label>
              <input
                type="password"
                required
                minLength={6}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg py-2.5 text-sm transition-colors disabled:opacity-50"
            >
              <Lock size={15} />
              {loading ? "Kaydediliyor…" : "Şifremi Güncelle"}
            </button>
            <p className="text-center text-gray-500 text-xs pt-1">
              <Link to="/login" className="text-brand-400 hover:text-brand-300">
                ← Giriş sayfasına dön
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
