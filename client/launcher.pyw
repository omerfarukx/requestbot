import customtkinter as ctk
import tkinter as tk
import subprocess
import threading
import webbrowser
import winreg
import sys
import os
import time
import atexit
import ctypes
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import pystray

# License client (sunucudan auth + lisans)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import license_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
APP_NAME = "RequestHitBot"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# ========== SINGLE INSTANCE LOCK ==========
_MUTEX_NAME = "Global\\RequestHitBot_Client_SingleInstance"

def _check_single_instance():
    """Windows named mutex — PID yerine daha guvenli."""
    kernel = ctypes.windll.kernel32
    mutex = kernel.CreateMutexW(None, False, _MUTEX_NAME)
    err = kernel.GetLastError()
    if err == 183:  # ERROR_ALREADY_EXISTS
        # Zaten calisiyor — mevcut pencereyi one cikarmaya calis
        try:
            import tkinter.messagebox as mb
            mb.showinfo(
                "RequestHitBot Zaten Çalışıyor",
                "RequestHitBot zaten arka planda çalışıyor.\n\n"
                "Sistem tepsisinden (sağ alt köşe) sağ tıklayarak açabilirsiniz.\n"
                "Veya Görev Yöneticisi'nden Python process'lerini sonlandırıp tekrar deneyin."
            )
        except Exception:
            pass
        sys.exit(0)
    # Mutex handle'ını program boyunca tut (kapaninca otomatik silinir)
    atexit.register(lambda: kernel.CloseHandle(mutex))

_check_single_instance()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

_ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logo.ico")

COLORS = {
    "bg":       "#0b0f1a",
    "surface":  "#111827",
    "surface2": "#1c2333",
    "border":   "#1f2d47",
    "primary":  "#6366f1",
    "primary_h":"#4f46e5",
    "success":  "#10b981",
    "danger":   "#f87171",
    "danger_bg":"#1c0a0a",
    "danger_br":"#7f1d1d",
    "text":     "#f1f5f9",
    "muted":    "#64748b",
    "muted2":   "#94a3b8",
}


