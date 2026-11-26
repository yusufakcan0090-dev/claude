"""Kesit Studyosu kurulum yardımcısı: ffmpeg + altyazı modeli + GPU kontrolü."""
import io
import os
import sys
import warnings

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
warnings.filterwarnings("ignore")
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIN = ROOT / "bin"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"


def step(t):
    print("\n" + "=" * 60 + f"\n  {t}\n" + "=" * 60, flush=True)


def ffmpeg():
    step("1/3  FFmpeg (video motoru)")
    BIN.mkdir(exist_ok=True)
    if (BIN / "ffmpeg.exe").exists() and (BIN / "ffprobe.exe").exists():
        print("  Zaten kurulu.")
        return True
    try:
        print("  Indiriliyor (~200 MB)...")
        with urllib.request.urlopen(FFMPEG_URL, timeout=60) as r:
            total = int(r.headers.get("Content-Length") or 0)
            buf = io.BytesIO()
            done = 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                buf.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  %{done * 100 // total}  ({done >> 20} / {total >> 20} MB)", end="", flush=True)
        print()
        with zipfile.ZipFile(buf) as z:
            for n in z.namelist():
                name = n.rsplit("/", 1)[-1]
                if name in ("ffmpeg.exe", "ffprobe.exe"):
                    (BIN / name).write_bytes(z.read(n))
        print("  FFmpeg hazir.")
        return True
    except Exception as e:
        print("  HATA: FFmpeg indirilemedi:", e)
        print("  Internet baglantini kontrol edip KUR.bat'i tekrar calistir.")
        return False


def gpu():
    step("2/3  Ekran karti kontrolu")
    try:
        sys.path.insert(0, str(ROOT / "app"))
        from transcribe import _add_cuda_dlls
        _add_cuda_dlls()
        import ctranslate2
        n = ctranslate2.get_cuda_device_count()
        if n:
            print(f"  NVIDIA ekran karti bulundu ({n}). Altyazi hizli calisacak.")
        else:
            print("  NVIDIA ekran karti bulunamadi. Altyazi islemciyle (daha yavas) calisacak.")
            print("  Ekran karti surucun eskiyse NVIDIA sitesinden guncellemen iyi olur.")
    except Exception as e:
        print("  Kontrol edilemedi:", e)


def model():
    step("3/3  Turkce altyazi modeli (ilk seferde ~3 GB)")
    try:
        from faster_whisper import download_model
        print("  Indiriliyor... (ilerleme gorunmeyebilir, pencereyi kapatma)", flush=True)
        download_model("large-v3")
        print("  Model hazir.")
        return True
    except Exception as e:
        print("  Model simdi indirilemedi:", e)
        print("  Sorun degil: ilk altyazida otomatik indirilecek.")
        return False


if __name__ == "__main__":
    ok = ffmpeg()
    gpu()
    model()
    print("\n" + ("KURULUM TAMAM!" if ok else "Kurulum eksik kaldi, yukaridaki hatalara bak."))
