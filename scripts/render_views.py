#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""无头 Chromium 批量出图 + JS 运行时错误检查（WebGL 走 SwiftShader）。

用法：
  python render_views.py --html 黄鹤楼_数字孪生.html --out out --prefix 黄鹤楼 \
      --modes main,floors,cut,skel,top,wide,pick

约定：模板必须在 window.__TDBG 暴露 setMode / applyCut / applySep / camera / st，
并提供 btnAll / btnFloors / btnSkel / btnTop / btnWide 按钮（缺失的模式自动跳过）。
产物：<prefix>_<mode>.png（main 用「主预览」）+ <prefix>_渲染报告.json
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# 与模板 UI 的按钮 id 约定
MODE_BTN = dict(floors='btnFloors', skel='btnSkel', top='btnTop',
                wide='btnWide', all='btnAll')
INJECT = {
    'cut': "if(window.__TDBG.setMode)window.__TDBG.setMode('btnAll');window.__TDBG.applyCut(3);",
    'explode': "if(window.__TDBG.setMode)window.__TDBG.setMode('btnAll');window.__TDBG.applySep(7);",
    'pick': "var p=document.querySelectorAll('.pi');if(p.length>2)p[2].click();",
}


def find_chromium(explicit=None):
    if explicit:
        return explicit
    pats = [os.path.expanduser('~/Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium'),
            os.path.expanduser('~/Library/Caches/ms-playwright/chromium-*/chrome-linux/chrome')]
    for p in pats:
        hits = sorted(glob.glob(p), reverse=True)
        if hits:
            return hits[0]
    for cmd in ('chromium', 'google-chrome', 'chrome'):
        from shutil import which
        if which(cmd):
            return which(cmd)
    raise SystemExit('找不到 Chromium，用 --chromium 指定绝对路径')


def chromium_args(ch, extra=None):
    return [ch, '--headless', '--no-sandbox', '--disable-gpu-sandbox',
            '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader',
            '--hide-scrollbars', '--allow-file-access-from-files'] + (extra or [])


def run(ch, args, timeout=120):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def probe_html(src, code, tmpdir, tag):
    s = Path(src).read_text(encoding='utf-8')
    inject = ("<script>setTimeout(function(){try{%s}catch(e){"
              "document.title='PROBE_ERR '+e.message;}},90);</script>" % code)
    out = Path(tmpdir) / ('probe_%s.html' % tag)
    out.write_text(s.replace('</body>', inject + '</body>'), encoding='utf-8')
    return str(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--prefix', default='twin')
    ap.add_argument('--modes', default='main,floors,cut,skel,top,wide,pick')
    ap.add_argument('--width', type=int, default=1680)
    ap.add_argument('--height', type=int, default=1050)
    ap.add_argument('--budget', type=int, default=8000, help='virtual-time-budget ms')
    ap.add_argument('--chromium')
    a = ap.parse_args()

    ch = find_chromium(a.chromium)
    os.makedirs(a.out, exist_ok=True)
    modes = [m.strip() for m in a.modes.split(',') if m.strip()]
    report = dict(chromium=ch, html=os.path.abspath(a.html), views=[], js_errors=[])
    tmpdir = tempfile.mkdtemp(prefix='twin_probe_')

    for mode in modes:
        if mode == 'main':
            target, name = a.html, '%s_主预览.png' % a.prefix
        else:
            if mode in MODE_BTN:
                code = ("var m=window.__TDBG&&window.__TDBG.setMode;"
                        "if(m)m('%s');else{var b=document.getElementById('%s');"
                        "if(b)b.click();else document.title='PROBE_NO_BTN';}" %
                        (MODE_BTN[mode], MODE_BTN[mode]))
            elif mode in INJECT:
                code = INJECT[mode]
            else:
                report['views'].append(dict(mode=mode, status='unknown-mode'))
                continue
            target = probe_html(a.html, code, tmpdir, mode)
            name = '%s_%s.png' % (a.prefix, mode)
        shot = os.path.join(a.out, name)
        r = run(ch, chromium_args(ch, [
            '--virtual-time-budget=%d' % a.budget,
            '--window-size=%d,%d' % (a.width, a.height),
            '--screenshot=' + shot, Path(target).as_uri()]))
        ok = bool(r and r.returncode == 0 and os.path.exists(shot) and os.path.getsize(shot) > 40000)
        report['views'].append(dict(mode=mode, file=name, ok=ok,
                                    bytes=os.path.getsize(shot) if os.path.exists(shot) else 0))
        print('  [%s] %s %s' % (mode, 'OK' if ok else 'FAIL', name))

    # JS 错误检查：dump-dom + stderr 抓 CONSOLE / Uncaught
    r = run(ch, chromium_args(ch, [
        '--enable-logging=stderr', '--v=0',
        '--virtual-time-budget=%d' % max(a.budget, 6000),
        '--window-size=1200,800', '--dump-dom', Path(a.html).as_uri()]))
    if r:
        for line in (r.stderr or '').splitlines():
            if 'Uncaught' in line or 'CONSOLE' in line and ('Error' in line or 'error' in line):
                report['js_errors'].append(line.strip()[:300])
        dom = r.stdout or ''
        import re
        lm = re.search(r'<div[^>]*id="loading"[^>]*>([^<]*)', dom)
        if lm and '正在' in lm.group(1) and 'opacity: 0' not in lm.group(0):
            report['loading_stuck'] = True   # 多半 JS 中途抛错，loading 未移除
    report_path = os.path.join(a.out, '%s_渲染报告.json' % a.prefix)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('\n报告：%s' % report_path)
    bad = [v for v in report['views'] if not v['ok']]
    if report['js_errors'] or report.get('loading_stuck') or bad:
        print('需要修复：js_errors=%d loading_stuck=%s bad_views=%d' %
              (len(report['js_errors']), report.get('loading_stuck', False), len(bad)))
        return 1
    print('全部通过：%d 张截图，无 JS 异常' % len(report['views']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