def is_port_open(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{port}/api/stats", timeout=2)
        return True
    except urllib.error.HTTPError:
        # 401/403 dahil — server cevap veriyorsa ayakta sayilir
        return True
    except Exception:
        return False


def create_logo_image(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size // 5
    # Rounded square — koyu indigo
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=(79, 70, 229, 255))
    # Subtle top highlight
    d.rounded_rectangle([0, 0, size - 1, size // 2], radius=r, fill=(120, 100, 255, 55))
    # "R" harfi
    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    fnt = None
    for fp in font_paths:
        try:
            fnt = ImageFont.truetype(fp, int(size * 0.55))
            break
        except Exception:
            pass
    if fnt is None:
        fnt = ImageFont.load_default()
    bbox = d.textbbox((0, 0), "R", font=fnt)
    tx = (size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty = (size - (bbox[3] - bbox[1])) // 2 - bbox[1]
    d.text((tx, ty), "R", font=fnt, fill=(255, 255, 255, 245))
    return img


def create_tray_icon_image():
    return create_logo_image(64)


class App(ctk.CTk):
    def __init__(self, auth_token: str = None, auth_user: dict = None):
        super().__init__()

        self.backend_proc = None
        self.frontend_proc = None
        self.tray_icon = None
        self._closing = False
        self._pulse_phase = 0
        self._auth_token = auth_token
        self._auth_user = auth_user
        self._browser_opened = False

        self.title("RequestBot")
        self.geometry("460x570")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close_button)
        if os.path.exists(_ICON_PATH):
            self.after(100, lambda: self.iconbitmap(_ICON_PATH))

        # Logo
        self.logo_img = ctk.CTkImage(light_image=create_logo_image(), dark_image=create_logo_image(), size=(52, 52))

        self._build_ui()
        self._start_tray()
        self._poll_status()
        self._pulse_animation()

        # Login sonrasi otomatik baslatma
        if self._auth_token:
            self.after(800, self._auto_start)

    def _build_ui(self):
        # ── HEADER ─────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0)
        hdr.pack(fill="x")
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(hdr_inner, image=self.logo_img, text="").pack(side="left", padx=(0, 12))

        name_col = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        name_col.pack(side="left", fill="y", expand=True)
        ctk.CTkLabel(
            name_col, text="RequestBot",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_col, text="SEO Trafik & Sıralama Botu",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=COLORS["muted2"],
        ).pack(anchor="w")

        # Sağ taraf: plan badge + çıkış butonu
        right = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        right.pack(side="right")

        if self._auth_user:
            plan = self._auth_user.get("plan", "free")
            plan_cfg = {
                "free":   ("#1f2937", "#6b7280"),
                "pro":    ("#1e3a5f", "#60a5fa"),
                "agency": ("#2d1b69", "#a78bfa"),
            }.get(plan, ("#1f2937", "#6b7280"))
            bf = ctk.CTkFrame(right, fg_color=plan_cfg[0], corner_radius=6)
            bf.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                bf, text=plan.upper(),
                font=ctk.CTkFont("Segoe UI", 9, "bold"),
                text_color=plan_cfg[1], padx=8, pady=4,
            ).pack()

        ctk.CTkButton(
            right, text="⏻",
            fg_color="transparent", hover_color=COLORS["surface2"],
            text_color=COLORS["muted"], width=32, height=32,
            corner_radius=8, font=ctk.CTkFont("Segoe UI", 14),
            command=self._logout,
        ).pack(side="left")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1, corner_radius=0).pack(fill="x")

        # ── BODY ────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        # Status card
        sc = ctk.CTkFrame(body, fg_color=COLORS["surface"], corner_radius=12,
                          border_width=1, border_color=COLORS["border"])
        sc.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(sc, text="SERVİS DURUMU",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=COLORS["muted"]).pack(anchor="w", padx=14, pady=(10, 6))

        brow = ctk.CTkFrame(sc, fg_color="transparent")
        brow.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(brow, text="API Backend",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=COLORS["text"]).pack(side="left")
        self.backend_status = ctk.CTkLabel(
            brow, text="● Kapalı",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=COLORS["danger"],
        )
        self.backend_status.pack(side="right")

        frow = ctk.CTkFrame(sc, fg_color="transparent")
        frow.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(frow, text="Web Arayüzü",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=COLORS["text"]).pack(side="left")
        self.frontend_status = ctk.CTkLabel(
            frow, text="● Kapalı",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=COLORS["danger"],
        )
        self.frontend_status.pack(side="right")

        # Primary start button
        self.start_btn = ctk.CTkButton(
            body, text="▶   Sistemi Başlat",
            fg_color=COLORS["primary"], hover_color=COLORS["primary_h"],
            text_color="white", height=46,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            corner_radius=10,
            command=self._start_services,
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        # Secondary buttons
        sec = ctk.CTkFrame(body, fg_color="transparent")
        sec.pack(fill="x", pady=(0, 10))
        sec.grid_columnconfigure(0, weight=3)
        sec.grid_columnconfigure(1, weight=2)
        ctk.CTkButton(
            sec, text="⬡  Paneli Aç",
            fg_color=COLORS["surface2"], hover_color=COLORS["border"],
            text_color=COLORS["muted2"], height=38,
            font=ctk.CTkFont("Segoe UI", 12),
            corner_radius=10, border_width=1, border_color=COLORS["border"],
            command=lambda: self._do_sso_and_open(force=True),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        self.stop_btn = ctk.CTkButton(
            sec, text="■  Durdur",
            fg_color=COLORS["danger_bg"], hover_color="#2d0a0a",
            text_color=COLORS["danger"], height=38,
            font=ctk.CTkFont("Segoe UI", 12),
            corner_radius=10, border_width=1, border_color=COLORS["danger_br"],
            command=self._stop_services, state="disabled",
        )
        self.stop_btn.grid(row=0, column=1, sticky="ew")

        # Settings row
        scard = ctk.CTkFrame(body, fg_color=COLORS["surface"], corner_radius=10,
                             border_width=1, border_color=COLORS["border"])
        scard.pack(fill="x", pady=(0, 10))
        srow = ctk.CTkFrame(scard, fg_color="transparent")
        srow.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(srow, text="Windows ile başlat",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=COLORS["text"]).pack(side="left")
        self.startup_var = ctk.BooleanVar(value=self._is_startup_enabled())
        ctk.CTkSwitch(srow, text="", variable=self.startup_var,
                      command=self._toggle_startup,
                      progress_color=COLORS["primary"],
                      button_color="#ffffff").pack(side="right")

        # Logs
        log_outer = ctk.CTkFrame(body, fg_color=COLORS["surface"], corner_radius=10,
                                  border_width=1, border_color=COLORS["border"])
        log_outer.pack(fill="both", expand=True)
        ctk.CTkLabel(log_outer, text="LOGLAR",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=COLORS["muted"]).pack(anchor="w", padx=14, pady=(10, 4))
        self.log_box = ctk.CTkTextbox(
            log_outer, fg_color=COLORS["bg"],
            text_color=COLORS["muted2"],
            font=ctk.CTkFont("Consolas", 10),
            corner_radius=8, border_width=0,
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_box.configure(state="disabled")

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _pulse_animation(self):
        pass  # Removed — no pulse canvas in new design

    def _auto_start(self):
        """Login sonrasi otomatik baslatma."""
        if is_port_open(8000) and is_port_open(3000):
            self._log("✅ Servisler zaten çalışıyor — panel açılıyor…")
            self._do_sso_and_open()
        elif not self.backend_proc and not self.frontend_proc:
            self._log("🔄 Otomatik başlatılıyor…")
            self._start_services()

    def _do_sso_and_open(self, force: bool = False):
        """SSO token al, tarayiciyi ac."""
        if not force and self._browser_opened:
            return
        self._browser_opened = True
        threading.Thread(target=self._sso_open_thread, daemon=True).start()

    def _sso_open_thread(self):
        """SSO endpoint'ini cagir, local JWT al, tarayiciyi ac."""
        import json as _json
        if not self._auth_token or not self._auth_user:
            webbrowser.open("http://localhost:3000")
            return
        url = "http://localhost:8000/api/auth/sso"
        body = _json.dumps({
            "license_token": self._auth_token,
            "user": self._auth_user,
        }).encode()
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    url, data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    data = _json.loads(r.read())
                    local_token = data.get("access_token", "")
                    if local_token:
                        webbrowser.open(
                            f"http://localhost:3000/sso?t={urllib.parse.quote(local_token)}"
                        )
                        return
            except Exception as e:
                try:
                    if self.winfo_exists():
                        self.after(0, lambda a=attempt + 1, err=e: self._log(f"[SSO] Deneme {a}: {err}"))
                except Exception:
                    pass
                if attempt < 4:
                    time.sleep(1)
        webbrowser.open("http://localhost:3000")

    def _start_services(self):
        self.start_btn.configure(state="disabled", text="Başlatılıyor…")
        self._log("Backend başlatılıyor…")
        threading.Thread(target=self._launch_backend, daemon=True).start()

    def _launch_backend(self):
        try:
            # Onceki ölü processleri temizle
            for port, svc in [(8000, "backend"), (3000, "frontend")]:
                if is_port_open(port):
                    self.after(0, lambda s=svc: self._log(f"⚠️ {s} portu meşgul, temizleniyor…"))
                    subprocess.run(
                        f"for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{port}') do taskkill /F /PID %a",
                        shell=True, capture_output=True,
                    )
                    time.sleep(1)

            # python.exe kullan (pythonw degil) — uvicorn stdout istiyor
            exe = sys.executable.replace("pythonw.exe", "python.exe")
            log_file = open(os.path.join(BASE_DIR, "backend.log"), "w", encoding="utf-8")
            self.backend_proc = subprocess.Popen(
                [exe, "-m", "uvicorn", "main:app", "--port", "8000"],
                cwd=BACKEND_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=log_file, stderr=subprocess.STDOUT,
            )
            # Backend portu acilana kadar bekle (max 15sn)
            for i in range(15):
                time.sleep(1)
                if is_port_open(8000):
                    break
                if self.backend_proc.poll() is not None:
                    # Cokmus — log dosyasinin son satirini oku
                    log_file.close()
                    try:
                        with open(os.path.join(BASE_DIR, "backend.log"), encoding="utf-8") as f:
                            tail = f.read()[-300:]
                    except Exception:
                        tail = "?"
                    self.after(0, lambda: self._log(f"❌ Backend çöktü: {tail.strip()}"))
                    self.after(0, lambda: self.start_btn.configure(state="normal", text="▶   Sistemi Başlat"))
                    return
            self.after(0, lambda: self._log("Frontend başlatılıyor…"))
            frontend_log = open(os.path.join(BASE_DIR, "frontend.log"), "w", encoding="utf-8")
            self.frontend_proc = subprocess.Popen(
                ["npm.cmd", "run", "dev"],
                cwd=FRONTEND_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=frontend_log, stderr=subprocess.STDOUT,
                shell=True,
            )
            # Frontend portu acilana kadar bekle (max 30sn)
            for i in range(30):
                time.sleep(1)
                if is_port_open(3000):
                    break
            self.after(0, self._check_and_update_status)
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ Başlatma hatası: {e}"))
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶   Sistemi Başlat"))

    def _check_and_update_status(self):
        backend_up = is_port_open(8000)
        frontend_up = is_port_open(3000)
        self._update_status(backend_up, frontend_up)
        if backend_up and frontend_up:
            self.start_btn.configure(state="disabled", text="▶   Sistemi Başlat")
            self.stop_btn.configure(state="normal", text="■  Durdur")
            self._log("✅ Sistem hazır — http://localhost:3000")
            self._do_sso_and_open()
        elif not backend_up:
            self._log("❌ Backend yanıt vermiyor")
            self.start_btn.configure(state="normal", text="▶   Sistemi Başlat")
        else:
            self._log("⚠️ Frontend yanıt vermiyor")

    def _kill_tree(self, proc):
        """Tum alt process'leri dahil ederek oldurmek icin taskkill kullan."""
        if proc is None:
            return
        try:
            pid = proc.pid
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
            )
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _stop_services(self):
        self._log("Servisler durduruluyor…")
        self.stop_btn.configure(state="disabled", text="Durduruluyor…")
        threading.Thread(target=self._do_stop, daemon=True).start()

    def _do_stop(self):
        self._kill_tree(self.frontend_proc)
        self._kill_tree(self.backend_proc)
        self.backend_proc = None
        self.frontend_proc = None
        self._browser_opened = False
        # Port tamamen kapanana kadar bekle (max 5sn)
        for _ in range(10):
            time.sleep(0.5)
            if not is_port_open(8000) and not is_port_open(3000):
                break
        self.after(0, lambda: self.start_btn.configure(state="normal", text="▶   Sistemi Başlat"))
        self.after(0, lambda: self.stop_btn.configure(state="disabled", text="■  Durdur"))
        self.after(0, lambda: self._update_status(False, False))
        self.after(0, lambda: self._log("✅ Sistem durduruldu"))

    def _poll_status(self):
        def check():
            backend_up = is_port_open(8000)
            frontend_up = is_port_open(3000)
            self.after(0, lambda: self._update_status(backend_up, frontend_up))

            # Proc yoksa ama port aciksa -> yabanci process, butonu duzelt
            def sync_buttons():
                we_own = self.backend_proc is not None or self.frontend_proc is not None
                if not we_own:
                    self.start_btn.configure(state="normal", text="▶   Sistemi Başlat")
                    self.stop_btn.configure(state="disabled")

            self.after(0, sync_buttons)
            if not self._closing:
                self.after(6000, self._poll_status)
        threading.Thread(target=check, daemon=True).start()

    def _update_status(self, backend_up: bool, frontend_up: bool):
        if backend_up:
            self.backend_status.configure(text="● Çalışıyor", text_color=COLORS["success"])
        else:
            self.backend_status.configure(text="● Kapalı", text_color=COLORS["danger"])
        if frontend_up:
            self.frontend_status.configure(text="● Çalışıyor", text_color=COLORS["success"])
        else:
            self.frontend_status.configure(text="● Kapalı", text_color=COLORS["danger"])

    def _is_startup_enabled(self) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _toggle_startup(self):
        exe = sys.executable.replace("python.exe", "pythonw.exe")
        script = os.path.abspath(__file__)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
            if self.startup_var.get():
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe}" "{script}"')
                self._log("Windows başlangıcına eklendi")
            else:
                winreg.DeleteValue(key, APP_NAME)
                self._log("Windows başlangıcından kaldırıldı")
            winreg.CloseKey(key)
        except Exception as e:
            self._log(f"Hata: {e}")

    def _logout(self):
        import tkinter.messagebox as mb
        if not mb.askyesno("Çıkış", "Oturumu kapat ve uygulamadan çık?"):
            return
        self._closing = True
        self._stop_services()
        license_client.clear_session()
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        self.after(500, lambda: os._exit(0))

    def _start_tray(self):
        def on_open(_icon, _item):
            self.after(0, self._restore_window)

        def on_quit(_icon, _item):
            self._closing = True
            self._stop_services()
            # Pystray icon'u once durdur, sonra pencereyi yok et
            try:
                _icon.stop()
            except Exception:
                pass
            self.after(100, self.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("Aç / Göster", on_open, default=True),
            pystray.MenuItem("Paneli Aç", lambda i, it: webbrowser.open("http://localhost:3000")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Çıkış", on_quit),
        )
        self.tray_icon = pystray.Icon(APP_NAME, create_tray_icon_image(), APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _restore_window(self):
        """Pencereyi gizliden geri getir — en onde ve odakli."""
        self.deiconify()
        self.update_idletasks()
        self.lift()
        self.attributes('-topmost', True)
        self.after(300, lambda: self.attributes('-topmost', False))
        self.focus_force()

    def _on_close_button(self):
        self.withdraw()
        self._log("Tepside calismaya devam ediyor - sag tikla acabilirsin")

    def destroy(self):
        self._closing = True
        try:
            super().destroy()
        except Exception:
            pass


# ========== LOGIN WINDOW ==========


class LoginWindow(ctk.CTk):
    """Login + register dialog. Returns (token, user) via self.result."""

    def __init__(self):
        super().__init__()
        self.result = None  # (token, user) | None

        self.title("RequestBot — Giriş")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        if os.path.exists(_ICON_PATH):
            self.after(100, lambda: self.iconbitmap(_ICON_PATH))

        # Logo
        try:
            logo_img = ctk.CTkImage(light_image=create_logo_image(), dark_image=create_logo_image(), size=(64, 64))
            ctk.CTkLabel(self, image=logo_img, text="").pack(pady=(30, 8))
        except Exception:
            pass

        ctk.CTkLabel(self, text="RequestBot",
                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                     text_color="#fff").pack()
        self.subtitle = ctk.CTkLabel(self, text="Hesabınıza giriş yapın",
                                     font=ctk.CTkFont(size=11), text_color=COLORS["muted2"])
        self.subtitle.pack(pady=(2, 18))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(padx=30, fill="x")

        self.email_entry = ctk.CTkEntry(form, placeholder_text="E-posta (sadece kayıt için)",
                                        height=38, fg_color=COLORS["surface"],
                                        border_color=COLORS["border"])
        self.username_entry = ctk.CTkEntry(form, placeholder_text="Kullanıcı adı veya e-posta",
                                           height=38, fg_color=COLORS["surface"],
                                           border_color=COLORS["border"])
        self.username_entry.pack(fill="x", pady=4)
        self.password_entry = ctk.CTkEntry(form, placeholder_text="Şifre", show="•",
                                           height=38, fg_color=COLORS["surface"],
                                           border_color=COLORS["border"])
        self.password_entry.pack(fill="x", pady=4)

        # Submit
        self.submit_btn = ctk.CTkButton(form, text="Giriş Yap", height=40,
                                        fg_color=COLORS["primary"], hover_color=COLORS["primary_h"],
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        command=self._submit)
        self.submit_btn.pack(fill="x", pady=(10, 4))

        # Mode toggle
        self.mode = "login"
        self.toggle_btn = ctk.CTkButton(form, text="Hesabın yok mu? Kayıt ol", height=28,
                                        fg_color="transparent", text_color=COLORS["muted2"],
                                        hover_color=COLORS["surface"],
                                        command=self._toggle_mode)
        self.toggle_btn.pack(fill="x", pady=(6, 0))

        # Status
        self.status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                   text_color=COLORS["danger"], wraplength=360)
        self.status.pack(pady=10)

        # Server info
        ctk.CTkLabel(self, text=f"Sunucu: {license_client.server_url()}",
                     font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(side="bottom", pady=8)

        self.bind("<Return>", lambda e: self._submit())
        self.username_entry.focus()

    def _toggle_mode(self):
        if self.mode == "login":
            self.mode = "register"
            self.subtitle.configure(text="Yeni hesap oluştur")
            self.email_entry.pack(fill="x", pady=4, before=self.username_entry)
            self.submit_btn.configure(text="Kayıt Ol")
            self.toggle_btn.configure(text="Zaten hesabın var? Giriş yap")
        else:
            self.mode = "login"
            self.subtitle.configure(text="Hesabınıza giriş yapın")
            self.email_entry.pack_forget()
            self.submit_btn.configure(text="Giriş Yap")
            self.toggle_btn.configure(text="Hesabın yok mu? Kayıt ol")

    def _safe_after(self, ms, fn):
        """after çağrısı — window destroyed ise sessiz."""
        try:
            if self.winfo_exists():
                self.after(ms, fn)
        except Exception:
            pass

    def _submit(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.status.configure(text="Tüm alanları doldurun")
            return

        self.submit_btn.configure(state="disabled", text="Bekleyin…")
        self.status.configure(text="")
        threading.Thread(target=self._do_auth, args=(username, password), daemon=True).start()

    def _do_auth(self, username, password):
        try:
            if self.mode == "register":
                email = self.email_entry.get().strip()
                if not email:
                    self._safe_after(0, lambda: self.status.configure(text="E-posta gerekli"))
                    self._safe_after(0, lambda: self.submit_btn.configure(state="normal", text="Kayıt Ol"))
                    return
                r = license_client.register(email, username, password)
            else:
                r = license_client.login(username, password)

            token = r["access_token"]
            user = r["user"]

            # Lisans + cihaz dogrulama
            self._safe_after(0, lambda: self.submit_btn.configure(text="Lisans kontrol ediliyor…"))
            v = license_client.validate(token)
            if not v.get("valid"):
                reason = v.get("reason", "Lisans gecersiz")
                self._safe_after(0, lambda: self.status.configure(text=f"❌ {reason}"))
                self._safe_after(0, lambda: self.submit_btn.configure(state="normal",
                                                                text="Giriş Yap" if self.mode == "login" else "Kayıt Ol"))
                return

            # Basari — session kaydet
            license_client.save_session(token, user)
            self.result = (token, user)
            self._safe_after(0, self.destroy)

        except license_client.LicenseError as e:
            self._safe_after(0, lambda: self.status.configure(text=f"❌ {e}"))
            self._safe_after(0, lambda: self.submit_btn.configure(state="normal",
                                                            text="Giriş Yap" if self.mode == "login" else "Kayıt Ol"))
        except Exception as e:
            self._safe_after(0, lambda: self.status.configure(text=f"❌ Beklenmedik hata: {e}"))
            self._safe_after(0, lambda: self.submit_btn.configure(state="normal",
                                                            text="Giriş Yap" if self.mode == "login" else "Kayıt Ol"))

    def _cancel(self):
        self.result = None
        self.destroy()


def authenticate() -> Optional[tuple]:
    """
    Login flow:
    1. Cached session var ise validate dene → OK ise direkt geç
    2. Yoksa veya geçersizse login penceresi göster
    """
    cached = license_client.load_session()
    if cached:
        try:
            v = license_client.validate(cached["token"])
            if v.get("valid"):
                print(f"[Auth] Cached session valid: {cached['user']['username']}")
                if v.get("plan"):
                    cached["user"]["plan"] = v["plan"]
                if v.get("expires_at"):
                    cached["user"]["license_expires_at"] = v["expires_at"]
                license_client.save_session(cached["token"], cached["user"])
                return (cached["token"], cached["user"])
            else:
                print(f"[Auth] Cached session reddedildi: {v.get('reason')}")
        except Exception as e:
            print(f"[Auth] Cached validate hatasi: {e}")
        license_client.clear_session()

    # Login penceresi
    win = LoginWindow()
    win.mainloop()
    return win.result


if __name__ == "__main__":
    auth = authenticate()
    if not auth:
        sys.exit(0)

    token, user = auth
    print(f"[Auth] Giris basarili: {user['username']} (plan={user.get('plan', '?')})")

    # Heartbeat thread — lisans iptali olursa programi kapat
    def _on_license_invalid(reason: str):
        try:
            import tkinter.messagebox as mb
            mb.showerror("Lisans Hatasi", f"Lisans dogrulanamadi:\n\n{reason}\n\nProgram kapatilacak.")
        except Exception:
            pass
        license_client.clear_session()
        # Process'leri öldür
        try:
            os._exit(1)
        except Exception:
            sys.exit(1)

    heartbeat = license_client.HeartbeatManager(token, _on_license_invalid, interval_seconds=300)
    heartbeat.start()

    # Ana launcher penceresi
    app = App(auth_token=token, auth_user=user)
    try:
        plan_label = {"free": "Free", "pro": "Pro", "agency": "Agency"}.get(user.get('plan', 'free'), 'Free')
        app.title(f"RequestBot  ·  {user['username']}  [{plan_label}]")
    except Exception:
        pass
    app.mainloop()
