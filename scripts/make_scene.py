#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装标准 scene_data.json：真实 DEM 地形 + OSM 矢量（或示意矢量）+ 主角占位。

用法：
  python make_scene.py --bbox 114.286,30.537,114.309,30.554 \
      --dem raster/dem.tif --osm osm.json --subject tower \
      --subject-xy 114.2966,30.5453 --extra subject.json --out scene_data.json

  # OSM 不可达时（fetch_osm.py 退出码 2）：
  python make_scene.py --bbox ... --dem raster/dem.tif --subject bridge --out scene_data.json

主角几何（bridge / tower / city 的构件层）由 assets/templates/<subject>/ 里的
build_*.py 生成，可用 --extra 把 tower / bridge / parts 等顶层键合并进来。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twin_common import (Projector, dem_to_terrain, parse_bbox, parse_osm,
                         schematic_fallback, write_json)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bbox', required=True)
    ap.add_argument('--dem', required=True, help='Copernicus DEM GeoTIFF')
    ap.add_argument('--osm', help='Overpass JSON；不传则使用示意矢量')
    ap.add_argument('--out', required=True)
    ap.add_argument('--subject', default='city', choices=['city', 'bridge', 'tower'])
    ap.add_argument('--subject-xy', help='主角中心 lon,lat（WGS84）')
    ap.add_argument('--extra', help='额外 JSON，顶层键合并（tower / bridge / parts 等）')
    ap.add_argument('--water-threshold', type=float, default=20.0)
    ap.add_argument('--lake-base', type=float, default=15.0)
    ap.add_argument('--schematic-buildings', type=int, default=1200)
    ap.add_argument('--nx', type=int, default=108)
    ap.add_argument('--ny', type=int, default=84)
    a = ap.parse_args()

    proj = Projector(parse_bbox(a.bbox))
    terrain, water_grid, dem_stats, _ = dem_to_terrain(
        a.dem, proj, nx=a.nx, ny=a.ny,
        water_threshold=a.water_threshold, lake_base=a.lake_base)
    subj_xy = None
    if a.subject_xy:
        lon, lat = [float(x) for x in a.subject_xy.split(',')]
        subj_xy = proj.xy(lon, lat)

    if a.osm and os.path.exists(a.osm):
        vec, vec_stats = parse_osm(a.osm, proj, terrain)
        osm_ok = True
    else:
        vec, vec_stats = schematic_fallback(proj, subj_xy, a.schematic_buildings)
        osm_ok = False
        print('[降级] OSM 缺失，周边路网/建筑为示意矢量（osm_ok=False）')

    meta = proj.meta()
    meta.update(dem_stats)
    meta.update({k: v for k, v in vec_stats.items() if k not in meta})
    meta.update(dict(subject=a.subject, n_floor=0, n_part=0,
                     tower_h=0, osm_ok=osm_ok, dem_ok=True,
                     subject_xy=[round(v, 1) for v in subj_xy] if subj_xy else None))

    scene = dict(meta=meta, terrain=terrain, waterGrid=water_grid,
                 waterPoly=vec['waterPoly'], roads=vec['roads'],
                 buildings=vec['buildings'], poi=vec['poi'],
                 subject={}, parts=[])
    if a.extra:
        with open(a.extra, encoding='utf-8') as f:
            extra = json.load(f)
        for k, v in extra.items():
            if k == 'meta':
                scene['meta'].update(v)
            else:
                scene[k] = v
        scene['meta']['n_part'] = len(scene.get('parts', []))
        if 'floors' in scene.get('subject', {}):
            scene['meta']['n_floor'] = len(scene['subject']['floors'])
    write_json(scene, a.out)
    print('%s  W=%.1f H=%.1f  buildings=%d roads=%s km water=%s km² osm=%s' %
          (a.out, proj.w, proj.h, meta.get('n_building', 0),
           meta.get('road_km', '?'), meta.get('water_km2', '?'), osm_ok))


if __name__ == '__main__':
    main()
