"""统一网络层：走本地代理，带重试/退避/限速，抗代理抖动。"""
from __future__ import annotations
import os, time, random, threading
import requests


class Net:
    def __init__(self, proxy: str | None = None, min_interval: float = 0.0,
                 ua: str = "AnimeRexorder/0.1 (personal anime stats collection)"):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": ua, "Accept": "application/json"})
        px = proxy or os.environ.get("BGMPROXY") or self._autodetect_proxy()
        if px:
            self.s.proxies = {"http": px, "https": px}
        self._lock = threading.Lock()
        self._last = 0.0
        self.min_interval = min_interval
        self._silence_proxy_warn = False

    @staticmethod
    def _autodetect_proxy() -> str | None:
        """探测本地常见代理端口，找到就用。"""
        for port in (7897, 7890, 10809, 7891, 8118, 10808):
            import socket
            s = socket.socket()
            s.settimeout(0.25)
            try:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return f"http://127.0.0.1:{port}"
            finally:
                s.close()
        env = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        return env

    def request(self, method: str, url: str, *, retries: int = 8, timeout: int = 30, **kw):
        last = None
        for attempt in range(retries):
            self._throttle()
            try:
                r = self.s.request(method, url, timeout=timeout, **kw)
            except requests.RequestException as e:
                last = e
                self._sleep_backoff(attempt)
                continue
            if r.status_code == 429:
                ra = r.headers.get("Retry-After")
                self._sleep_backoff(attempt, extra=float(ra) if ra and ra.isdigit() else 0)
                last = RuntimeError("429")
                continue
            if r.status_code >= 500:
                last = RuntimeError(f"{r.status_code}")
                self._sleep_backoff(attempt)
                continue
            return r
        raise RuntimeError(f"request failed after {retries} tries: {url} ({last})")

    def get_json(self, url, **kw):
        r = self.request("GET", url, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code} {url}: {r.text[:200]}")
        return r.json()

    def get_bytes(self, url, **kw):
        r = self.request("GET", url, **kw)
        r.raise_for_status()
        return r.content

    def post_json(self, url, **kw):
        r = self.request("POST", url, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code} {url}: {r.text[:200]}")
        return r.json()

    def _throttle(self):
        if self.min_interval <= 0:
            return
        with self._lock:
            wait = self.min_interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()

    @staticmethod
    def _sleep_backoff(attempt: int, extra: float = 0.0):
        time.sleep(min(60.0, (1.5 ** attempt) + extra + random.uniform(0, 0.6)))
