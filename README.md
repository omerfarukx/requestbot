# Request Hit Bot

SEO trafik simülasyonu için web panel + bot motoru.

## Kurulum

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Frontend (Node.js)
```bash
cd frontend
npm install
npm run dev
```

Panel: http://localhost:3000
API:   http://localhost:8000

## Özellikler
- Çoklu kampanya yönetimi
- Proxy rotasyonu (HTTP / SOCKS5)
- User-Agent rotasyonu
- Organik referrer simülasyonu (Google / Yandex / Bing)
- Oturum simülasyonu: 5-15 dakika, çok sayfa gezme
- WebSocket ile canlı log akışı
- Eşzamanlı işçi kontrolü

## Proxy Formatları
- `host:port`
- `host:port:kullanici:sifre`
- `kullanici:sifre@host:port`
- `http://host:port`
- `socks5://kullanici:sifre@host:port`
