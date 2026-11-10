---
name: digital-twin-studio
description: 把真实地点（西湖、江东大桥、黄鹤楼、园区、桥梁、楼阁等）做成离线单文件 three.js 数字孪生大屏：Copernicus DEM 地形 + Overpass OSM 矢量（不可达时降级为示意矢量并标注）+ 主角构件重建（城区体块 / 桥梁构件 / 楼阁逐层），含图层开关、剖切、点选属性、搜索定位、多视角预设与无头 Chromium 出图验证；可选写实质感增强（PBR 软阴影 / 天空穹顶 / 水面着色器 / 三档光影氛围 / 日照方位 / 夜景灯点 / 纯净沙盘图）。当用户说「把 X 做成数字孪生」「做个三维沙盘 / 数字孪生大屏」「按那个 Three.js 思路优化一下」「界面更精美 / 更逼真」，或提到 OSM、Overpass、DEM、Three.js 地理可视化、桥梁或楼阁逐层模型时使用。DEM 下载与地形产品可复用 cn-dem 技能；纯业务指标看板走 big-screen。避免与两者重复。
agent_created: true
---

# 地理矢量数字孪生单文件大屏

## Overview

把一个真实地点做成**双击即可打开、断网可用**的单文件 HTML：真实 DEM 地形打底，
OSM 矢量铺路网/建筑/水系，主角（城区、桥梁、楼阁）按公开参数或设计资料重建构件，
外加大屏 UI（指标、图层、模式、剖切、点选属性、构件清单、搜索）。
所有数据内联进 HTML，不依赖 CDN 或本地服务。
视觉上默认走清爽科技蓝；需要「像效果图」时再叠加一层可选写实质感增强
（`scripts/visual_fx.py` + `references/visual_fx.md`），数据与坐标完全不变、可随时整层摘掉。

## 适用与边界

- 适用：地标 / 景区 / 桥梁 / 园区 / 历史建筑的三维可视化与交互查阅。
- 不适用：纯业务指标看板（用 `big-screen`）、行政区 DEM 晕渲与地形产品（用 `cn-dem`）、
  竣工 BIM / IFC 级构件管理与结构分析（本流程产出的是可视化 LOD1/LOD2）。
- 与 `cn-dem` 的分工：DEM 下载、裁切、坡度晕渲交给 `cn-dem`；本技能只用 DEM 做场景底座，
  轻量路径已内置在 `scripts/fetch_raster.py`。

## 快速开始

**提示词优先**：用户通常只给一句自然语言，不会给命令。先把这句话解析成
「地点 / 主角类型 / 交互或画质 / 产物路径」，再按工作流执行；不要反过来要求用户先跑脚本。

| 用户说 | 主角类型 | 解析出的关键要求 |
| --- | --- | --- |
| 「把杭州西湖做成数字孪生大屏」 | `city` | 面状城区 / 水系 / 白堤，真实 OSM 优先 |
| 「把江东大桥做成数字孪生，构件要能点选」 | `bridge` | 塔 / 主缆 / 吊索构件、构件清单与属性面板 |
| 「黄鹤楼要每层都能看清」 | `tower` | 五层独立 mesh、逐层剖切与爆炸展开 |
| 「做张长江大桥的沙盘图，要黄昏」 | `sandbox` | DEM 江面、三档光影、无 UI 纯净出图 |
| 「界面再精美 / 逼真一点」 | 任意 | 走第 7 步 `visual_fx.py`，不改数据与坐标 |

最小必要信息缺了就问一句，别自己假设 bbox；OSM 不可达时按第 3 步降级为示意矢量并在
页面、数据、说明三处标注。跑完必须调 `render_views.py` 出多视角图、`smoke_check.py` 冒烟，
并写明哪些属于表达性渲染（不作量测）。

### 脚本参考（辅 · 手动执行或校验时用）

最短路径（以黄鹤楼为例；`$S` 为技能根、`$W` 为工作目录）：

```bash
S=~/MyProject/skills/digital-twin-studio
PY=~/MyProject/tmp/voxcity-env/bin/python     # 有 numpy / rasterio / VoxCity
W=~/MyProject/tmp/voxcity/tower               # 产物在 W/../out

$PY $S/scripts/fetch_raster.py --bbox 114.286,30.537,114.309,30.554 --out $W/raster
$PY $S/scripts/fetch_osm.py  --bbox 114.286,30.537,114.309,30.554 --out $W/osm.json
# 退出码 2 时：下一步不要带 --osm，走示意矢量降级
$PY $S/scripts/make_scene.py --bbox 114.286,30.537,114.309,30.554 \
    --dem $W/raster/dem.tif --osm $W/osm.json --subject tower \
    --subject-xy 114.2966,30.5453 --out $W/scene_data.json

# 复制对应主角模板，按新 bbox / 主角参数改常量后生成 HTML
cp -r $S/assets/templates/tower/*.py $W/ && cp $S/assets/lib/three.min.js $W/
$PY $W/build_tower.py && python3 $W/make_tower_html.py

$PY $S/scripts/render_views.py --html $W/../out/黄鹤楼_数字孪生.html \
    --out $W/../out --prefix 黄鹤楼 --modes main,floors,cut,skel,top,wide,pick
$PY $S/scripts/smoke_check.py --html $W/../out/黄鹤楼_数字孪生.html
```

