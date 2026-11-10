#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多镜像探测拉取 Overpass OSM 矢量；全不可达时明确降级为示意矢量。

用法：
  python fetch_osm.py --bbox 120.125,30.225,120.165,30.265 --out osm.json
  python fetch_osm.py --bbox ... --out osm.json --mirrors mailru,kumi --timeout 20
  python fetch_osm.py --bbox ... --out osm.json --query 'way["building"]({bbox});out geom;'
  # 注意查询里的占位符是单花括号 {bbox}，会被替换为 south,west,north,east
  python fetch_osm.py --from-file /path/to/existing.json --out osm.json

退出码：0 = 拿到真实 OSM；2 = 全部镜像不可达（调用方必须走 schematic_fallback，
并在页面与说明文档里标注「示意矢量，非实测 OSM，不作量测」）。
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twin_common import parse_bbox, write_json

# 顺序即优先级。坑位见 references/data_sources.md
MIRRORS = [
    ('mailru', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter'),
    ('overpass.de', 'https://overpass-api.de/api/interpreter'),
    ('kumi', 'https://overpass.kumi.systems/api/interpreter'),
    ('lz4', 'https://lz4.overpass-api.de/api/interpreter'),
    ('nchc', 'https://overpass.nchc.org.tw/api/interpreter'),
    ('private.coffee', 'https://overpass.private.coffee/api/interpreter'),
]

DEFAULT_QUERY = '''[out:json][timeout:60];
(
  way["highway"]({bbox});
  way["building"]({bbox});
  way["waterway"]({bbox});
  way["natural"="water"]({bbox});
  relation["natural"="water"]({bbox});
  node["name"]({bbox});
);
out geom;'''


def build_query(bbox, custom=None):
    # Overpass bbox 顺序：south,west,north,east
    ob = '%.6f,%.6f,%.6f,%.6f' % (bbox[1], bbox[0], bbox[3], bbox[2])
    return (custom or DEFAULT_QUERY).replace('{bbox}', ob)


def try_endpoint(name, url, query, timeout, method='POST'):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; digital-twin-studio/1.0)',
               'Accept': 'application/json'}
    try:
        if method == 'POST':
            req = urllib.request.Request(
                url, data=urllib.parse.urlencode({'data': query}).encode(), headers=headers)
        else:
            req = urllib.request.Request(
                url + '?' + urllib.parse.urlencode({'data': query}), headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode('utf-8', 'replace')
            if r.status != 200:
                return None, '%s HTTP %s' % (method, r.status)
            # 406/504 页面是 HTML，不是 JSON
            if body.lstrip().startswith('<'):
                return None, '%s 返回 HTML（多半是网关 406/504 拦截）' % method
            obj = json.loads(body)
            n = len(obj.get('elements', []))
            if n == 0:
                return None, '%s 0 要素（镜像可能只覆盖局部，如 overpass.osm.ch 仅瑞士）' % method
            return obj, '%s %d 要素' % (method, n)
    except Exception as e:
        return None, '%s %s: %s' % (method, type(e).__name__, str(e)[:100])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bbox', help='lon0,lat0,lon1,lat1（WGS84）')
    ap.add_argument('--out', required=True)
    ap.add_argument('--query', help='自定义 Overpass 查询，{bbox} 会被替换')
    ap.add_argument('--timeout', type=int, default=20, help='单端点单次请求超时（秒）')
    ap.add_argument('--mirrors', help='只测指定镜像，逗号分隔（默认全测）')
    ap.add_argument('--from-file', help='直接拷贝已有 OSM JSON，跳过网络')
    ap.add_argument('--cache', action='store_true', help='已有输出文件则直接复用')
    a = ap.parse_args()

    if a.cache and os.path.exists(a.out):
        print('复用缓存：', a.out)
        return 0
    if a.from_file:
        with open(a.from_file, encoding='utf-8') as f:
            obj = json.load(f)
        write_json(obj, a.out)
        print('拷贝：%s -> %s（%d 要素）' %
              (a.from_file, a.out, len(obj.get('elements', []))))
        return 0
    if not a.bbox:
        ap.error('需要 --bbox 或 --from-file')

    query = build_query(parse_bbox(a.bbox), a.query)
    print('Overpass bbox:', query.splitlines()[0])
    mirrors = MIRRORS
    if a.mirrors:
        wanted = set(x.strip() for x in a.mirrors.split(','))
        mirrors = [m for m in MIRRORS if m[0] in wanted]
        if not mirrors:
            ap.error('未知镜像名，可选：' + ', '.join(n for n, _ in MIRRORS))
    report = []
    for name, url in mirrors:
        for method in ('POST', 'GET'):
            obj, msg = try_endpoint(name, url, query, a.timeout, method)
            print('  [%s] %s' % (name, msg))
            report.append((name, msg))
            if obj is not None:
                write_json(obj, a.out)
                print('OK -> %s' % a.out)
                return 0
            # 网关明确拒绝（406/504/HTML）时，同端点换 method 也不会通，跳过
            if 'HTTP' in msg or '返回 HTML' in msg:
                break
    write_json({'mirror_report': report, 'note': 'OSM_UNAVAILABLE'}, a.out + '.failed.json')
    print('\n全部镜像不可达。不要伪造 OSM：调用 make_scene.py 不带 --osm，'
          '走 schematic_fallback，并在页面/说明里标注示意矢量。')
    return 2


if __name__ == '__main__':
    sys.exit(main())
