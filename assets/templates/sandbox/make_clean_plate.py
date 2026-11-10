#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「无 UI 纯净沙盘图」：隐藏大屏面板与 3D 浮动标签，叠加信息展板，
并用计算好的机位保证沙盘底座四角完整入画。

用法：
    python3 make_clean_plate.py
输出：
    probe/whb_clean_{tech,dusk}.html （注入后的中间页，供 Chromium 打开）
    ../out/武汉长江大桥_沙盘图.png       （科技蓝，1760x1100）
    ../out/武汉长江大桥_沙盘图_黄昏.png  （写实黄昏，1760x1100）
"""
import glob
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
OUT = os.path.join(ROOT, 'out')
PROBE = os.path.join(ROOT, 'probe')
SRC = os.path.join(OUT, '武汉长江大桥_数字沙盘.html')
PNG = os.path.join(OUT, '武汉长江大桥_沙盘图.png')

CSS = r'''<style>
header,#left,#right,#deckcard,#bottom,#north,#scale,#tip,.vig,.scan,#inset{display:none!important}
#labels .lab{display:none!important}
#app{background:#050b13}
#plate{position:absolute;top:52px;left:56px;z-index:9;width:326px;
  background:linear-gradient(150deg,rgba(8,20,34,.94),rgba(8,20,34,.72));
  border:1px solid rgba(214,178,104,.42);border-radius:10px;padding:18px 20px 16px;
  box-shadow:0 16px 50px rgba(0,0,0,.6);font-family:"PingFang SC","Microsoft YaHei",sans-serif}
#plate .t1{font-size:19px;color:#f3e3c4;letter-spacing:2px;font-weight:600}
#plate .t2{font-size:9.5px;color:#8aa8bf;letter-spacing:1.4px;margin-top:6px}
#plate .ln{height:1px;background:linear-gradient(90deg,rgba(214,178,104,.75),transparent);margin:14px 0}
#plate .nums{display:grid;grid-template-columns:1fr 1fr;gap:12px 14px}
#plate .n b{display:block;font-size:17px;color:#e8c689;font-weight:500;line-height:1.2}
#plate .n span{font-size:9.5px;color:#809cb5;letter-spacing:.3px}
#plate .ft{font-size:9px;color:#7895ad;line-height:1.75;margin-top:14px;
  border-top:1px dashed rgba(120,160,200,.2);padding-top:10px}
#corner{position:absolute;right:56px;bottom:48px;z-index:9;text-align:right;
  font-size:10.5px;color:#8aa8bf;letter-spacing:1.2px;line-height:1.9}
#corner b{color:#d8b878;font-weight:500}
</style>'''

PLATE = r'''<div id="plate">
  <div class="t1">武汉长江大桥 · 数字沙盘</div>
  <div class="t2">WUHAN YANGTZE RIVER BRIDGE &nbsp;·&nbsp; 1957</div>
  <div class="ln"></div>
  <div class="nums">
    <div class="n"><b>1670.4 m</b><span>全桥长 · 公铁两用</span></div>
    <div class="n"><b>1155.5 m</b><span>正桥 3 联 9 孔 ×128 m</span></div>
    <div class="n"><b>1150 m</b><span>DEM 实测跨江宽</span></div>
    <div class="n"><b>8 墩 2 堡</b><span>管柱基础 · 7 层桥头堡</span></div>
  </div>
  <div class="ft">Copernicus DEM 30 m + ESA WorldCover 10 m 地形；桥体按 1957 年公开设计参数程序化重建。
  周边路网与建筑为示意矢量，垂直 / 横向有可视化夸张，不作量测。</div>
</div>
<div id="corner"><b>龟山 · 蛇山夹江</b><br>WGS84 / 1 场景单位 = 4 m<br>本地可视化 · 非竣工 BIM</div>'''

# 机位由「四角 NDC 全落在 [-1,1]」反算得到，见说明文档第六节
JS = r'''<script>setTimeout(function(){try{
  window.__TDBG.setInset(false);          // 关掉右上角画中画双视口
  var t=window.__TDBG;
  t.setMood('__MOOD__');                  // 科技蓝 / 写实黄昏各出一版
  t.st.th=-0.40;t.st.ph=0.48;t.st.dist=1350;
  t.st.ty=24;t.st.tx=t.st.tx+60;t.st.tz=t.st.tz+40;
  t.applyCam();
}catch(e){document.title='ERR '+e.message;}},160);</script>'''


def find_chromium():
    pats = [
        os.path.expanduser('~/Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium'),
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/usr/bin/chromium',
    ]
    for p in pats:
        hits = sorted(glob.glob(p)) if '*' in p else ([p] if os.path.exists(p) else [])
        if hits:
            return hits[-1]
    raise RuntimeError('未找到 Chromium，请手动指定')


def main():
    os.makedirs(PROBE, exist_ok=True)
    ch = find_chromium()
    src = open(SRC, encoding='utf-8').read()
    for mood, name in [('tech', '武汉长江大桥_沙盘图.png'),
                       ('dusk', '武汉长江大桥_沙盘图_黄昏.png')]:
        s = src.replace('</head>', CSS + '</head>')
        s = s.replace('<div id="loading">', PLATE + '<div id="loading">')
        s = s.replace('</body>', JS.replace('__MOOD__', mood) + '</body>')
        hp = os.path.join(PROBE, 'whb_clean_%s.html' % mood)
        open(hp, 'w', encoding='utf-8').write(s)
        png = os.path.join(OUT, name)
        cmd = [ch, '--headless', '--no-sandbox', '--disable-gpu-sandbox',
               '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader',
               '--hide-scrollbars', '--allow-file-access-from-files',
               '--virtual-time-budget=15000', '--window-size=1760,1100',
               '--screenshot=' + png, 'file://' + hp]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print('OK ->', png, '%.0f KB' % (os.path.getsize(png) / 1024))


if __name__ == '__main__':
    main()