## 工作流

### 1. 确定范围与主角类型

先定 WGS84 bbox（不宜超过约 3 km × 3 km，否则要素量与三角面失控）与主角类型：

| 类型 | 主角 | 模板目录 | 典型交付 |
| --- | --- | --- | --- |
| `city` | 面状城区 / 水系 / 路网 | `assets/templates/city/` | 西湖：4,106 要素、2,422 栋建筑、197.8 km 路网 |
| `bridge` | 桥梁构件（主梁 / 塔 / 缆 / 吊索 / 墩） | `assets/templates/bridge/` | 江东大桥：28 个可点选构件、4 塔 8 缆 112 吊索 |
| `tower` | 单栋楼阁逐层（柱网 / 平座 / 腰檐 / 攒尖顶） | `assets/templates/tower/` | 黄鹤楼：五层独立构件、逐层剖切与爆炸展开 |
| `sandbox` | 数字沙盘 + 写实质感增强（DEM 江面 / 画中画 / 三档光影 / 纯净出图） | `assets/templates/sandbox/` | 武汉长江大桥：22 构件、双层分解、双视口细部、黄昏 / 夜景氛围 |

### 2. 取真实栅格

运行 `scripts/fetch_raster.py`。记录 DEM 高程范围，据此设 `--water-threshold`
（江河段一般 15–20 m）与 `--lake-base`。
WorldCover 在强涌潮河段、窄堤、湖面常把水误判为建成区，**江面一律用 DEM 低地判定**，
WorldCover 只作配色参考。细节见 `references/data_sources.md`。

### 3. 取 OSM 矢量，或明确降级

运行 `scripts/fetch_osm.py`（内置多镜像探测、超时与 HTML 拦截识别）。

- 退出码 0 → 真实 OSM，进入 `make_scene.py --osm`。
- 退出码 2 → **必须**走 `make_scene.py` 不带 `--osm` 的 `schematic_fallback`，
  并在 `meta.osm_ok=false`、页面数据来源块、说明文档三处同时写明
  「周边路网/建筑为示意矢量，非实测 OSM，不作量测」。
  不得把示意矢量描述成 OSM 实测。接口恢复后重跑第 3 步即可替换。

镜像可用性会变，先跑探测再决定，不要凭上次经验假定某个端点可用。
用 `--mirrors mailru,kumi` 限定端点、`--timeout 20` 控制单次超时；
失败时会在 `<out>.failed.json` 留下各镜像的判读记录，便于复盘。

### 4. 组装标准数据

`scripts/make_scene.py` 输出 `scene_data.json`，顶层契约见 `references/pipeline.md`：
`meta / terrain / waterGrid / waterPoly / roads / buildings / poi / subject / parts`。
主角构件数据（`tower` / `bridge` / `parts`）由所选模板的 `build_*.py` 生成，
可用 `--extra subject.json` 合并进同一份 JSON。

坐标换算固定：经度系数 `111320 × cos(纬度)`、纬度 `110540` 米/度，
**1 场景单位 = 4 m**，`V(x,y,h)` 里垂直再乘 `ZEX = 3.2`。
地形插值 `twin_common.terrain_z` 必须与 three.js 侧 `terrainZ()` 完全一致，
否则建筑/道路会被埋进山体。

### 5. 生成单文件 HTML

复制 `assets/templates/<subject>/` 两个脚本与 `assets/lib/three.min.js` 到工作目录。
按 `references/pipeline.md` 的「改哪几个常量」清单替换：标题、bbox 派生常量、
主角坐标与尺寸、POI、构件清单、数据来源文案、模式按钮 id。

硬约定（保证 `render_views.py` / `smoke_check.py` 能自动验证）：
- three.js 与数据 JSON 全部内联；脚本内容里的 `</script` 要转义后再拼进 HTML。
- 提供 `#kpis / #layers / #plist / #legend / #labels / #right / #rbody / #loading`。
- 模式按钮 id：`btnAll / btnFloors / btnSkel / btnTop / btnWide`（缺失的允许跳过）。
- 暴露 `window.__TDBG = {scene, camera, st, applyCam, setMode, applyCut, applySep, ...}`。
- 点选走 `THREE.Raycaster`，构件用 `userData.pid` 或 `faceIndex → hit[]` 映射。
- 每个 mesh 单独可控显隐，剖切/爆炸/图层开关不得互相覆盖（见 `references/pitfalls.md`）。

