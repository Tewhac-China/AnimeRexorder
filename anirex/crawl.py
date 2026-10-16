"""按 (年, 月) 分桶抓取 bangumi TV 动画条目，缓存到 cache/pages/ 可断点续跑。

用法:
    python -m anirex.crawl              # 2006-2025 全量
    python -m anirex.crawl --years 2024-2025
"""
from __future__ import annotations
import argparse, json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from anirex.net import Net

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "pages"
API = "https://api.bgm.tv/v0/subjects"


def bucket_file(year: int, month: int, page: int) -> pathlib.Path:
    return CACHE / f"{year:04d}-{month:02d}_p{page}.json"


def crawl_bucket(net: Net, year: int, month: int, log) -> list[dict]:
    """返回该月全部条目；分页直到取空。"""
    items, page = [], 1
    seen_ids = set()
    while True:
        fp = bucket_file(year, month, page)
        if fp.exists():
            data = json.loads(fp.read_text(encoding="utf-8"))
        else:
            data = net.get_json(API, params={
                "type": 2, "cat": 1, "year": year, "month": month,
                "limit": 100, "page": page,
            })
            fp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            time.sleep(0.15)
        batch = data.get("data") or []
        if not batch:
            break
        for it in batch:
            if it["id"] not in seen_ids:
                seen_ids.add(it["id"])
                items.append(it)
        if len(batch) < 100:
            break
        page += 1
        if page > 6:      # 安全阀：单月不可能超 600 条
            break
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2006-2025")
    ap.add_argument("--interval", type=float, default=1.1, help="API 请求间隔秒(限速用)")
    args = ap.parse_args()
    y0, y1 = (args.years.split("-") + [""])[:2]
    y0, y1 = int(y0), int(y1 or y0)

    CACHE.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "cache" / "crawl.log"
    net = Net(min_interval=args.interval)

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    log(f"start crawl {y0}-{y1}, proxy={net.s.proxies}")
    summary = {}
    t0 = time.time()
    for year in range(y0, y1 + 1):
        year_items = {}
        for month in range(1, 13):
            try:
                items = crawl_bucket(net, year, month, log)
            except Exception as e:
                log(f"  !! {year}-{month:02d} FAILED: {str(e)[:160]}")
                # 失败时清掉该月缓存，下次重跑
                for f in CACHE.glob(f"{year:04d}-{month:02d}_p*.json"):
                    f.unlink()
                continue
            for it in items:
                year_items[it["id"]] = it
            summary[f"{year}-{month:02d}"] = len(items)
        (ROOT / "cache" / f"year_{year}.json").write_text(
            json.dumps(list(year_items.values()), ensure_ascii=False), encoding="utf-8")
        log(f"year {year}: {len(year_items)} 条 (月度累计 {sum(summary.get(f'{year}-{m:02d}',0) for m in range(1,13))})")
    log(f"DONE in {time.time()-t0:.0f}s, total years cached")


if __name__ == "__main__":
    main()
