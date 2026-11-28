"""B.E.K (Bul · Editle · Kalite) - başlatıcı."""
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# pythonw ile açılınca konsol yok: hataları dosyaya yaz
if sys.stdout is None or sys.stderr is None:
    _log = open(Path(__file__).resolve().parent.parent / "veri" / "log.txt", "a", encoding="utf-8", buffering=1) \
        if (Path(__file__).resolve().parent.parent / "veri").exists() else None
    if _log is None:
        (Path(__file__).resolve().parent.parent / "veri").mkdir(exist_ok=True)
        _log = open(Path(__file__).resolve().parent.parent / "veri" / "log.txt", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log

import logging  # noqa: E402
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # her isteği kayda yazmasın

import core
import server  # noqa: E402


def windows_fixes():
    """Görev çubuğu/pencere ikonu ve Masaüstü kısayolunun ikonunu düzelt (Windows)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Animeci.KesitStudyosu")
    except Exception:
        pass
    root = Path(__file__).resolve().parent.parent
    marker = root / "veri" / ".kisayol_v4"
    if marker.exists():
        return
    try:
        import subprocess
        import tempfile
        ico = root / "app" / "ui" / "bek_simge.ico"
        pyw = root / ".venv" / "Scripts" / "pythonw.exe"
        main_py = root / "app" / "main.py"
        ps = f"""
$desk = [Environment]::GetFolderPath('Desktop')
foreach ($o in @('Kesit Studyosu.lnk', 'Kesit Stüdyosu.lnk')) {{ $p = Join-Path $desk $o; if (Test-Path $p) {{ Remove-Item $p -Force }} }}
$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desk 'B.E.K.lnk'))
$s.TargetPath = '{pyw}'
$s.Arguments = '"{main_py}"'
$s.WorkingDirectory = '{root}'
$s.IconLocation = '{ico},0'
$s.Description = 'B.E.K - Bul, Editle, Kaliteyi artir'
$s.Save()
try {{ & "$env:SystemRoot\\System32\\ie4uinit.exe" -show }} catch {{}}
"""
        f = Path(tempfile.gettempdir()) / "ks_kisayol.ps1"
        f.write_text(ps, encoding="utf-8-sig")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(f)],
                       capture_output=True, timeout=30, creationflags=0x08000000)
        marker.write_text("ok")
    except Exception as e:
        print("Kısayol güncellenemedi:", e)


APP_ID = "Animeci.BEK"


def _app_id_process():
    """Görev çubuğu B.E.K'i Python olarak değil, kendi programı olarak tanısın."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception as e:
        print("Uygulama kimliği ayarlanamadı:", e)


