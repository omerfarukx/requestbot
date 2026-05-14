import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Globe, LogIn } from "lucide-react";
import { useAuth } from "../lib/auth";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      await login(username, password);
      nav("/");
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Giriş başarısız");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Globe className="mx-auto text-brand-500 mb-3" size={42} />
          <h1 className="text-2xl font-bold text-white">
            Request<span className="text-brand-500">Bot</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">SEO Trafik Botu — Giriş</p>
        </div>

        <form onSubmit={submit} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          {err && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-3 py-2">
              {err}
            </div>
          )}

          <div>
            <label className="block text-gray-400 text-xs mb-1.5">Kullanıcı adı veya e-posta</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-gray-400 text-xs mb-1.5">Şifre</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg py-2.5 text-sm transition-colors disabled:opacity-50"
          >
            <LogIn size={16} />
            {loading ? "Giriş yapılıyor…" : "Giriş Yap"}
          </button>

          <p className="text-center text-gray-500 text-xs pt-2">
            Hesabın yok mu?{" "}
            <Link to="/register" className="text-brand-400 hover:text-brand-300">
              Kayıt ol
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
