"""Donanım koruması: ağır işler sırasında ekran kartını ve işlemciyi korur.

- Ekran kartı (NVIDIA) ve işlemci sıcaklığını birkaç saniyede bir okur.
- Sınır aşılırsa ağır işleri dondurur, soğuyunca kendiliğinden devam ettirir.
- "Sessiz" modda işler aralıklarla dinlenir, işlemci çekirdeklerinin yarısı kullanılır.
- Alt süreçler düşük öncelikte çalışır: bilgisayar donmaz, diğer programlar akıcı kalır.
"""
import glob
import os
import shutil
import subprocess
import sys
import threading
import time

from core import IS_WIN, JOBS, NO_WINDOW, load_settings

MODES = {
    "sessiz": {"gpu": 72, "cpu": 85, "run": 50, "rest": 15, "ad": "Sessiz"},
    "dengeli": {"gpu": 80, "cpu": 90, "run": 0, "rest": 0, "ad": "Dengeli"},
    "tam": {"gpu": 86, "cpu": 95, "run": 0, "rest": 0, "ad": "Tam güç"},
}
_seen = [0.0]   # arayüz en son ne zaman sıcaklığa baktı (canlı takip)
STATE = {"gpu_ad": None, "gpu_temp": None, "gpu_util": None, "cpu_temp": None, "soguma": False, "dinlenme": False, "son": 0}
_lock = threading.Lock()
_started = False
_cpu_ok = None   # işlemci sıcaklığı okunabiliyor mu (None: henüz denenmedi)
_smi_path = None


def cfg():
    k = load_settings().get("koruma") or {}
    mod = k.get("mod") if k.get("mod") in MODES else "dengeli"
    m = dict(MODES[mod])
    m["mod"] = mod
    try:
        if k.get("gpu_limit"):
            m["gpu"] = max(60, min(90, int(k["gpu_limit"])))
    except (TypeError, ValueError):
        pass
    return m


