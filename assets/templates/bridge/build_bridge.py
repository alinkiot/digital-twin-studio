#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
杭州江东大桥（钱江九桥）数字孪生 · 底图数据构建

链路（与参考文章一致）：
  1. Overpass 按 bbox 抓取 OSM 矢量 → 按 id 去重、校验坐标与轮廓闭合
  2. 经纬度 → 局部平面米制：经度 × cos(φ) 做纬度修正
  3. 统一场景单位：1 unit = 4 m
  4. 先铺地理骨架：Copernicus DEM / ESA WorldCover 钱塘江水格 / 路网 / 水系
  5. 再叠工程构件：真实桥面矢量 + 按公开设计参数重建的桥塔、空间主缆、吊索、桥墩
  6. 输出紧凑 JSON 供 Three.js 挤出、点选构件看属性

真实设计参数（公开资料）：
  全长 4332 m；桥梁范围 3520 m；跨江桥梁 2248 m；两侧引桥 1272 m
  双向八车道 / 80 km·h⁻¹ / 城-A 级 / 2008-12-26 通车
  通航孔：两座三跨空间缆自锚式悬索桥 83+260+83 m + 一座刚构桥 91.5+160+91.5 m
  独柱桥塔、分离式钢箱梁、空间缆索、矢跨比 1/4.5、吊索间距 9 m
  悬索段桥宽 46.5 m（含风嘴 47 m）；梁式段双幅 18.75×2 m
  通航净空 ≥24 m；设计通航水位 7.64 m
