#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载 Copernicus DEM 30 m 与 ESA WorldCover 10 m 栅格（VoxCity 内置 AWS 开放数据）。

用法：
  python fetch_raster.py --bbox 114.286,30.537,114.309,30.554 --out ./raster
  python fetch_raster.py --bbox ... --out ./raster --dem-only

依赖：VoxCity 源码（默认 ~/MyProject/uzy/VoxCity/src）+ rasterio。
本机可直接用 ~/MyProject/tmp/voxcity-env/bin/python 运行本脚本。
"""
import argparse
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twin_common import parse_bbox


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bbox', required=True, help='lon0,lat0,lon1,lat1（WGS84）')
    ap.add_argument('--out', required=True, help='栅格输出目录')
    ap.add_argument('--voxcity', default=os.path.expanduser('~/MyProject/uzy/VoxCity/src'),
                    help='VoxCity src 目录')
    ap.add_argument('--dem-only', action='store_true')
    a = ap.parse_args()
    bbox = parse_bbox(a.bbox)
    os.makedirs(a.out, exist_ok=True)
    if not os.path.isdir(a.voxcity):
        raise SystemExit('VoxCity src 不存在：%s（用 --voxcity 指定）' % a.voxcity)
    sys.path.insert(0, a.voxcity)
    from voxcity.cli import rectangle_from_bbox
    from voxcity.downloader.aws_opendata import fetch_copernicus_dem
    rect = rectangle_from_bbox(*bbox)
    # VoxCity 内部固定把文件写到 cwd 下的 raster/，且返回相对路径；
    # 用临时工作目录隔离，再把结果拷进 --out，避免嵌套目录。
    cwd = os.getcwd()
    work = tempfile.mkdtemp(prefix='twin_raster_')
    produced = []
    os.chdir(work)
    try:
        produced.append(fetch_copernicus_dem(rect, 'raster'))
        print('DEM ->', produced[-1])
        if not a.dem_only:
            from voxcity.downloader.aws_opendata import fetch_esa_worldcover
            produced.append(fetch_esa_worldcover(rect, 'raster'))
            print('WorldCover ->', produced[-1])
    finally:
        os.chdir(cwd)
    for rel in produced:
        src = os.path.join(work, rel)
        dst = os.path.join(a.out, os.path.basename(str(rel)))
        if os.path.exists(src):
            shutil.copyfile(src, dst)
            print('  copied ->', dst)
        else:
            print('  [warn] 找不到下载产物：', src)
    shutil.rmtree(work, ignore_errors=True)
    # 打印高程范围，便于确定水面阈值
    try:
        import rasterio
        import numpy as np
        with rasterio.open(os.path.join(a.out, 'dem.tif')) as ds:
            arr = ds.read(1)
            print('DEM shape=%s bounds=%s min=%.1f max=%.1f' %
                  (arr.shape, ds.bounds, float(np.nanmin(arr)), float(np.nanmax(arr))))
        print('下一步：make_scene.py --water-threshold 取江面/湖面上沿（一般 20 m 左右）')
    except Exception as e:
        print('高程统计失败（不致命）：', e)


if __name__ == '__main__':
    main()
