#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武汉长江大桥 · 数字沙盘数据构造

数据分层（严格区分真实 / 公开参数 / 示意）：
  1) 真实栅格：Copernicus DEM 30 m（7.6–97.2 m）+ ESA WorldCover 10 m
     江面用 DEM<18 m 低地判定，与 WorldCover 永久水体一致，实测跨江宽 1,150 m
     （公开资料「龟蛇锁江」江面 1,126 m，吻合）
  2) 桥轴线：按 DEM 江面中心线拟合 + 垂直方向定位，非实测 OSM
  3) 桥梁构件：按公开设计参数重建（1957 年通车，公铁两用，3 联 9 孔，
     每孔 128 m，米字形钢桁梁，桁高 16 m，8 墩，桥头堡 35 m）
  4) 周边路网 / 建筑 / 地标：本轮 Overpass 全镜像不可达（退出码 2），
     走示意矢量降级，osm_ok=false
"""
import json, math, os, random
import numpy as np
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
os.makedirs(OUT, exist_ok=True)
random.seed(1957)

# ---------------------------------------------------------------- 坐标框架
LON0, LAT0, LON1, LAT1 = 114.268, 30.532, 114.306, 30.560
KX = 111320.0 * math.cos(math.radians((LAT0 + LAT1) / 2))
KY = 110540.0
S = 4.0                                  # 1 场景单位 = 4 m
W = (LON1 - LON0) * KX / S
H = (LAT1 - LAT0) * KY / S


def ll2xy(lon, lat):
    return [(lon - LON0) * KX / S, (lat - LAT0) * KY / S]


def m2xy(xm, ym, cx, cy, ux, uy):
    """沿桥轴线按里程（m）取场景坐标"""
    return [cx + xm * ux / S, cy + ym * uy / S]

# ---------------------------------------------------------------- 1. 栅格
with rasterio.open(os.path.join(HERE, 'raster', 'dem.tif')) as ds:
    dem = ds.read(1).astype(float)
    db = ds.bounds
with rasterio.open(os.path.join(HERE, 'raster', 'land_cover.tif')) as ds:
    lrgb = ds.read()
    lb = ds.bounds
# ESA WorldCover 2021 v200 类别 RGB（与 VoxCity `get_land_cover_classes('ESA WorldCover')` 一致）。
# 这里内联常量，模板不依赖任何本机绝对路径 / VoxCity 安装；换用别的色彩表时改这里即可。
WC_RGB = {
    10: (0, 112, 0), 20: (255, 224, 80), 30: (255, 255, 170),
    40: (255, 176, 176), 50: (230, 0, 0), 60: (191, 191, 191),
    70: (192, 192, 255), 80: (0, 60, 255), 90: (0, 236, 230),
    95: (0, 255, 0), 100: (255, 255, 0),
}
lcode = np.zeros(lrgb.shape[1:], dtype=np.uint8)
for code, col in WC_RGB.items():
    lcode[(lrgb[0] == col[0]) & (lrgb[1] == col[1]) & (lrgb[2] == col[2])] = code


def bilinear(arr, bounds, lon, lat):
    fx = (lon - bounds.left) / (bounds.right - bounds.left) * (arr.shape[1] - 1)
    fy = (bounds.top - lat) / (bounds.top - bounds.bottom) * (arr.shape[0] - 1)
    c0 = max(0, min(arr.shape[1] - 2, int(fx)))
    r0 = max(0, min(arr.shape[0] - 2, int(fy)))
    tx, ty = fx - c0, fy - r0
    return float((arr[r0, c0] * (1 - tx) + arr[r0, c0 + 1] * tx) * (1 - ty)
                 + (arr[r0 + 1, c0] * (1 - tx) + arr[r0 + 1, c0 + 1] * tx) * ty)


def nearest(arr, bounds, lon, lat):
    c = int((lon - bounds.left) / (bounds.right - bounds.left) * (arr.shape[1] - 1))
    r = int((bounds.top - lat) / (bounds.top - bounds.bottom) * (arr.shape[0] - 1))
    if 0 <= r < arr.shape[0] and 0 <= c < arr.shape[1]:
        return int(arr[r, c])
    return 50


def DEM(lon, lat):
    return bilinear(dem, db, lon, lat)


def LC(lon, lat):
    return nearest(lcode, lb, lon, lat)


RIVER_T = 18.0                            # 江面阈值（DEM 绝对高程 m）
LAKE_M = 15.0                             # 江面基准高程 m
TERRAIN_SQUEEZE = 0.60                    # 地形垂直压缩（可视化，文档标注）
LAKEZ = 0.40                              # 江面场景高程

NX, NY = 132, 106
zs = np.zeros((NY, NX), float)
lcs = np.zeros((NY, NX), int)


def lonlat(c, r):
    return (LON0 + (LON1 - LON0) * c / (NX - 1),
            LAT0 + (LAT1 - LAT0) * r / (NY - 1))


for r in range(NY):
    for c in range(NX):
        lon, lat = lonlat(c, r)
        z = DEM(lon, lat)
        code = LC(lon, lat)
        if z < RIVER_T:
            code = 80
        elif z > 34:
            code = 10                      # 龟山 / 蛇山林地（含山坡）
        elif code not in (10, 20, 30, 40, 50, 60, 90, 95):
            code = 50
        lcs[r, c] = code
        zs[r, c] = LAKEZ if code == 80 else max(0.0, (z - LAKE_M) / S) * TERRAIN_SQUEEZE
T = dict(nx=NX, ny=NY, z=[round(float(v), 3) for v in zs.ravel()], lc=lcs.ravel().tolist())

GNX, GNY = 176, 140
gm = []
for r in range(GNY):
    for c in range(GNX):
        lon = LON0 + (LON1 - LON0) * c / (GNX - 1)
        lat = LAT0 + (LAT1 - LAT0) * r / (GNY - 1)
        gm.append(1 if DEM(lon, lat) < RIVER_T else 0)
G = dict(nx=GNX, ny=GNY, m=gm)


def water_at(x, y):
    """场景坐标是否落在江面（用细网格，供建筑/道路避让）"""
    c = max(0, min(GNX - 1, int(x / W * (GNX - 1))))
    r = max(0, min(GNY - 1, int(y / H * (GNY - 1))))
    return bool(gm[r * GNX + c])


def dem_at(x, y):
    c = max(0, min(NX - 1.001, x / W * (NX - 1)))
    r = max(0, min(NY - 1.001, y / H * (NY - 1)))
    c0, r0 = int(c), int(r)
    tx, ty = c - c0, r - r0
    i00 = r0 * NX + c0
    return (T['z'][i00] * (1 - tx) + T['z'][i00 + 1] * tx) * (1 - ty) + \
           (T['z'][i00 + NX] * (1 - tx) + T['z'][i00 + NX + 1] * tx) * ty

# ---------------------------------------------------------------- 2. 桥轴线
# 江中心拟合：lon = 114.280370 + 0.454771*(lat-30.545)，桥轴线垂直于江道
UX, UY = 0.9303, -0.3669                 # 桥轴线单位向量（东, 北）
BC_LON, BC_LAT = 114.281717, 30.548583    # 桥中心（水段中心对齐正桥中心）
CX, CY = ll2xy(BC_LON, BC_LAT)

TOTAL = 1670.4                            # 全桥长 m
MAIN = 1155.5                             # 正桥长 m
HANYANG_APPR = 303.45                     # 汉阳岸引桥 m
WUCHANG_APPR = 211.45                     # 武昌岸引桥 m
SPAN = MAIN / 9.0                         # 每孔 128.39 m
T0 = -MAIN / 2.0                          # 正桥起点里程
T1 = MAIN / 2.0                           # 正桥终点里程
TA = T0 - HANYANG_APPR                    # 汉阳端
TB = T1 + WUCHANG_APPR                    # 武昌端

DECKZ = 15.0                             # 上层公路桥面（沙盘垂直夸张，文档标注）
RAILZ = DECKZ - 8.0                      # 下层铁路桥面（桁高可视化夸张 2×）
WVIS = 4.0                               # 桥梁横向放大（详见说明文档）
TRUSS_W = 2.5 * WVIS                     # 桁距 10 m × WVIS
DECK_W = 5.625 * WVIS                    # 公路宽 22.5 m × WVIS
PIER_TOP = RAILZ - 0.55

deck, deckA, deckB = [], [], []
for i in range(int((TB - TA) / 8) + 2):
    t = TA + i * 8
    if t > TB:
        t = TB
    x = CX + t * UX / S
    y = CY + t * UY / S
    deck.append([round(x, 2), round(y, 2)])
    # 引桥段桥面从地面渐升到正桥标高
    if t < T0:
        f = (t - TA) / HANYANG_APPR
        z = dem_at(x, y) + 1.4 + (DECKZ - dem_at(x, y) - 1.4) * f
    elif t > T1:
        f = (TB - t) / WUCHANG_APPR
        z = dem_at(x, y) + 1.4 + (DECKZ - dem_at(x, y) - 1.4) * f
    else:
        z = DECKZ
    deckA.append([round(x - UY * TRUSS_W / 2, 2), round(y + UX * TRUSS_W / 2, 2), round(z, 2)])
    deckB.append([round(x + UY * TRUSS_W / 2, 2), round(y - UX * TRUSS_W / 2, 2), round(z, 2)])
    if t >= TB:
        break

# ---------------------------------------------------------------- 3. 构件清单
PARTS = []


def P(n, k, spec, src, mat, t0, t1, z0, z1, note=''):
    tm = (t0 + t1) / 2
    x, y = CX + tm * UX / S, CY + tm * UY / S
    PARTS.append(dict(id=len(PARTS), n=n, k=k, spec=spec, src=src, mat=mat,
                      s=round(t0 - TA, 1), e=round(t1 - TA, 1),
                      l=round(t1 - t0, 1), st='K%.3f' % ((tm - TA) / 1000),
                      z0=round(z0, 2), z1=round(z1, 2), note=note,
                      c=[round(x, 1), round(y, 1)],
                      pid=len(PARTS)))
    return PARTS[-1]


# 3 联 9 孔米字形连续钢桁梁
for j in range(3):
    s = T0 + j * 3 * SPAN
    e = s + 3 * SPAN
    p = P('第%d联 · 三孔连续钢桁梁' % (j + 1), 'truss',
          '3 孔 × 128 m · 平弦菱形（米字形）桁架 · 桁高 16 m · 桁距 10 m',
          '公开设计参数 / 武汉市志', '3 号桥梁钢 · 铆接', s, e, RAILZ, DECKZ,
          '每联于中间墩设固定支座')
# 双层桥面
P('上层公路桥面', 'deck',
  '宽 22.5 m（车行 18 m + 双侧人行道各 2.25 m）· 双向四车道 · 设计 100 km/h',
  '公开设计参数', '钢筋混凝土桥面板 / 沥青', T0, T1, DECKZ, DECKZ + 0.35)
P('下层铁路双线桥面', 'rail',
  '宽 14.5 m · 双线轨距中心间距 4.1 m · 铁路净空 6.125 m · 设计 160 km/h',
  '公开设计参数 / 武汉市志', '钢梁 + 道砟 / 钢轨', T0, T1, RAILZ, RAILZ + 0.3)
P('米字形主桁 · 上下弦 / 斜腹杆', 'truss',
  '每孔 8 个 16 m 大节间，再分 8 m 小节间 · 补充竖杆 · 桁高 16 m',
  '公开设计参数', '3 号桥梁钢 · Φ26 mm 铆钉', T0, T1, RAILZ, DECKZ)
# 8 座水中桥墩
for i in range(1, 9):
    t = T0 + i * SPAN
    x, y = CX + t * UX / S, CY + t * UY / S
    fixed = ' · 固定支座（第 3 / 6 号墩）' if i in (3, 6) else ''
    p = P('%d 号桥墩' % i, 'pier',
          '圆形管柱基础 Φ16.76 m · 30 或 35 根 Φ1.55 m 管柱 · 墩高 47–64 m' + fixed,
          '公开设计参数 / 武汉市志', '钢筋混凝土 / 管柱钻孔法',
          t - 6, t + 6, LAKEZ - 1.6, PIER_TOP,
          '世界首次采用大型管柱钻孔法修建深水基础')
    p['p'] = [round(x, 2), round(y, 2)]
    p['main'] = True
# 管柱基础汇总
P('大型管柱钻孔基础 · 全桥', 'foundation',
  'Φ1.55 m 管柱 3,600 延米 · 管柱内钻孔 224 个 / 钻岩 779 延米',
  '公开设计参数', '钢筋混凝土管柱', T0, T1, LAKEZ - 2.2, LAKEZ + 0.4,
  '1955 年首创，替代气压沉箱法')
# 2 座桥头堡（桥台）
for nm, t, side in [('汉阳岸桥头堡', T0, -1), ('武昌岸桥头堡', T1, 1)]:
    x, y = CX + t * UX / S, CY + t * UY / S
    p = P(nm, 'tower',
          '平面 15 × 32 m · 7 层 · 高 35 m · 民族风格 · 内设楼梯与电梯',
          '公开设计参数 / 武汉市志', '钢筋混凝土框架 · 花岗石镶面',
          t - 12, t + 12, round(dem_at(x, y), 2), round(dem_at(x, y) + 8.75, 2),
          '正桥与引桥的连结、分界点')
    p['p'] = [round(x, 2), round(y, 2)]
    p['side'] = side
# 4 座民族形式桥亭
P('民族形式桥亭 · 4 座', 'pavilion',
  '公路桥面两端两侧各 1 座 · 铸铁栏杆嵌「百花齐放 / 百鸟和鸣」图案',
  '公开资料 / 示意', '仿古亭阁 / 铸铁', T0, T1, DECKZ, DECKZ + 2.4)
# 引桥
P('汉阳岸引桥 · 17 孔', 'approach',
  '长 303.45 m · 17 孔 × 17.2 m · 上层拱式 T 梁 · 公铁双分',
  '公开设计参数 / 武汉市志', '钢筋混凝土 T 梁', TA, T0,
  LAKEZ + 1.2, DECKZ)
P('武昌岸引桥 · 12 孔', 'approach',
  '长 211.45 m · 12 孔（7 × 17.2 m + 5 × 16.0 m）· 铁路面形成长廊',
  '公开设计参数 / 武汉市志', '钢筋混凝土 T 梁', T1, TB,
  LAKEZ + 1.2, DECKZ)
P('大桥照明 / 栏杆系统', 'annex',
  '72 套路灯 · 正桥铸铁栏杆每两片嵌民族风格栏板',
  '公开资料 / 示意', '铸铁 / LED', T0, T1, DECKZ, DECKZ + 1.6)
P('建桥纪念碑 · 武昌桥头', 'annex',
  '象征管柱钻孔法 · 毛泽东「一桥飞架南北 天堑变通途」手书',
  '公开资料 / 示意', '汉白玉 / 石碑', T1, T1 + 40, 0, 5.0)

# ---------------------------------------------------------------- 4. 示意矢量（osm_ok=false）
ROADS = []
# 两岸沿江主干道（贴合江岸线，示意；遇水面断段）
for bank, off in [('汉阳沿江大道', -720), ('武昌临江大道', 720)]:
    seg, segs = [], []
    for k in range(61):
        lat = LAT0 + (LAT1 - LAT0) * k / 60
        lon = 114.280370 + 0.454771 * (lat - 30.545) + off / KX
        x, y = ll2xy(lon, lat)
        if water_at(x, y):
            if len(seg) > 1:
                segs.append(seg)
            seg = []
        else:
            seg.append([round(x, 1), round(y, 1)])
    if len(seg) > 1:
        segs.append(seg)
    for j, pts in enumerate(segs):
        ROADS.append(dict(k=5, n=bank if len(segs) == 1 else bank + ' %d' % (j + 1), p=pts))
# 垂江道路（网格）：遇水面必须断段，否则 ribbon 会把两岸点直接连成跨江假斜线
for i, lat in enumerate([30.534, 30.539, 30.544, 30.549, 30.554, 30.559]):
    seg, segs = [], []
    for k in range(41):
        lon = LON0 + 0.002 + (LON1 - LON0 - 0.004) * k / 40
        x, y = ll2xy(lon, lat)
        if water_at(x, y):
            if len(seg) > 1:
                segs.append(seg)
            seg = []
        else:
            seg.append([round(x, 1), round(y, 1)])
    if len(seg) > 1:
        segs.append(seg)
    for j, pts in enumerate(segs):
        if len(pts) > 1:
            ROADS.append(dict(k=3 if i % 2 else 4,
                              n='示意城市道路 %d-%d' % (i + 1, j + 1), p=pts))
# 龟山 / 蛇山山路
for nm, a, b in [('龟山山路', (114.267, 30.5565), (114.279, 30.5585)),
                 ('蛇山首义路', (114.293, 30.5450), (114.309, 30.5435))]:
    ROADS.append(dict(k=2, n=nm,
                      p=[[round(v, 1) for v in ll2xy(a[0], a[1])],
                         [round(v, 1) for v in ll2xy((a[0]+b[0])/2, (a[1]+b[1])/2)],
                         [round(v, 1) for v in ll2xy(b[0], b[1])]]))
# 注：桥面公路已由桥梁构件表达，不再叠示意路带，避免江面上出现假斜线

# 地标（示意体块）
NAME_PTS = [
    ('黄鹤楼', 114.2966, 30.5453, 5, 51.4, '1985 重建 · 五层攒尖顶 · 金色琉璃瓦'),
    ('白云阁', 114.3018, 30.5462, 7, 26, '蛇山东端'),
    ('胜像宝塔', 114.2948, 30.5461, 3, 12, '元代白塔'),
    ('晴川阁', 114.2875, 30.5530, 3, 18, '汉阳龟山禹功矶'),
    ('龟山电视塔', 114.2740, 30.5565, 4, 90, '龟山制高点'),
    ('辛亥革命博物馆', 114.2955, 30.5398, 3, 18, '首义广场南侧'),
    ('古琴台', 114.2700, 30.5510, 2, 12, '汉阳月湖'),
    ('武昌江滩', 114.2900, 30.5420, 1, 5, '临江观景区'),
]
BUILDINGS = []
for nm, lon, lat, lv, hh, note in NAME_PTS:
    x, y = ll2xy(lon, lat)
    w = 5.0 + lv * 0.9
    poly = [[x - w/2, y - w/2], [x + w/2, y - w/2],
            [x + w/2, y + w/2], [x - w/2, y + w/2]]
    BUILDINGS.append(dict(p=[[round(v, 1) for v in q] for q in poly],
                          h=round(hh / S, 2), lv=lv, n=nm,
                          a=round(w * w * S * S), c=[round(x, 1), round(y, 1)],
                          s='公开资料 / 示意推定', k='landmark',
                          at={'名称': nm, '层数': str(lv) + ' 层', '说明': note}))
# 城区网格填充
n_fill = 0
for gx in range(3, 45):
    for gy in range(3, 39):
        x = gx * 20.5 + random.uniform(-3.0, 3.0)
        y = gy * 20.0 + random.uniform(-2.8, 2.8)
        if not (12 < x < W - 12 and 12 < y < H - 12):
            continue
        if water_at(x, y):
            continue
        # 桥走廊避让
        dx, dy = x - CX, y - CY
        if abs(-dx * UY + dy * UX) < 34 and abs(dx * UX + dy * UY) < 220:
            continue
        # 山体少建
        if dem_at(x, y) > 6.5:
            continue
        w = random.uniform(7.0, 14.0)
        d = random.uniform(6.4, 13.0)
        lv = random.choice([2, 3, 4, 5, 6, 8, 10, 12, 16])
        if x > W * 0.62 or y < H * 0.32:
            lv = random.choice([4, 6, 9, 12, 16, 22])
        hh = lv * 3.1 / S
        poly = [[x - w/2, y - d/2], [x + w/2, y - d/2],
                [x + w/2, y + d/2], [x - w/2, y + d/2]]
        BUILDINGS.append(dict(p=[[round(v, 1) for v in q] for q in poly],
                              h=round(hh, 2), lv=lv, n=None,
                              a=round(w * d * S * S), c=[round(x, 1), round(y, 1)],
                              s='按用途推定层数 ×3.1 m', k='urban', at=None))
        n_fill += 1

# ---------------------------------------------------------------- 5. POI
POI = [
    dict(n='武汉长江大桥', p=[CX, CY], z=DECKZ + 3.2, hot=True),
    dict(n='长江', p=ll2xy(114.2790, 30.5350), z=LAKEZ + 1.0, hot=False),
    dict(n='龟山 · 汉阳', p=ll2xy(114.2720, 30.5565), z=dem_at(*ll2xy(114.2720, 30.5565)) + 4.5, hot=True),
    dict(n='蛇山 · 武昌', p=ll2xy(114.3010, 30.5450), z=dem_at(*ll2xy(114.3010, 30.5450)) + 4.5, hot=True),
    dict(n='黄鹤楼', p=ll2xy(114.2966, 30.5453), z=dem_at(*ll2xy(114.2966, 30.5453)) + 15.0, hot=True),
    dict(n='汉阳岸桥头堡', p=PARTS[[p['n'] for p in PARTS].index('汉阳岸桥头堡')]['p'], z=DECKZ + 10.5, hot=False),
    dict(n='武昌岸桥头堡', p=PARTS[[p['n'] for p in PARTS].index('武昌岸桥头堡')]['p'], z=DECKZ + 10.5, hot=False),
    dict(n='晴川阁', p=ll2xy(114.2875, 30.5530), z=dem_at(*ll2xy(114.2875, 30.5530)) + 6.0, hot=False),
    dict(n='辛亥革命博物馆', p=ll2xy(114.2955, 30.5398), z=dem_at(*ll2xy(114.2955, 30.5398)) + 6.0, hot=False),
]
POI = [dict(n=p['n'], p=[round(v, 1) for v in p['p']], z=round(p['z'], 2), hot=p['hot']) for p in POI]

# ---------------------------------------------------------------- 6. meta
BRIDGE_META = dict(total=1670.4, main=1155.5, span=128.39, n_span=9, n_pier=8,
                   truss_h=16, truss_w=10, deck_w=22.5, rail_w=14.5,
                   tower_h=35, n_tower=2, n_pavilion=4,
                   built='1957-10-15 通车', nick='万里长江第一桥',
                   deck_z=DECKZ, rail_z=RAILZ, lake_z=LAKEZ,
                   river_width=1150, n_part=len(PARTS),
                   hanyang_appr=303.45, wuchang_appr=211.45,
                   style='公铁两用 · 3 联 9 孔平弦菱形（米字形）连续钢桁梁')

META = dict(
    bbox=[LON0, LAT0, LON1, LAT1], kx=round(KX), ky=KY, scale=S,
    w=round(W, 1), h=round(H, 1),
    bridge_center=[round(CX, 1), round(CY, 1)], axis=[UX, UY],
    t_start=TA, t_end=TB, t_main0=T0, t_main1=T1, span_m=SPAN,
    truss_w=TRUSS_W, deck_w=DECK_W,
    n_building=len(BUILDINGS), n_named=len(NAME_PTS), n_fill=n_fill,
    road_km=round(sum(math.dist(a, b) * S for r in ROADS
                      for a, b in zip(r['p'][:-1], r['p'][1:])) / 1000, 1),
    water_km2=round(sum(gm) / len(gm) * (W * S / 1000) * (H * S / 1000), 2),
    dem_min=round(float(np.nanmin(dem)), 1), dem_max=round(float(np.nanmax(dem)), 1),
    bridge=BRIDGE_META,
    osm_ok=False, dem_ok=True, worldcover_ok=True,
    terrain_squeeze=TERRAIN_SQUEEZE, wvis=WVIS,
)

BRIDGE = dict(
    axis=dict(c=[round(CX, 2), round(CY, 2)], u=[UX, UY], t0=TA, t1=TB,
              main0=T0, main1=T1, span=SPAN, step=8),
    deck=[[round(v, 2) for v in p] for p in deck],
    deckA=deckA, deckB=deckB,
    spans=[dict(n='第%d孔 · 128 m' % (i + 1), s=T0 + i * SPAN, e=T0 + (i + 1) * SPAN,
                pid=0 if i < 3 else (1 if i < 6 else 2))
           for i in range(9)],
    piers=[dict(p=p['p'], n=p['n'], pid=p['id'], main=True) for p in PARTS if p['k'] == 'pier'],
    towers=[dict(p=p['p'], n=p['n'], pid=p['id'], side=p['side'])
            for p in PARTS if p['k'] == 'tower'],
    parts=PARTS,
    deckZ=DECKZ, railZ=RAILZ, lakeZ=LAKEZ, trussW=TRUSS_W, deckW=DECK_W,
)

DATA = dict(meta=META, terrain=T, waterGrid=G, waterPoly=[],
            roads=ROADS, buildings=BUILDINGS, poi=POI,
            bridge=BRIDGE)

for d in (HERE, OUT):
    with open(os.path.join(d, 'wuhan_data.json'), 'w', encoding='utf-8') as f:
        json.dump(DATA, f, ensure_ascii=False, separators=(',', ':'))
print('W/H %.1f x %.1f | bridge center %.1f,%.1f | parts %d | buildings %d | water %.2f km2'
      % (W, H, CX, CY, len(PARTS), len(BUILDINGS), META['water_km2']))
print('river width实测 1150 m / 公开 1126 m，正桥 %.1f m，全桥 %.1f m' % (MAIN, TOTAL))
