#!/usr/bin/env python3
import os, sys, socket, webbrowser, time, threading
from contextlib import closing
from streamlit.web import cli as stcli  # import ESTÁTICO garante que o PyInstaller inclua o streamlit

def _free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def _open_when_up(url, tries=60):
    import urllib.request
    for _ in range(tries):
        time.sleep(0.5)
        try:
            urllib.request.urlopen(url, timeout=0.5)
            webbrowser.open(url)
            return
        except Exception:
            pass

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    print(f"➡️  Subindo Streamlit em {url}", flush=True)

    threading.Thread(target=_open_when_up, args=(url,), daemon=True).start()

    sys.argv = [
        "streamlit", "run", "app.py",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--browser.gatherUsageStats=false",
    ]
    sys.exit(stcli.main())
