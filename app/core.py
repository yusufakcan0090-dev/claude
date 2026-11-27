"""Kesit Stüdyosu - ortak yardımcılar: yollar, ayarlar, işler (job), ffmpeg."""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
BIN = ROOT / "bin"
VERI = ROOT / "veri"
INDIRILEN = VERI / "indirilenler"
ONIZLEME = VERI / "onizleme"
ANALIZ = VERI / "analizler"
PROJELER = VERI / "projeler"
CACHE = VERI / "cache"
FONTS = APP / "ui" / "fonts"
for _d in (VERI, INDIRILEN, ONIZLEME, ANALIZ, PROJELER, CACHE):
    _d.mkdir(parents=True, exist_ok=True)

IS_WIN = sys.platform.startswith("win")
NO_WINDOW = 0x08000000 if IS_WIN else 0  # CREATE_NO_WINDOW


def _tool(name):
    exe = BIN / (name + (".exe" if IS_WIN else ""))
    if exe.exists():
        return str(exe)
    found = shutil.which(name)
    return found or name


FFMPEG = _tool("ffmpeg")
FFPROBE = _tool("ffprobe")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=NO_WINDOW, **kw)


def popen(cmd, **kw):
    return subprocess.Popen(cmd, creationflags=NO_WINDOW, **kw)


# ---------------------------------------------------------------- süreç duraklatma / kapanış
SHUTTING_DOWN = False


def proc_pause(p, pause=True):
    """Çalışan bir alt süreci dondurur / devam ettirir (Windows: NtSuspendProcess)."""
    try:
        if p.poll() is not None:
            return
        if sys.platform.startswith("win"):
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x0800, False, p.pid)  # PROCESS_SUSPEND_RESUME
            if h:
                (ctypes.windll.ntdll.NtSuspendProcess if pause else ctypes.windll.ntdll.NtResumeProcess)(h)
                ctypes.windll.kernel32.CloseHandle(h)
        else:
            import signal
            os.kill(p.pid, signal.SIGSTOP if pause else signal.SIGCONT)
    except Exception:
        pass


def shutdown():
    """Uygulama kapanırken: yarım işler diskte kalsın (sonra devam edilir), alt süreçler kapansın."""
    global SHUTTING_DOWN
    SHUTTING_DOWN = True
    try:
        for j in list(JOBS.jobs.values()):
            for p in list(j.procs):
                try:
                    proc_pause(p, False)
                    p.kill()
                except Exception:
                    pass
    except Exception:
        pass


# ---------------------------------------------------------------- ayarlar
DEFAULT_SETTINGS = {
    "cikti_klasoru": str(Path.home() / "Videos" / "Kesit Studyosu"),
    "whisper_model": "large-v3",
    "ipucu_isimler": "RRaenee, Kick, Animeci",
    "duzeltmeler": {},          # yanlis -> dogru (otomatik uygulanır)
    "an_modu": "orta",          # kisa | orta | uzun
    "an_sayisi": 20,            # 0 = sınırsız
    "kalite": "yuksek",         # yuksek | normal
    "cozunurluk": 1080,         # 720 | 1080 | 1440 (2K)
    "fps": "kaynak",            # kaynak | 30 | 60 | 90
    "ses_dengele": True,
    "oto_altyazi": False,
    "tema": "koyu",
    "tur_goruldu": False,
    "oto_guncelle": True,
    "son_kanal": "",
    "varsayilan_stil": None,
    "varsayilan_duzen": None,
}
_settings_lock = threading.Lock()
SETTINGS_FILE = VERI / "ayarlar.json"


def load_settings():
    s = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            s.update(json.loads(SETTINGS_FILE.read_text("utf-8")))
        except Exception:
            pass
    return s


def save_settings(patch):
    with _settings_lock:
        s = load_settings()
        s.update(patch)
        write_json(SETTINGS_FILE, s)
        return s


