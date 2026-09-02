#!/usr/bin/env python3
"""Launch the 5279 studio.

    python3 studio/app.py                 # serve and open the default browser
    python3 studio/app.py --window        # native window (pywebview) when available
    python3 studio/app.py --no-browser    # serve only
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import serve  # noqa: E402


def _free_port(host: str, preferred: int) -> int:
    for port in (preferred, *range(preferred + 1, preferred + 20)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex((host, port)) != 0:
                return port
    return preferred


def _wait_for(host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.15)
    return False


def run_window(host: str, port: int) -> None:
    """Serve in a thread and show the studio in a native window."""
    threading.Thread(target=serve, args=(host, port, False), daemon=True).start()
    url = f"http://{host}:{port}/"
    _wait_for(host, port)
    try:
        import webview  # pywebview: WKWebView on macOS
    except Exception:
        import webbrowser

        print(f"pywebview not installed; opening {url} in the browser", flush=True)
        webbrowser.open(url)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            return
    webview.create_window("5279 Studio", url, width=1560, height=980, min_size=(1100, 700), background_color="#121210")
    webview.start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kodak VISION 500T 5279 film studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--window", action="store_true", help="open a native application window")
    args = parser.parse_args()
    port = _free_port(args.host, args.port)
    if args.window:
        run_window(args.host, port)
    else:
        serve(args.host, port, not args.no_browser)
