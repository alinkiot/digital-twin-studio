# sandbox 模板 · 数字沙盘 + 写实质感增强（武汉长江大桥）

四套模板里画质最完整的一套：真实 DEM 地形 + 江面、程序化重建的公铁两用桁架桥、
双层分解、桥身细部画中画、三档光影氛围、日照方位、夜景灯点、无 UI 纯净沙盘图。
既是可直接复用的「沙盘」骨架，也是 `../references/visual_fx.md` 配方的完整参考实现。

## 文件

| 文件 | 作用 |
| --- | --- |
| `build_wuhan.py` | 由 DEM / WorldCover 栅格 + 公开桥梁参数生成 `wuhan_data.json`（同时写工作目录与 `out/`） |
| `make_wuhan_html.py` | 把 three.js + 数据 + 大屏 UI 拼成**离线单文件** `武汉长江大桥_数字沙盘.html` |
| `make_clean_plate.py` | 注入 CSS 隐藏 UI / 浮动标签 / 画中画，叠信息展板，出科技蓝与黄昏两张纯净沙盘图 |

## 复现

```bash
S=~/MyProject/skills/digital-twin-studio
PY=~/MyProject/tmp/voxcity-env/bin/python          # numpy + rasterio
W=~/MyProject/tmp/voxcity/wuhan_bridge            # 工作目录；产物在 W/../out
mkdir -p "$W" && cp "$S"/assets/templates/sandbox/*.py "$W"/
cp "$S/assets/lib/three.min.js" "$W/"             # 或设置 THREE_JS=/path/to/three.min.js
$PY "$S/scripts/fetch_raster.py" --bbox 114.268,30.532,114.306,30.560 --out "$W/raster"

$PY "$W/build_wuhan.py"                           # 读 $W/raster/{dem,land_cover}.tif
python3 "$W/make_wuhan_html.py"
python3 "$W/make_clean_plate.py"

$PY "$S/scripts/render_views.py" --html "$W/../out/武汉长江大桥_数字沙盘.html" \
    --out "$W/../out" --prefix 武汉长江大桥 --modes main,floors,cut,skel,top,wide,pick
$PY "$S/scripts/smoke_check.py"  --html "$W/../out/武汉长江大桥_数字沙盘.html"
```

`build_wuhan.py` 的 WorldCover 颜色 LUT 已内联（`WC_RGB`），**不依赖 VoxCity 源码或任何本机绝对路径**；
`make_wuhan_html.py` 的 three.js 查找顺序为 `THREE_JS` 环境变量 → 工作目录 → 技能 `assets/lib/`。

## 换一个地点要改哪些常量

1. `build_wuhan.py`：`LON0,LAT0,LON1,LAT1`（bbox）、`S`（1 场景单位 = 4 m）、
   DEM 江面阈值（本例 `<18 m`）、`random.seed`、桥轴线 `AX.c/u` 与 `main0/main1`、
   桥长 / 跨径 / 墩数 / 桥头堡层数、`ZEX / WVIS / BEX`、周边建筑与路网降级参数。
2. `make_wuhan_html.py`：标题、`BD/AX` 派生常量、`DECKZ/RAILZ`、
   `MOOD` 三档配色、`waterTone()` 的江心—近岸渐变、灯点循环步长、
   机位 `th/ph/dist/tx/ty/tz`、数据来源文案、构件清单与模式按钮 id。
3. `make_clean_plate.py`：信息展板文案、右下角注记、
   `t.st.dist/ph/ty/tx/tz` 机位（用底座 8 角 `project(camera)` 全落 `[-1,1]` 反算，
   不要凭肉眼猜）、输出文件名。

其余通用约定（DOM id、`window.__TDBG`、点选、剖切、图层）见
`../../references/pipeline.md`；画质配方见 `../../references/visual_fx.md`；
已踩过的坑见 `../../references/pitfalls.md`。

## 数据与限制（务必保留声明）

- 真实：Copernicus DEM 30 m、ESA WorldCover 10 m；江面用 DEM 低地判定并与 WorldCover
  永久水体互证，实测跨江约 1150 m。
- 公开参数：全桥 1670.4 m、正桥 1155.5 m（3 联 9 孔 ×128 m）、8 水中墩、
  2 座 7 层桥头堡、上层公路 / 下层铁路。
- **示意**：本轮 Overpass 全镜像不可达，周边路网 / 871 栋建筑 / 地标为示意矢量
  （`osm_ok=false`），接口恢复后重跑 `fetch_osm.py` 即可替换。
- 垂直 `ZEX=3.2`、桥面横向 `WVIS=4.0`、地形压缩 `×0.60` 均为可视化夸张，
  **不作量测**；程序化重建不等于竣工 BIM / Scan-to-BIM。
- 对外发布需 WGS84 → GCJ-02 转换、国内合规底图与审图号。