def write_json(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except Exception:
        return default


def new_id(prefix=""):
    return prefix + uuid.uuid4().hex[:10]


def safe_name(text, maxlen=60):
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", text or "").strip().strip(".")
    text = re.sub(r"\s+", " ", text)
    return (text[:maxlen].strip() or "kesit")


# ---------------------------------------------------------------- türkçe
_TR_UP = str.maketrans({"i": "İ", "ı": "I"})
_TR_LO = str.maketrans({"I": "ı", "İ": "i"})


def tr_upper(s):
    return s.translate(_TR_UP).upper()


def tr_lower(s):
    return s.translate(_TR_LO).lower()


# ---------------------------------------------------------------- medya
def probe(path):
    r = run([FFPROBE, "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", str(path)])
    info = {"duration": 0.0, "width": 1920, "height": 1080, "fps": 30.0, "has_audio": False}
    try:
        d = json.loads(r.stdout)
        info["duration"] = float(d.get("format", {}).get("duration") or 0)
        for st in d.get("streams", []):
            if st.get("codec_type") == "video" and st.get("width"):
                info["width"], info["height"] = int(st["width"]), int(st["height"])
                num, _, den = (st.get("r_frame_rate") or "30/1").partition("/")
                try:
                    info["fps"] = round(float(num) / float(den or 1), 3)
                except Exception:
                    pass
            if st.get("codec_type") == "audio":
                info["has_audio"] = True
    except Exception:
        pass
    return info


def thumbnail(path, out, t=1.0, width=480):
    out = Path(out)
    if out.exists():
        return out
    run([FFMPEG, "-y", "-ss", str(max(0, t)), "-i", str(path), "-frames:v", "1",
         "-vf", f"scale={width}:-2", "-q:v", "4", str(out)])
    return out


def run_ffmpeg_progress(cmd, duration, on_progress, cancel_flag=None, cwd=None, job=None):
    """ffmpeg'i -progress ile çalıştırır, ilerlemeyi (0-1) bildirir."""
    full = [cmd[0], "-hide_banner", "-nostats", "-progress", "pipe:1"] + cmd[1:]
    p = popen(full, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
              encoding="utf-8", errors="replace", cwd=cwd)
    if job is not None:
        job.procs.add(p)
        if job.paused:
            proc_pause(p, True)
    err_lines = []

    def _drain():
        for line in p.stderr:
            err_lines.append(line)
            if len(err_lines) > 80:
                del err_lines[:40]
    th = threading.Thread(target=_drain, daemon=True)
    th.start()
    for line in p.stdout:
        if cancel_flag and cancel_flag():
            p.kill()
            raise RuntimeError("İptal edildi")
        if line.startswith("out_time_us=") or line.startswith("out_time_ms="):
            try:
                us = int(line.split("=")[1])
                if duration > 0:
                    on_progress(min(0.999, us / 1e6 / duration))
            except ValueError:
                pass
    p.wait()
    if job is not None:
        job.procs.discard(p)
    th.join(timeout=2)
    return p.returncode, "".join(err_lines[-30:])


# ---------------------------------------------------------------- işler
class Job:
    def __init__(self, kind, title):
        self.id = new_id("j")
        self.kind = kind
        self.title = title
        self.progress = 0.0
        self.status = "bekliyor"   # bekliyor | calisiyor | bitti | hata
        self.message = "Sırada..."
        self.result = None
        self.created = time.time()
        self.cancelled = False
        self.paused = False
        self.procs = set()          # çalışan alt süreçler (duraklat / iptal için)
        self.pause_total = 0.0
        self.pause_t = None
        self.extra = {}             # arayüz için: kalan süre, geçen süre, parça...
        self.eta_at = None

    def set(self, progress=None, message=None):
        if progress is not None:
            self.progress = max(0.0, min(1.0, float(progress)))
        if message is not None:
            self.message = message

    def active_time(self, since):
        """since'ten beri duraklatmalar hariç geçen süre."""
        pz = self.pause_total + ((time.time() - self.pause_t) if self.pause_t else 0)
        return max(0.0, time.time() - since - pz)

    def pause(self, on=True):
        if on == self.paused or self.status not in ("calisiyor", "bekliyor"):
            return
        self.paused = on
        if on:
            self.pause_t = time.time()
        else:
            if self.pause_t:
                self.pause_total += time.time() - self.pause_t
            self.pause_t = None
        for p in list(self.procs):
            proc_pause(p, on)

    def cancel(self):
        self.cancelled = True
        if self.paused:
            self.pause(False)
        for p in list(self.procs):
            try:
                p.kill()
            except Exception:
                pass

    def wait_if_paused(self):
        while self.paused and not self.cancelled and not SHUTTING_DOWN:
            time.sleep(0.25)

    def to_dict(self):
        ex = dict(self.extra)
        if "eta" in ex and self.eta_at:
            ex["eta"] = max(0, ex["eta"] - (0 if self.paused else (time.time() - self.eta_at)))
        if "t0" in ex:
            ex["elapsed"] = self.active_time(ex.pop("t0"))
        return {"id": self.id, "kind": self.kind, "title": self.title,
                "progress": round(self.progress, 4), "status": self.status,
                "message": self.message, "result": self.result, "created": self.created,
                "paused": self.paused, "extra": ex}


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
        self.gpu_lock = threading.Lock()   # altyazı ve dışa aktarma sırayla

    def start(self, kind, title, fn, *args, heavy=False, **kw):
        job = Job(kind, title)
        with self.lock:
            self.jobs[job.id] = job
            # eski bitmiş işleri temizle
            done = [j for j in self.jobs.values() if j.status in ("bitti", "hata")]
            for j in sorted(done, key=lambda j: j.created)[:-25]:
                self.jobs.pop(j.id, None)

        def _run():
            try:
                if heavy:
                    job.message = "Sırada bekliyor..."
                    with self.gpu_lock:
                        job.status = "calisiyor"
                        job.result = fn(job, *args, **kw)
                else:
                    job.status = "calisiyor"
                    job.result = fn(job, *args, **kw)
                job.status = "bitti"
                job.progress = 1.0
                if job.message in ("Sırada...", "Sırada bekliyor..."):
                    job.message = "Tamamlandı"
            except Exception as e:  # noqa
                traceback.print_exc()
                job.status = "hata"
                job.message = str(e) or e.__class__.__name__
        threading.Thread(target=_run, daemon=True).start()
        return job

    def list(self):
        with self.lock:
            return [j.to_dict() for j in sorted(self.jobs.values(), key=lambda j: j.created)]

    def get(self, jid):
        return self.jobs.get(jid)


JOBS = JobManager()
