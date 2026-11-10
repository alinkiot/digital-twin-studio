#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武汉黄鹤楼 · 楼阁数字孪生数据构造

数据分层：
  1) 地形：Copernicus DEM 30 m 真实高程（本轮实测 7.7–86.6 m，蛇山 / 长江水面）
  2) 江面：DEM < 20 m 低地判定（ESA WorldCover 在该河段同样误判为建成区）
  3) 周边矢量：本轮 Overpass / OSM API 均不可达，按公开地理轮廓绘制「示意矢量」，
     不冒充实测 OSM；楼阁本体按公开设计参数重建（1985 年重建，五层攒尖顶，51.4 m）
  4) 楼层：逐层独立构件，可点选 / 逐层剖切 / 爆炸展开
"""
import json, math, os, random
import numpy as np
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
os.makedirs(OUT, exist_ok=True)
random.seed(1985)

LON0, LAT0, LON1, LAT1 = 114.286, 30.537, 114.309, 30.554
KX = 111320 * math.cos(math.radians((LAT0 + LAT1) / 2))
KY = 110540.0
S = 4.0                     # 1 场景单位 = 4 m
W = (LON1 - LON0) * KX / S
H = (LAT1 - LAT0) * KY / S


def ll2xy(lon, lat):
    return [(lon - LON0) * KX / S, (lat - LAT0) * KY / S]


# ---------------------------------------------------------------- 1. DEM 地形
with rasterio.open(os.path.join(HERE, 'raster', 'dem.tif')) as ds:
    dem = ds.read(1).astype(float)
    db = ds.bounds
# DEM 略大于 bbox，按经纬度裁到 bbox 网格
NX, NY = 108, 84
zs = np.zeros((NY, NX), float)
lcs = np.zeros((NY, NX), int)
for r in range(NY):
    lat = LAT0 + (LAT1 - LAT0) * r / (NY - 1)
    for c in range(NX):
        lon = LON0 + (LON1 - LON0) * c / (NX - 1)
        fx = (lon - db.left) / (db.right - db.left) * (dem.shape[1] - 1)
        fy = (db.top - lat) / (db.top - db.bottom) * (dem.shape[0] - 1)
        c0 = max(0, min(dem.shape[1] - 2, int(fx)))
        r0 = max(0, min(dem.shape[0] - 2, int(fy)))
        tx, ty = fx - c0, fy - r0
        v = (dem[r0, c0] * (1 - tx) + dem[r0, c0 + 1] * tx) * (1 - ty) + \
            (dem[r0 + 1, c0] * (1 - tx) + dem[r0 + 1, c0 + 1] * tx) * ty
        zs[r, c] = v
LAKE_M = 15.0
water = zs < 20.0
# 土地覆盖配色：江面 80 / 蛇山林地 20 / 公园绿地 30 / 建成区 50
for r in range(NY):
    for c in range(NX):
        x = c / (NX - 1) * W
        y = r / (NY - 1) * H
        if water[r, c]:
            lcs[r, c] = 80
        elif zs[r, c] > 42:
            lcs[r, c] = 20
        elif 180 < x < 430 and 175 < y < 285:      # 黄鹤楼公园 / 蛇山
            lcs[r, c] = 30
        else:
            lcs[r, c] = 50
        zs[r, c] = 0.4 if water[r, c] else (zs[r, c] - LAKE_M) / S
T = dict(nx=NX, ny=NY, z=[round(float(v), 3) for v in zs.ravel()],
         lc=lcs.ravel().tolist())
# 水面细网格
GNX, GNY = 150, 118
gm = []
for r in range(GNY):
    for c in range(GNX):
        x = c / (GNX - 1) * W
        y = r / (GNY - 1) * H
        cc = min(NX - 1, int(x / W * (NX - 1)))
        rr = min(NY - 1, int(y / H * (NY - 1)))
        gm.append(1 if water[rr, cc] else 0)
G = dict(nx=GNX, ny=GNY, m=gm)


def dem_at(x, y):
    c = max(0, min(NX - 1.001, x / W * (NX - 1)))
    r = max(0, min(NY - 1.001, y / H * (NY - 1)))
    c0, r0 = int(c), int(r)
    tx, ty = c - c0, r - r0
    i00 = r0 * NX + c0
    return (T['z'][i00] * (1 - tx) + T['z'][i00 + 1] * tx) * (1 - ty) + \
           (T['z'][i00 + NX] * (1 - tx) + T['z'][i00 + NX + 1] * tx) * ty


# ---------------------------------------------------------------- 2. 黄鹤楼
TX, TY = ll2xy(114.2966, 30.5453)         # 楼中心（WGS84 公开坐标）
BASEZ = dem_at(TX, TY)                     # 台基处地面（场景单位，未乘 ZEX）
FLOOR_H = [9.0, 7.8, 7.4, 7.0, 6.6]       # 五层层高 m
EDGE = [30.0, 27.0, 24.5, 22.0, 19.5]     # 各层平面边长 m
EAVE = 3.2                                 # 出檐 m
BASE_M = 2.4                               # 台基高 m
ROOF_BASE = 1.5                            # 顶层腰檐厚 m
ROOF_M = 6.5                               # 攒尖顶高 m
FINIAL_M = 3.2                             # 葫芦宝顶高 m
TOTAL_M = BASE_M + sum(FLOOR_H) + ROOF_BASE + ROOF_M + FINIAL_M   # 51.4 m
levels, acc = [], BASE_M
for i in range(5):
    levels.append(dict(i=i + 1, z0=acc, z1=acc + FLOOR_H[i], h=FLOOR_H[i],
                       edge=EDGE[i], eave=EAVE,
                       area=round(EDGE[i] ** 2, 1),
                       name=['一层 · 大厅 / 白云黄鹤壁画', '二层 · 历代黄鹤楼模型',
                             '三层 · 唐宋名人诗词', '四层 · 书画 / 会客',
                             '五层 · 观景 / 江城一览'][i]))
    acc += FLOOR_H[i]
TOWER = dict(x=TX, y=TY, basez=BASEZ, base_m=BASE_M, total_m=TOTAL_M,
             roof_base=BASE_M + sum(FLOOR_H) + ROOF_BASE,
             roof_m=ROOF_M, finial_m=FINIAL_M, floors=levels,
             n_col=12, style='钢筋混凝土仿木 · 五层攒尖顶 · 四望如一 · 金色琉璃瓦',
             built='1985 年重建（清同治楼形制）',
             height_src='公开设计参数：总高 51.4 m，底层平面约 30 m × 30 m')

# ---------------------------------------------------------------- 3. 示意矢量路网
def p(*pts):
    return [list(q) for q in pts]


ROADS = [
    dict(k=7, n='武汉长江大桥（公路 + 铁路）', p=p((88, 402), (128, 362), (170, 316), (205, 268), (232, 232))),
    dict(k=6, n='武珞路 / 黄鹤楼东路', p=p((0, 182), (110, 186), (215, 192), (330, 198), (W, 205))),
    dict(k=5, n='民主路', p=p((30, 118), (170, 126), (330, 132), (W - 20, 140))),
    dict(k=5, n='彭刘杨路', p=p((0, 96), (160, 100), (320, 108), (W, 112))),
    dict(k=5, n='解放路', p=p((78, 90), (84, 180), (92, 280), (100, 400))),
    dict(k=5, n='中山路', p=p((358, 96), (362, 190), (368, 300), (372, 410))),
    dict(k=4, n='首义路', p=p((250, 90), (252, 170), (256, 250))),
    dict(k=4, n='蛇山山路', p=p((150, 244), (200, 258), (252, 240), (310, 252), (372, 238), (430, 246))),
    dict(k=3, n='黄鹤楼公园游步道', p=p((TX - 52, TY - 34), (TX - 20, TY - 24), (TX + 24, TY - 26),
                                    (TX + 54, TY - 14))),
    dict(k=3, n='武昌江滩步道', p=p((28, 330), (110, 350), (190, 392), (260, 440))),
]
# 江面以 DEM 低地网格为准，不再叠手工河轴线，避免与真实 DEM 冲突
WATERPOLY = []

# ---------------------------------------------------------------- 4. 周边建筑（示意）
BUILDINGS = []
NAME_PTS = [
    ('白云阁', 114.3018, 30.5462, 7, 26), ('胜像宝塔', 114.2948, 30.5461, 3, 12),
    ('南楼', 114.2979, 30.5442, 2, 10), ('搁笔亭', 114.2972, 30.5459, 1, 6),
    ('岳飞广场', 114.2992, 30.5443, 1, 5), ('黄鹤楼公园牌坊', 114.2938, 30.5444, 1, 9),
    ('辛亥革命博物馆', 114.2955, 30.5398, 3, 18), ('首义广场', 114.2950, 30.5407, 1, 5),
    ('武昌江滩', 114.2910, 30.5500, 1, 5), ('户部巷', 114.2918, 30.5428, 2, 9),
    ('武汉长江大桥桥头堡', 114.2935, 30.5484, 6, 24),
]
for nm, lon, lat, lv, hh in NAME_PTS:
    x, y = ll2xy(lon, lat)
    w = 4.2 + lv * 1.0
    poly = [[x - w / 2, y - w / 2], [x + w / 2, y - w / 2],
            [x + w / 2, y + w / 2], [x - w / 2, y + w / 2]]
    BUILDINGS.append(dict(p=poly, h=hh / S, lv=lv, n=nm, a=round(w * w * S * S),
                          c=[round(x, 1), round(y, 1)], s='公开资料 / 示意推定',
                          k='landmark', at={'名称': nm, '层数': str(lv) + ' 层'}))
# 城区网格填充
n_fill = 0
for gx in range(5, 52):
    for gy in range(4, 45):
        x = gx * 10.5 + random.uniform(-1.4, 1.4)
        y = gy * 10.5 + random.uniform(-1.4, 1.4)
        if not (0 < x < W and 0 < y < H):
            continue
        if water[min(NY - 1, int(y / H * (NY - 1))), min(NX - 1, int(x / W * (NX - 1)))]:
            continue
        if 175 < x < 435 and 168 < y < 292:        # 公园核心留空
            continue
        if abs(x - TX) < 34 and abs(y - TY) < 34:
            continue
        # 路网避让
        if any(abs(y - (182 + x * 0.04)) < 5 or abs(y - 124) < 4 or abs(y - 102) < 4
               for _ in [0]):
            continue
        w = random.uniform(3.6, 7.2)
        d = random.uniform(3.6, 7.0)
        lv = random.choice([2, 3, 4, 6, 8, 12, 18])
        if y > 330 or x > 420:
            lv = random.choice([3, 5, 8, 14, 22])
        hh = lv * 3.1 / S
        poly = [[x - w / 2, y - d / 2], [x + w / 2, y - d / 2],
                [x + w / 2, y + d / 2], [x - w / 2, y + d / 2]]
        BUILDINGS.append(dict(p=poly, h=round(hh, 2), lv=lv, n=None,
                              a=round(w * d * S * S), c=[round(x, 1), round(y, 1)],
                              s='按用途推定层数 ×3.1 m', k='urban', at=None))
        n_fill += 1

# ---------------------------------------------------------------- 5. POI / 构件清单
POI = [
    dict(n='黄鹤楼', p=[TX, TY], z=BASEZ + TOTAL_M / S * 1.38 + 3.0, hot=True),
    dict(n='蛇山', p=[300, 246], z=dem_at(300, 246) + 3.0, hot=False),
    dict(n='长江', p=[130, 392], z=1.5, hot=False),
    dict(n='武汉长江大桥', p=[168, 318], z=12.0, hot=True),
    dict(n='白云阁', p=ll2xy(114.3018, 30.5462), z=dem_at(*ll2xy(114.3018, 30.5462)) + 8, hot=False),
    dict(n='胜像宝塔', p=ll2xy(114.2948, 30.5461), z=dem_at(*ll2xy(114.2948, 30.5461)) + 5, hot=False),
    dict(n='辛亥革命博物馆', p=ll2xy(114.2955, 30.5398), z=dem_at(*ll2xy(114.2955, 30.5398)) + 6, hot=False),
    dict(n='户部巷', p=ll2xy(114.2918, 30.5428), z=dem_at(*ll2xy(114.2918, 30.5428)) + 4, hot=False),
]
PARTS = []
def P(n, k, spec, src, mat, z0, z1, note=''):
    PARTS.append(dict(id=len(PARTS), n=n, k=k, spec=spec, src=src, mat=mat,
                      z0=z0, z1=z1, note=note,
                      c=[round(TX, 1), round(TY, 1)]))

P('台基 · 须弥座 / 月台', 'base', '高 2.4 m · 边长约 34 m', '公开设计参数', '花岗岩 / 混凝土', 0, BASE_M)
for f in levels:
    P('第' + '一二三四五'[f['i'] - 1] + '层 · ' + f['name'].split(' · ')[1], 'floor',
      '层高 ' + str(f['h']) + ' m · 平面 ' + str(f['edge']) + ' m 见方 · 面积约 ' + str(f['area']) + ' m²',
      '公开设计参数 / 程序化推定', '钢筋混凝土仿木 · 12 根檐柱', f['z0'], f['z1'],
      f['name'])
P('五层平座 · 回廊栏杆', 'balcony', '出檐 3.2 m · 四面回廊', '程序化推定', '仿木栏杆', 40.2, 41.0)
P('攒尖屋顶 · 四面坡', 'roof', '高 6.5 m · 四角起翘 · 金色琉璃瓦', '公开形制', '金色琉璃瓦', 41.7, 48.2)
P('葫芦宝顶', 'finial', '高 3.2 m · 总高至 51.4 m', '公开设计参数', '鎏金铜', 48.2, 51.4)
P('黄鹤楼公园牌坊', 'annex', '三间四柱 · 公园东门', '示意矢量', '仿木 / 琉璃', 0, 9)
P('白云阁', 'annex', '蛇山东端 · 7 层约 26 m', '公开资料 / 示意', '仿古建筑', 0, 26)
P('胜像宝塔', 'annex', '元代白塔 · 约 12 m', '公开资料 / 示意', '石塔', 0, 12)
P('武汉长江大桥桥头堡', 'bridge', '公铁两用 · 1957 年通车 · 全长 1,670 m', '公开资料', '钢桁梁 / 混凝土', 0, 24)
P('武汉长江大桥桥面', 'bridge', '本场景内跨江段示意', '公开资料 / 示意', '钢桁梁 / 公路铁路', 0, 0)

META = dict(
    bbox=[LON0, LAT0, LON1, LAT1], kx=round(KX), ky=KY, scale=S,
    w=round(W, 1), h=round(H, 1), tower=[round(TX, 1), round(TY, 1)],
    n_building=len(BUILDINGS), n_named=len(NAME_PTS),
    road_km=round(sum(math.dist(a, b) * S for r in ROADS
                      for a, b in zip(r['p'][:-1], r['p'][1:])) / 1000, 1),
    water_km2=round(sum(1 for v in gm if v) / (GNX * GNY) * (W * S / 1000) * (H * S / 1000), 2),
    dem_min=round(float(np.nanmin(dem)), 1), dem_max=round(float(np.nanmax(dem)), 1),
    tower_h=TOTAL_M, n_floor=5, n_part=len(PARTS), n_fill=n_fill,
    osm_ok=False, dem_ok=True,
)

DATA = dict(meta=META, terrain=T, waterGrid=G, waterPoly=WATERPOLY,
            roads=ROADS, buildings=BUILDINGS, poi=POI, tower=TOWER, parts=PARTS)

for d in (HERE, OUT):
    with open(os.path.join(d, 'tower_data.json'), 'w', encoding='utf-8') as f:
        json.dump(DATA, f, ensure_ascii=False, separators=(',', ':'))
print('W/H', round(W, 1), round(H, 1), 'tower', round(TX, 1), round(TY, 1),
      'baseZ', round(BASEZ, 2), 'buildings', len(BUILDINGS),
      'parts', len(PARTS), 'road_km', META['road_km'], 'water', META['water_km2'])
