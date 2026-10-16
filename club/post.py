"""抓取后的整理：清杂项、修 album.md、按证据判定秘封叙事、生成 index.md 总览。"""
from __future__ import annotations
import pathlib, re, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent / "meifang-club"
ALB = ROOT / "albums"
MEI = ("秘封", "梅莉", "マエリー", "莲子", "レンコ", "宇佐见", "玛艾露贝莉")


def dedupe_sections(path: pathlib.Path) -> None:
    """album.md 里 基本信息/曲目 会被内置表和区块正文各写一次 → 同名只留第一次。"""
    t = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(## .*)$", t)
    head, out, seen = parts[0], [], set()
    for i in range(1, len(parts), 2):
        name, body = parts[i], parts[i + 1]
        if name in seen:
            continue
        seen.add(name); out.append(name + body)
    new = head + "".join(out)
    if new != t:
        path.write_text(new, encoding="utf-8")


def field(md_text, key):
    m = re.search(r"\|\s*" + key + r"\s*\|\s*(.+?)\s*\|", md_text)
    return m.group(1) if m else ""


def story_text(d: pathlib.Path) -> str:
    parts = []
    for f in sorted(d.glob("story*.md")):
        parts.append(f.read_text(encoding="utf-8"))
    ab = d / "album.md"
    if ab.exists():
        t = ab.read_text(encoding="utf-8")
        m = re.search(r"## 附带故事(.*)$", t, re.S)
        parts.append(m.group(1) if m else "")
    return "\n".join(parts)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    removed = 0
    for p in ALB.glob("*/images/*蓬莱人形*"):
        p.unlink(); removed += 1
    fixed = 0
    for f in ALB.glob("*/album.md"):
        t = f.read_text(encoding="utf-8")
        n = re.sub(r"\n\| # 基本信息 \|\s*\|", "", t)
        if n != t:
            f.write_text(n, encoding="utf-8"); fixed += 1

    rows = []
    for d in sorted(p for p in ALB.iterdir() if p.is_dir()):
        if (d / "album.md").exists():
            dedupe_sections(d / "album.md")
        ab = (d / "album.md").read_text(encoding="utf-8") if (d / "album.md").exists() else ""
        st = story_text(d)
        tracks = len(re.findall(r"^\| \d+ \|", ab, re.M))
        imgs = len(list((d / "images").glob("*")))
        stories = len([p for p in d.glob("story*.md")])
        hit = [k for k in MEI if k in st or k in ab]
        rows.append({
            "dir": d.name, "title": field(ab, "制作方") and d.name.split("-", 1)[1],
            "date": field(ab, "发行日期"), "no": field(ab, "编号"),
            "tracks": tracks, "imgs": imgs, "stories": stories,
            "chars": len(st), "mei": bool(hit), "hit": hit[:3],
        })

    lines = ["# 秘封俱乐部 · THBWiki 专辑档案", ""]
    lines.append(f"数据源：[THBWiki（thwiki.cc）](https://thwiki.cc/)，用 browser-use 模拟浏览逐页抓取。")
    lines.append(f"抓取时间：{datetime.date.today().isoformat()}  ·  共 {len(rows)} 张专辑，"
                 f"{sum(r['tracks'] for r in rows)} 条曲目，{sum(r['imgs'] for r in rows)} 张图片，"
                 f"{sum(r['chars'] for r in rows):,} 字故事文本。")
    lines.append("")
    lines.append("每张专辑一个文件夹：`album.md`（基本信息+曲目+相关信息+其他信息）、"
                 "`story.md`/`story2.md`（附带故事与光盘扫图全文，日中对照）、`images/`（封面与 booklet 扫图）、"
                 "`page.html`/`story.html`（原始页面存档，可复核）、`links.txt`（来源链接）。")
    lines.append("")
    lines.append("| 专辑 | 发行日期 | 编号 | 曲目 | 故事子页 | 故事字数 | 图片 | 秘封叙事 | 目录 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        mark = "✔ " + "/".join(r["hit"][:2]) if r["mei"] else "—（同系列CD，正文无秘封角色）"
        lines.append(f"| {r['title']} | {r['date'][:11]} | {r['no']} | {r['tracks']} | {r['stories']} | "
                     f"{r['chars']:,} | {r['imgs']} | {mark} | [albums/{r['dir']}](albums/{r['dir']}/album.md) |")
    lines.append("")
    lines.append("## 说明与边界")
    lines.append("")
    lines.append("- **收录范围**：THBWiki 导航盒「官方音乐 › 独立音乐CD」中与秘封俱乐部相关的专辑，"
                 "以及同系列的两张单曲（未知之花·魅知之旅、虹色的北斗七星）——它们是否属于"
                 "「秘封专辑」可按上表证据自行判断。")
    lines.append("- **未收录**：`蓬莱人形`（ZUN 首张 CD，秘封俱乐部尚未登场，属对照项）。如需可再补抓。")
    lines.append("- **判定依据**：正文（附带故事或专辑页内联故事）是否出现 秘封/梅莉/莲子/宇佐见 等角色名。")
    lines.append("- **故事原文**：THBWiki 的 booklet 翻译以「日文｜中文」双列表格呈现，已原样保留为 Markdown 表格。")
    lines.append("- **缺图说明**：`灵长新益京` 的 booklet 扫图在 THBWiki 上只有占位文件（default_m.jpg，站点本身没上传），"
                 "已剔除；因此该张只有封面与一张内页图。`莲台野夜行` 站点上没有独立的「后记」子页，故只有 story.md。")
    lines.append("- **`# 基本信息` 之外的字段**（音轨数/总时长/售价等）都在各 album.md 的表格里。")
    (ROOT / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"清理杂项 {removed} 张，修 album.md {fixed} 个，专辑 {len(rows)} 张 → index.md")
    for r in rows:
        print(f"  {r['dir']:22s} 曲目{r['tracks']:2d} 故事{r['stories']}篇 {r['chars']:>6,}字 图{r['imgs']:2d} "
              f"{'秘封' if r['mei'] else '——'}")


if __name__ == "__main__":
    main()
