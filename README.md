<div align="center">

# AnimeRex · 我的日本动番档案

**2006 – 2025 每季日本 TV 动画 · 数据源 [bangumi.tv](https://bgm.tv)**

<br>

[![打开 Web UI · Open Live Site](https://img.shields.io/badge/%E2%96%B6%20%E6%89%93%E5%BC%80%20Web%20UI%20%C2%B7%20Open%20Live%20Site-6D28D9?style=for-the-badge&logo=githubpages&logoColor=white)](https://tewhac-china.github.io/AnimeRexorder/)

**👆 点这里直接在线使用，无需安装 · Click above to use it in the browser**

🔗 https://tewhac-china.github.io/AnimeRexorder/

<br>

![Static site](https://img.shields.io/badge/site-100%25_static-16a34a?style=flat-square)
![Entries](https://img.shields.io/badge/entries-6,023-2563eb?style=flat-square)
![JP titles](https://img.shields.io/badge/Japanese-4,173-0891b2?style=flat-square)
![Covers](https://img.shields.io/badge/local_covers-4,220-d97706?style=flat-square)
![No backend](https://img.shields.io/badge/backend-none-gray?style=flat-square)

[English ↓](#english)

</div>

---

## 中文

AnimeRex 是一个纯前端的番剧档案与追番标记工具。它把 bangumi.tv 上 2006 到 2025 年每季的日本 TV 动画条目抓到本地、清洗成一份结构化数据集，再用一个单页界面呈现出来：你可以按年份、季度、题材、改编来源、集数体量、评分、热度层层筛选，给每一部番打上「看过 / 在看 / 想看 / 弃番」，最后把清单导出成 Excel。

它不是一个在线服务，而是一份**自带数据、断网可用的个人档案**——所有标记只存在你浏览器的 localStorage 里，不会上传到任何地方。

### 功能

- **多维筛选**：年份（含全选 / 近 5 年 / 近 10 年快捷档）、季度（冬春夏秋冬）、题材、改编来源（漫画改 / 小说改 / 游戏改 / 原创 / 动画衍生）、集数体量（≤13 / 14–26 / 27–60 / >60）、评分下限、热度下限，另有「包含非日番」「包含 R18」两个开关。
- **四种标记状态**：左键点卡片 = 看过；右键（触屏长按）= 状态菜单，可选在看 / 想看 / 弃番 / 清除。支持批量标记与撤销。
- **撤销栈**：`Ctrl+Z` 回退上一次标记，批量操作也一并回退，最多 30 步。
- **三种视图密度**：网格 → 列表 → 海报，一键切换，深浅色主题。
- **统计面板**：标记进度、日番覆盖率等实时汇总。
- **导出 / 导入**：勾选清单或当前筛选结果导出为 `.xlsx`（含统计页），标记数据可导出 JSON 备份、换设备再导入。
- **可分享的筛选态**：筛选条件写进地址栏 `#` 之后，复制链接就是当前视图。
- **离线封面**：4,220 张封面已下载到仓库内，不依赖外部图床（bangumi 图床在部分网络环境下不可达）。

### 快捷键

| 键 | 作用 |
|---|---|
| 左键点卡片 | 标记 / 取消「看过」 |
| 右键 · 长按 | 打开状态菜单：在看 / 想看 / 弃番 / 清除 |
| `/` | 跳到搜索框，即时过滤（`Esc` 清空） |
| `V` | 切换视图密度：网格 → 列表 → 海报 |
| `T` | 深色 / 浅色主题 |
| `S` | 展开 / 收起统计面板 |
| `Ctrl+Z` | 撤销上一次标记（含批量） |
| `?` | 使用说明 |

### 数据规模

| 指标 | 数值 |
|---|---|
| 数据集条目总数 | 6,023 |
| 其中日本 TV 动画 | 4,173 |
| 时间跨度 | 2006 – 2025 |
| 有 bangumi 评分的日番 | 4,011 |
| 日番累计话数 | 83,693 |
| 出现过的制作公司 | 2,575 |
| 本地封面 | 4,220 张 |

字段包含：中日标题、开播日期、年份 / 月份 / 季度、总话数、评分与评分人数、地区、改编来源、题材标签、热门 tag、制作公司、播放电视台、放送星期、单集时长、NSFW 标记、封面。

### 快速开始

**在线用**：直接打开 https://tewhac-china.github.io/AnimeRexorder/

**本地跑**（任意静态服务器都行，甚至双击 `web/index.html` 也能开）：

```bash
git clone https://github.com/Tewhac-China/AnimeRexorder.git
cd AnimeRexorder
python -m anirex.serve        # → http://127.0.0.1:8000
```

> 用 `file://` 直接打开时，个别浏览器会禁用 localStorage 导致标记存不住；这种情况改用上面的本地服务。

### 数据管线

从零重建数据集需要四步（仓库里已经带好构建产物 `data/anime.json`、`web/data.js`、`web/covers/`，只想改 UI 的话跳过本节）：

```bash
pip install -r requirements.txt

python -m anirex.crawl                     # 按 (年,月) 分桶抓 Bangumi v0 列表 → cache/
python -m anirex.build                     # 归并清洗 → data/anime.json
python -m anirex.covers --workers 8        # 下载封面 → web/covers/<id>.jpg
python -m anirex.build_web                 # 生成前端数据 → web/data.js
```

实现上的几个取舍（踩过坑的地方写在代码注释里）：

- Bangumi 只有 `v0` 列表接口可用，且响应里**没有地区字段**，地区靠 `meta_tags` 判定；`cat=1` 的返回里约 30% 混着国创和欧美作品，因此用标题字符集（假名 / 谚文 / 纯拉丁）+ tag 兜底推断，推断不出标 `unk`。默认视图只显示日番，非日番需要手动勾选「包含非日番」。
- 抓取走统一网络层 `anirex/net.py`：自动探测本地代理端口、重试退避、限速，缓存分页文件可断点续跑。
- 前端不请求任何接口，数据一次性内联在 `data.js`（约 2.4 MB）。这样做的代价是首屏体积，换来的是零后端、零鉴权、任意静态托管都能跑。

### 目录结构

```
AnimeRexorder/
├── web/                    # ← GitHub Pages 站点根（纯静态，无构建步骤）
│   ├── index.html          #   全部 UI 与逻辑（单文件，含样式）
│   ├── data.js             #   前端数据，由 anirex/build_web.py 生成
│   ├── xlsx.js             #   轻量 xlsx 写出器（导出用）
│   └── covers/             #   4,220 张本地封面
├── anirex/                 # 数据管线
│   ├── net.py              #   代理 / 重试 / 限速网络层
│   ├── crawl.py            #   按年月分桶抓取 Bangumi
│   ├── build.py            #   清洗归并 → data/anime.json
│   ├── covers.py           #   封面下载
│   ├── build_web.py        #   生成 web/data.js
│   └── serve.py            #   本地预览服务
├── data/anime.json         # 结构化数据集（构建产物，已提交）
└── club/                   # 另一个抓取任务（秘封俱乐部）的脚本，与 UI 无关
```

### 部署

站点根目录是 `web/`，通过 GitHub Actions 官方 Pages 工作流部署：`push` 到 `main` 后自动上传 `web/` 并发布，通常 1–2 分钟内生效。配置见 `.github/workflows/pages.yml`，仓库 Settings → Pages 的 Build source 需设为 **GitHub Actions**。

### 数据与版权说明

- 元数据来自 [bangumi.tv](https://bgm.tv) 公开接口，卡片上的 `bgm` 链接可跳回原条目页。
- 封面图片版权归各作品版权方所有，仅作个人观看记录与识别用途，请勿用于商业用途或二次分发。
- 本项目为个人档案工具，非商业、无后端、不收集任何用户数据；标记记录只写入你自己浏览器的 localStorage。
- 数据快照抓于 2026-10，不会自动更新；重跑上面的数据管线即可刷新。

---

<a name="english"></a>

## English

**AnimeRex is a fully static anime archive and watch-tracking app.** It crawls every Japanese TV anime season from 2006 to 2025 out of [bangumi.tv](https://bgm.tv), cleans the raw responses into one structured dataset, and renders it as a single-page UI: filter by year, season, genre, source material, episode count, score and popularity, tag each title as *watched / watching / wishlist / dropped*, then export your list to Excel.

It is not a hosted service. It is a **self-contained, offline-capable personal archive** — every mark you make lives only in your browser's `localStorage`, nothing is uploaded.

### Features

- **Layered filtering** — year (with all / last 5 / last 10 shortcuts), cours (winter → autumn), genres, source material (manga / novel / game / original / spin-off), length buckets (≤13, 14–26, 27–60, >60), minimum score, minimum popularity, plus toggles for non-Japanese titles and NSFW.
- **Four states per title** — click a card for *watched*; right-click (or long-press on touch) opens a menu for *watching / wishlist / dropped / clear*. Batch marking supported.
- **Undo stack** — `Ctrl+Z` rolls back the last mark, including batches, up to 30 steps.
- **Three view densities** — grid → list → poster, with dark / light themes.
- **Live stats panel** — progress and coverage of your marks against the dataset.
- **Export / import** — selected or currently filtered titles to `.xlsx` (with a stats sheet); marks to JSON for backup and cross-device restore.
- **Shareable filter state** — filters are written to the URL hash, so copying the link copies the exact view.
- **Local covers** — 4,220 cover images ship inside the repo, so the UI never depends on an external image CDN.

### Keyboard

| Key | Action |
|---|---|
| Click card | Toggle *watched* |
| Right-click / long-press | State menu: watching / wishlist / dropped / clear |
| `/` | Jump to search (live filter, `Esc` clears) |
| `V` | Cycle view density: grid → list → poster |
| `T` | Dark / light theme |
| `S` | Toggle stats panel |
| `Ctrl+Z` | Undo last mark (batches included) |
| `?` | Help |

### Dataset at a glance

| Metric | Value |
|---|---|
| Total entries | 6,023 |
| Japanese TV anime | 4,173 |
| Year range | 2006 – 2025 |
| JP titles with a bangumi score | 4,011 |
| Total episodes tracked | 83,693 |
| Distinct studios | 2,575 |
| Bundled cover images | 4,220 |

Per-entry fields: original and Chinese titles, air date, year / month / cours, episode count, rating and rating count, region, source material, genre tags, top tags, studio, TV station, broadcast weekday, episode duration, NSFW flag, cover image.

### Quick start

**Online** — just open https://tewhac-china.github.io/AnimeRexorder/

**Locally** — any static server works; double-clicking `web/index.html` also works:

```bash
git clone https://github.com/Tewhac-China/AnimeRexorder.git
cd AnimeRexorder
python -m anirex.serve        # → http://127.0.0.1:8000
```

> Some browsers disable `localStorage` on `file://` origins, which silently drops your marks. Use the local server above if that happens.

### Rebuilding the data

The repo ships its build outputs (`data/anime.json`, `web/data.js`, `web/covers/`), so skip this section unless you want fresh data:

```bash
pip install -r requirements.txt

python -m anirex.crawl                     # crawl Bangumi v0 by (year, month) → cache/
python -m anirex.build                     # merge & clean → data/anime.json
python -m anirex.covers --workers 8        # fetch covers → web/covers/<id>.jpg
python -m anirex.build_web                 # emit frontend bundle → web/data.js
```

Two implementation notes worth knowing before you fork this:

- Bangumi only exposes the `v0` subject list and it carries **no region field**. The `cat=1` response mixes in roughly 30% Chinese and Western productions, so region is inferred from `meta_tags` first, then from the title's character set (kana → JP, hangul → KR, pure Latin → Western) and tag fallbacks; unresolved rows are tagged `unk` and hidden from the default view.
- Crawling goes through `anirex/net.py`: local proxy autodetect, retries with backoff, rate limiting, and page-level cache files that make an interrupted crawl resumable.
- The frontend makes zero runtime requests — the dataset is inlined into `data.js` (~2.4 MB). That costs first-load bytes and buys a backend-free, auth-free, host-anywhere static site.

### Repository layout

```
AnimeRexorder/
├── web/                    # ← GitHub Pages site root (static, no build step)
│   ├── index.html          #   all UI, logic and styles in one file
│   ├── data.js             #   dataset bundle generated by anirex/build_web.py
│   ├── xlsx.js             #   minimal .xlsx writer used by the export
│   └── covers/             #   4,220 cover images
├── anirex/                 # data pipeline (Python 3.13)
│   ├── net.py              #   proxy / retry / rate-limit transport
│   ├── crawl.py            #   year-month bucketed Bangumi crawler
│   ├── build.py            #   cleaning & merging → data/anime.json
│   ├── covers.py           #   cover downloader
│   ├── build_web.py        #   web/data.js generator
│   └── serve.py            #   local preview server
├── data/anime.json         # structured dataset (committed)
└── club/                   # scripts for an unrelated crawl task, not part of the UI
```

### Deployment

The site root is `web/`, published with the official GitHub Pages Actions workflow: pushing to `main` uploads `web/` and deploys it, usually live within 1–2 minutes. See `.github/workflows/pages.yml`; the repository's *Settings → Pages* build source must be set to **GitHub Actions**.

### Data & licensing

- Metadata comes from the public [bangumi.tv](https://bgm.tv) API; each card links back to its subject page.
- Cover artwork belongs to the respective rights holders and is bundled purely for personal viewing records and visual identification. Please do not redistribute or use it commercially.
- This is a personal tracking tool: non-commercial, no backend, no telemetry. Your marks never leave your browser.
- The data snapshot was crawled in 2026-10 and does not refresh itself; rerun the pipeline above to update.