# ---------------------------------------------------------------- iş yükü ayarları (diğer modüller sorar)
def ffmpeg_threads():
    if cfg()["mod"] == "sessiz":
        return max(2, (os.cpu_count() or 4) // 2)
    return 0


def ai_threads():
    return "1:1:1" if cfg()["mod"] == "sessiz" else ""


def ai_tile():
    return 200 if cfg()["mod"] == "sessiz" else 0


def low_priority():
    return cfg()["mod"] != "tam"


# ---------------------------------------------------------------- sensörler
def _smi():
    global _smi_path
    if _smi_path is None:
        cands = [shutil.which("nvidia-smi") or ""]
        if IS_WIN:
            cands += [r"C:\Windows\System32\nvidia-smi.exe", r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"]
        _smi_path = next((c for c in cands if c and os.path.exists(c)), "")
    return _smi_path


def read_gpu():
    exe = _smi()
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "--query-gpu=temperature.gpu,utilization.gpu,name", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=5, creationflags=NO_WINDOW)
        line = (r.stdout or "").strip().splitlines()
        if r.returncode != 0 or not line:
            return None
        # birden çok kart varsa en sıcağı
        best = None
        for ln in line:
            p = [x.strip() for x in ln.split(",")]
            t, u = float(p[0]), float(p[1]) if p[1].replace(".", "").isdigit() else None
            if best is None or t > best[0]:
                best = (t, u, ",".join(p[2:]))
        return best
    except Exception:
        return None


def read_cpu():
    global _cpu_ok
    if _cpu_ok is False:
        return None
    try:
        if IS_WIN:
            r = subprocess.run(["powershell", "-NoProfile", "-Command",
                                "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop | "
                                "Measure-Object -Property CurrentTemperature -Maximum).Maximum"],
                               capture_output=True, text=True, timeout=8, creationflags=NO_WINDOW)
            v = float((r.stdout or "").strip() or 0)
            t = v / 10 - 273.15 if v > 0 else None
        else:
            vals = []
            for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
                try:
                    vals.append(int(open(f).read().strip()) / 1000)
                except Exception:
                    pass
            t = max(vals) if vals else None
        if t is None or not (5 < t < 125):
            _cpu_ok = False
            return None
        _cpu_ok = True
        return round(t)
    except Exception:
        _cpu_ok = False
        return None


# ---------------------------------------------------------------- iş dondurma
def _heavy_jobs():
    with JOBS.lock:
        return [j for j in JOBS.jobs.values() if getattr(j, "heavy", False) and j.status == "calisiyor"]


def _hold(job, why):
    if not getattr(job, "guard", None):
        if job.paused:  # kullanıcı zaten duraklattı: dokunma
            return
        job.guard = {"msg": job.message}
        job.pause(True)
    job.message = why


def _release(job):
    g = getattr(job, "guard", None)
    if not g:
        return
    job.guard = None
    job.pause(False)
    job.message = g["msg"]


def _loop():
    hot_since = None
    peak = 0
    run_since = None
    rest_until = 0
    last_cpu = 0
    while True:
        try:
            jobs = _heavy_jobs()
            c = cfg()
            busy = bool(jobs)
            watching = time.time() - _seen[0] < 10
            g = read_gpu() if (busy or watching or time.time() - STATE["son"] > 20) else None
            if g:
                STATE["gpu_temp"], STATE["gpu_util"], STATE["gpu_ad"] = g
            if (busy or watching) and time.time() - last_cpu > (10 if IS_WIN else 3):
                last_cpu = time.time()
                STATE["cpu_temp"] = read_cpu()
            STATE["son"] = time.time()
            gt, ct = STATE["gpu_temp"] if g else None, STATE["cpu_temp"]
            hot = (gt is not None and gt >= c["gpu"]) or (ct is not None and ct >= c["cpu"])
            now = time.time()
            # kullanıcı devam ettirdiyse koruma bayrağını bırak (ama hâlâ sıcaksa yine dinlendir)
            for j in jobs:
                if getattr(j, "guard", None) and not j.paused:
                    j.message, j.guard = j.guard["msg"], None
            if not busy:
                hot_since, run_since, STATE["soguma"], STATE["dinlenme"] = None, None, False, False
            elif STATE["soguma"]:
                peak = max(peak, gt or 0, ct or 0)
                cool = ((gt is None or gt <= c["gpu"] - 8) and (ct is None or ct <= c["cpu"] - 8))
                # sensör hiç düşmüyorsa (ortam sıcak): zirveden 8 derece inince ya da 4 dk sonra devam
                if cool or (peak and max(gt or 0, ct or 0) <= peak - 8) or now - hot_since > 240:
                    STATE["soguma"] = False
                    for j in jobs:
                        _release(j)
                else:
                    for j in jobs:
                        _hold(j, f"🌡 Donanım dinleniyor ({_temps(gt, ct)}). Soğuyunca kendiliğinden devam edecek...")
            elif hot:
                STATE["soguma"], hot_since, peak = True, now, max(gt or 0, ct or 0)
                for j in jobs:
                    _hold(j, f"🌡 Donanım çok ısındı ({_temps(gt, ct)}). Soğuması bekleniyor...")
            elif c["run"]:
                # sessiz mod: belirli aralıklarla kısa mola
                if STATE["dinlenme"]:
                    if now >= rest_until:
                        STATE["dinlenme"], run_since = False, now
                        for j in jobs:
                            _release(j)
                else:
                    run_since = run_since or now
                    if now - run_since >= c["run"]:
                        STATE["dinlenme"], rest_until = True, now + c["rest"]
                        for j in jobs:
                            _hold(j, "😌 Sessiz mod: kısa mola (donanım dinleniyor)...")
            else:
                run_since = None
                if STATE["dinlenme"]:
                    STATE["dinlenme"] = False
                    for j in jobs:
                        _release(j)
            # yeni başlayan alt süreçleri düşük önceliğe al
            if busy and low_priority():
                for j in jobs:
                    for p in list(j.procs):
                        _lower(p)
        except Exception:
            pass
        time.sleep(2 if time.time() - _seen[0] < 10 else 3 if _heavy_jobs() else 6)


def _temps(gt, ct):
    p = []
    if gt is not None:
        p.append(f"ekran kartı {round(gt)}°C")
    if ct is not None:
        p.append(f"işlemci {round(ct)}°C")
    return ", ".join(p) or "sıcaklık yüksek"


_lowered = set()


def _lower(p):
    if p.pid in _lowered or p.poll() is not None:
        return
    _lowered.add(p.pid)
    try:
        if IS_WIN:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x0200 | 0x0400, False, p.pid)  # SET_INFORMATION | QUERY
            if h:
                ctypes.windll.kernel32.SetPriorityClass(h, 0x4000)  # BELOW_NORMAL
                ctypes.windll.kernel32.CloseHandle(h)
        else:
            os.setpriority(os.PRIO_PROCESS, p.pid, 10)
    except Exception:
        pass


def start():
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, daemon=True, name="koruma").start()


def status():
    _seen[0] = time.time()
    c = cfg()
    return {"mod": c["mod"], "gpu_limit": c["gpu"], "cpu_limit": c["cpu"], "gpu_ad": STATE["gpu_ad"], "gpu_temp": STATE["gpu_temp"],
            "gpu_util": STATE["gpu_util"], "cpu_temp": STATE["cpu_temp"], "soguma": STATE["soguma"], "dinlenme": STATE["dinlenme"], "okuma": STATE["son"],
            "sensor": bool(_smi()) or bool(_cpu_ok)}
