"""生成前端数据 web/data.js（含本地封面可用性检测）。"""
from __future__ import annotations
import json, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


def main():
    rows = json.load((ROOT / "data" / "anime.json").open(encoding="utf-8"))
    have = {int(p.stem) for p in (WEB / "covers").glob("*.jpg")} if (WEB / "covers").exists() else set()
    out = []
    for r in rows:
        local = f"covers/{r['id']}.jpg" if r["id"] in have else None
        out.append({
            "i": r["id"], "n": r["name"], "c": r["cn"], "y": r["year"], "mo": r["month"],
            "d": r["date"],
            "q": r["q"], "e": r["eps"], "s": r["score"], "p": r["raters"], "rg": r["region"],
            "so": r["source"], "g": r["genres"][:4], "t": r["tags"][:6],
            "st": (r["studio"] or "")[:40] or None, "sta": (r["station"] or "")[:26] or None,
            "nf": r["nsfw"],
            "L": local, "U": r["cover"],
        })
    js = ("// 由 anirex/build_web.py 生成 @ " + time.strftime("%Y-%m-%d %H:%M") +
          "\nwindow.ANIME=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    (WEB / "data.js").write_text(js, encoding="utf-8")
    print("写出 web/data.js:", len(out), "条, 本地封面", len([o for o in out if o["L"]]), "张,",
          f"{len(js)/1e6:.2f} MB")


if __name__ == "__main__":
    main()
