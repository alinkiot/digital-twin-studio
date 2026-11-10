# 踩坑清单（按现象 → 原因 → 修复）

## A. 页面 JS / DOM（最容易让整页卡在 loading）

### A1. `#loading` 一直显示、截图只有一行字
先抓 `Uncaught`，不要靠猜：

```bash
CH=~/Library/Caches/ms-playwright/chromium-1187/chrome-mac/Chromium.app/Contents/MacOS/Chromium
"$CH" --headless --no-sandbox --disable-gpu-sandbox --enable-unsafe-swiftshader \
  --use-gl=angle --use-angle=swiftshader --allow-file-access-from-files \
  --enable-logging=stderr --v=0 --virtual-time-budget=6000 \
  --window-size=1200,800 --dump-dom "file:///path/to/twin.html" >/dev/null 2>err.log
grep -i uncaught err.log
```

也可临时注入 `window.onerror` 把 `m + e.stack` 写进 `document.title`，
再 `--dump-dom` 抓 `<title>`。浏览器日志给出的行号是**整个 HTML 文档的行号**。

### A2. `Cannot set properties of null (setting 'textContent')`
典型：时钟元素写成 `<div class="clock" id="clk">--:--:--<small id="date">…</small></div>`，
`tick()` 里 `getElementById('clk').textContent = ...` 会**删掉内部 `<small id="date">`**，
下一行再取 `date` 就是 null，脚本中断，`ld.style.opacity=0` 永远不执行。
修复：把 id 放到内层 `<span id="clk">`，`<small id="date">` 作为兄弟节点。
教训：给容器设 id 前先确认后续不会用 `innerHTML/textContent` 覆写它。

### A3. strict mode 下隐式全局
IIFE 顶部写了 `'use strict'`，函数里 `dx = q2[0]-q1[0]` 这类未声明赋值会抛
`ReferenceError: dx is not defined`。所有中间变量显式 `var`。
批量自查：把 JS 抽出来用 `node --check` 只能查语法，仍需真实浏览器跑一遍。

### A4. 3D 浮动标签不显示、`style=""`
楼层标签用 `tmp.project(camera)` 时若投影出 NaN，`left/top` 赋值被 CSS 忽略，
DOM 里只剩空 `style`，页面看不到字。不要死磕：改成**右侧 HTML 信息卡**
（「逐层剖面」列出层高/平面/功能），比浮动标签更稳、信息量更大。
`--dump-dom` 抓 `.lab` 的 style 即可确认。

### A5. 图层开关与剖切/爆炸互相覆盖
`setLayer()` 直接改 `mesh.visible`，`applyCut()` 又改一次，切个模式楼层全冒出来。
修复：维护 `floorVisible / roofVisible / baseVisible` 三个标志，包装 `setLayer`
后统一调用 `applyCut(CUT)`（代码见 `pipeline.md`）。
模式切换末尾要同步图层 checkbox 的 `checked`，否则 UI 与实际显隐不一致。

### A6. 标签压住主角 / 主角不够突出
- POI 标签的高程必须和主角用**同一个放大系数**：楼阁用 `TVIS` 放大后，
  `z` 要写 `BASEZ + TOTAL_M/S*TVIS + 边距`，否则标签落在屋顶中间。
- 主视相机 `dist` 从 168 收到 138，主角立刻成为视觉中心。
- 周边建筑过高会形成「灰色柱子森林」：把 `BEX` 降到 0.6，
  地形绿地配色压暗（如 `[0.27,0.40,0.29]`），具名地标缩小 footprint。

### A7. 左面板内容被裁切
`display:flex; max-height` 会直接裁掉溢出内容，看起来像「清单坏了」。
修复：`overflow-y:auto` + KPI 改 3 列 + 缩短模式按钮文字
（主视/分层/骨架/俯视/全景）+ `max-height: calc(100% - 250px)` 给底部工具条留位。

### A8. 其他
- 内联 three.js / JSON 前把 `</script` 转义，否则脚本被提前截断。
- `THREE.ColorManagement.enabled = false`，否则 vertexColors 偏色。
- `ShapeUtils.triangulateShape` 可能失败，回落成 fan 三角。
- `faceIndex → hit[]` 区间映射要连续累加，否则点选到错误构件。
- pointer 事件要 `setPointerCapture`，否则拖出画布后卡住。
- three.min.js 在 r150+ 会打印弃用警告，无害，不必处理。

## B. 数据与地理

