import customtkinter as ctk
import yt_dlp
import threading
import os
import re
import queue
import urllib.request
from tkinter import filedialog
from PIL import Image
from io import BytesIO

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG     = "#0a0a0a"
PANEL  = "#111111"
CARD   = "#181818"
CARD2  = "#1f1f1f"
BORDER = "#2c2c2c"
ACCENT = "#e63946"
ACCENT2= "#ff6b6b"
BLUE   = "#3b82f6"
GREEN  = "#22c55e"
AMBER  = "#f59e0b"
TEXT   = "#f1f1f1"
MUTED  = "#666666"
MUTED2 = "#444444"

F_TITLE = ("Segoe UI", 22, "bold")
F_SUB   = ("Segoe UI", 10)
F_LABEL = ("Segoe UI", 11)
F_BOLD  = ("Segoe UI", 11, "bold")
F_MONO  = ("Consolas", 10)
F_BTN   = ("Segoe UI", 12, "bold")
F_SMALL = ("Segoe UI", 9)


class QueueItem:
    def __init__(self, url, fmt, quality):
        self.url         = url
        self.fmt         = fmt
        self.quality     = quality
        self.title       = "Bilgi alınıyor…"
        self.duration    = ""
        self.thumb_url   = ""
        self.status      = "bekliyor"
        self.frame       = None
        self.thumb_label = None
        self.title_label = None
        self.dur_label   = None
        self.stat_label  = None
        self.prog_bar    = None
        self.pct_label   = None


class YTDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("800x720")
        self.minsize(700, 600)
        self.configure(fg_color=BG)

        self.save_dir    = os.path.join(os.path.expanduser("~"), "Downloads")
        self.items       = []
        self.dl_queue    = queue.Queue()
        self.cancel_flag = threading.Event()

        self._build_ui()
        threading.Thread(target=self._worker, daemon=True).start()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        hi = ctk.CTkFrame(hdr, fg_color="transparent")
        hi.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(hi, text="▶  YT Downloader",
                     font=F_TITLE, text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(hi, text="yt-dlp  •  çoklu indirme kuyruğu",
                     font=F_SUB, text_color=MUTED).pack(side="right")

        self.body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=MUTED2,
            scrollbar_button_hover_color=MUTED)
        self.body.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        self._card(self.body, "🔗  Link Ekle", self._add_section)
        self._card(self.body, "🎛️  Format & Kayıt Konumu", self._settings_section)
        self.q_title_lbl = self._card(
            self.body, "📋  Kuyruk  (0 video)", self._queue_section)

        bar = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=64)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        bi = ctk.CTkFrame(bar, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=16, pady=10)

        self.start_btn = ctk.CTkButton(
            bi, text="⬇  KUYRUĞU BAŞLAT", font=F_BTN,
            fg_color=ACCENT, hover_color=ACCENT2, height=44,
            corner_radius=10, command=self._start_queue)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            bi, text="⏹  Durdur", font=F_BTN, width=120, height=44,
            fg_color=MUTED2, hover_color="#555", corner_radius=10,
            command=self._cancel)
        self.cancel_btn.pack(side="left")

    def _card(self, parent, title, builder):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=BORDER)
        f.pack(fill="x", pady=(0, 10))
        lbl = ctk.CTkLabel(f, text=title, font=("Segoe UI", 10, "bold"),
                           text_color=MUTED)
        lbl.pack(anchor="w", padx=14, pady=(10, 2))
        builder(f)
        return lbl

    def _add_section(self, p):
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 12))
        self.url_entry = ctk.CTkEntry(
            row, placeholder_text="https://youtube.com/watch?v=…",
            font=F_MONO, height=40, corner_radius=8,
            border_color=BORDER, fg_color="#0d0d0d", text_color=TEXT)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda e: self._add_item())
        ctk.CTkButton(row, text="+ Ekle", width=88, height=40,
                      fg_color=BLUE, hover_color="#2563eb",
                      font=F_BOLD, corner_radius=8,
                      command=self._add_item).pack(side="left", padx=(8, 0))
        ctk.CTkButton(row, text="✕", width=40, height=40,
                      fg_color=CARD2, hover_color=BORDER,
                      font=("Segoe UI", 14), corner_radius=8,
                      command=lambda: self.url_entry.delete(0, "end")
                      ).pack(side="left", padx=(6, 0))

    def _settings_section(self, p):
        r1 = ctk.CTkFrame(p, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=(0, 6))
        self.fmt_var = ctk.StringVar(value="video")
        ctk.CTkRadioButton(r1, text="🎬  Video (MP4)", variable=self.fmt_var,
                           value="video", font=F_LABEL, text_color=TEXT,
                           fg_color=ACCENT, hover_color=ACCENT
                           ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(r1, text="🎵  Ses (MP3)", variable=self.fmt_var,
                           value="ses", font=F_LABEL, text_color=TEXT,
                           fg_color=BLUE, hover_color=BLUE
                           ).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(r1, text="Kalite:", font=F_LABEL,
                     text_color=MUTED).pack(side="left", padx=(12, 6))
        self.quality_box = ctk.CTkComboBox(
            r1, values=["En Yüksek", "1080p", "720p", "480p", "360p"],
            font=F_LABEL, width=130, height=36,
            fg_color="#0d0d0d", border_color=BORDER,
            button_color=BORDER, dropdown_fg_color=CARD2)
        self.quality_box.pack(side="left")

        r2 = ctk.CTkFrame(p, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=(0, 12))
        self.dir_lbl = ctk.CTkLabel(r2, text=self.save_dir,
                                    font=F_MONO, text_color="#999", anchor="w")
        self.dir_lbl.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(r2, text="📁 Klasör Seç", width=120, height=34,
                      fg_color=CARD2, hover_color=BORDER,
                      font=F_LABEL, corner_radius=8,
                      command=self._pick_dir).pack(side="right")

    def _queue_section(self, p):
        self.q_frame = ctk.CTkFrame(p, fg_color="transparent")
        self.q_frame.pack(fill="x", padx=14, pady=(0, 12))
        self.empty_lbl = ctk.CTkLabel(
            self.q_frame,
            text="Henüz video eklenmedi. Yukarıya link yapıştırın.",
            font=F_LABEL, text_color=MUTED)
        self.empty_lbl.pack(pady=16)

    def _pick_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir)
        if d:
            self.save_dir = d
            self.dir_lbl.configure(text=d)

    def _add_item(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.url_entry.delete(0, "end")
        item = QueueItem(url, self.fmt_var.get(), self.quality_box.get())
        self.items.append(item)
        self._render_card(item)
        self._refresh_header()
        threading.Thread(target=self._fetch_info, args=(item,), daemon=True).start()

    def _fetch_info(self, item):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                   "skip_download": True}) as ydl:
                info = ydl.extract_info(item.url, download=False)
            item.title     = info.get("title", "Bilinmeyen")
            secs           = info.get("duration", 0) or 0
            item.duration  = f"{secs//60}:{secs%60:02d}"
            item.thumb_url = info.get("thumbnail", "")
        except Exception:
            item.title = "Bilgi alınamadı"
        self.after(0, self._apply_info, item)

    def _apply_info(self, item):
        if item.title_label and item.title_label.winfo_exists():
            item.title_label.configure(text=item.title)
        if item.dur_label and item.dur_label.winfo_exists() and item.duration:
            item.dur_label.configure(text=f"⏱ {item.duration}")
        if item.thumb_url:
            threading.Thread(target=self._load_thumb,
                             args=(item,), daemon=True).start()

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
        if self.empty_lbl.winfo_ismapped():
            self.empty_lbl.pack_forget()

        card = ctk.CTkFrame(self.q_frame, fg_color=CARD2, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=(0, 8))
        item.frame = card

        thumb = ctk.CTkLabel(card, text="⏳", width=112, height=63,
                             fg_color="#0d0d0d", corner_radius=6,
                             font=("Segoe UI", 20), text_color=MUTED)
        thumb.pack(side="left", padx=(10, 0), pady=10)
        item.thumb_label = thumb

        mid = ctk.CTkFrame(card, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        t_lbl = ctk.CTkLabel(mid, text=item.title, font=F_BOLD,
                             text_color=TEXT, anchor="w",
                             wraplength=400, justify="left")
        t_lbl.pack(fill="x")
        item.title_label = t_lbl

        meta = ctk.CTkFrame(mid, fg_color="transparent")
        meta.pack(fill="x", pady=(2, 0))
        d_lbl = ctk.CTkLabel(meta, text="", font=F_SMALL, text_color=MUTED)
        d_lbl.pack(side="left")
        item.dur_label = d_lbl
        fc = ACCENT if item.fmt == "video" else BLUE
        ft = "MP4" if item.fmt == "video" else "MP3"
        ctk.CTkLabel(meta, text=f"  •  {ft} / {item.quality}",
                     font=F_SMALL, text_color=fc).pack(side="left")

        bar = ctk.CTkProgressBar(mid, height=6, corner_radius=3,
                                 fg_color=BORDER, progress_color=ACCENT)
        bar.pack(fill="x", pady=(8, 0))
        bar.set(0)
        item.prog_bar = bar

        bot = ctk.CTkFrame(mid, fg_color="transparent")
        bot.pack(fill="x", pady=(3, 0))
        s_lbl = ctk.CTkLabel(bot, text="● Bekliyor", font=F_SMALL,
                             text_color=MUTED, anchor="w")
        s_lbl.pack(side="left")
        item.stat_label = s_lbl
        p_lbl = ctk.CTkLabel(bot, text="", font=F_SMALL,
                             text_color=MUTED, anchor="e")
        p_lbl.pack(side="right")
        item.pct_label = p_lbl

        ctk.CTkButton(card, text="✕", width=30, height=30,
                      fg_color="transparent", hover_color=BORDER,
                      font=("Segoe UI", 13), text_color=MUTED,
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
        self.q_title_lbl.configure(
            text=f"📋  Kuyruk  ({len(self.items)} video)")

    def _start_queue(self):
        pending = [i for i in self.items if i.status == "bekliyor"]
        if not pending:
            return
        self.cancel_flag.clear()
        for item in pending:
            self.dl_queue.put(item)
        self.start_btn.configure(state="disabled", text="⏳ İndiriliyor…")

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
                    state="normal", text="⬇  KUYRUĞU BAŞLAT"))

    def _download(self, item):
        item.status = "indiriliyor"
        self.after(0, self._set_stat, item, "⬇ İndiriliyor…", ACCENT, 0)

        def hook(d):
            if self.cancel_flag.is_set():
                raise Exception("__CANCEL__")
            if d["status"] == "downloading":
                raw  = re.sub(r"\x1b\[[0-9;]*m", "",
                              d.get("_percent_str", "0%")).strip()
                pct  = float(re.sub(r"[^\d.]", "", raw) or 0) / 100
                spd  = re.sub(r"\x1b\[[0-9;]*m", "",
                              d.get("_speed_str", "")).strip()
                eta  = re.sub(r"\x1b\[[0-9;]*m", "",
                              d.get("_eta_str", "")).strip()
                info = f"🚀 {spd}   ⏱ Kalan: {eta}" if spd else "İndiriliyor…"
                self.after(0, self._upd_prog, item, pct, f"{pct*100:.0f}%", info)
            elif d["status"] == "finished":
                self.after(0, self._upd_prog, item, 1.0, "100%", "İşleniyor…")

        qmap = {
            "En Yüksek": "bestvideo+bestaudio/best",
            "1080p":     "bestvideo[height<=1080]+bestaudio/best",
            "720p":      "bestvideo[height<=720]+bestaudio/best",
            "480p":      "bestvideo[height<=480]+bestaudio/best",
            "360p":      "bestvideo[height<=360]+bestaudio/best",
        }

        opts = {
            "outtmpl":         os.path.join(self.save_dir, "%(title)s.%(ext)s"),
            "noplaylist":      True,
            "progress_hooks":  [hook],
            "quiet":           True,
            "no_warnings":     True,
        }

        if item.fmt == "ses":
            # MP3 çıkarma
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key":             "FFmpegExtractAudio",
                "preferredcodec":  "mp3",
                "preferredquality":"192",
            }]
        else:
            # ── VİDEO: sesi kesinlikle AAC'ye çevir ──────────────────────
            # YouTube Opus/Vorbis sesi Windows Media Player'da çalmaz.
            # "-c:a aac" ile ffmpeg birleştirme sırasında dönüştürüyoruz.
            opts["format"]             = qmap.get(item.quality, "bestvideo+bestaudio/best")
            opts["merge_output_format"]= "mp4"
            # postprocessor_args liste olarak verildiğinde ffmpeg'e direkt geçer
            opts["postprocessor_args"] = [
                "-c:v", "copy",         # videoyu yeniden kodlama (hızlı)
                "-c:a", "aac",          # sesi AAC'ye çevir
                "-b:a", "192k",         # ses bit hızı
                "-movflags", "+faststart",
            ]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([item.url])
            item.status = "tamam"
            self.after(0, self._set_stat, item, "✅ Tamamlandı", GREEN, 1.0)
        except Exception as e:
            if "__CANCEL__" in str(e):
                item.status = "iptal"
                self.after(0, self._set_stat, item, "⏹ İptal edildi", AMBER, 0)
            else:
                item.status = "hata"
                self.after(0, self._set_stat, item, "❌ Hata oluştu", ACCENT, 0)

    def _upd_prog(self, item, ratio, pct, info):
        if item.prog_bar and item.prog_bar.winfo_exists():
            item.prog_bar.set(ratio)
        if item.pct_label and item.pct_label.winfo_exists():
            item.pct_label.configure(text=pct)
        if item.stat_label and item.stat_label.winfo_exists():
            item.stat_label.configure(text=info, text_color=TEXT)

    def _set_stat(self, item, text, color, ratio):
        if item.prog_bar and item.prog_bar.winfo_exists():
            item.prog_bar.set(ratio)
            item.prog_bar.configure(progress_color=color)
        if item.stat_label and item.stat_label.winfo_exists():
            item.stat_label.configure(text=text, text_color=color)
        if item.pct_label and item.pct_label.winfo_exists():
            item.pct_label.configure(text="")


if __name__ == "__main__":
    app = YTDownloader()
    app.mainloop()
