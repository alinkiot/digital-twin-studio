# 数据源、镜像实测与合规

## 1. 地形：Copernicus DEM GLO-30（真实）

通过 VoxCity 内置的 AWS Open Data 读取，无需账号：

```python
import sys; sys.path.insert(0, '/Users/kenneth/MyProject/uzy/VoxCity/src')
from voxcity.cli import rectangle_from_bbox
from voxcity.downloader.aws_opendata import fetch_copernicus_dem, fetch_esa_worldcover
rect = rectangle_from_bbox(114.286, 30.537, 114.309, 30.554)
fetch_copernicus_dem(rect, 'raster')      # -> raster/dem.tif
fetch_esa_worldcover(rect, 'raster')      # -> raster/land_cover.tif
```

注意 `fetch_*` 返回的是**相对路径字符串**，且会写到当前工作目录，
调用前先 `os.chdir(outdir)`。DEM 覆盖范围通常略大于请求 bbox，
重采样时按 `ds.bounds` 做双线性插值，不要假设像元与 bbox 对齐。

实测（黄鹤楼，2026-11-10）：DEM 69×91，7.7–86.6 m，蛇山与长江水面可分；
WorldCover 206×278，取值 0 / 191 / 230 / 255，**并非标准 ESA 10 m 分类码**
（正常应为 10/20/30/40/50/60/80/90/95），因此只作配色参考，不用于地类判定。

**江面判定一律用 DEM 低地阈值**（`zs < 20 m`，长江段可参考 `3 m`）。
已两次踩到 WorldCover 把水面误判为建成区：钱塘江主槽、西湖窄堤。
阈值按实测 DEM 直方图调整，写进说明文档。

## 2. 矢量：Overpass / OSM

Overpass bbox 顺序是 **south,west,north,east**，与常见的 `lon0,lat0,lon1,lat1` 不同；
`fetch_osm.py` 已做转换。查询务必带 `out geom;`，否则要自己拼 node 表。

### 镜像实测（2026-11-10 01:30 GMT+8，同一台机器）

| 端点 | 结果 | 判读 |
| --- | --- | --- |
| `maps.mail.ru/osm/tools/overpass/api/interpreter` | 504 Gateway Time-out | 上游挂了；此前曾可用，不能假定长期可用 |
| `overpass-api.de/api/interpreter`（GET 与 POST） | 406 Not Acceptable | 网关/WAF 拦截带 `data=` 的请求，换 UA 无效 |
| `lz4.overpass-api.de/api/interpreter` | 406 | 同上 |
| `overpass.kumi.systems` | 000 | 连接失败 |
| `overpass.nchc.org.tw` | 000 | 连接失败 |
| `overpass.private.coffee` | 000 | 连接失败 |
| `overpass.osm.jp` | 000 | 连接失败 |
| `api.openstreetmap.org/api/0.6/map` | 000 | OSM 主 API 不可达 |
| `nominatim.openstreetmap.org` | 000 | 不可达 |
| `tile.openstreetmap.org` | 000 | 不可达 |
| `api.openstreetmap.fr` | 000 | 不可达 |
| `overpass.osm.ch/api/interpreter` | 400（可达） | **只覆盖瑞士**，中国数据返回 0 要素 |
| `www.baidu.com` | 200 | 网络本身通，是 OSM 域名被挡/不可达 |

结论：OSM 可用性随网络环境变化，**每次先跑 `fetch_osm.py` 探测**，
退出码 2 就走 `schematic_fallback`，不要编造矢量。

补充：OSM 主 API `map?bbox=` 单次面积上限约 0.25 平方度，返回 XML 而非 JSON；
若某天主 API 可用，需把 XML 转成 `elements` 结构再用 `parse_osm`。
`overpass.osm.ch` 必须排除在中国项目之外。

### OSM 解析注意

- 按 `way.id` 去重；`out geom` 时优先用 `geometry`，否则用 `nodes` 查 node 表。
- polygon 首尾闭合点要去掉，少于 3 点直接丢弃。
- 水系 `relation` 通常不会展开成 polygon（西湖即如此），需要另找水面来源（DEM 低地或体素 H5 的 `waterGrid`）。
- 长条状地名（白堤、苏堤）在 OSM 里是多段 way，用「最近端点贪心串联」拼成折线。
- 建筑底面要按 `terrainZ()` 抬高，否则会被 DEM 埋掉。
- 高度优先 `building:levels` / `height`，缺失时按 `building` 用途推定，
  并在 `s` 字段写明来源。

## 3. 坐标与单位

```
KX = 111320 × cos(中心纬度)   米/度（经度）
KY = 110540                  米/度（纬度）
x = (lon - lon0) × KX / S
y = (lat - lat0) × KY / S
S = 4                        1 场景单位 = 4 m
three.js: V(x,y,h) = (x - W/2, h × ZEX, -(y - H/2))，ZEX = 3.2
```

**WGS84 vs GCJ-02**：OSM / Copernicus / Overture 都是 WGS84；
国内底图（高德、腾讯）是 GCJ-02，直接混用会偏几百米。
本地可视化保持 WGS84 即可；对外发布到国内地图必须做 WGS84 → GCJ-02 转换，
并使用有审图号的合规底图。

## 4. 主角参数（无需网络）

桥梁、名楼等主角几何通常来自公开设计资料，可离线重建：
- 黄鹤楼：1985 年重建，总高 51.4 m，五层攒尖顶，底层约 30 m × 30 m，
  「四面八方」切角八边形平面，金色琉璃瓦、葫芦宝顶。
- 江东大桥：设计全长 4,332 m，跨江段 `83+260+83` 自锚式空间缆悬索桥两联 + 刚构桥，
  4 塔 / 8 主缆 / 112 吊索 / 84 墩台。
- 桥面高程避免把吴淞水位基准与 DEM 椭球高混用，统一改「相对江面」。

凡属推定值（柱网、格栅、起翘、楼高层数、构件间距）都在 `parts[].src` 与
说明文档里标「程序化推定 / 公开资料示意」。

## 5. 合规清单

- 数据授权：OSM ODbL 署名；Copernicus / ESA 开放数据注明来源。
- 对外发布：WGS84 → GCJ-02、国内合规底图、审图号。
- 精度声明：可视化 LOD1/LOD2，非竣工 BIM，不含构件级结构/监测属性；
  垂直与横向放大均为可视化夸张，不作量测。
- 示意矢量必须显式标注「非实测 OSM，不作量测」。
