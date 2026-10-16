"""把 cache/year_*.json 归并成结构化数据集 data/anime.json。

地区/题材来自 bangumi 的 meta_tags（日本/中国/韩国/欧美 + 漫画改/小说改/原创 + 题材词）。
"""
from __future__ import annotations
import json, pathlib, re, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"

REGIONS = {
    "日本": "jp", "中国": "cn", "中国大陆": "cn", "国产": "cn", "国漫": "cn",
    "韩国": "kr", "美国": "us", "欧美": "west", "欧洲": "west", "法国": "west",
    "英国": "west", "加拿大": "west", "台湾": "tw", "其他地区": "other",
}
SOURCE_TAGS = {"漫画改", "小说改", "轻小说改", "游戏改", "原创", "动画衍生", "四格漫画",
               "同人作品", "短片", "其它", "剧场版", "OVA", "TV"}
QUARTER = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4, 11: 4, 12: 4}
Q_NAME = {1: "冬", 2: "春", 3: "夏", 4: "秋"}


def info(infobox, key):
    for x in infobox or []:
        if isinstance(x, dict) and x.get("key") == key:
            v = x.get("value")
            if isinstance(v, str):
                return v.strip()
            if isinstance(v, list):
                return " / ".join(str(i.get("v", i)) if isinstance(i, dict) else str(i) for i in v)
    return None


def derive_month(it, path_hint):
    d = it.get("date")
    m = None
    if d and re.match(r"\d{4}-\d{2}-\d{2}", d):
        m = int(d[5:7])
    if m is None:
        bs = info(it.get("infobox"), "放送开始") or info(it.get("infobox"), "首播")
        mm = re.search(r"\d{4}年(\d{1,2})月", bs or "")
        m = int(mm.group(1)) if mm else path_hint
    return m


def build(year_months=None):
    """year_months: {(year,month): [items]} 若给出则用桶月份兜底。"""
    items_by_id = {}
    bucket_month = {}
    for fp in sorted(CACHE.glob("year_*.json")):
        year = int(fp.stem.split("_")[1])
        for it in json.load(fp.open(encoding="utf-8")):
            items_by_id.setdefault(it["id"], it)
            bucket_month.setdefault(it["id"], (year, None))
    if year_months:
        for (y, m), lst in year_months.items():
            for it in lst:
                items_by_id.setdefault(it["id"], it)
                bucket_month[it["id"]] = (y, m)

    rows = []
    for sid, it in items_by_id.items():
        bt = bucket_month.get(sid, (None, None))
        infobox = it.get("infobox") or []
        mt = [t for t in (it.get("meta_tags") or [])]
        region_codes = {REGIONS[t] for t in mt if t in REGIONS}
        if not region_codes:
            name = it.get("name") or ""
            tagset = {t["name"] for t in (it.get("tags") or [])}
            if re.search(r"[\uac00-\ud7a3\u1100-\u11ff]", name):
                region = "kr"
            elif re.search(r"[\u3040-\u30ff]", name):
                region = "jp"                      # 有假名 → 日本（含 Disney 日本短篇等）
            elif tagset & {"国产", "国漫", "中国", "中国大陆", "动态漫画"}:
                region = "cn"
            elif tagset & {"欧美", "美国", "英国", "法国", "加拿大", "日本动画"}:
                region = "west" if "日本动画" not in tagset else "jp"
            elif re.search(r"[\u4e00-\u9fff]", name) and not it.get("name_cn"):
                region = "cn"                      # 纯中文标题且无译名 → 国创
            elif re.fullmatch(r"[A-Za-z0-9 .:!'&\-–—?]+", name):
                region = "west"                    # 纯拉丁标题 → 非日番概率高
            else:
                region = "unk"
        else:
            region = "jp" if "jp" in region_codes else sorted(region_codes)[0]
        month = derive_month(it, bt[1])
        tags = [(t["name"], t.get("count", 0)) for t in (it.get("tags") or [])]
        tags.sort(key=lambda x: -x[1])
        genres = list(dict.fromkeys(t for t in mt if t not in REGIONS and t not in SOURCE_TAGS and t != "TV"))
        eps = it.get("total_episodes") or it.get("eps")
        if not eps:
            s = info(infobox, "话数")
            eps = int(re.sub(r"\D", "", s)[:3]) if s and re.sub(r"\D", "", s) else None
        rows.append({
            "id": sid,
            "name": it.get("name") or "",
            "cn": it.get("name_cn") or "",
            "date": it.get("date") or "",
            "year": int(it["date"][:4]) if it.get("date") else bt[0],
            "month": month,
            "q": QUARTER.get(month or 0, None),
            "eps": eps,
            "score": (it.get("rating") or {}).get("score"),
            "raters": (it.get("rating") or {}).get("total"),
            "rank": (it.get("rating") or {}).get("rank"),
            "region": region,
            "source": next((t for t in mt if t in ("漫画改", "小说改", "轻小说改", "游戏改", "原创", "动画衍生", "四格漫画", "同人作品")), None),
            "genres": genres,
            "tags": [t for t, c in tags[:10]],
            "studio": info(infobox, "製作") or info(infobox, "动画制作") or info(infobox, "制作公司"),
            "station": info(infobox, "播放电视台"),
            "weekday": info(infobox, "放送星期"),
            "dur": info(infobox, "单集时长") or info(infobox, "每集长度"),
            "nsfw": bool(it.get("nsfw")),
            "cover": it.get("images", {}).get("common") or it.get("images", {}).get("large") or "",
        })
    rows.sort(key=lambda r: (-(r["year"] or 0), r["q"] or 9, -(r["raters"] or 0)))
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = build()
    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    (out / "anime.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("总条目:", len(rows))
    print("地区:", collections.Counter(r["region"] for r in rows).most_common())
    print("年份覆盖:", min(r["year"] for r in rows if r["year"]), "-", max(r["year"] for r in rows if r["year"]))
    print("无季度:", sum(1 for r in rows if not r["q"]), "| 无封面:", sum(1 for r in rows if not r["cover"]))
    by_year = collections.Counter(r["year"] for r in rows)
    print("每年:", {y: by_year[y] for y in sorted(by_year)})
    print("日本条目每年:", {y: sum(1 for r in rows if r["year"] == y and r["region"] == "jp") for y in sorted(by_year)})


if __name__ == "__main__":
    main()
