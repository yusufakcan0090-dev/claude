"""Kesit Stüdyosu - başlatıcı."""
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

import server  # noqa: E402


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _bind_drop(win):
    """Sürükle-bırak: dosyanın gerçek yolunu arayüze gönder."""
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
        win = webview.create_window("Kesit Stüdyosu", url, width=1480, height=900,
                                    min_size=(1180, 720), background_color="#0A0A12")
        server.WINDOW = win
        webview.start(_bind_drop, win, gui="edgechromium" if sys.platform.startswith("win") else None)
    except Exception as e:
        print("Pencere açılamadı, tarayıcıda açılıyor:", e)
        webbrowser.open(url)
        th.join()


if __name__ == "__main__":
    main()
