import { useState } from "react";
import { Link } from "react-router-dom";
import { Globe, KeyRound } from "lucide-react";
import { api } from "../lib/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [resetUrl, setResetUrl] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const r = await api.auth.forgotPassword(email);
      if (r.reset_url) {
        setResetUrl(r.reset_url);
      } else {
        setErr("Bu e-posta adresiyle kayıtlı hesap bulunamadı.");
      }
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Bir hata oluştu, tekrar deneyin.");
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
          <p className="text-gray-500 text-sm mt-1">Şifre Sıfırlama</p>
        </div>

        {resetUrl ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-green-400 text-sm font-medium">
              <KeyRound size={16} />
              Sıfırlama bağlantınız hazır
            </div>
            <p className="text-gray-400 text-sm">
              Aşağıdaki bağlantıya tıklayarak yeni şifrenizi belirleyin.
              Bağlantı <span className="text-white font-semibold">1 saat</span> geçerlidir.
            </p>
            <a
              href={resetUrl}
              className="block text-center px-4 py-3 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm transition-colors"
            >
              Şifremi Sıfırla →
            </a>
            <p className="text-center text-gray-600 text-xs">
              Bu bağlantıyı yalnızca siz kullanabilirsiniz.
            </p>
          </div>
        ) : (
          <form onSubmit={submit} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            {err && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-3 py-2">
                {err}
              </div>
            )}
            <p className="text-gray-400 text-sm">
              Kayıtlı e-posta adresinizi girin. Size bir sıfırlama bağlantısı oluşturacağız.
            </p>
            <div>
              <label className="block text-gray-400 text-xs mb-1.5">E-posta adresi</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg py-2.5 text-sm transition-colors disabled:opacity-50"
            >
              <KeyRound size={15} />
              {loading ? "Kontrol ediliyor…" : "Sıfırlama Bağlantısı Al"}
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
