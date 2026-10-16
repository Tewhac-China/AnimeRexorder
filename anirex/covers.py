"""下载封面到 covers/，只下日本条目(+未判定)，可断点续跑。

用法: python -m anirex.covers [--workers 8] [--include-nonjp]
"""
from __future__ import annotations
import argparse, json, pathlib, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from anirex.net import Net

ROOT = pathlib.Path(__file__).resolve().parent.parent
COVERS = ROOT / "web" / "covers"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--include-nonjp", action="store_true")
    ap.add_argument("--proxy", default=None)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    rows = json.load((ROOT / "data" / "anime.json").open(encoding="utf-8"))
    if args.include_nonjp:
        todo = rows
    else:
        todo = [r for r in rows if r["region"] in ("jp", "unk", "unk_cn?")]
    todo = [r for r in todo if r["cover"].startswith("http")]
    COVERS.mkdir(exist_ok=True)

    done = {int(p.stem) for p in COVERS.glob("*.jpg") if p.stat().st_size > 2000}
    todo = [r for r in todo if r["id"] not in done]
    print(f"待下载 {len(todo)} / 已有 {len(done)}", flush=True)

    # 每个线程一个连接池，避免单 session 争用
    nets = [Net(proxy=args.proxy) for _ in range(args.workers)]

    def fetch(i, r):
        net = nets[i % len(nets)]
        fp = COVERS / f"{r['id']}.jpg"
        try:
            b = net.get_bytes(r["cover"], timeout=25, retries=5)
            if len(b) < 1500:
                raise ValueError(f"too small {len(b)}")
            fp.write_bytes(b)
            return True, None
        except Exception as e:
            return False, {"id": r["id"], "url": r["cover"], "err": str(e)[:150]}

    t0 = time.time()
    ok, fails = 0, []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch, i, r): r for i, r in enumerate(todo)}
        for n, f in enumerate(as_completed(futs), 1):
            good, err = f.result()
            ok += good
            if err:
                fails.append(err)
            if n % 100 == 0 or n == len(futs):
                el = time.time() - t0
                print(f"  {n}/{len(futs)} ok={ok} fail={len(fails)} {el:.0f}s "
                      f"({n/el:.1f}/s, eta {(len(futs)-n)*el/n:.0f}s)", flush=True)
    (ROOT / "data" / "cover_failures.json").write_text(json.dumps(fails, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE ok={ok} fail={len(fails)} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