### 6. 出图、冒烟、写说明

- `scripts/render_views.py` 批量出主预览 + 各模式截图，并抓 JS `Uncaught`；
  `scripts/smoke_check.py` 校验 DOM 初始化与点选属性面板。
  **两者全绿才算完成**，失败按 `references/pitfalls.md` 排查。
- 写 `<名称>_说明.md`，必须包含：交付物清单、数据链路与来源（逐层区分真实/示意/推定）、
  模型参数表、交互说明、与前版差异、限制与合规、复现命令。
- 对外发布前提醒：WGS84 → GCJ-02 转换、国内合规底图与审图号、数据授权。

### 7.（可选）写实质感增强

当用户要「更精美 / 更逼真 / 像效果图」时才启用，配方与参数全部在 `references/visual_fx.md`：

```python
import sys; sys.path.insert(0, '$S/scripts')
from visual_fx import inline_fx
css_tag, js_tag = inline_fx({'water': {...}, 'lamps': [...]})
html = html.replace('</head>', css_tag + '</head>').replace('</body>', js_tag + '</body>')
```

页面初始化后 `var fx = TwinFX.install({THREE, scene, camera, renderer, waterMesh})`，
渲染循环里 `fx.tick()`。优先级：**PBR + 软阴影 > 天空穹顶 / 水面着色器 > 三档氛围与
日照方位 > 夜景灯点 > UI 微动效**；不要一上来就做后处理。
完整可运行的实现直接抄 `assets/templates/sandbox/`。
验收要求：三档氛围各出一张图目检（江面碎斑、画中画过曝、面板截断、底边色带），
再出一张无 UI 纯净沙盘图。

## 硬约束

- 不伪造数据：OSM 不可达就标注示意；楼高、构件尺寸为推定就写「推定」；
  程序化重建不等于竣工 BIM / Scan-to-BIM。
- 所有可视化夸张（垂直 `ZEX`、主角放大 `TVIS`、桥面横向 `WVIS`）必须在页面和文档里写明，
  并声明「不作量测」。第 7 步的材质、天空、水面波纹、桥影、灯点同属**表达性渲染**，
  同样要写明；平面投影桥影不等于真实阴影，顶点色渐变不等于水深。
- 主角为楼阁时，把每层做成**独立 mesh**，支持逐层剖切与爆炸展开；
  这是无 IFC 时「每层楼都能看清」的可行做法。
- 交付物放工作目录的 `out/`（本机约定 `~/MyProject/tmp/voxcity/out/`），
  复现脚本与数据同目录归档；说明文档不堆进技能目录。
- 新建技能后在 `~/MyProject/skills/README.md` 索引登记。

## 资源索引

| 路径 | 用途 |
| --- | --- |
| `scripts/twin_common.py` | 坐标换算、DEM → 地形/水面、OSM 解析、示意矢量降级 |
| `scripts/fetch_raster.py` | Copernicus DEM + ESA WorldCover 下载 |
| `scripts/fetch_osm.py` | Overpass 多镜像探测（退出码 2 = 降级） |
| `scripts/make_scene.py` | 组装标准 `scene_data.json` |
| `scripts/render_views.py` | 批量无头截图 + JS 异常检查 |
| `scripts/smoke_check.py` | DOM / 交互冒烟 |
| `scripts/visual_fx.py` | 可选写实质感增强片段库（返回可内联的 CSS / JS，暴露 `TwinFX.install`） |
| `scripts/validate_skill.py` | 仓库自检：Python 编译、JS 语法、资源与文档完整性 |
| `references/pipeline.md` | 数据契约、图层与模式设计、改常量清单 |
| `references/data_sources.md` | 数据源、镜像实测记录、坐标系与合规 |
| `references/visual_fx.md` | 写实质感增强配方、shader 关键段、参数表、收敛记录与验证清单 |
| `references/pitfalls.md` | 全部踩坑与对应修复 |
| `references/cases.md` | 四个已交付案例的参数与产物路径 |
| `assets/lib/three.min.js` | 内联用 three.js（r15x，MIT，文件头含 SPDX 许可） |
| `assets/templates/{city,bridge,tower}/` | 三套可直接改的参考实现 |
| `assets/templates/sandbox/` | 第四套：数字沙盘 + 写实质感增强完整实现（含 `README.md` 改常量清单） |

依赖：`numpy` + `rasterio`（本机 `~/MyProject/tmp/voxcity-env/bin/python` 或
`~/MyProject/.venv-dem/bin/python`）、VoxCity 源码（默认 `~/MyProject/uzy/VoxCity/src`）、
Playwright Chromium（默认 `~/Library/Caches/ms-playwright/chromium-*/...`）。
生成 HTML 的脚本本身只需 Python 3 标准库。