"""
import json, math, os, collections
import numpy as np
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
OSM = os.path.join(HERE, 'osm_bridge.json')
DEM_TIF = os.path.join(HERE, 'raster', 'dem.tif')
LC_TIF = os.path.join(HERE, 'raster', 'land_cover.tif')

LON0, LAT0, LON1, LAT1 = 120.380, 30.290, 120.445, 30.350
KX = 111320.0 * math.cos(math.radians((LAT0 + LAT1) / 2))
KY = 110540.0
S = 4.0
W = round((LON1 - LON0) * KX / S)
H = round((LAT1 - LAT0) * KY / S)

def xy(lon, lat):
    return [round((lon - LON0) * KX / S, 1), round((lat - LAT0) * KY / S, 1)]

def ll2m(lon, lat):
    return ((lon - LON0) * KX, (lat - LAT0) * KY)

# ---------- 栅格读取工具 ----------
with rasterio.open(DEM_TIF) as ds:
    dem = ds.read(1).astype(float)
    db = ds.bounds; dr = ds.res
with rasterio.open(LC_TIF) as ds:
    lrgb = ds.read()
    lb = ds.bounds; lr = ds.res

import sys
sys.path.insert(0, '/Users/kenneth/MyProject/uzy/VoxCity/src')
from voxcity.downloader.aws_opendata import _worldcover_rgb_lut, _WORLDCOVER_CODES
_lut = _worldcover_rgb_lut()
lc_codes = np.zeros(lrgb.shape[1:], dtype=np.uint8)
for code in _WORLDCOVER_CODES:
    col = tuple(int(x) for x in _lut[code])
    m = (lrgb[0] == col[0]) & (lrgb[1] == col[1]) & (lrgb[2] == col[2])
    lc_codes[m] = code

def sample(arr, bounds, res, lon, lat, nearest=False):
    left, bottom, right, top = bounds
    c = (lon - left) / res[0]; r = (top - lat) / res[1]
    if nearest:
        c, r = int(round(c)), int(round(r))
        if 0 <= r < arr.shape[0] and 0 <= c < arr.shape[1]: return float(arr[r, c])
        return 0.0
    c0, r0 = int(c), int(r)
    if not (0 <= r0 < arr.shape[0]-1 and 0 <= c0 < arr.shape[1]-1): return 0.0
    tx, ty = c-c0, r-r0
    return float((arr[r0,c0]*(1-tx)+arr[r0,c0+1]*tx)*(1-ty)
                 + (arr[r0+1,c0]*(1-tx)+arr[r0+1,c0+1]*tx)*ty)

def DEM(lon, lat): return max(0.0, sample(dem, db, dr, lon, lat))
def LC(lon, lat): return int(sample(lc_codes, lb, lr, lon, lat, nearest=True))
def WATER(lon, lat): return LC(lon, lat) == 80

# ---------- OSM ----------
raw = json.load(open(OSM, encoding='utf-8'))['elements']
seen = set(); els = []
for e in raw:
    if e['id'] in seen: continue
    seen.add(e['id']); els.append(e)
byid = {e['id']: e for e in els}

def ring_of(e):
    g = e.get('geometry') or []
    p = [q for q in g if q and 'lon' in q and 'lat' in q]
    return p if len(p) >= 2 else None

def area_m2(pts):
    a = 0.0
    X = [(p['lon']-LON0)*KX for p in pts]; Y = [(p['lat']-LAT0)*KY for p in pts]
    for i in range(len(X)):
        j = (i+1) % len(X); a += X[i]*Y[j]-X[j]*Y[i]
    return abs(a)/2

# ---------- 1. 建筑 ----------
buildings = []
for e in els:
    t = e.get('tags', {})
    if 'building' not in t or e['type'] != 'way': continue
    pts = ring_of(e)
    if not pts or len(pts) < 3: continue
    ar = area_m2(pts)
    if ar < 12: continue
    if not (pts[0]['lon'] == pts[-1]['lon'] and pts[0]['lat'] == pts[-1]['lat']):
        pts = pts + [pts[0]]
    Xs = [p['lon'] for p in pts]; Ys = [p['lat'] for p in pts]
    cx, cy = sum(Xs)/len(Xs), sum(Ys)/len(Ys)
    lv = None
    if 'building:levels' in t:
        try: lv = int(float(t['building:levels']))
        except: pass
    h, src = 0.0, ''
    if lv: h, src = lv*3.2, 'OSM 层数'
    elif 'height' in t:
        try: h, src = float(str(t['height']).replace('m','').strip()), 'OSM 标注高度'
        except: pass
    if h <= 0:
        kind = t.get('building','')
        h = 24.0 if kind in ('commercial','office','retail','hotel','industrial','warehouse') else 10.0
        src = '按用途推定（示意）'
    h = min(h, 90.0)
    if not lv: lv = max(1, int(round(h/3.2)))
    name = t.get('name') or t.get('name:zh') or ''
    attrs = {k:t[k] for k in ('name','name:en','building','amenity','office','shop',
                              'addr:street','building:levels','height','landuse') if k in t}
    buildings.append({
        'id': e['id'], 'p': [xy(p['lon'],p['lat']) for p in pts],
        'h': round(h/S,2), 'bz': round(max(DEM(cx,cy), 4.0)/S, 2),
        'lv': lv, 'a': round(ar), 'n': name,
        'k': t.get('building','yes'), 's': src, 'at': attrs,
        'c': [round(cx,6), round(cy,6)],
    })

# ---------- 2. 路网 ----------
ROAD = {'motorway':7,'trunk':6,'primary':5,'secondary':4,'tertiary':3,
        'residential':2,'unclassified':2,'service':1,'pedestrian':2,
        'footway':1,'cycleway':1,'construction':1,'living_street':1,'motorway_link':5}
roads = []
for e in els:
    t = e.get('tags', {})
    hw = t.get('highway')
    if not hw or hw not in ROAD: continue
    # 江东大桥主线/匝道由桥面构件单独表达，其余跨河小桥保留以维持路网连续
    nm = t.get('name','')
    if t.get('bridge') and (('江东大桥' in nm) or t.get('ref')=='G9221'
                            or t.get('layer') in ('2','3')):
        continue
    pts = ring_of(e)
    if not pts or len(pts) < 2: continue
    roads.append({'p':[xy(p['lon'],p['lat']) for p in pts], 'k':ROAD[hw],
                  'n':t.get('name',''), 'hw':hw})

# ---------- 3. 次要水系（OSM 真实轮廓） ----------
water_poly = []
for e in els:
    t = e.get('tags', {})
    if t.get('natural') != 'water' and t.get('waterway') not in ('river','riverbank'): continue
    pts = ring_of(e)
    if not pts or len(pts) < 4: continue
    if e['type'] != 'way': continue
    if not (pts[0]['lon']==pts[-1]['lon'] and pts[0]['lat']==pts[-1]['lat']): continue
    ar = area_m2(pts)
    if ar > 100000: continue          # 钱塘江主体由栅格铺，避免与大江面重叠
    if ar < 300: continue
    water_poly.append({'p':[xy(p['lon'],p['lat']) for p in pts],
                       'n':t.get('name',''), 'w':t.get('water') or t.get('waterway','')})

# ---------- 4. 地形 / 江面骨架栅格 ----------
# ESA WorldCover 在这段把桥面与强涌潮露滩判成「建成区」(LC=50)，
# 但 Copernicus DEM 的江面稳定在 1.5 m、两岸 6~18 m，分界干净。
# 因此江面骨架统一用 DEM<3 m 判定，WorldCover 只用于陆地配色。
RIVER_T = 3.0
def IS_RIVER(lon,lat): return DEM(lon,lat) < RIVER_T

NX, NY = 62, 58
tz, tlc = [], []
for r in range(NY):
    for c in range(NX):
        lon = LON0 + (c/(NX-1))*(LON1-LON0)
        lat = LAT0 + (r/(NY-1))*(LAT1-LAT0)
        z = DEM(lon,lat); code = LC(lon,lat)
        if z < RIVER_T: code = 80
        tz.append(round(z/S,2)); tlc.append(code)
terrain = {'nx':NX,'ny':NY,'z':tz,'lc':tlc,'w':W,'h':H}
WGX, WGY = 79, 73
wm = []
for r in range(WGY):
    for c in range(WGX):
        lon = LON0 + (c/(WGX-1))*(LON1-LON0)
        lat = LAT0 + (r/(WGY-1))*(LAT1-LAT0)
        wm.append(1 if IS_RIVER(lon,lat) else 0)
water_grid = {'nx':WGX,'ny':WGY,'m':wm}
water_km2 = round(sum(wm)/len(wm) * (LON1-LON0)*KX * (LAT1-LAT0)*KY / 1e6, 2)

# ---------- 5. 桥轴线：两条 OSM 上下行矢量取中线 ----------
def polyline_m(pts):
    return [ll2m(p['lon'],p['lat']) for p in pts]

def resample(P, step=5.0):
    """按弧长重采样（米制）"""
    cum = [0.0]
    for i in range(len(P)-1):
        cum.append(cum[-1]+math.hypot(P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]))
    L = cum[-1]; out=[]; j=0; s=0.0
    while s <= L:
        while j < len(cum)-2 and cum[j+1] < s: j += 1
        t = (s-cum[j])/(cum[j+1]-cum[j]) if cum[j+1]>cum[j] else 0
        out.append((P[j][0]+(P[j+1][0]-P[j][0])*t, P[j][1]+(P[j+1][1]-P[j][1])*t))
        s += step
    return out, L

A = polyline_m(byid[152634143]['geometry'])             # 东南 → 西北
B = list(reversed(polyline_m(byid[154701036]['geometry'])))  # 东南 → 西北
RA, LA = resample(A); RB, LB = resample(B)
n = min(len(RA), len(RB))
axis = [((RA[i][0]+RB[i][0])/2, (RA[i][1]+RB[i][1])/2) for i in range(n)]
# 统一到 0..LA 里程
axis_len = 0.0
for i in range(len(axis)-1):
    axis_len += math.hypot(axis[i+1][0]-axis[i][0], axis[i+1][1]-axis[i][1])

# 两端按切线延伸出引桥（设计全长 4332 m，OSM 实测桥面 way 约 2930 m）
EXT = (4332.0 - axis_len)/2
def extend(P, d, at_head):
    if at_head:
        p0,p1 = P[1],P[0]   # 反方向
    else:
        p0,p1 = P[-2],P[-1]
    dx,dy = p1[0]-p0[0], p1[1]-p0[1]; L=math.hypot(dx,dy)
    ux,uy = dx/L, dy/L
    out=[]
    for k in range(1, int(d/5)+1):
        t = k*5
        out.append((p1[0]+ux*t, p1[1]+uy*t))
    return out
axis_full = list(reversed(extend(axis, EXT, True))) + axis + extend(axis, EXT, False)
# 累计里程（米）
cum = [0.0]
for i in range(len(axis_full)-1):
    cum.append(cum[-1]+math.hypot(axis_full[i+1][0]-axis_full[i][0], axis_full[i+1][1]-axis_full[i][1]))
TOTAL = cum[-1]

def at(dist):
    """按里程取轴线点（米制）"""
    if dist <= 0: return axis_full[0]
    if dist >= TOTAL: return axis_full[-1]
    lo,hi = 0,len(cum)-1
    while lo+1 < hi:
        mid=(lo+hi)//2
        if cum[mid] <= dist: lo=mid
        else: hi=mid
    t=(dist-cum[lo])/(cum[hi]-cum[lo]) if cum[hi]>cum[lo] else 0
    return (axis_full[lo][0]+(axis_full[hi][0]-axis_full[lo][0])*t,
            axis_full[lo][1]+(axis_full[hi][1]-axis_full[lo][1])*t)

def tangent(dist):
    a=at(max(0,dist-6)); b=at(min(TOTAL,dist+6))
    dx,dy=b[0]-a[0],b[1]-a[1]; L=math.hypot(dx,dy) or 1
    return (dx/L,dy/L)

def lonlat_of(m): return (LON0 + m[0]/KX, LAT0 + m[1]/KY)

# ---------- 6. 跨江段：沿轴线用 DEM 低地检测连续江面段 ----------
wet = []
for d in np.arange(0, TOTAL, 10.0):
    lo,la = lonlat_of(at(d)); wet.append(IS_RIVER(lo,la))
best=(0,0); cur=None
for i,v in enumerate(wet+[False]):
    if v and cur is None: cur=i
    elif not v and cur is not None:
        if i-cur > best[1]-best[0]: best=(cur,i)
        cur=None
w_s = best[0]*10.0; w_e = min(best[1]*10.0, TOTAL)
print('跨江水面段 里程 %.0f–%.0f m（长 %.0f m）' % (w_s,w_e,w_e-w_s))

# 按真实 2248 m 跨江桥梁长度居中对齐到水段
RIVER_LEN = 2248.0
mid = (w_s+w_e)/2
river_s = max(0.0, min(TOTAL-RIVER_LEN, mid-RIVER_LEN/2))
river_e = river_s + RIVER_LEN
print('跨江桥梁段 里程 %.0f–%.0f m' % (river_s,river_e))

# ---------- 7. 桥型分段（按公开设计参数） ----------
# 三座通航孔桥串联，余下为跨江连续梁引桥；整体居中于跨江段
SUSP_L, RIGID_L = 426.0, 343.0
triples = [('西侧自锚式悬索桥', SUSP_L, 'susp'),
           ('中央连续刚构桥', RIGID_L, 'rigid'),
           ('东侧自锚式悬索桥', SUSP_L, 'susp')]
tri_total = sum(x[1] for x in triples)
tri_s = river_s + (RIVER_LEN-tri_total)/2
spans=[]; d=tri_s
for name,length,kind in triples:
    spans.append({'n':name,'s':d,'e':d+length,'k':kind,'l':length}); d+=length
# 两侧跨江连续梁段
spans.insert(0, {'n':'西侧跨江连续梁','s':river_s,'e':tri_s,'k':'beam','l':tri_s-river_s})
spans.append({'n':'东侧跨江连续梁','s':tri_s+tri_total,'e':river_e,'k':'beam','l':river_e-tri_s-tri_total})

# ---------- 8. 桥面高程（相对 DEM 江面，避免混用吴淞水位与椭球高基准） ----------
RIVER_DEM = 1.5          # Copernicus DEM 实测钱塘江江面高程 (m)
WATER_LEVEL = 7.64       # 设计通航水位（吴淞基准，仅作展示信息）
CLEARANCE = 24.0         # 通航净空
GIRDER = 3.5             # 钢箱梁梁高
DECK_Z = RIVER_DEM + CLEARANCE + GIRDER        # ≈ 29.0 m（椭球高基准）
TOWER_H = 62.0           # 塔顶高出桥面；矢跨比 1/4.5 → 260/4.5≈57.8 m
SAG = 260.0/4.5

def z_scene(m): return round(m/S, 2)
deck_z = z_scene(DECK_Z)

# 桥面折线（场景坐标，沿里程每 15 m 一点）
deck_pts=[]
for d in np.arange(0, TOTAL+1, 15.0):
    m=at(d); deck_pts.append([round(m[0]/S,1), round(m[1]/S,1)])
# 上下行分离箱梁：沿法线各偏移 9.5 m
def normals_of(pts):
    out=[]
    for i in range(len(pts)):
        a=pts[max(0,i-1)]; b=pts[min(len(pts)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1]; L=math.hypot(dx,dy) or 1
        out.append((-dy/L,dx/L))
    return out
NORM=normals_of(deck_pts)
SEP = z_scene(9.5)
deckA=[[round(deck_pts[i][0]+NORM[i][0]*SEP,1), round(deck_pts[i][1]+NORM[i][1]*SEP,1)] for i in range(len(deck_pts))]
deckB=[[round(deck_pts[i][0]-NORM[i][0]*SEP,1), round(deck_pts[i][1]-NORM[i][1]*SEP,1)] for i in range(len(deck_pts))]

# ---------- 9. 工程构件（可点选） ----------
parts=[]; towers=[]; cables=[]; hangers=[]; piers=[]; anchors=[]
def P(name,kind,s,e,**kw):
    mid_ = at((s+e)/2)
    o={'id':len(parts),'n':name,'k':kind,'s':round(s,1),'e':round(e,1),
       'l':round(e-s,1),'c':[round(mid_[0]/S,1),round(mid_[1]/S,1)],
       'st':'K%d+%03d'%(int((s+e)/2//1000), round((s+e)/2)%1000),
       'mat':'','spec':'','src':'按公开设计参数重建（非竣工 BIM）'}
    o.update(kw); parts.append(o); return o

for sp in spans:
    gp = P(sp['n']+' · 主梁','girder',sp['s'],sp['e'],
      mat='分离式流线形钢箱梁 / 预应力砼连续梁',
      spec=('桥宽 46.5 m（含风嘴 47 m）' if sp['k']=='susp' else '双幅 18.75×2 m'),
      deck=sp['k'])
    sp['pid'] = gp['id']

# 桥塔：每座悬索桥 2 座独柱塔，位于 83 | 260 分界
for sp in spans:
    if sp['k']!='susp': continue
    for j,off in enumerate((83.0, 83.0+260.0), start=1):
        d=sp['s']+off; m=at(d); ux,uy=tangent(d); nx,ny=-uy,ux
        tp = P('%s · %d 号独柱主塔'%(sp['n'],j),'tower',sp['s'],sp['e'],
          mat='钢筋混凝土独柱塔 / 空间主索鞍',
          spec='桥面以上约 62 m；矢跨比 1/4.5', d=round(d,1))
        towers.append({'p':[round(m[0]/S,1),round(m[1]/S,1)],
                       'ux':round(ux,4),'uy':round(uy,4),'nx':round(nx,4),'ny':round(ny,4),
                       'n':tp['n'],'d':round(d,1),'pid':tp['id']})
        pp = P('%s · %d 号主墩/承台'%(sp['n'],j),'pier',sp['s'],sp['e'],
          mat='钢筋混凝土 / 大直径变截面深孔桩',spec='主通航孔支承墩',d=round(d,1))
        piers.append({'p':[round(m[0]/S,1),round(m[1]/S,1)],'d':round(d,1),
                      'n':pp['n'],'main':1,'pid':pp['id']})

# 空间主缆 + 吊索（每座悬索桥中跨 260 m）
for sp in spans:
    if sp['k']!='susp': continue
    t1,t2 = at(sp['s']+83.0), at(sp['s']+83.0+260.0)
    # 两侧空间缆：塔顶交汇于中央，跨中横向张开到桥面两侧
    cable_pids=[]
    for side in (-1,1):
        line=[]
        for k in range(27):
            u=k/26
            # 平面位置线性插值
            mx=t1[0]+(t2[0]-t1[0])*u; my=t1[1]+(t2[1]-t1[1])*u
            # 横向张开：塔顶 0，跨中 ±19 m
            spread=(19.0*side)*math.sin(math.pi*u)**0.7
            d=sp['s']+83.0+260.0*u
            ux,uy=tangent(d); nx,ny=-uy,ux
            mx+=nx*spread; my+=ny*spread
            # 抛物线垂度：塔顶 DECK_Z+TOWER_H，跨中 DECK_Z+TOWER_H-SAG
            zz=DECK_Z+TOWER_H-SAG*4*u*(1-u)
            line.append([round(mx/S,1),round(my/S,1),z_scene(zz)])
        cp = P(sp['n']+' · 空间主缆 '+('上游' if side<0 else '下游'),'cable',sp['s']+83.0,sp['s']+343.0,
          mat='高强度镀锌钢丝 / 索夹',
          spec='中跨 260 m，矢跨比 1/4.5；塔顶交汇、跨中横向张开成空间缆')
        cable_pids.append(cp['id'])
        cables.append({'p':line,'n':cp['n'],
                       's':sp['s']+83.0,'e':sp['s']+83.0+260.0,'pid':cp['id']})
    # 吊索：中跨每 9 m 一道，两侧各一
    hp = P(sp['n']+' · 吊索组','hanger',sp['s']+83.0,sp['s']+343.0,
      mat='平行钢丝吊索 + 索夹',spec='间距 9 m，双向布置')
    nh=0
    d=sp['s']+83.0+9.0
    while d < sp['s']+83.0+260.0-4:
        u=(d-(sp['s']+83.0))/260.0
        zc=DECK_Z+TOWER_H-SAG*4*u*(1-u)
        m=at(d); ux,uy=tangent(d); nx,ny=-uy,ux
        for side in (-1,1):
            spread=(19.0*side)*math.sin(math.pi*u)**0.7
            hangers.append({'a':[round((m[0]+nx*spread)/S,1),round((m[1]+ny*spread)/S,1),z_scene(zc)],
                            'b':[round((m[0]+nx*spread)/S,1),round((m[1]+ny*spread)/S,1),z_scene(DECK_Z+0.6)],
                            'pid':hp['id']})
            nh+=1
        d+=9.0
    hp['spec']='间距 9 m，共 %d 根（双向）'%nh; hp['count']=nh
    # 边跨主缆（不设吊索，中央分隔带内平行下垂至锚固点）
    for side,dd in ((-1,0.0),(1,343.0)):
        line=[]
        for k in range(9):
            u=k/8
            d0=sp['s']+(83.0*u if dd==0 else 83.0+260.0+83.0*(1-u))
            m=at(d0)
            zz=DECK_Z+TOWER_H-(TOWER_H-6.0)*u
            line.append([round(m[0]/S,1),round(m[1]/S,1),z_scene(zz)])
        ap = P(sp['n']+' · 边跨主缆/自锚锚固端','cable',sp['s'],sp['e'],
          mat='高强度镀锌钢丝 + 钢横梁锚固区',
          spec='边跨 83 m 不设吊索，中央分隔带内平行布置，自锚于主梁')
        cables.append({'p':line,'n':ap['n'],'pid':ap['id'],'side':1})
        anchors.append({'p':[round(at(sp['s']+dd)[0]/S,1),round(at(sp['s']+dd)[1]/S,1)],
                        'n':ap['n'],'pid':ap['id']})

# 引桥 / 跨江连续梁桥墩：每 40 m
for sp in spans:
    if sp['k'] not in ('beam','rigid'): continue
    pp = P(sp['n']+' · 桥墩群','pier',sp['s'],sp['e'],
      mat='钢筋混凝土 / 桩柱式墩',spec='标准跨径约 40 m')
    cnt=0; d=sp['s']+20.0
    while d < sp['e']-10:
        m=at(d)
        piers.append({'p':[round(m[0]/S,1),round(m[1]/S,1)],'d':round(d,1),
                      'n':pp['n']+' K%.0f'%d,'main':0,'pid':pp['id']})
        cnt+=1; d+=40.0
    pp['spec']='标准跨径约 40 m，共 %d 座'%cnt; pp['count']=cnt

# 两岸引桥（陆上段）：每隔 45 m 一墩
for s0,e0,lbl in ((0.0,river_s,'西岸 · 下沙侧引桥'),(river_e,TOTAL,'东岸 · 江东侧引桥')):
    if e0-s0 < 30: continue
    ap = P(lbl,'approach',s0,e0,mat='预应力砼连续梁',
           spec='设计引桥合计 1272 m；本段按设计长度示意延伸，非 OSM 实测')
    cnt=0; d=s0+22.0
    while d < e0-10:
        m=at(d)
        piers.append({'p':[round(m[0]/S,1),round(m[1]/S,1)],'d':round(d,1),
                      'n':ap['n']+' 墩 K%.0f'%d,'main':0,'pid':ap['id']})
        cnt+=1; d+=45.0
    ap['spec']+='；共 %d 座墩'%cnt

# ---------- 10. 地名标注 ----------
POI = [
    ('江东大桥 · 主通航孔', 120.4095, 30.3198, 1),
    ('钱塘江', 120.4110, 30.3090, 0),
    ('下沙 · 德胜快速路', 120.3940, 30.3270, 0),
    ('江东片区 · 江东大道', 120.4270, 30.3125, 0),
    ('下沙高教园区', 120.3890, 30.3180, 0),
    ('钱江观潮城', 120.4300, 30.3020, 0),
]
poi=[{'n':n,'p':xy(lo,la),'z':z_scene(DECK_Z+14 if hot else 6.0),'hot':hot} for n,lo,la,hot in POI]

# ---------- 统计 ----------
road_len = sum(sum(math.hypot(r['p'][i+1][0]-r['p'][i][0], r['p'][i+1][1]-r['p'][i][1])
                   for i in range(len(r['p'])-1))*S for r in roads)
meta = {
    'title':'杭州江东大桥 · 桥梁数字孪生',
    'bbox':[LON0,LAT0,LON1,LAT1],'kx':round(KX),'ky':KY,'scale':S,'w':W,'h':H,
    'n_building':len(buildings),'n_road':len(roads),'n_water':len(water_poly),
    'road_km':round(road_len/1000,1),'water_km2':water_km2,
    'bld_km2':round(sum(b['a'] for b in buildings)/1e6,2),
    'osm_bytes':os.path.getsize(OSM),'named':sum(1 for b in buildings if b['n']),
    'src_h':dict(collections.Counter(b['s'] for b in buildings)),
    'bridge':{
        'total':round(TOTAL),'osm_deck':round(axis_len),'river':RIVER_LEN,
        'deck_z':deck_z,'tower_h':z_scene(TOWER_H),'water_level':WATER_LEVEL,
        'clearance':CLEARANCE,'sag':z_scene(SAG),'river_s':round(river_s,1),
        'river_e':round(river_e,1),'sep':SEP,
        'n_part':len(parts),'n_tower':len(towers),'n_cable':len(cables),
        'n_hanger':len(hangers),'n_pier':len(piers),
        'spans':[{'n':s['n'],'s':round(s['s'],1),'e':round(s['e'],1),'k':s['k'],'l':round(s['l'],1)} for s in spans],
    }
}
span_pids=[{'s':round(s['s'],1),'e':round(s['e'],1),'pid':s['pid'],'k':s['k'],'n':s['n']} for s in spans]
appr_pids=[{'s':round(p['s'],1),'e':round(p['e'],1),'pid':p['id']} for p in parts if p['k']=='approach']
data = {'meta':meta,'buildings':buildings,'roads':roads,'waterPoly':water_poly,
        'terrain':terrain,'waterGrid':water_grid,'poi':poi,
        'bridge':{'axis':[[round(p[0]/S,1),round(p[1]/S,1)] for p in axis_full],
                  'deck':deck_pts,'deckA':deckA,'deckB':deckB,'cum':[round(v,1) for v in cum],
                  'total':round(TOTAL,1),'deckZ':deck_z,'sep':SEP,
                  'towers':towers,'cables':cables,'hangers':hangers,
                  'piers':piers,'anchors':anchors,'parts':parts,'spans':meta['bridge']['spans'],
                  'spanPids':span_pids,'apprPids':appr_pids}}

outp = os.path.join(HERE,'bridge_data.json')
json.dump(data, open(outp,'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
print('OK ->',outp,'%.2f MB'%(os.path.getsize(outp)/1024/1024))
print('meta:',json.dumps(meta,ensure_ascii=False)[:900])
print('parts by kind:',dict(collections.Counter(p['k'] for p in parts)))
