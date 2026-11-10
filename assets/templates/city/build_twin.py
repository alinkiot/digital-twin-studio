#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按「数据获取与地形铺设」思路重建西湖数字孪生底图数据。
数据源：OpenStreetMap / Overpass API（真实矢量轮廓）+ VoxCity H5（DEM / 土地覆盖 / 建筑高度）

流程（与参考文章一致）：
  1. 分块抓取（已完成：Overpass 一次取全 bbox）→ 按 OSM id 去重、检查坐标与轮廓闭合
  2. 经纬度 → 局部平面米制；经度方向乘 cos(lat) 做纬度修正
  3. 统一场景单位：1 unit = 4 m
  4. 先铺地理骨架（西湖水面 / 山体 DEM / 主干道 / 白堤苏堤），再叠建筑构件
  5. 输出紧凑 JSON 供 Three.js 挤出与点选
"""
import json, math, os, collections
import numpy as np
import h5py

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
OSM = os.path.join(HERE, 'osm_xihu.json')
H5 = os.path.join(OUT, '杭州西湖.h5')

LON0, LAT0, LON1, LAT1 = 120.125, 30.225, 120.165, 30.265
KX = 111320.0 * math.cos(math.radians((LAT0 + LAT1) / 2))   # 纬度修正
KY = 110540.0
S = 4.0                                                       # 1 场景单位 = 4 米

def xy(lon, lat):
    return [round((lon - LON0) * KX / S, 1), round((lat - LAT0) * KY / S, 1)]

# ---------- 读 VoxCity 栅格（用于高度与地形） ----------
f = h5py.File(H5, 'r'); g = f['voxcity']
dem = g['dem'][:]; lc = g['land_cover'][:]; bh = g['building_height'][:]
NY, NX = dem.shape
DLON = (LON1 - LON0) / NX; DLAT = (LAT1 - LAT0) / NY

def raster(lon, lat, arr):
    c = int((lon - LON0) / DLON); r = int((lat - LAT0) / DLAT)
    if 0 <= r < NY and 0 <= c < NX: return float(arr[r, c])
    return 0.0

def max_in_ring(lonlat, arr, pad=0):
    """轮廓包围盒内取最大值，弥补 OSM 与 Overture 轮廓不完全对齐"""
    xs = [p['lon'] for p in lonlat]; ys = [p['lat'] for p in lonlat]
    c0 = int((min(xs) - LON0) / DLON) - pad; c1 = int((max(xs) - LON0) / DLON) + pad + 1
    r0 = int((min(ys) - LAT0) / DLAT) - pad; r1 = int((max(ys) - LAT0) / DLAT) + pad + 1
    c0, c1 = max(0, c0), min(NX, c1); r0, r1 = max(0, r0), min(NY, r1)
    if c1 <= c0 or r1 <= r0: return 0.0
    return float(np.nanmax(arr[r0:r1, c0:c1]))

# ---------- 读 OSM ----------
raw = json.load(open(OSM, encoding='utf-8'))['elements']
seen = set(); els = []
for e in raw:
    if e['id'] in seen: continue          # 按编号去重
    seen.add(e['id']); els.append(e)

def ring_of(e):
    geo = e.get('geometry') or []
    pts = [p for p in geo if p and 'lon' in p and 'lat' in p]
    if len(pts) >= 3: return pts
    return None

def area_m2(pts):
    """球面近似面积（鞋带公式，米制）"""
    a = 0.0
    X = [(p['lon'] - LON0) * KX for p in pts]
    Y = [(p['lat'] - LAT0) * KY for p in pts]
    for i in range(len(X)):
        j = (i + 1) % len(X)
        a += X[i] * Y[j] - X[j] * Y[i]
    return abs(a) / 2

def closed(pts):
    return pts[0]['lon'] == pts[-1]['lon'] and pts[0]['lat'] == pts[-1]['lat']

# ---------- 1. 建筑：真实 footprint ----------
buildings = []
for e in els:
    t = e.get('tags', {})
    if 'building' not in t or e['type'] != 'way': continue
    pts = ring_of(e)
    if not pts: continue
    ar = area_m2(pts)
    if ar < 12: continue                   # 过滤噪声小面
    if not closed(pts): pts = pts + [pts[0]]   # 轮廓闭合检查
    lonlat = pts
    Ys = [p['lat'] for p in pts]; Xs = [p['lon'] for p in pts]
    cx, cy = sum(Xs) / len(Xs), sum(Ys) / len(Ys)

    # 高度：OSM 层数 > OSM height > VoxCity 栅格 > 按用途推定
    lv = None
    if 'building:levels' in t:
        try: lv = int(float(t['building:levels']))
        except: pass
    h, src = 0.0, ''
    if lv: h, src = lv * 3.2, 'OSM 层数'
    elif 'height' in t:
        try: h, src = float(str(t['height']).replace('m', '').strip()), 'OSM 标注高度'
        except: pass
    if h <= 0:
        v = max_in_ring(lonlat, bh, pad=1)
        if v > 0.5: h, src = v, 'VoxCity / Overture'
    if h <= 0:
        kind = t.get('building', '')
        h = 18.0 if kind in ('commercial', 'office', 'retail', 'hotel') else 10.0
        src = '按用途推定（示意）'
        lv = lv or int(round(h / 3.2))
    h = min(h, 90.0)
    if not lv: lv = max(1, int(round(h / 3.2)))

    name = t.get('name') or t.get('name:zh') or ''
    attrs = {k: t[k] for k in ('name', 'name:en', 'building', 'amenity', 'historic',
                               'tourism', 'office', 'shop', 'addr:street', 'addr:housenumber',
                               'roof:shape', 'building:levels', 'height') if k in t}
    buildings.append({
        'id': e['id'], 'p': [xy(p['lon'], p['lat']) for p in pts],
        'h': round(h / S, 2), 'bz': round(raster(cx, cy, dem) / S, 2),  # 基座 DEM 高程
        'lv': lv, 'a': round(ar), 'n': name,
        'k': t.get('building', 'yes'), 's': src, 'at': attrs,
        'c': [round(cx, 6), round(cy, 6)],
    })

# ---------- 2. 道路（骨架） ----------
ROAD = {'trunk': 7, 'primary': 6, 'secondary': 5, 'tertiary': 4,
        'residential': 3, 'service': 2, 'pedestrian': 3, 'footway': 1}
roads = []
for e in els:
    t = e.get('tags', {})
    if 'highway' not in t or t['highway'] not in ROAD: continue
    pts = ring_of(e)
    if not pts or len(pts) < 2: continue
    roads.append({'p': [xy(p['lon'], p['lat']) for p in pts],
                  'k': ROAD[t['highway']], 'n': t.get('name', ''),
                  'hw': t['highway']})

# ---------- 3. 水系：OSM 小水面 + VoxCity land_cover 铺西湖主体 ----------
water = []
for e in els:
    t = e.get('tags', {})
    if t.get('natural') != 'water' and 'waterway' not in t: continue
    pts = ring_of(e)
    if not pts: continue
    is_area = t.get('natural') == 'water' and len(pts) >= 4
    water.append({'p': [xy(p['lon'], p['lat']) for p in pts],
                  'a': 1 if is_area else 0, 'n': t.get('name', '')})

# 西湖主体是 multipolygon relation（Overpass 未展开 member），
# 改由 ESA WorldCover 土地覆盖栅格铺水面骨架 —— 与 DEM 完全配准，不会错位。
WL = 5                       # 水面格降采样步长
wl = lc[::WL, ::WL]
water_grid = {'nx': wl.shape[1], 'ny': wl.shape[0],
              'm': [1 if v == 7 else 0 for v in wl.ravel()]}
water_area_km2 = round(float((lc == 7).sum()) * (KX * DLON) * (KY * DLAT) / 1e6, 2)

# ---------- 4. 白堤 / 苏堤：把 OSM 分段折线按端点串联成完整堤线 ----------
DIKE = ('白堤', '苏堤', '断桥', '锦带桥', '西泠桥')
segs = []
for e in els:
    t = e.get('tags', {})
    n = t.get('name', '')
    if not any(k in n for k in DIKE): continue
    if t.get('natural') == 'water': continue          # 排除「断桥荷塘」等水面
    pts = ring_of(e)
    if not pts or len(pts) < 2: continue
    segs.append({'p': [xy(p['lon'], p['lat']) for p in pts], 'n': n,
                 'b': 1 if t.get('bridge') == 'yes' else 0})

def chain(segs, tol=55):
    """最近端点贪心串联（tol 场景单位，55 = 220m）"""
    def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])
    segs = [dict(s) for s in segs]
    out = []
    while segs:
        cur = segs.pop(0)['p']
        while True:
            best, bi, mode = tol, -1, None
            for i, s in enumerate(segs):
                p = s['p']
                for d, m in [(dist(cur[-1], p[0]), 'fwd'), (dist(cur[-1], p[-1]), 'rev'),
                             (dist(cur[0], p[-1]), 'pre'), (dist(cur[0], p[0]), 'prev')]:
                    if d < best: best, bi, mode = d, i, m
            if bi < 0: break
            p = segs.pop(bi)['p']
            if mode == 'fwd': cur = cur + p[1:]
            elif mode == 'rev': cur = cur + p[-2::-1]
            elif mode == 'pre': cur = p[:-1] + cur
            else: cur = p[::-1] + cur[1:]
        out.append(cur)
    return out

bseg = [s for s in segs if '白堤' in s['n'] or '断桥' in s['n'] or '锦带桥' in s['n']]
sseg = [s for s in segs if '苏堤' in s['n'] or '西泠桥' in s['n']]
dikes = ([{'p': p, 'n': '白堤 · 断桥 — 锦带桥 — 平湖秋月', 'b': 0} for p in chain(bseg)] +
         [{'p': p, 'n': '苏堤', 'b': 0} for p in chain(sseg)])
dikes = [d for d in dikes if len(d['p']) >= 4]

# ---------- 5. 公园绿地 ----------
parks = []
for e in els:
    t = e.get('tags', {})
    if t.get('leisure') != 'park': continue
    pts = ring_of(e)
    if pts and len(pts) >= 3: parks.append({'p': [xy(p['lon'], p['lat']) for p in pts],
                                            'n': t.get('name', '')})

# ---------- 6. 地形 DEM 降采样（山体骨架） ----------
STEP = 6
zr = dem[::STEP, ::STEP]; lr = lc[::STEP, ::STEP]
tn_y, tn_x = zr.shape
terrain = {
    'nx': tn_x, 'ny': tn_y,
    'z': [round(float(v) / S, 2) for v in zr.ravel()],
    'lc': [int(v) for v in lr.ravel()],
    'w': round((LON1 - LON0) * KX / S), 'h': round((LAT1 - LAT0) * KY / S),
}

# ---------- 7. 地名标注 ----------
POI = [
    ('白堤', 120.1446, 30.2582), ('断桥', 120.14737, 30.26153),
    ('锦带桥', 120.1445, 30.2581), ('平湖秋月', 120.14147, 30.25468),
    ('孤山', 120.1373, 30.2534), ('苏堤', 120.1337, 30.2506),
    ('北里湖', 120.1436, 30.2601), ('外西湖', 120.1490, 30.2460),
    ('湖滨 · 城区', 120.1530, 30.2593), ('宝石山', 120.1408, 30.2630),
]
poi = [{'n': n, 'p': xy(lo, la), 'z': round(raster(lo, la, dem) / S, 2)} for n, lo, la in POI]

# ---------- 统计 ----------
road_len = 0.0
for r in roads:
    P = r['p']
    road_len += sum(math.hypot(P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]) for i in range(len(P)-1)) * S
bld_area = sum(b['a'] for b in buildings)

data = {
    'meta': {
        'title': '杭州西湖 · 城市数字孪生',
        'bbox': [LON0, LAT0, LON1, LAT1], 'kx': round(KX), 'ky': KY, 'scale': S,
        'w': terrain['w'], 'h': terrain['h'],
        'n_building': len(buildings), 'n_road': len(roads),
        'n_water': len(water), 'n_dike': len(dikes),
        'road_km': round(road_len / 1000, 1), 'water_km2': water_area_km2,
        'bld_km2': round(bld_area / 1e6, 2),
        'osm_bytes': os.path.getsize(OSM),
        'named': sum(1 for b in buildings if b['n']),
        'src_h': dict(collections.Counter(b['s'] for b in buildings)),
    },
    'buildings': buildings, 'roads': roads, 'water': water,
    'dikes': dikes, 'parks': parks, 'terrain': terrain,
    'waterGrid': water_grid, 'poi': poi,
}

outp = os.path.join(HERE, 'twin_data.json')
json.dump(data, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('OK ->', outp, '%.2f MB' % (os.path.getsize(outp)/1024/1024))
print('meta:', json.dumps(data['meta'], ensure_ascii=False))
print('dikes:', [(d['n'], len(d['p'])) for d in dikes])