def _taskbar_identity(hwnd):
    """Pencereye kimlik + yeniden açma komutu + simge ver: görev çubuğuna sabitleyince B.E.K logosu çıkar ve doğrudan programı açar."""
    import ctypes
    from ctypes import wintypes, c_void_p, byref, POINTER, Structure, c_ushort, c_ulong, c_wchar_p, HRESULT, WINFUNCTYPE

    class GUID(Structure):
        _fields_ = [("a", c_ulong), ("b", c_ushort), ("c", c_ushort), ("d", ctypes.c_ubyte * 8)]

    def guid(s):
        import uuid
        u = uuid.UUID(s)
        g = GUID(u.fields[0], u.fields[1], u.fields[2])
        g.d[:] = (ctypes.c_ubyte * 8).from_buffer_copy(u.bytes[8:])
        return g

    class PKEY(Structure):
        _fields_ = [("fmtid", GUID), ("pid", c_ulong)]

    class PROPVARIANT(Structure):
        _fields_ = [("vt", c_ushort), ("r1", c_ushort), ("r2", c_ushort), ("r3", c_ushort), ("val", c_wchar_p), ("pad", c_void_p)]

    fmt = guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3")
    iid = guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")  # IPropertyStore
    store = c_void_p()
    hr = ctypes.windll.shell32.SHGetPropertyStoreForWindow(wintypes.HWND(hwnd), byref(iid), byref(store))
    if hr != 0 or not store:
        raise OSError(f"SHGetPropertyStoreForWindow {hr:#x}")
    vtbl = ctypes.cast(ctypes.cast(store, POINTER(c_void_p))[0], POINTER(c_void_p))
    SetValue = WINFUNCTYPE(HRESULT, c_void_p, POINTER(PKEY), POINTER(PROPVARIANT))(vtbl[6])
    Commit = WINFUNCTYPE(HRESULT, c_void_p)(vtbl[7])
    Release = WINFUNCTYPE(c_ulong, c_void_p)(vtbl[2])
    root = Path(__file__).resolve().parent.parent
    pyw = root / ".venv" / "Scripts" / "pythonw.exe"
    if not pyw.exists():
        pyw = Path(sys.executable).with_name("pythonw.exe")
    ico = Path(__file__).resolve().parent / "ui" / "bek_simge.ico"
    keep = []
    # kimlik en son: Windows yeniden açma bilgilerini kimlik değişince okur
    for pid, text in ((2, f'"{pyw}" "{Path(__file__).resolve()}"'), (3, f"{ico},0"), (4, "B.E.K"), (5, APP_ID)):
        pv = PROPVARIANT(31, 0, 0, 0, c_wchar_p(text), None)  # VT_LPWSTR
        keep.append(pv)
        SetValue(store, byref(PKEY(fmt, pid)), byref(pv))
    Commit(store)
    Release(store)


def _set_window_icon(win):
    try:
        import time as _t
        from System import Action  # pythonnet (Windows)
        from System.Drawing import Icon
        ico = Icon(str(Path(__file__).resolve().parent / "ui" / "icon.ico"))
        for _ in range(50):
            if getattr(win, "native", None) is not None:
                break
            _t.sleep(0.1)
        form = win.native

        def _apply():
            form.Icon = ico
            try:
                _taskbar_identity(form.Handle.ToInt64())
            except Exception as e:
                print("Görev çubuğu kimliği ayarlanamadı:", e)
        form.Invoke(Action(_apply))
    except Exception as e:
        print("Pencere ikonu ayarlanamadı:", e)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _bind_drop(win):
    """Sürükle-bırak: dosyanın gerçek yolunu arayüze gönder."""
    if sys.platform.startswith("win"):
        _set_window_icon(win)
    try:
        import json
        from webview.dom import DOMEventHandler

        def on_drop(e):
            files = (e.get("dataTransfer") or {}).get("files") or []
            paths = [f.get("pywebviewFullPath") for f in files if f.get("pywebviewFullPath")]
            if paths:
                win.evaluate_js(f"KS.onDropPath({json.dumps(paths)})")
        win.dom.document.events.drop += DOMEventHandler(on_drop, True, True)
    except Exception as e:  # eski pywebview: arayüz dosyayı yükleyerek ekler
        print("Sürükle-bırak yolu alınamadı, yükleme yöntemi kullanılacak:", e)


def main():
    if sys.platform.startswith("win"):
        _app_id_process()
    threading.Thread(target=windows_fixes, daemon=True).start()
    port = free_port()
    th = threading.Thread(target=lambda: server.app.run(
        host="127.0.0.1", port=port, threaded=True, use_reloader=False), daemon=True)
    th.start()
    url = f"http://127.0.0.1:{port}/"
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    if "--tarayici" in sys.argv:
        webbrowser.open(url)
        th.join()
        return
    try:
        import webview
        win = webview.create_window("B.E.K", url, width=1480, height=900,
                                    min_size=(1180, 720), background_color="#0A0A12")
        server.WINDOW = win
        webview.start(_bind_drop, win, gui="edgechromium" if sys.platform.startswith("win") else None)
        core.shutdown()  # pencere kapandı: yarım işler diskte kalır, sonra devam edilir
    except Exception as e:
        print("Pencere açılamadı, tarayıcıda açılıyor:", e)
        webbrowser.open(url)
        th.join()


if __name__ == "__main__":
    main()
