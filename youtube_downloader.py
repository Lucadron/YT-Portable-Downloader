import customtkinter as ctk
import yt_dlp
import threading
import os
import re
import queue
import subprocess
import sys
import urllib.request
from tkinter import filedialog
from PIL import Image
from io import BytesIO

# ══════════════════════════════════════════════════════════════
# DİL / LANGUAGE STRINGS
# ══════════════════════════════════════════════════════════════
STRINGS = {
    "tr": {
        "app_subtitle":    "yt-dlp  •  çoklu indirme kuyruğu",
        "sec_link":        "🔗  Link Ekle",
        "sec_format":      "🎛️  Format & Kayıt Konumu",
        "placeholder":     "https://youtube.com/watch?v=…",
        "add_btn":         "+ Ekle",
        "video_radio":     "🎬  Video (MP4)",
        "audio_radio":     "🎵  Ses (MP3)",
        "quality_lbl":     "Kalite:",
        "quality_opts":    ["En Yüksek", "1080p", "720p", "480p", "360p"],
        "folder_btn":      "📁 Klasör Seç",
        "open_folder_btn": "📂 Klasörü Aç",
        "start_btn":       "⬇  KUYRUĞU BAŞLAT",
        "stop_btn":        "⏹  Durdur",
        "starting_btn":    "⏳ İndiriliyor…",
        "empty_queue":     "Henüz video eklenmedi. Yukarıya link yapıştırın.",
        "fetching":        "Bilgi alınıyor…",
        "fetch_fail":      "Bilgi alınamadı",
        "waiting":         "● Bekliyor",
        "downloading":     "⬇ İndiriliyor…",
        "processing":      "İşleniyor…",
        "done":            "✅ Tamamlandı",
        "cancelled":       "⏹ İptal edildi",
        "error":           "❌ Hata oluştu",
        "queue_n":         lambda n: f"📋  Kuyruk  ({n} video)",
        "theme_toggle":    "☀️  Açık Tema",
        "theme_toggle2":   "🌙  Koyu Tema",
        "lang_btn":        "🌐  EN",
    },
    "en": {
        "app_subtitle":    "yt-dlp  •  multi-download queue",
        "sec_link":        "🔗  Add Link",
        "sec_format":      "🎛️  Format & Save Location",
        "placeholder":     "https://youtube.com/watch?v=…",
        "add_btn":         "+ Add",
        "video_radio":     "🎬  Video (MP4)",
        "audio_radio":     "🎵  Audio (MP3)",
        "quality_lbl":     "Quality:",
        "quality_opts":    ["Best", "1080p", "720p", "480p", "360p"],
        "folder_btn":      "📁 Choose Folder",
        "open_folder_btn": "📂 Open Folder",
        "start_btn":       "⬇  START QUEUE",
        "stop_btn":        "⏹  Stop",
        "starting_btn":    "⏳ Downloading…",
        "empty_queue":     "No videos added yet. Paste a link above.",
        "fetching":        "Fetching info…",
        "fetch_fail":      "Could not fetch info",
        "waiting":         "● Waiting",
        "downloading":     "⬇ Downloading…",
        "processing":      "Processing…",
        "done":            "✅ Done",
        "cancelled":       "⏹ Cancelled",
        "error":           "❌ Error occurred",
        "queue_n":         lambda n: f"📋  Queue  ({n} videos)",
        "theme_toggle":    "☀️  Light",
        "theme_toggle2":   "🌙  Dark",
        "lang_btn":        "🌐  TR",
    },
}

# ══════════════════════════════════════════════════════════════
# TEMA / THEMES
# ══════════════════════════════════════════════════════════════
THEMES = {
    "dark": {
        "BG":       "#0a0a0a",
        "PANEL":    "#111111",
        "CARD":     "#181818",
        "CARD2":    "#1f1f1f",
        "BORDER":   "#2c2c2c",
        "TEXT":     "#f1f1f1",
        "MUTED":    "#666666",
        "MUTED2":   "#3a3a3a",
        "ENTRY_BG": "#0d0d0d",
        "mode":     "dark",
    },
    "light": {
        "BG":       "#efefef",
        "PANEL":    "#ffffff",
        "CARD":     "#ffffff",
        "CARD2":    "#f5f5f5",
        "BORDER":   "#dedede",
        "TEXT":     "#111111",
        "MUTED":    "#888888",
        "MUTED2":   "#d0d0d0",
        "ENTRY_BG": "#f9f9f9",
        "mode":     "light",
    },
}

