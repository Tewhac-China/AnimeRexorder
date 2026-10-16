"""本地预览：python -m anirex.serve  →  http://127.0.0.1:8000

直接用浏览器双击 web/index.html 也能用；若发现勾选记录存不住（个别浏览器的
file:// 禁用 localStorage），就改用这个本地服务。
"""
import http.server, os, pathlib, socketserver, sys, webbrowser

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(ROOT / "web")
    with socketserver.TCPServer(("127.0.0.1", port), Quiet) as httpd:
        url = f"http://127.0.0.1:{port}/"
        print(f"AnimeRex → {url}  (Ctrl+C 停止)")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()


if __name__ == "__main__":
    main()
