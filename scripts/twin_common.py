#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数字孪生公共库：坐标换算、DEM 栅格 → 地形/水面网格、Overpass JSON → 矢量要素。

数据结构契约见 references/pipeline.md。依赖 numpy + rasterio
（本机用 ~/MyProject/tmp/voxcity-env/bin/python 或 ~/MyProject/.venv-dem/bin/python）。
"""
import json
import math
import os

import numpy as np

# 1 场景单位 = 4 m；这是三套模板共用的约定，不要单独改
DEFAULT_SCALE = 4.0
ZEX = 3.2          # 垂直放大（three.js 侧 V() 里乘）
DEFAULT_NX, DEFAULT_NY = 108, 84
DEFAULT_GNX, DEFAULT_GNY = 150, 118


def parse_bbox(text):
    """'lon0,lat0,lon1,lat1' → tuple(float)（WGS84）。"""
    parts = [float(x) for x in text.replace(' ', '').split(',')]
    if len(parts) != 4:
        raise ValueError('bbox must be lon0,lat0,lon1,lat1')
    lon0, lat0, lon1, lat1 = parts
    if not (lon0 < lon1 and lat0 < lat1):
        raise ValueError('bbox order is west,south,east,north')
    return lon0, lat0, lon1, lat1


class Projector:
    """WGS84 经纬度 → 场景平面坐标（x 向东、y 向北，单位 = S 米）。"""

    def __init__(self, bbox, scale=DEFAULT_SCALE):
        self.lon0, self.lat0, self.lon1, self.lat1 = bbox
        self.s = scale
        lat_mid = (self.lat0 + self.lat1) / 2
        self.kx = 111320.0 * math.cos(math.radians(lat_mid))
        self.ky = 110540.0
        self.w = (self.lon1 - self.lon0) * self.kx / scale
        self.h = (self.lat1 - self.lat0) * self.ky / scale

    def xy(self, lon, lat):
        return [(lon - self.lon0) * self.kx / self.s,
                (lat - self.lat0) * self.ky / self.s]

    def meta(self):
        return dict(bbox=[self.lon0, self.lat0, self.lon1, self.lat1],
                    kx=round(self.kx), ky=self.ky, scale=self.s,
                    w=round(self.w, 1), h=round(self.h, 1))


def dem_to_terrain(dem_path, proj, nx=DEFAULT_NX, ny=DEFAULT_NY,
                   gnx=DEFAULT_GNX, gny=DEFAULT_GNY,
                   water_threshold=20.0, lake_base=15.0):
    """Copernicus DEM → terrain{nx,ny,z[],lc[]} + waterGrid + dem 统计。

    z 为「场景单位、未乘 ZEX」，以 lake_base 高程为 0 基准。
    lc：80 水面 / 20 高地林地 / 30 公园绿地 / 50 建成区。
    水面判定用 DEM 低地阈值——ESA WorldCover 在江河段常把水面误判为建成区。
    """
    import rasterio
    with rasterio.open(dem_path) as ds:
        dem = ds.read(1).astype(float)
        db = ds.bounds
    zs = np.zeros((ny, nx), float)
    for r in range(ny):
        lat = proj.lat0 + (proj.lat1 - proj.lat0) * r / (ny - 1)
        for c in range(nx):
            lon = proj.lon0 + (proj.lon1 - proj.lon0) * c / (nx - 1)
            fx = (lon - db.left) / (db.right - db.left) * (dem.shape[1] - 1)
            fy = (db.top - lat) / (db.top - db.bottom) * (dem.shape[0] - 1)
            c0 = max(0, min(dem.shape[1] - 2, int(fx)))
            r0 = max(0, min(dem.shape[0] - 2, int(fy)))
            tx, ty = fx - c0, fy - r0
            zs[r, c] = ((dem[r0, c0] * (1 - tx) + dem[r0, c0 + 1] * tx) * (1 - ty) +
                        (dem[r0 + 1, c0] * (1 - tx) + dem[r0 + 1, c0 + 1] * tx) * ty)
    water = zs < water_threshold
    lc = np.full((ny, nx), 50, dtype=int)
    lc[zs > 42] = 20
    lc[water] = 80
    z = np.where(water, 0.4, (zs - lake_base) / proj.s)
    gm = []
    for r in range(gny):
        for c in range(gnx):
            cc = min(nx - 1, int(c / (gnx - 1) * (nx - 1)))
            rr = min(ny - 1, int(r / (gny - 1) * (ny - 1)))
            gm.append(1 if water[rr, cc] else 0)
    terrain = dict(nx=nx, ny=ny,
                   z=[round(float(v), 3) for v in z.ravel()],
                   lc=lc.ravel().tolist())
    water_grid = dict(nx=gnx, ny=gny, m=gm)
    stats = dict(dem_min=round(float(np.nanmin(dem)), 1),
                 dem_max=round(float(np.nanmax(dem)), 1),
                 water_km2=round(sum(gm) / (gnx * gny) *
                                 (proj.w * proj.s / 1000) * (proj.h * proj.s / 1000), 3),
                 dem_grid=f'{dem.shape[1]}x{dem.shape[0]}')
    return terrain, water_grid, stats, water


def terrain_z(terrain, w, h, x, y):
    """从渲染网格双线性插值地面高程（与 three.js 侧 terrainZ 必须一致）。"""
    nx, ny = terrain['nx'], terrain['ny']
    fx = max(0, min(nx - 1.001, x / w * (nx - 1)))
    fy = max(0, min(ny - 1.001, y / h * (ny - 1)))
    c0, r0 = int(fx), int(fy)
    tx, ty = fx - c0, fy - r0
    i00 = r0 * nx + c0
    z = terrain['z']
    return ((z[i00] * (1 - tx) + z[i00 + 1] * tx) * (1 - ty) +
            (z[i00 + nx] * (1 - tx) + z[i00 + nx + 1] * tx) * ty)


HIGHWAY_K = {'motorway': 7, 'trunk': 6, 'primary': 5, 'secondary': 4,
             'tertiary': 3, 'residential': 2, 'service': 1, 'footway': 1,
             'path': 1, 'pedestrian': 1, 'unclassified': 2, 'living_street': 1}


def _geom_point(p, proj):
    """Overpass `out geom` 的点通常是 {'lat','lon'}；兼容 [lat,lon] / [lon,lat] / 已转坐标。"""
    if isinstance(p, dict):
        return proj.xy(float(p['lon']), float(p['lat']))
    a, b = float(p[0]), float(p[1])
    if abs(a) <= 90 and abs(b) <= 180:
        if proj.lat0 - 1 <= a <= proj.lat1 + 1 and proj.lon0 - 1 <= b <= proj.lon1 + 1:
            return proj.xy(b, a)
        if proj.lon0 - 1 <= a <= proj.lon1 + 1 and proj.lat0 - 1 <= b <= proj.lat1 + 1:
            return proj.xy(a, b)
    return [a, b]


def _closed(poly, tol=0.01):
    if len(poly) > 2:
        a, b = poly[0], poly[-1]
        if abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol:
            poly = poly[:-1]
    return poly if len(poly) >= 3 else None


def _area(poly, s):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2 * s * s


def parse_osm(osm, proj, terrain=None):
    """Overpass [out:json] 结果 → roads / buildings / waterPoly / poi。

    支持 OutPass `out geom` 的 geometry 字段；否则回落到 node 表查坐标。
    按 way/relation id 去重，校验 polygon 闭合，建筑高度取 building:levels / height，
    缺失时按用途推定。返回 (dict, stats)。
    """
    if isinstance(osm, (str, bytes)):
        path = osm if isinstance(osm, str) else osm.decode()
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                osm = json.load(f)
        else:
            osm = json.loads(path)
    els = osm.get('elements', [])
    nodes = {}
    for e in els:
        if e.get('type') == 'node' and 'lat' in e:
            nodes[e['id']] = proj.xy(e['lon'], e['lat'])
    roads, buildings, water_poly, poi = [], [], [], []
    seen = set()
    for e in els:
        if e.get('type') != 'way' or e.get('id') in seen:
            continue
        tags = e.get('tags', {}) or {}
        if e.get('geometry'):
            geom = [_geom_point(g, proj) for g in e['geometry']]
        else:
            geom = [nodes[n] for n in e.get('nodes', []) if n in nodes]
        if len(geom) < 2:
            continue
        pts = [[round(p[0], 2), round(p[1], 2)] for p in geom]
        seen.add(e['id'])
        if 'highway' in tags:
            roads.append(dict(k=HIGHWAY_K.get(tags['highway'], 2),
                              n=tags.get('name', ''), p=pts,
                              id=e['id']))
        elif 'building' in tags:
            poly = _closed(pts)
            if not poly:
                continue
            try:
                lv = int(float(tags.get('building:levels', 0)))
            except ValueError:
                lv = 0
            if 'height' in tags:
                try:
                    lv = max(lv, int(float(str(tags['height']).replace('m', '')) / 3.1))
                except ValueError:
                    pass
            if not lv:
                lv = {'retail': 2, 'industrial': 2, 'office': 8,
                      'residential': 6, 'apartments': 12}.get(tags['building'], 3)
            h = lv * 3.1 / proj.s
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            bz = None
            if terrain is not None:
                bz = max(terrain_z(terrain, proj.w, proj.h, p[0], p[1]) for p in poly) - 0.1
            buildings.append(dict(p=poly, h=round(h, 2), lv=lv, n=tags.get('name'),
                                  a=round(_area(poly, proj.s)), c=[round(cx, 1), round(cy, 1)],
                                  s='OSM building:levels' if 'building:levels' in tags else '按用途推定',
                                  k='osm', id=e['id'], bz=bz,
                                  at={k: v for k, v in
                                      {'name': tags.get('name'),
                                       'building': tags.get('building')}.items() if v}))
        elif tags.get('waterway') or tags.get('natural') == 'water':
            water_poly.append(dict(p=pts, id=e['id']))
        elif tags.get('name'):
            poi.append(dict(n=tags['name'], p=pts[len(pts) // 2], z=2.0, hot=False))
    stats = dict(n_elements=len(els), n_road=len(roads), n_building=len(buildings),
                 n_named=sum(1 for b in buildings if b['n']),
                 road_km=round(sum(math.dist(a, b) * proj.s for r in roads
                                   for a, b in zip(r['p'][:-1], r['p'][1:])) / 1000, 2))
    return dict(roads=roads, buildings=buildings, waterPoly=water_poly, poi=poi), stats


def schematic_fallback(proj, subject_xy=None, building_count=1200, seed=1985):
    """OSM 不可达时的示意矢量：规则路网 + 网格建筑 + 空 POI。

    必须在 meta 里标 osm_ok=False，并在页面上明示「示意矢量，不作量测」。
    """
    import random
    random.seed(seed)
    sx, sy = subject_xy or (proj.w / 2, proj.h / 2)
    W, H = proj.w, proj.h
    roads = []
    for i, yy in enumerate([0.20, 0.38, 0.56, 0.74]):
        roads.append(dict(k=5 - (i % 2), n='示意主干路 %d' % (i + 1),
                          p=[[0, H * yy], [W * 0.35, H * (yy + 0.01)],
                             [W * 0.7, H * yy], [W, H * (yy - 0.01)]]))
    for i, xx in enumerate([0.22, 0.48, 0.76]):
        roads.append(dict(k=4, n='示意纵路 %d' % (i + 1),
                          p=[[W * xx, 0], [W * (xx + 0.01), H * 0.5], [W * xx, H]]))
    buildings = []
    step = math.sqrt(W * H / max(building_count, 1))
    gx, gy = int(W / step), int(H / step)
    for a in range(1, gx):
        for b in range(1, gy):
            x = a * step + random.uniform(-step * 0.12, step * 0.12)
            y = b * step + random.uniform(-step * 0.12, step * 0.12)
            if abs(x - sx) < step * 3 and abs(y - sy) < step * 3:
                continue
            if random.random() < 0.08:
                continue
            w = step * random.uniform(0.42, 0.72)
            d = step * random.uniform(0.42, 0.72)
            lv = random.choice([2, 3, 4, 6, 8, 12, 18])
            poly = [[x - w / 2, y - d / 2], [x + w / 2, y - d / 2],
                    [x + w / 2, y + d / 2], [x - w / 2, y + d / 2]]
            buildings.append(dict(p=poly, h=round(lv * 3.1 / proj.s, 2), lv=lv, n=None,
                                  a=round(w * d * proj.s * proj.s), c=[round(x, 1), round(y, 1)],
                                  s='示意推定层数 ×3.1 m', k='schematic', at=None))
    return dict(roads=roads, buildings=buildings, waterPoly=[], poi=[]), \
        dict(n_road=len(roads), n_building=len(buildings), n_named=0,
             road_km=round(sum(math.dist(a, b) * proj.s for r in roads
                               for a, b in zip(r['p'][:-1], r['p'][1:])) / 1000, 2),
             osm_ok=False)


def write_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    return path
