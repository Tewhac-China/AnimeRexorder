"""本地接收服务：让浏览器把爬到的页面/图片 POST 回来落盘（大内容不经过对话上下文）。

用法: python -m club.sink [port]        默认 8788
接口: POST /save?path=<相对路径>   body=任意字节 → 写入 raw/<path>
      GET  /ping                    → ok
"""
from __future__ import annotations
import http.server, os, pathlib, socketserver, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent / "meifang-club"


class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/file":
            rel = urllib.parse.parse_qs(u.query).get("path", [""])[0].replace("..", "_")
            fp = pathlib.Path(__file__).resolve().parent.parent / rel
            if fp.exists():
                body = fp.read_bytes()
                self.send_response(200); self._cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers(); self.wfile.write(body)
            else:
                self.send_response(404); self._cors(); self.end_headers()
            return
        self.send_response(200); self._cors(); self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self):
        q = urllib.parse.urlparse(self.path).query
        rel = urllib.parse.parse_qs(q).get("path", ["stdout.txt"])[0]
        rel = rel.replace("..", "_").lstrip("/\\")
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        fp = ROOT / "raw" / rel if not rel.startswith("albums/") else ROOT / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_bytes(data)
        self.send_response(200); self._cors()
        self.send_header("Content-Type", "text/plain"); self.end_headers()
        self.wfile.write(f"saved {fp} {len(data)}B".encode("utf-8"))
        print(f"saved {rel}  {len(data):,} bytes", flush=True)

    def log_message(self, *a):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8788
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "raw").mkdir(exist_ok=True)
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), H) as s:
        print(f"sink on http://127.0.0.1:{port}  root={ROOT}", flush=True)
        s.serve_forever()


if __name__ == "__main__":
    main()
