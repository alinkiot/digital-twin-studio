# 流程细节：数据契约、渲染分层、改常量清单

## 1. scene_data.json 契约

三套模板共用同一份顶层结构。所有长度量都是**场景单位**（1 单位 = 4 m），
高程 `z` **未乘 ZEX**（three.js 的 `V()` 里才乘 3.2）。

| 键 | 类型 | 说明 |
| --- | --- | --- |
| `meta` | obj | `bbox, kx, ky, scale, w, h, subject_xy, n_building, n_named, road_km, water_km2, dem_min, dem_max, dem_grid, osm_ok, dem_ok, n_floor, n_part, tower_h, subject` |
| `terrain` | obj | `nx, ny, z[nx*ny], lc[nx*ny]`；`lc`：80 水 / 20 林地 / 30 公园 / 50 建成区 |
| `waterGrid` | obj | `nx, ny, m[]`（0/1）；用于生成贴地水面片，与 terrain 独立配准 |
| `waterPoly` | arr | 次要水系折线 `[{p:[[x,y],...]}]`；为空时只显示 waterGrid |
| `roads` | arr | `[{k:1-7, n, p, col?}]`；`k` 决定 ribbon 宽度 |
| `buildings` | arr | `[{p, h, lv, n, a, c, s, k, at?, bz?}]`；`h` 已除以 scale，`bz` 为地形底面 |
| `poi` | arr | `[{n, p:[x,y], z, hot}]`；`z` 场景单位 |
| `subject` | obj | 主角数据：`tower`（楼阁）/ `bridge`（桥梁）/ `city`（城区），由模板填 |
| `parts` | arr | 可点选构件 `[{id,n,k,spec,src,mat,z0,z1,note,c}]` |

`meta.osm_ok=false` 是硬标记：页面数据来源块必须据此显示「示意矢量」警示。

## 2. three.js 渲染分层（14 步，三套模板同构）

1. 渲染器 / 场景 / 相机 / 雾 / 三光源（ambient + sun + fill，楼阁再加暖色 point light）
2. DEM 地形：`BufferGeometry` + `vertexColors` + 双线性 `terrainZ()`
3. `waterGrid` 水面片（Phong + 高光），`LAKEZ` 固定
4. 路网 `ribbon()`：沿折线生成带宽的 quad，高程取 `max(hFn, terrainZ+0.07)`
5. 周边建筑挤出：闭环校验 → 侧面 quad → `ShapeUtils.triangulateShape` 封顶 → `hitB[]` 记录面区间
6. 主角构件：`GeomBuilder`（`tri/quad/mesh` + `hit[]` 记录 `faceIndex → pid`）
7. 沙盘底座 + 边框线
8. HTML 标注（地名 / 楼层），`tmp.project(camera)` 每帧更新位置
9. 相机：`st={th,ph,dist,tx,ty,tz}`，`applyCam()`；pointer 旋转、wheel 缩放、右键/Shift 平移
10. `Raycaster` 点选：`pickMeshes` → `faceIndex` 查 `hit[]` / `hitB[]` → 右侧属性面板
11. 图层 `LY[]` + `setLayer()`；最后一个通常是「标注」（mesh 为 null，走 `labelsHidden`）
12. 模式 `setMode()`：主视 / 分层 / 骨架 / 俯视 / 全景
13. 剖切 `applyCut()` 与爆炸 `applySep()`
14. 指标 / 图例 / 数据来源 / 时钟 / `loop()` / `window.__TDBG`

### 图层与剖切的联动（易错）

`setLayer(i,on)` 会立刻改 `mesh.visible`，而 `applyCut()` 也会改同一批 mesh。
两者互相覆盖时会出现「剖切到第 3 层，切个模式又全冒出来」。
正确做法：维护 `floorVisible / roofVisible / baseVisible` 三个独立标志，
包装 `setLayer`：

```js
var _setLayer=setLayer;
setLayer=function(i,on){
  if(i===6)floorVisible=on;
  if(i===7)roofVisible=on;
  if(i===5)baseVisible=on;
  _setLayer(i,on);
  applyCut(CUT);          // 用最新标志重算一次
};
```

`applyCut(n)`：`floorMeshes[i].visible = floorVisible && i<n`；
`roofMesh.visible = (n>=6) && roofVisible`；`baseMesh.visible = baseVisible`。
爆炸位移用 `mesh.position.y = i*SEP*ZEX*0.62`，屋顶跟随第 5 层。

## 3. 模式设计

| 模式 | 图层策略 | 相机 | 用途 |
| --- | --- | --- | --- |
| 主视 | 全开 | 贴近主角（dist ≈ 140–560） | 看主角细节 |
| 分层展开 | 隐藏周边建筑，`SEP=7`，显示「逐层剖面」卡片 | dist ≈ 205，target 略抬高 | 单栋楼阁逐层看 |
| 地形骨架 | 只留地形 / 水面 / 路网 / 标注，隐藏所有构件 | 高俯视（ph ≈ 1.32, dist ≈ 1250） | 先核地理关系 |
| 正射俯视 | 全开 | ph ≈ 1.47 | 核平面、轴线、收分 |
| 全景沙盘 | 全开 | ph ≈ 0.58, dist ≈ 940 | 主角与山水城的关系 |

模式切换后要同步图层 checkbox 的勾选状态，否则 UI 与实际显隐不一致。

## 4. 改模板常量的清单

复制 `assets/templates/<subject>/` 后，按序替换。模板里保留了案例的
`~/MyProject/tmp/voxcity/...` 绝对路径、中文输出名与 `../out` 相对目录，
全部改成当前工作目录；`three.min.js` 从 `assets/lib/` 复制到脚本同级。

**`build_*.py`（数据构造）**
- `LON0/LAT0/LON1/LAT1`、`KX/KY/S`（`S` 固定 4）
- 主角中心经纬度、`basez`（用 DEM 插值）、层高/边长/跨度等公开参数
- `POI`、`PARTS`（构件清单：名称、规格、材料、数据来源、`z0/z1`）
- 示意矢量段（仅 OSM 不可达时）：路网折线、建筑网格、留空区
- `META` 统计与 `osm_ok`

**`make_*_html.py`（页面）**
- `<title>` / `h1` / `.sub` / badge
- `W,H,ZEX,BEX,TVIS/WVIS,LAKEZ,HALF_W,HALF_H` 与主角 `TX,TY,BZ`
- 配色 `LC / RC / BC` 与主角材质色
- 主角几何函数（`buildFloor` / `deckBand` / `buildingMesh` 等）
- `LY[]` 图层项、`setMode()` 各分支相机参数与 tip 文案
- `K[]` 指标、`LEG[]` 图例、`#srcbox` 数据来源与限制（**逐层区分真实/示意/推定**）
- 模式按钮 id 保持约定；`window.__TDBG` 暴露的键保持约定

## 5. 性能与体量参考

| 项 | 建议上限 | 实测（黄鹤楼） |
| --- | --- | --- |
| 地形网格 | 120 × 100 | 108 × 84 |
| 周边建筑 | ≤ 2,500 栋 | 1,524 栋 |
| 单文件 HTML | ≤ 3 MB | 1.17 MB（含 670 KB three.js） |
| 三角面 | ≤ 100 万 | 约 30 万 |
| 首屏 | 本机瞬时 | 无头 SwiftShader 约 5–8 s |

超过范围用 LOD 或缩小 bbox；不要靠加大 `BEX` 掩盖构图问题。
