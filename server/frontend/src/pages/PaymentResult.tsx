import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { CheckCircle, XCircle } from "lucide-react";

/**
 * PayTR iFrame içinde yüklenen sonuç sayfası.
 * PayTR, ödeme tamamlanınca merchant_ok_url / merchant_fail_url'e yönlendirir.
 */
export default function PaymentResult() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const status = params.get("status") ?? "failed";
  const success = status === "success";

  useEffect(() => {
    const t = setTimeout(() => navigate("/account", { replace: true }), 3000);
    return () => clearTimeout(t);
  }, [navigate]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0b0f1a",
        fontFamily: "system-ui, sans-serif",
        color: "#f1f5f9",
        padding: "2rem",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: 360 }}>
        {success ? (
          <>
            <CheckCircle size={64} color="#10b981" style={{ marginBottom: 16 }} />
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
              Ödeme Başarılı!
            </h2>
            <p style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6 }}>
              Planınız güncellendi. Hesabınıza yansıması birkaç saniye alabilir.
            </p>
          </>
        ) : (
          <>
            <XCircle size={64} color="#f87171" style={{ marginBottom: 16 }} />
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
              Ödeme Başarısız
            </h2>
            <p style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6 }}>
              İşlem tamamlanamadı. Kart bilgilerinizi kontrol ederek tekrar deneyin.
            </p>
          </>
        )}
        <button
          onClick={() => navigate("/account", { replace: true })}
          style={{ marginTop: 24, padding: "8px 20px", borderRadius: 8, border: "none", background: success ? "#10b981" : "#ef4444", color: "#fff", fontWeight: 600, fontSize: 13, cursor: "pointer" }}
        >
          {success ? "Hesabımı Aç" : "Hesabıma Dön"}
        </button>
        <p style={{ color: "#475569", fontSize: 11, marginTop: 12 }}>Otomatik yönlendiriliyorsunuz…</p>
      </div>
    </div>
  );
}