ACCENT  = "#e63946"
ACCENT2 = "#c1121f"
BLUE    = "#3b82f6"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"

F_TITLE = ("Segoe UI", 22, "bold")
F_SUB   = ("Segoe UI", 10)
F_LABEL = ("Segoe UI", 11)
F_BOLD  = ("Segoe UI", 11, "bold")
F_MONO  = ("Consolas", 10)
F_BTN   = ("Segoe UI", 12, "bold")
F_SMALL = ("Segoe UI", 9)

QUALITY_FMT = {
    "En Yüksek": "bestvideo+bestaudio/best",
    "Best":      "bestvideo+bestaudio/best",
    "1080p":     "bestvideo[height<=1080]+bestaudio/best",
    "720p":      "bestvideo[height<=720]+bestaudio/best",
    "480p":      "bestvideo[height<=480]+bestaudio/best",
    "360p":      "bestvideo[height<=360]+bestaudio/best",
}


# ══════════════════════════════════════════════════════════════
class QueueItem:
    def __init__(self, url, fmt, quality):
        self.url         = url
        self.fmt         = fmt
        self.quality     = quality
        self.title       = ""
        self.duration    = ""
        self.thumb_url   = ""
        self.status      = "bekliyor"
        self.saved_path  = None
        self.frame       = None
        self.thumb_label = None
        self.title_label = None
        self.dur_label   = None
        self.stat_label  = None
        self.prog_bar    = None
        self.pct_label   = None
        self.open_btn    = None


