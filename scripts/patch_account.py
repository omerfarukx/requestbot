"""Account.tsx'te <a href> download'ı fetch+blob download'a çevirir."""
import re

path = "/opt/requestbot/server/frontend/src/pages/Account.tsx"
with open(path, "r", encoding="utf-8") as f:
    src = f.read()

# handleDownload fonksiyonu ekle (load fonksiyonundan önce)
handle_fn = """
  const handleDownload = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/download/latest", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        showToast("İndirme başarısız: " + res.status, false);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = download?.filename ?? "RequestBot.exe";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      showToast("İndirme hatası", false);
    }
  };

"""

# load fonksiyonundan önce ekle
src = src.replace("  const load = async () => {", handle_fn + "  const load = async () => {")

# <a href> download butonunu <button> ile değiştir
old_a = '''                <a
                  href={api.download.url()}
                  className="block w-full text-center px-4 py-3 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm transition-colors"
                  download
                >
                  <Download size={14} className="inline mr-1" /> {download.filename}
                </a>'''

new_btn = '''                <button
                  onClick={handleDownload}
                  className="block w-full text-center px-4 py-3 bg-brand-500 hover:bg-brand-600 text-black font-semibold rounded-lg text-sm transition-colors"
                >
                  <Download size={14} className="inline mr-1" /> {download.filename}
                </button>'''

if old_a in src:
    src = src.replace(old_a, new_btn)
    print("✓ <a> → <button> değiştirildi")
else:
    print("❌ <a> bulunamadı, manuel kontrol gerekli")

with open(path, "w", encoding="utf-8") as f:
    f.write(src)

print("Dosya yazıldı.")
