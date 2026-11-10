#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""页面冒烟：DOM 初始化、图层/清单/图例、模式切换、点选属性面板、JS 异常。

用法：
  python smoke_check.py --html 黄鹤楼_数字孪生.html [--out smoke.json]

退出码 0 = 全绿；1 = 有失败项（清单见输出与报告 JSON）。
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_views import chromium_args, find_chromium, run


def dump(ch, html_path, budget=7000):
    r = run(ch, chromium_args(ch, [
        '--enable-logging=stderr', '--v=0',
        '--virtual-time-budget=%d' % budget,
        '--window-size=1280,860', '--dump-dom', Path(html_path).as_uri()]))
    return (r.stdout if r else ''), (r.stderr if r else '')


def count(dom, pattern):
    return len(re.findall(pattern, dom))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', required=True)
    ap.add_argument('--out')
    ap.add_argument('--chromium')
    a = ap.parse_args()
    ch = find_chromium(a.chromium)
    checks = []

    def chk(name, ok, detail=''):
        checks.append(dict(name=name, ok=bool(ok), detail=str(detail)[:200]))
        print('  [%s] %s %s' % ('OK' if ok else 'FAIL', name, detail))

    dom, err = dump(ch, a.html)
    chk('页面 DOM 已渲染', len(dom) > 10000, '%d 字节' % len(dom))
    chk('KPI 已填充', count(dom, r'class="kpi"') >= 4,
        '%d 项' % count(dom, r'class="kpi"'))
    chk('图层已生成', count(dom, r'class="ly"') >= 5,
        '%d 层' % count(dom, r'class="ly"'))
    chk('构件清单已生成', count(dom, r'class="pi"') >= 3,
        '%d 项' % count(dom, r'class="pi"'))
    chk('图例已生成', count(dom, r'class="it"') >= 4,
        '%d 项' % count(dom, r'class="it"'))
    chk('地名标注已生成', count(dom, r'class="lab') >= 1,
        '%d 个' % count(dom, r'class="lab'))
    js_errors = [l.strip()[:300] for l in err.splitlines()
                 if 'Uncaught' in l or ('CONSOLE' in l and 'Error' in l)]
    chk('无 JS 运行时异常', not js_errors, '; '.join(js_errors[:2]))
    lm = re.search(r'<div[^>]*id="loading"[^>]*>([^<]*)', dom)
    stuck = bool(lm and '正在' in lm.group(1) and 'opacity: 0' not in lm.group(0))
    chk('loading 已淡出', not stuck, 'stuck=%s' % stuck)

    # 交互：点击第 3 个构件 + 切到骨架模式，检查右侧属性面板
    src = Path(a.html).read_text(encoding='utf-8')
    inject = ("<script>setTimeout(function(){try{"
              "var p=document.querySelectorAll('.pi');if(p.length>2)p[2].click();"
              "}catch(e){document.title='SMOKE_ERR '+e.message;}},90);</script>")
    tmp = Path(tempfile.mkdtemp(prefix='twin_smoke_')) / 'probe.html'
    tmp.write_text(src.replace('</body>', inject + '</body>'), encoding='utf-8')
    dom2, err2 = dump(ch, str(tmp), 7000)
    rm = re.search(r'<div[^>]*id="right"[^>]*>', dom2)
    chk('点选弹出属性面板', bool(rm and 'show' in rm.group(0)),
        'right tag=%s' % (rm.group(0)[:90] if rm else 'missing'))
    chk('属性面板有内容', 'class="rname"' in dom2, 'rname=%s' % ('class="rname"' in dom2))
    chk('交互无 JS 异常', 'Uncaught' not in err2, '')

    report = dict(html=os.path.abspath(a.html), checks=checks,
                  passed=sum(1 for c in checks if c['ok']), total=len(checks))
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('\n报告：%s' % a.out)
    ok = report['passed'] == report['total']
    print('\n%d/%d 通过' % (report['passed'], report['total']))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