# ══════════════════════════════════════════════════════════════
class YTDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("820x740")
        self.minsize(700, 580)

        self.lang       = "tr"
        self.theme_name = "dark"
        self.T          = THEMES["dark"]
        self.S          = STRINGS["tr"]

        self.save_dir    = os.path.join(os.path.expanduser("~"), "Downloads")
        self.items       = []
        self.dl_queue    = queue.Queue()
        self.cancel_flag = threading.Event()

        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.T["BG"])
        self._build_ui()
        threading.Thread(target=self._worker, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    # UI OLUŞTURMA
    # ══════════════════════════════════════════════════════════
    def _build_ui(self):
        T = self.T
        S = self.S

        # ── Başlık
        self.hdr = ctk.CTkFrame(self, fg_color=T["PANEL"], corner_radius=0, height=68)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        hi = ctk.CTkFrame(self.hdr, fg_color="transparent")
        hi.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(hi, text="▶  YT Downloader",
                     font=F_TITLE, text_color=ACCENT).pack(side="left")

        # Sağ kontroller
        right = ctk.CTkFrame(hi, fg_color="transparent")
        right.pack(side="right")

        self.lang_btn_w = ctk.CTkButton(
            right, text=S["lang_btn"], width=76, height=32,
            fg_color=BLUE, hover_color="#2563eb",
            font=("Segoe UI", 10, "bold"), corner_radius=8,
            command=self._toggle_lang)
        self.lang_btn_w.pack(side="right", padx=(6, 0))

        self.theme_btn_w = ctk.CTkButton(
            right,
            text=S["theme_toggle"],
            width=110, height=32,
            fg_color=T["MUTED2"], hover_color=T["BORDER"],
            font=("Segoe UI", 10), corner_radius=8,
            command=self._toggle_theme)
        self.theme_btn_w.pack(side="right")

        self.subtitle_lbl = ctk.CTkLabel(
            hi, text=S["app_subtitle"], font=F_SUB, text_color=T["MUTED"])
        self.subtitle_lbl.pack(side="right", padx=(0, 16))

        # ── Scrollable gövde
        self.body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=T["MUTED2"],
            scrollbar_button_hover_color=T["MUTED"])
        self.body.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        self._build_link_card()
        self._build_settings_card()
        self._build_queue_card()

        # ── Alt buton çubuğu
        self.bot_bar = ctk.CTkFrame(self, fg_color=T["PANEL"], corner_radius=0, height=64)
        self.bot_bar.pack(fill="x", side="bottom")
        self.bot_bar.pack_propagate(False)
        bi = ctk.CTkFrame(self.bot_bar, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=16, pady=10)

        self.start_btn = ctk.CTkButton(
            bi, text=S["start_btn"], font=F_BTN,
            fg_color=ACCENT, hover_color=ACCENT2, height=44,
            corner_radius=10, command=self._start_queue)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn_w = ctk.CTkButton(
            bi, text=S["stop_btn"], font=F_BTN, width=120, height=44,
            fg_color=T["MUTED2"], hover_color="#777777", corner_radius=10,
            command=self._cancel)
        self.stop_btn_w.pack(side="left")

    def _build_link_card(self):
        T = self.T
        S = self.S
        f = ctk.CTkFrame(self.body, fg_color=T["CARD"], corner_radius=12,
                         border_width=1, border_color=T["BORDER"])
        f.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(f, text=S["sec_link"], font=("Segoe UI", 10, "bold"),
                     text_color=T["MUTED"]).pack(anchor="w", padx=14, pady=(10, 2))

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 12))
        self.url_entry = ctk.CTkEntry(
            row, placeholder_text=S["placeholder"],
            font=F_MONO, height=40, corner_radius=8,
            border_color=T["BORDER"], fg_color=T["ENTRY_BG"],
            text_color=T["TEXT"])
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda e: self._add_item())
        ctk.CTkButton(row, text=S["add_btn"], width=88, height=40,
                      fg_color=BLUE, hover_color="#2563eb",
                      font=F_BOLD, corner_radius=8,
                      command=self._add_item).pack(side="left", padx=(8, 0))
        ctk.CTkButton(row, text="✕", width=40, height=40,
                      fg_color=T["CARD2"], hover_color=T["BORDER"],
                      font=("Segoe UI", 14), corner_radius=8,
                      command=lambda: self.url_entry.delete(0, "end")
                      ).pack(side="left", padx=(6, 0))

    def _build_settings_card(self):
        T = self.T
        S = self.S
        f = ctk.CTkFrame(self.body, fg_color=T["CARD"], corner_radius=12,
                         border_width=1, border_color=T["BORDER"])
        f.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(f, text=S["sec_format"], font=("Segoe UI", 10, "bold"),
                     text_color=T["MUTED"]).pack(anchor="w", padx=14, pady=(10, 2))

        r1 = ctk.CTkFrame(f, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=(0, 6))
        self.fmt_var = ctk.StringVar(value="video")
        ctk.CTkRadioButton(r1, text=S["video_radio"], variable=self.fmt_var,
                           value="video", font=F_LABEL, text_color=T["TEXT"],
                           fg_color=ACCENT, hover_color=ACCENT
                           ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(r1, text=S["audio_radio"], variable=self.fmt_var,
                           value="ses", font=F_LABEL, text_color=T["TEXT"],
                           fg_color=BLUE, hover_color=BLUE
                           ).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(r1, text=S["quality_lbl"], font=F_LABEL,
                     text_color=T["MUTED"]).pack(side="left", padx=(12, 6))
        self.quality_box = ctk.CTkComboBox(
            r1, values=S["quality_opts"],
            font=F_LABEL, width=130, height=36,
            fg_color=T["ENTRY_BG"], border_color=T["BORDER"],
            button_color=T["BORDER"], dropdown_fg_color=T["CARD2"])
        self.quality_box.pack(side="left")

        r2 = ctk.CTkFrame(f, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=(0, 12))
        self.dir_lbl = ctk.CTkLabel(r2, text=self.save_dir,
                                    font=F_MONO, text_color=T["MUTED"], anchor="w")
        self.dir_lbl.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(r2, text=S["open_folder_btn"], width=130, height=34,
                      fg_color=T["CARD2"], hover_color=T["BORDER"],
                      font=F_LABEL, corner_radius=8,
                      command=lambda: self._open_folder(self.save_dir)
                      ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(r2, text=S["folder_btn"], width=120, height=34,
                      fg_color=T["CARD2"], hover_color=T["BORDER"],
                      font=F_LABEL, corner_radius=8,
                      command=self._pick_dir).pack(side="right")

    def _build_queue_card(self):
        T = self.T
        S = self.S
        f = ctk.CTkFrame(self.body, fg_color=T["CARD"], corner_radius=12,
                         border_width=1, border_color=T["BORDER"])
        f.pack(fill="x", pady=(0, 10))
        self.q_title_lbl = ctk.CTkLabel(
            f, text=S["queue_n"](len(self.items)),
            font=("Segoe UI", 10, "bold"), text_color=T["MUTED"])
        self.q_title_lbl.pack(anchor="w", padx=14, pady=(10, 2))

        self.q_frame = ctk.CTkFrame(f, fg_color="transparent")
        self.q_frame.pack(fill="x", padx=14, pady=(0, 12))
        self.empty_lbl = ctk.CTkLabel(
            self.q_frame, text=S["empty_queue"],
            font=F_LABEL, text_color=T["MUTED"])
        self.empty_lbl.pack(pady=16)

    # ══════════════════════════════════════════════════════════
    # TEMA & DİL
    # ══════════════════════════════════════════════════════════
    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.T = THEMES[self.theme_name]
        ctk.set_appearance_mode(self.T["mode"])
        self._rebuild()

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "tr" else "tr"
        self.S = STRINGS[self.lang]
        # Kalite seçimini sıfırla (dil değişince seçenekler değişir)
        self._rebuild()

    def _rebuild(self):
        saved_items = self.items[:]
        saved_dir   = self.save_dir
        saved_fmt   = self.fmt_var.get() if hasattr(self, "fmt_var") else "video"

        for w in self.winfo_children():
            w.destroy()

        self.configure(fg_color=self.T["BG"])
        self.items    = []
        self.save_dir = saved_dir
        self._build_ui()

        # Kalite seçimini koru
        self.fmt_var.set(saved_fmt)
        self.dir_lbl.configure(text=saved_dir)

        # Kartları yeniden render et
        for item in saved_items:
            self.items.append(item)
            self._render_card(item)
            # Durum bilgisini geri yükle
            if item.stat_label and item.stat_label.winfo_exists():
                pass  # render_card zaten "bekliyor" yazar, durum label güncellenir

        self._refresh_header()
        if self.items:
            if self.empty_lbl.winfo_ismapped():
                self.empty_lbl.pack_forget()

    # ══════════════════════════════════════════════════════════
    # KLASÖR
    # ══════════════════════════════════════════════════════════
    def _pick_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir)
        if d:
            self.save_dir = d
            self.dir_lbl.configure(text=d)

    def _open_folder(self, path):
        target = os.path.dirname(path) if os.path.isfile(path) else path
        if not os.path.exists(target):
            target = self.save_dir
        if sys.platform == "win32":
            os.startfile(target)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])

    # ══════════════════════════════════════════════════════════
    # KUYRUK KARTI
    # ══════════════════════════════════════════════════════════
    def _add_item(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.url_entry.delete(0, "end")
        item = QueueItem(url, self.fmt_var.get(), self.quality_box.get())
        item.title = self.S["fetching"]
        self.items.append(item)
        self._render_card(item)
        self._refresh_header()
        threading.Thread(target=self._fetch_info, args=(item,), daemon=True).start()

    def _fetch_info(self, item):
        S = self.S
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                   "skip_download": True}) as ydl:
                info = ydl.extract_info(item.url, download=False)
            item.title    = info.get("title", "Unknown")
            secs          = info.get("duration", 0) or 0
            item.duration = f"{secs//60}:{secs%60:02d}"
            item.thumb_url = info.get("thumbnail", "")
        except Exception:
            item.title = S["fetch_fail"]
        self.after(0, self._apply_info, item)

    def _apply_info(self, item):
        if item.title_label and item.title_label.winfo_exists():
            item.title_label.configure(text=item.title)
        if item.dur_label and item.dur_label.winfo_exists() and item.duration:
            item.dur_label.configure(text=f"⏱ {item.duration}")
        if item.thumb_url:
            threading.Thread(target=self._load_thumb, args=(item,), daemon=True).start()

    def _load_thumb(self, item):
        try:
            with urllib.request.urlopen(item.thumb_url, timeout=6) as r:
                data = r.read()
            img   = Image.open(BytesIO(data)).convert("RGB")
            img   = img.resize((112, 63), Image.LANCZOS)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(112, 63))
            def apply():
                if item.thumb_label and item.thumb_label.winfo_exists():
                    item.thumb_label.configure(image=photo, text="")
                    item.thumb_label._photo = photo
            self.after(0, apply)
        except Exception:
            pass

    def _render_card(self, item):
        T = self.T
        S = self.S

        if self.empty_lbl.winfo_ismapped():
            self.empty_lbl.pack_forget()

        card = ctk.CTkFrame(self.q_frame, fg_color=T["CARD2"], corner_radius=10,
                            border_width=1, border_color=T["BORDER"])
        card.pack(fill="x", pady=(0, 8))
        item.frame = card

        # Thumbnail
        thumb = ctk.CTkLabel(card, text="⏳", width=112, height=63,
                             fg_color=T["ENTRY_BG"], corner_radius=6,
                             font=("Segoe UI", 20), text_color=T["MUTED"])
        thumb.pack(side="left", padx=(10, 0), pady=10)
        item.thumb_label = thumb

        # Orta
        mid = ctk.CTkFrame(card, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        t_lbl = ctk.CTkLabel(mid, text=item.title or S["fetching"],
                             font=F_BOLD, text_color=T["TEXT"],
                             anchor="w", wraplength=380, justify="left")
        t_lbl.pack(fill="x")
        item.title_label = t_lbl

        meta = ctk.CTkFrame(mid, fg_color="transparent")
        meta.pack(fill="x", pady=(2, 0))
        d_lbl = ctk.CTkLabel(meta, text=(f"⏱ {item.duration}" if item.duration else ""),
                             font=F_SMALL, text_color=T["MUTED"])
        d_lbl.pack(side="left")
        item.dur_label = d_lbl
        fc = ACCENT if item.fmt == "video" else BLUE
        ft = "MP4" if item.fmt == "video" else "MP3"
        ctk.CTkLabel(meta, text=f"  •  {ft} / {item.quality}",
                     font=F_SMALL, text_color=fc).pack(side="left")

        prog = ctk.CTkProgressBar(mid, height=6, corner_radius=3,
                                  fg_color=T["BORDER"], progress_color=ACCENT)
        prog.pack(fill="x", pady=(8, 0))
        prog.set(0)
        item.prog_bar = prog

        bot = ctk.CTkFrame(mid, fg_color="transparent")
        bot.pack(fill="x", pady=(3, 0))
        s_lbl = ctk.CTkLabel(bot, text=S["waiting"], font=F_SMALL,
                             text_color=T["MUTED"], anchor="w")
        s_lbl.pack(side="left")
        item.stat_label = s_lbl
        p_lbl = ctk.CTkLabel(bot, text="", font=F_SMALL,
                             text_color=T["MUTED"], anchor="e")
        p_lbl.pack(side="right")
        item.pct_label = p_lbl

        # "Klasörü Aç" — başta gizli
        open_btn = ctk.CTkButton(
            mid, text=S["open_folder_btn"], height=28, width=140,
            fg_color=T["CARD2"], hover_color=T["BORDER"],
            font=F_SMALL, corner_radius=6,
            command=lambda i=item: self._open_folder(i.saved_path or self.save_dir))
        item.open_btn = open_btn

        # Tamamlanmışsa hemen göster
        if item.status == "tamam":
            item.open_btn.pack(anchor="w", pady=(6, 0))

        # Sil butonu
        ctk.CTkButton(card, text="✕", width=30, height=30,
                      fg_color="transparent", hover_color=T["BORDER"],
                      font=("Segoe UI", 13), text_color=T["MUTED"],
                      corner_radius=6,
                      command=lambda i=item: self._remove(i)
                      ).pack(side="right", padx=(0, 10))

    def _remove(self, item):
        if item.status == "indiriliyor":
            return
        self.items.remove(item)
        if item.frame and item.frame.winfo_exists():
            item.frame.destroy()
        self._refresh_header()
        visible = [i for i in self.items if i.frame and i.frame.winfo_exists()]
        if not visible:
            self.empty_lbl.pack(pady=16)

    def _refresh_header(self):
        self.q_title_lbl.configure(text=self.S["queue_n"](len(self.items)))

    # ══════════════════════════════════════════════════════════
    # İNDİRME
    # ══════════════════════════════════════════════════════════
    def _start_queue(self):
        pending = [i for i in self.items if i.status == "bekliyor"]
        if not pending:
            return
        self.cancel_flag.clear()
        for item in pending:
            self.dl_queue.put(item)
        self.start_btn.configure(state="disabled", text=self.S["starting_btn"])

    def _cancel(self):
        self.cancel_flag.set()

    def _worker(self):
        while True:
            item = self.dl_queue.get()
            self.cancel_flag.clear()
            self._download(item)
            self.dl_queue.task_done()
            if self.dl_queue.empty():
                self.after(0, lambda: self.start_btn.configure(
                    state="normal", text=self.S["start_btn"]))

    def _download(self, item):
        S = self.S
        item.status = "indiriliyor"
        self.after(0, self._set_stat, item, S["downloading"], ACCENT, 0)

        actual_height = [None]

        def hook(d):
            if self.cancel_flag.is_set():
                raise Exception("__CANCEL__")
            if d["status"] == "downloading":
                if actual_height[0] is None:
                    h = d.get("info_dict", {}).get("height")
                    if h:
                        actual_height[0] = h
                raw = re.sub(r"\x1b\[[0-9;]*m", "",
                             d.get("_percent_str", "0%")).strip()
                pct = float(re.sub(r"[^\d.]", "", raw) or 0) / 100
                spd = re.sub(r"\x1b\[[0-9;]*m", "",
                             d.get("_speed_str", "")).strip()
                eta = re.sub(r"\x1b\[[0-9;]*m", "",
                             d.get("_eta_str", "")).strip()
                info = f"🚀 {spd}   ⏱ {eta}" if spd else S["downloading"]
                self.after(0, self._upd_prog, item, pct, f"{pct*100:.0f}%", info)
            elif d["status"] == "finished":
                if actual_height[0] is None:
                    h = d.get("info_dict", {}).get("height")
                    if h:
                        actual_height[0] = h
                self.after(0, self._upd_prog, item, 1.0, "100%", S["processing"])

        # Dosya adı şablonu — video için çözünürlük etiketi
        if item.fmt == "video":
            # Kalite sabit seçildiyse (1080p, 720p…) direkt yaz
            # "En Yüksek" / "Best" ise indirme sonrası gerçek çözünürlük eklenir
            q_label = item.quality if item.quality not in ("En Yüksek", "Best") else "%(height)sp"
            out_tmpl = os.path.join(self.save_dir, f"%(title)s [{q_label}].%(ext)s")
        else:
            out_tmpl = os.path.join(self.save_dir, "%(title)s.%(ext)s")

        opts = {
            "outtmpl":        out_tmpl,
            "noplaylist":     True,
            "progress_hooks": [hook],
            "quiet":          True,
            "no_warnings":    True,
        }

        if item.fmt == "ses":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   "mp3",
                "preferredquality": "192",
            }]
        else:
            opts["format"]              = QUALITY_FMT.get(item.quality, "bestvideo+bestaudio/best")
            opts["merge_output_format"] = "mp4"
            opts["postprocessor_args"]  = [
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
            ]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([item.url])

            item.status     = "tamam"
            item.saved_path = self.save_dir
            h = actual_height[0]
            res_tag = f" — {h}p" if h and item.fmt == "video" else ""
            self.after(0, self._finish_item, item, res_tag)

        except Exception as e:
            if "__CANCEL__" in str(e):
                item.status = "iptal"
                self.after(0, self._set_stat, item, S["cancelled"], AMBER, 0)
            else:
                item.status = "hata"
                self.after(0, self._set_stat, item, S["error"], ACCENT, 0)

    def _finish_item(self, item, res_tag):
        S = self.S
        self._set_stat(item, S["done"] + res_tag, GREEN, 1.0)
        if item.open_btn:
            item.open_btn.pack(anchor="w", pady=(6, 0))

    def _upd_prog(self, item, ratio, pct, info):
        T = self.T
        if item.prog_bar and item.prog_bar.winfo_exists():
            item.prog_bar.set(ratio)
        if item.pct_label and item.pct_label.winfo_exists():
            item.pct_label.configure(text=pct)
        if item.stat_label and item.stat_label.winfo_exists():
            item.stat_label.configure(text=info, text_color=T["TEXT"])

    def _set_stat(self, item, text, color, ratio):
        if item.prog_bar and item.prog_bar.winfo_exists():
            item.prog_bar.set(ratio)
            item.prog_bar.configure(progress_color=color)
        if item.stat_label and item.stat_label.winfo_exists():
            item.stat_label.configure(text=text, text_color=color)
        if item.pct_label and item.pct_label.winfo_exists():
            item.pct_label.configure(text="")


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = YTDownloader()
    app.mainloop()