| 现象 | 原因 | 修复 |
| --- | --- | --- |
| Overpass 返回 406/504/000 | 网关拦截或 OSM 域名不可达 | `fetch_osm.py` 多镜像探测；退出码 2 走示意矢量并三处标注 |
| 中国数据返回 0 要素 | 用了 `overpass.osm.ch`（仅瑞士） | 排除该镜像；改用其它端点 |
| 江面变成建成区 | ESA WorldCover 把强涌潮河段/窄堤/湖面误判 | 用 DEM 低地阈值判定水面，WorldCover 仅配色 |
| 楼/路被地形埋掉 | 建筑底面用 0 海拔，而 DEM 有 30–80 m 起伏 | 底面取 footprint 各点 `terrainZ()` 最大值 |
| 白堤/苏堤断成几截 | OSM 把长条地名拆成多段 way | 最近端点贪心串联（白堤 990 m、苏堤 2,292 m） |
| 湖面 relation 画不出来 | `out geom` 不展开 multipolygon relation | 改用 DEM 低地 `waterGrid` 或体素 H5 的 `waterGrid` |
| 白堤「没 3D 效果」 | 只有斜顶视 + 平面色块 | 改透视投影、柱体侧墙、AO、沙盘底座、可旋转 HTML |
| 「方块是精度不够吗」 | 10 m/20 m 降采样 + 30 m DEM + 缺楼高 | 说明三者叠加，别只调一个；逐层看清要走 LOD2/IFC |
| 桥面忽高忽低 | 吴淞水位基准与 DEM 椭球高混用 | 统一改成「相对江面」的相对高程 |
| 桥梁标注在骨架模式残留 | 只隐藏了 mesh 没隐藏 bridge 标注 | 加 `bridgeLabelsHidden` / `labelsHidden` 标志 |
| 江面出现规则斜纹 / 雨丝感 | 等间距 `LineSegments` 短流线在斜向水面上形成摩尔纹 | 去掉规则流线，只保留顶点色深浅渐变 + 弱正弦波纹 |
| 沙盘图底座四角出画 | 机位凭肉眼调 `dist` / `ph` | 把底座 8 个角点 `project(camera)`，要求 NDC 全落 `[-1,1]` 再定机位（还可微调 `tx/tz/ty` 居中） |
| 画中画边框压住属性面板 | 只在 loop 里停了 3D 双视口渲染，CSS 边框还在 | `#right.show~#inset{display:none!important}`，同时 `blocked` 判断跳过第二次 `render` |
| 全景里主角（桥/塔）太细 | 一味加大横向夸张系数，破坏整体比例 | 加独立相机画中画：`setViewport` + `setScissor` 双视口共用同一 scene，整体与细部同时可见 |
| 纯净图仍有一堆浮动标签 | CSS 只隐藏了 `.panel`，3D 标签是 JS 每帧设 inline `display` | 用 `.lab{display:none!important}` 覆盖 inline style；别忘了 `setInset(false)` 关掉双视口 |

## C. VoxCity / Python 环境

- `python3.13` 路径与系统 python 不一致，脚本要显式用 venv 解释器。
- pip 卡住时用 micromamba `--no-deps` 装；`pyarrow` 写死 Homebrew lz4 路径时
  用 `install_name_tool -change` 改 dylib 引用。
- 缺 `ee` 时补 `earthengine-api` / `geemap`；HuggingFace 走 `hf-mirror`。
- `plt.show()` 在无 GUI 环境会阻塞：设 `MPLBACKEND=Agg`，
  `get_voxcity(..., gridvis=False, mapvis=False)`。
- `fetch_copernicus_dem()` 返回**相对路径字符串**且写到 cwd，调用前 `os.chdir`。
- DEM 覆盖范围通常略大于 bbox，按 `ds.bounds` 插值，不要假设对齐。

## D. 无头截图 / 验证

- Chromium 固定参数（SwiftShader 必需）：
  `--headless --no-sandbox --disable-gpu-sandbox --enable-unsafe-swiftshader
   --use-gl=angle --use-angle=swiftshader --allow-file-access-from-files
   --hide-scrollbars --virtual-time-budget=8000 --window-size=1680,1050`。
- 中文路径用 `pathlib.Path(...).as_uri()` 生成 `file://` URL，别手拼。
- **12 KB 左右的 PNG = 黑屏/loading 卡住**，正常成片应 500 KB 以上；
  `render_views.py` 用 40 KB 阈值自动判失败。
- 验证每个模式：复制 HTML 到临时文件，在 `</body>` 前注入
  `setTimeout(function(){window.__TDBG.setMode('btnFloors');},90)` 再截图。
- `--enable-logging=stderr --v=0 --dump-dom` 同时拿 DOM 与 JS 异常；
  `grep -i uncaught` 是最后一关。
- 点选冒烟：注入 `document.querySelectorAll('.pi')[2].click()`，
  检查 `#right` 出现 `show` 且 `#rbody` 有 `.rname`。
- **切换清屏色 / 多套光影氛围时，同步设 `html / body / #app` 的背景色**：
  无头 Chromium 的 `innerHeight` 常比 `--window-size` 高度小几十像素，
  只改 `renderer.setClearColor` 会在成品图底边露出一条旧色带。
- **天空日轮要随氛围缩放强度**：画中画独立相机可能正对日轮，
  `pow(s,320)*常数` 不乘氛围系数会让 inset 出现一条过曝白横带。
- **ShaderMaterial 不自动接阴影 / 雾 / tone mapping**：水面、天空这类自定义材质要么
  手写距离雾与高光，要么只用在不需要接收阴影的对象上，别指望和 PBR 材质表现一致。
- **加性混合灯点在近距画中画里会过曝**：`sizeAttenuation:true` 的 `THREE.Points`
  在 inset 相机 360 距离下被放大成一整条白带；渲染第二个视口前临时 `lampPts.visible=false`，
  `render()` 后恢复，细部视口反而更清楚。
