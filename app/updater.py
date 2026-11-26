"""Otomatik güncelleme: GitHub'daki 'kesit-studyosu' dalından yeni sürümü çeker.
veri/, .venv/ ve bin/ klasörlerine asla dokunmaz."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

from core import APP, ROOT, IS_WIN

REPO = "yusufakcan0090-dev/claude"
BRANCH = "kesit-studyosu"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/app/version.json"
ZIP = f"https://github.com/{REPO}/archive/refs/heads/{BRANCH}.zip"
PROTECTED = {"veri", ".venv", "bin", ".git", "__pycache__"}
UA = {"User-Agent": "KesitStudyosu-Updater", "Cache-Control": "no-cache"}

_cache = {"t": 0, "data": None}


def local_version():
    try:
        return json.loads((APP / "version.json").read_text("utf-8"))
    except Exception:
        return {"version": "1.0.0", "notes": []}


def _vt(v):
    out = []
    for p in str(v).split("."):
        try:
            out.append(int("".join(c for c in p if c.isdigit()) or 0))
        except ValueError:
            out.append(0)
    return tuple(out + [0] * (3 - len(out)))


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def check(force=False):
    if not force and _cache["data"] and time.time() - _cache["t"] < 600:
        return _cache["data"]
    cur = local_version()
    res = {"current": cur.get("version"), "latest": None, "available": False, "notes": []}
    try:
        remote = json.loads(_get(RAW + f"?t={int(time.time())}", 15))
        res["latest"] = remote.get("version")
        res["notes"] = remote.get("notes") or []
        res["available"] = _vt(remote.get("version")) > _vt(cur.get("version"))
    except Exception as e:
        res["error"] = str(e)
    _cache.update(t=time.time(), data=res)
    return res


def apply(job):
    job.set(0.02, "Güncelleme indiriliyor...")
    req = urllib.request.Request(ZIP, headers=UA)
    buf = io.BytesIO()
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            buf.write(chunk)
            done += len(chunk)
            if total:
                job.set(0.02 + 0.5 * done / total, f"İndiriliyor %{int(done * 100 / total)}")
    job.set(0.55, "Dosyalar açılıyor...")
    tmp = Path(tempfile.mkdtemp(prefix="ks_guncelle_"))
    try:
        with zipfile.ZipFile(buf) as z:
            z.extractall(tmp)
        roots = [p for p in tmp.iterdir() if p.is_dir()]
        if not roots or not (roots[0] / "app" / "main.py").exists():
            raise RuntimeError("Güncelleme paketi bozuk görünüyor")
        src = roots[0]
        # yeni paket gerekiyor mu?
        old_req = (ROOT / "requirements.txt").read_text("utf-8") if (ROOT / "requirements.txt").exists() else ""
        new_req = (src / "requirements.txt").read_text("utf-8") if (src / "requirements.txt").exists() else ""
        if new_req.strip() and new_req.strip() != old_req.strip():
            job.set(0.6, "Yeni paketler kuruluyor (biraz sürebilir)...")
            req_file = tmp / "requirements.txt"
            req_file.write_text(new_req, "utf-8")
            py = Path(sys.executable)
            if py.name.lower() == "pythonw.exe":
                py = py.with_name("python.exe")
            r = subprocess.run([str(py), "-m", "pip", "install", "-r", str(req_file)],
                               capture_output=True, text=True,
                               creationflags=0x08000000 if IS_WIN else 0)
            if r.returncode != 0:
                raise RuntimeError("Paketler kurulamadı: " + (r.stderr or r.stdout)[-300:])
        job.set(0.85, "Dosyalar yerleştiriliyor...")
        for item in src.iterdir():
            if item.name in PROTECTED:
                continue
            dest = ROOT / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(item, dest)
        new = local_version()
        _cache.update(t=0, data=None)
        job.set(1, f"Güncellendi: v{new.get('version')} — yeniden başlatılıyor")
        return {"version": new.get("version"), "restart": True}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def restart():
    """Programı yeniden başlatır (yeni sürüm yüklensin diye)."""
    def _go():
        time.sleep(0.6)
        flags = 0
        if IS_WIN:
            flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([sys.executable, str(APP / "main.py")], cwd=str(ROOT),
                         creationflags=flags, close_fds=True)
        time.sleep(0.4)
        os._exit(0)
    threading.Thread(target=_go, daemon=True).start()
