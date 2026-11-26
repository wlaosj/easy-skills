import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from bbolt_parser import parse_cache_db

SOURCE_MODE = os.environ.get("SOURCE_MODE", "auto").strip().lower()  # auto | local | ssh
ROS_HOST = os.environ.get("ROS_HOST", "").strip()
ROS_PORT = os.environ.get("ROS_PORT", "22").strip()
ROS_USER = os.environ.get("ROS_USER", "admin").strip()
ROS_DB_PATH = os.environ.get("ROS_DB_PATH", "etc-mihomo/cache.db").strip()
SSH_KEY_PATH = os.environ.get("SSH_KEY_PATH", "/ssh/id_ed25519").strip()
LOCAL_DB_PATH = os.environ.get("LOCAL_DB_PATH", "/data/cache.db").strip()
SYNC_INTERVAL = int(os.environ.get("SYNC_INTERVAL", "60"))
PORT = int(os.environ.get("PORT", "8899"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML_PATH = os.path.join(BASE_DIR, "static", "index.html")


def _resolve_mode() -> str:
    if SOURCE_MODE in ("local", "ssh"):
        return SOURCE_MODE
    if ROS_HOST:
        return "ssh"
    return "local"


class CacheStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = None
        self.last_sync_at = 0
        self.last_sync_error = ""
        self.syncing = False
        self.mode = _resolve_mode()

    def _source_label(self) -> str:
        if self.mode == "local":
            return f"本地直读 ({LOCAL_DB_PATH})"
        return f"{ROS_HOST}:{ROS_PORT}"

    def sync_now(self) -> tuple[bool, str]:
        with self.lock:
            if self.syncing:
                return True, "sync_in_progress"
            self.syncing = True

        mode = self.mode
        err_msg = ""
        ok = False
        tmp_path = "/tmp/cache.db.tmp"
        target_db = LOCAL_DB_PATH if mode == "local" else "/tmp/cache.db"

        try:
            if mode == "local":
                if not os.path.isfile(LOCAL_DB_PATH):
                    err_msg = f"cache.db not found at {LOCAL_DB_PATH}"
                else:
                    parsed = parse_cache_db(LOCAL_DB_PATH)
                    with self.lock:
                        self.data = parsed
                        self.last_sync_at = int(time.time())
                        self.last_sync_error = ""
                    ok = True
            else:
                if not ROS_HOST:
                    err_msg = "ROS_HOST is not configured"
                else:
                    cmd = [
                        "scp",
                        "-q",
                        "-P",
                        ROS_PORT,
                        "-o",
                        "BatchMode=yes",
                        "-o",
                        "ConnectTimeout=6",
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "UserKnownHostsFile=/dev/null",
                        "-i",
                        SSH_KEY_PATH,
                        f"{ROS_USER}@{ROS_HOST}:{ROS_DB_PATH}",
                        tmp_path,
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if res.returncode != 0:
                        err_msg = (res.stderr or res.stdout or f"scp exit {res.returncode}").strip()
                    else:
                        os.replace(tmp_path, target_db)
                        parsed = parse_cache_db(target_db)
                        with self.lock:
                            self.data = parsed
                            self.last_sync_at = int(time.time())
                            self.last_sync_error = ""
                        ok = True
        except Exception as exc:
            err_msg = str(exc)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            with self.lock:
                if not ok and err_msg:
                    self.last_sync_error = err_msg
                self.syncing = False
        return ok, err_msg

    def get_payload(self) -> dict:
        with self.lock:
            sync_info = {
                "mode": self.mode,
                "ros_host": self._source_label(),
                "source_label": self._source_label(),
                "last_sync_at": self.last_sync_at,
                "last_sync_error": self.last_sync_error,
                "sync_interval": SYNC_INTERVAL,
            }
            if self.data is None:
                return {"ready": False, "sync": sync_info}
            out = dict(self.data)
            out["ready"] = True
            out["sync"] = sync_info
            return out


store = CacheStore()


def background_sync_loop():
    while True:
        store.sync_now()
        time.sleep(max(SYNC_INTERVAL, 15))


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            try:
                with open(INDEX_HTML_PATH, "rb") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(html)
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return

        if path == "/api/data":
            self._send_json(200, store.get_payload())
            return

        if path == "/health":
            self._send_json(200, {"status": "ok", "mode": store.mode, "last_sync_at": store.last_sync_at})
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/sync":
            ok, err = store.sync_now()
            payload = store.get_payload()
            payload["sync_triggered_ok"] = ok
            if err:
                payload["sync_triggered_error"] = err
            self._send_json(200 if ok else 502, payload)
            return
        self._send_json(404, {"error": "not found"})


def main():
    store.sync_now()
    t = threading.Thread(target=background_sync_loop, daemon=True)
    t.start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"Mihomo Smart Dashboard listening on 0.0.0.0:{PORT} (mode={store.mode})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
