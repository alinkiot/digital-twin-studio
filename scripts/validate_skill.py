#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""digital-twin-studio 仓库自检（零第三方依赖）。

    python3 scripts/validate_skill.py            # 在技能根目录运行
    python3 scripts/validate_skill.py --root /path/to/digital-twin-studio

检查项：
  1. 必需文件与目录齐全；
  2. SKILL.md frontmatter 含 name / description；
  3. 所有 .py 可被 Python 编译（不生成 __pycache__）；
  4. visual_fx.build_fx() 生成的 JS 通过 node --check（没有 node 则跳过并提示）；
  5. SKILL.md 资源索引里列出的路径都真实存在。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

REQUIRED = [
    'SKILL.md', 'README.md', '.gitignore',
    'scripts/twin_common.py', 'scripts/fetch_raster.py', 'scripts/fetch_osm.py',
    'scripts/make_scene.py', 'scripts/render_views.py', 'scripts/smoke_check.py',
    'scripts/visual_fx.py', 'scripts/validate_skill.py',
    'assets/lib/three.min.js',
    'assets/templates/city/build_twin.py', 'assets/templates/city/make_html.py',
    'assets/templates/bridge/build_bridge.py', 'assets/templates/bridge/make_bridge_html.py',
    'assets/templates/tower/build_tower.py', 'assets/templates/tower/make_tower_html.py',
    'assets/templates/sandbox/build_wuhan.py', 'assets/templates/sandbox/make_wuhan_html.py',
    'assets/templates/sandbox/make_clean_plate.py', 'assets/templates/sandbox/README.md',
    'references/pipeline.md', 'references/data_sources.md', 'references/pitfalls.md',
    'references/cases.md', 'references/visual_fx.md',
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    root = os.path.abspath(os.path.expanduser(ap.parse_args().root))
    ok, fail = [], []

    def chk(cond, msg):
        (ok if cond else fail).append(msg)
        return cond

    # 1. 必需文件
    for rel in REQUIRED:
        chk(os.path.isfile(os.path.join(root, rel)), '文件存在 ' + rel)

    # 2. frontmatter
    sk = os.path.join(root, 'SKILL.md')
    if os.path.isfile(sk):
        s = open(sk, encoding='utf-8').read()
        chk(s.startswith('---\n'), 'SKILL.md 有 YAML frontmatter')
        chk(re.search(r'^name:\s*\S+', s, re.M) is not None, 'frontmatter 含 name')
        chk(re.search(r'^description:\s*\S+', s, re.M) is not None, 'frontmatter 含 description')
        # 3. 资源索引里的路径
        for m in re.finditer(r'`((?:scripts|references|assets)/[A-Za-z0-9_./{}*-]+\.(?:py|md|js))`', s):
            p = m.group(1)
            if '{' in p or '*' in p:
                continue
            chk(os.path.exists(os.path.join(root, p)), '索引路径有效 ' + p)

    # 4. Python 编译
    for base, _dirs, files in os.walk(root):
        if '.git' in base.split(os.sep) or '__pycache__' in base:
            continue
        for fn in files:
            if not fn.endswith('.py'):
                continue
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, root)
            try:
                compile(open(p, encoding='utf-8').read(), rel, 'exec')
                ok.append('Python 编译 ' + rel)
            except SyntaxError as e:
                fail.append('Python 编译失败 %s: %s' % (rel, e))

    # 5. visual_fx 生成的 JS
    sys.path.insert(0, os.path.join(root, 'scripts'))
    try:
        from visual_fx import build_fx, required_dom_ids
        css, js = build_fx({'water': {'center': [0, 0], 'axis': [1, 0],
                                      'normal': [0, 1], 'shadow': True}})
        chk('TwinFX' in js and 'install' in js, 'visual_fx 生成 TwinFX 模块')
        chk(len(css) > 1000, 'visual_fx 生成 CSS')
        chk(len(required_dom_ids()) >= 5, 'visual_fx DOM 契约清单')
        node = shutil.which('node')
        if node:
            with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(js)
                tmp = f.name
            try:
                r = subprocess.run([node, '--check', tmp], capture_output=True, text=True)
                chk(r.returncode == 0, 'node --check visual_fx JS' +
                    ('' if r.returncode == 0 else ': ' + r.stderr.strip()[:200]))
            finally:
                os.unlink(tmp)
        else:
            print('  [skip] 未找到 node，跳过 JS 语法检查')
    except Exception as e:
        fail.append('visual_fx 导入/生成失败: %s' % e)

    print('\n通过 %d 项，失败 %d 项' % (len(ok), len(fail)))
    for f in fail:
        print('  FAIL  ' + f)
    if fail:
        return 1
    print('PASS  digital-twin-studio 自检通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
