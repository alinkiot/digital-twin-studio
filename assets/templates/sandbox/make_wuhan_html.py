#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 three.js + 武汉长江大桥数据 + 沙盘大屏 UI 拼成离线单文件 HTML"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')


def find_three_js():
    """three.min.js 查找顺序：环境变量 > 工作目录 > 技能自带 lib。
    模板复制到任意工作目录后，只需 `cp $S/assets/lib/three.min.js $W/` 或设置 THREE_JS。"""
    cand = [
        os.environ.get('THREE_JS', ''),
        os.path.join(HERE, 'three.min.js'),
        os.path.abspath(os.path.join(HERE, '..', '..', '..', 'lib', 'three.min.js')),
    ]
    for p in cand:
        if p and os.path.isfile(p):
            return p
    raise SystemExit('找不到 three.min.js：设置 THREE_JS 环境变量，或从 '
                     'assets/lib/three.min.js 复制到工作目录')


three = open(find_three_js(), encoding='utf-8').read().replace('</script', '<\\/script')
data = open(os.path.join(HERE, 'wuhan_data.json'), encoding='utf-8').read().replace('</script', '<\\/script')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>武汉长江大桥 · 数字沙盘</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#050b13;color:#dce8f5;
  font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif;-webkit-font-smoothing:antialiased}
#app{position:relative;width:100%;height:100%}
canvas#gl{position:absolute;inset:0;display:block}
/* 大气辉光：在 3D 画面之上叠一层极淡的冷暖光晕，避免大屏背景死黑 */
.atm{position:absolute;inset:0;pointer-events:none;z-index:1;mix-blend-mode:screen;opacity:.9;
  background:radial-gradient(ellipse 68% 54% at 50% 34%,rgba(58,128,178,.16),transparent 72%),
             radial-gradient(ellipse 42% 36% at 16% 8%,rgba(92,180,224,.10),transparent 76%),
             radial-gradient(ellipse 40% 34% at 84% 12%,rgba(48,112,168,.10),transparent 76%)}
.vig{position:absolute;inset:0;pointer-events:none;z-index:2;
  background:radial-gradient(ellipse at 50% 42%,transparent 36%,rgba(2,6,12,.66) 100%)}
.scan{position:absolute;inset:0;pointer-events:none;z-index:2;opacity:.16;
  background:repeating-linear-gradient(0deg,transparent 0 3px,rgba(90,170,255,.05) 3px 4px)}
header{position:absolute;top:0;left:0;right:0;height:78px;display:flex;align-items:center;
  padding:0 26px;background:linear-gradient(180deg,rgba(5,12,22,.97),rgba(5,12,22,0));
  border-bottom:1px solid rgba(96,168,232,.15);pointer-events:none;z-index:6}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:34px;height:34px;border:1.5px solid #4fd0e0;border-radius:8px;position:relative;
  box-shadow:0 0 18px rgba(79,208,224,.35) inset,0 0 12px rgba(79,208,224,.2)}
.logo::before,.logo::after{content:"";position:absolute;background:#4fd0e0}
.logo::before{left:50%;top:6px;bottom:6px;width:1.5px;transform:translateX(-50%)}
.logo::after{top:50%;left:6px;right:6px;height:1.5px;transform:translateY(-50%)}
h1{font-size:19px;font-weight:600;letter-spacing:2px;color:#eaf5ff}
.sub{font-size:10.5px;color:#6f8aa6;letter-spacing:1.2px;margin-top:3px}
.hright{margin-left:auto;display:flex;align-items:center;gap:20px;text-align:right}
.clock{font-size:22px;font-weight:300;letter-spacing:1px;color:#bfe3ff;font-variant-numeric:tabular-nums}
.clock small{font-size:10.5px;color:#64809c;display:block;letter-spacing:1px}
.badge{font-size:11px;padding:5px 11px;border:1px solid rgba(79,208,224,.4);border-radius:20px;
  color:#7ee0e8;background:rgba(79,208,224,.07);letter-spacing:.5px}
.panel{position:absolute;z-index:5;background:rgba(8,17,30,.9);border:1px solid rgba(90,150,210,.2);
  border-radius:10px;backdrop-filter:blur(14px);box-shadow:0 12px 40px rgba(0,0,0,.5)}
#left{top:92px;left:22px;width:280px;padding:15px 15px 13px;max-height:calc(100% - 196px);
  display:flex;flex-direction:column;overflow-y:auto;scrollbar-width:thin}
#left::-webkit-scrollbar{width:5px}#left::-webkit-scrollbar-thumb{background:#3a6a8c;border-radius:3px}
.ptitle{font-size:11.5px;color:#8fb6d8;letter-spacing:2px;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.ptitle::before{content:"";width:3px;height:12px;background:#4fd0e0;border-radius:2px;box-shadow:0 0 8px #4fd0e0}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.kpi{background:rgba(30,58,88,.34);border:1px solid rgba(90,150,210,.13);border-radius:7px;padding:7px 8px}
.kpi b{display:block;font-size:15px;font-weight:500;color:#f0d394;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi b i{font-size:9.5px;font-style:normal;color:#7d9ab5;margin-left:2px}
.kpi span{font-size:9px;color:#7793ad;letter-spacing:.3px}
.divider{height:1px;background:rgba(90,150,210,.15);margin:11px 0 9px;flex:none}
.layers{display:grid;gap:1px}
.ly{display:flex;align-items:center;gap:8px;font-size:10.8px;color:#a8c2da;padding:3px 5px;border-radius:5px;cursor:pointer}
.ly:hover{background:rgba(80,150,220,.09)}
.ly input{appearance:none;width:13px;height:13px;border:1px solid #4a7398;border-radius:3px;position:relative;cursor:pointer;flex:none}
.ly input:checked{background:#3fbdd2;border-color:#3fbdd2}
.ly input:checked::after{content:"";position:absolute;left:4px;top:1px;width:3px;height:7px;
  border:solid #06131f;border-width:0 2px 2px 0;transform:rotate(45deg)}
.sw{width:9px;height:9px;border-radius:2px;flex:none}
.btnrow{display:flex;gap:4px;margin-top:9px;flex:none}
.btn{flex:1;min-width:0;text-align:center;font-size:10.5px;padding:7px 2px;border-radius:6px;cursor:pointer;
  border:1px solid rgba(90,160,220,.28);background:rgba(40,90,140,.16);color:#a9cbe6;transition:.18s}
.btn:hover{background:rgba(70,160,220,.3);color:#fff;border-color:#5ec8e0}
.btn.on{background:rgba(63,189,210,.24);border-color:#4fd0e0;color:#bff4fb}
.src{font-size:10px;line-height:1.7;color:#7996b1;overflow:auto;max-height:96px;flex:none}
.src em{font-style:normal;color:#a9c9e4}
.src .warn{color:#e8b478}
#plist{overflow:auto;max-height:112px;border:1px solid rgba(90,150,210,.14);border-radius:6px;
  background:rgba(10,24,42,.5);flex:none}
.pi{display:flex;align-items:center;gap:7px;font-size:10.5px;color:#9fbad2;padding:5px 8px;
  cursor:pointer;border-bottom:1px solid rgba(90,150,210,.07)}
.pi:hover{background:rgba(70,160,220,.16);color:#eaf7ff}
.pi .tag{font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(79,208,224,.14);color:#7fd9e6;flex:none}
.pi .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pi .st{margin-left:auto;color:#5f88a8;font-size:9.5px;flex:none}
#right{top:92px;right:22px;width:280px;padding:16px;display:none;max-height:calc(100% - 196px);overflow:auto}
#right.show{display:block}
.rname{font-size:15px;color:#eaf7ff;font-weight:600;margin:2px 0 3px;letter-spacing:.4px;line-height:1.4}
.rtype{font-size:10.5px;color:#6fd3e2;margin-bottom:11px;letter-spacing:1px}
.kv{display:flex;justify-content:space-between;gap:10px;font-size:11px;padding:5px 0;
  border-bottom:1px dashed rgba(90,150,210,.14)}
.kv k{color:#7b98b3;flex:none}
.kv v{color:#d3e6f6;text-align:right;word-break:break-all}
.close{position:absolute;right:12px;top:12px;cursor:pointer;color:#6f8ba6;font-size:16px;line-height:1}
.close:hover{color:#fff}
#bottom{position:absolute;left:22px;right:22px;bottom:20px;z-index:5;display:flex;align-items:flex-end;gap:12px;pointer-events:none}
#bottom>*{pointer-events:auto}
.legend{background:rgba(8,17,30,.9);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:10px 13px;backdrop-filter:blur(14px);font-size:10px;color:#91aec8;max-width:410px}
.legend .row{display:flex;gap:11px;flex-wrap:wrap;align-items:center}
.legend .it{display:flex;align-items:center;gap:5px;white-space:nowrap}
.legend .box{width:10px;height:10px;border-radius:2px}
.tools{background:rgba(8,17,30,.9);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:10px 13px;backdrop-filter:blur(14px);min-width:236px}
.tools label{font-size:10px;color:#8fb0cc;display:flex;justify-content:space-between;margin-bottom:6px}
.tools label b{color:#7fe3f0;font-weight:500}
input[type=range]{width:100%;height:4px;appearance:none;background:linear-gradient(90deg,#3fbdd2,#2a5878);
  border-radius:3px;outline:none;cursor:pointer}
input[type=range]::-webkit-slider-thumb{appearance:none;width:13px;height:13px;border-radius:50%;
  background:#9ff0fa;box-shadow:0 0 8px #4fd0e0;cursor:pointer}
.search{margin-left:auto;display:flex;gap:6px;background:rgba(8,17,30,.9);border:1px solid rgba(90,150,210,.2);
  border-radius:9px;padding:6px 8px;backdrop-filter:blur(14px)}
.search input{background:transparent;border:0;outline:0;color:#dceaf7;font-size:11px;width:132px}
.search input::placeholder{color:#5c7893}
.search button{background:rgba(63,189,210,.2);border:1px solid rgba(79,208,224,.4);color:#9fe9f2;
  border-radius:5px;padding:4px 10px;font-size:11px;cursor:pointer}
#labels{position:absolute;inset:0;pointer-events:none;z-index:4;overflow:hidden}
.lab{position:absolute;transform:translate(-50%,-100%);font-size:10.5px;color:#dff1ff;white-space:nowrap;
  text-shadow:0 1px 5px #000,0 0 10px rgba(0,0,0,.9);letter-spacing:.4px;opacity:.93}
.lab::after{content:"";position:absolute;left:50%;top:100%;width:1px;height:9px;
  background:linear-gradient(rgba(160,220,255,.8),transparent)}
.lab.hot{color:#ffd98a;font-weight:600;font-size:11.5px}
.lab.span{color:#a9d8ea;font-size:9.5px;opacity:.82}
.lab.dim{color:#8fa9c0;font-size:9.5px}
#north{position:absolute;right:26px;bottom:118px;z-index:5;width:50px;height:50px;border-radius:50%;
  border:1px solid rgba(90,150,210,.28);background:rgba(8,17,30,.72);text-align:center;pointer-events:none}
#north .ar{font-size:19px;color:#7fe3f0;line-height:29px}
#north .tx{font-size:9px;color:#7f9db8;letter-spacing:1px}
#scale{position:absolute;left:24px;bottom:98px;z-index:5;font-size:10px;color:#8fadc6;pointer-events:none}
#scale .bar{height:5px;border:1px solid #8fadc6;border-top:0;width:88px;margin-bottom:3px}
#tip{position:absolute;left:50%;top:86px;transform:translateX(-50%);z-index:7;font-size:11px;
  color:#9fc4dd;background:rgba(8,17,30,.84);border:1px solid rgba(90,150,210,.2);
  padding:6px 14px;border-radius:16px;letter-spacing:.4px;pointer-events:none;white-space:nowrap}
#loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:20;
  background:#050b13;color:#7fe3f0;font-size:13px;letter-spacing:3px;transition:opacity .5s}
#deckcard{top:92px;right:22px;width:262px;padding:14px;display:none;max-height:calc(100% - 196px);overflow:auto}
#deckcard.show{display:block}
.fr{display:flex;justify-content:space-between;gap:8px;font-size:10.5px;padding:6px 0;
  border-bottom:1px dashed rgba(90,150,210,.14);color:#cde0f0}
.fr b{color:#f0d394;font-weight:500;flex:none}
.fr span{color:#8ca7bf;text-align:right}
.fr i{font-style:normal;color:#6d89a2;font-size:9.5px;display:block}
#inset{position:absolute;top:92px;right:22px;width:330px;height:174px;z-index:5;
  border:1px solid rgba(79,208,224,.42);border-radius:9px;pointer-events:none;overflow:hidden;
  box-shadow:0 12px 38px rgba(0,0,0,.55),0 0 22px rgba(79,208,224,.10) inset;
  background:rgba(6,16,28,.12)}
#inset .ih{position:absolute;top:0;left:0;right:0;padding:6px 10px;font-size:10.5px;
  color:#c7eef8;letter-spacing:.6px;background:linear-gradient(180deg,rgba(6,16,28,.92),rgba(6,16,28,0));
  display:flex;justify-content:space-between;align-items:center}
#inset .ih span{color:#6f9ab5;font-size:9.5px}
#inset .if{position:absolute;left:0;right:0;bottom:0;padding:5px 10px;font-size:9.5px;color:#87b9d2;
  background:linear-gradient(0deg,rgba(6,16,28,.9),transparent)}
#inset.hide{display:none}
/* 属性面板 / 双层剖面卡占据同一右上角时，画中画整体让位（loop 里也同步停掉双视口渲染） */
#right.show~#inset,#deckcard.show~#inset{display:none!important}
/* ===== 视觉精修：入场动效 / 面板微光 / 光影控制 ===== */
@keyframes panelIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
#left,#inset,#bottom>*{animation:panelIn .6s cubic-bezier(.2,.72,.2,1) both}
#left{animation-delay:.04s}#inset{animation-delay:.24s}#bottom>*{animation-delay:.14s}
.panel{overflow:hidden}
.panel::before{content:"";position:absolute;left:12px;right:12px;top:0;height:1px;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(120,220,240,.5),transparent)}
.kpi{position:relative;overflow:hidden}
.kpi::before{content:"";position:absolute;left:0;right:0;top:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(240,211,148,.6),transparent)}
.kpi b{text-shadow:0 0 16px rgba(240,211,148,.3)}
.btn{position:relative;overflow:hidden}
.btn::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(118deg,transparent 36%,rgba(255,255,255,.16) 50%,transparent 64%);
  transform:translateX(-130%);transition:transform .6s}
.btn:hover::after{transform:translateX(130%)}
.moods{display:flex;gap:4px;margin-top:8px;flex:none}
.moods .btn{font-size:10px;padding:6px 2px}
.moods .btn.on{box-shadow:0 0 16px rgba(79,208,224,.2) inset}
.sunrow{margin-top:9px;border-top:1px solid rgba(90,150,210,.14);padding-top:8px}
.sunrow label{font-size:10px;color:#8fb0cc;display:flex;justify-content:space-between;margin-bottom:5px}
.sunrow label b{color:#f0d394;font-weight:500}
#inset::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(115deg,transparent 40%,rgba(130,235,255,.12) 50%,transparent 60%);
  animation:sheen 6s linear infinite}
@keyframes sheen{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
header::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,transparent,rgba(79,208,224,.55),transparent)}
body.mood-dusk .panel{border-color:rgba(224,176,116,.28);background:rgba(24,18,13,.9)}
body.mood-dusk .ptitle{color:#d8b98c}
body.mood-dusk .ptitle::before{background:#e8b478;box-shadow:0 0 8px #e8b478}
body.mood-dusk .scan{opacity:.05}
body.mood-dusk .btn.on{background:rgba(232,180,120,.24);border-color:#e8b478;color:#ffe4b8}
body.mood-night .panel{background:rgba(5,11,24,.93);border-color:rgba(110,145,220,.26)}
body.mood-night .scan{opacity:.08}
</style>
</head>
<body>
<div id="app">
  <canvas id="gl"></canvas><div class="atm"></div><div class="vig"></div><div class="scan"></div>
  <div id="labels"></div>
  <header>
    <div class="brand"><div class="logo"></div>
      <div><h1>武汉长江大桥 · 数字沙盘</h1>
      <div class="sub">WUHAN YANGTZE RIVER BRIDGE &nbsp;·&nbsp; COPERNICUS DEM + 公开设计参数构件重建</div></div>
    </div>
    <div class="hright">
      <div class="badge">万里长江第一桥 · 1957</div>
      <div class="clock"><span id="clk">--:--:--</span><small id="date">WGS84 / 1 单位 = 4 m</small></div>
    </div>
  </header>

  <div class="panel" id="left">
    <div class="ptitle">桥梁概览 · BRIDGE STATS</div>
    <div class="kpis" id="kpis"></div>
    <div class="divider"></div>
    <div class="ptitle">图层控制 · LAYERS</div>
    <div class="layers" id="layers"></div>
    <div class="btnrow">
      <div class="btn on" id="btnAll">沙盘</div>
      <div class="btn" id="btnFloors">双层</div>
      <div class="btn" id="btnSkel">骨架</div>
      <div class="btn" id="btnTop">俯视</div>
      <div class="btn" id="btnWide">桥身</div>
    </div>
    <div class="moods">
      <div class="btn on" id="moodTech">科技蓝</div>
      <div class="btn" id="moodDusk">写实黄昏</div>
      <div class="btn" id="moodNight">夜景灯光</div>
    </div>
    <div class="divider"></div>
    <div class="ptitle">构件清单 · ELEMENTS</div>
    <div id="plist"></div>
    <div class="divider"></div>
    <div class="src" id="srcbox"></div>
  </div>

  <div class="panel" id="deckcard"><div class="ptitle">公铁两用 · 双层剖面</div><div id="deckrows"></div>
    <div style="font-size:10px;color:#e8b478;line-height:1.7;margin-top:10px">
      上层公路与下层铁路可上下分离查看；也可拖动下方「高度剖切」逐层剖开。</div></div>
  <div class="panel" id="right">
    <div class="close" id="rclose">✕</div>
    <div class="ptitle">构件属性 · ELEMENT</div>
    <div id="rbody"></div>
  </div>

  <div id="inset">
    <div class="ih">桥身细部 · 米字形钢桁架 <span>3 联 9 孔 / 8 墩</span></div>
    <div class="if">上层公路 22.5 m · 下层铁路双线 14.5 m · 独立机位同步渲染</div>
  </div>
  <div id="north"><div class="ar">▲</div><div class="tx">N</div></div>
  <div id="scale"><div class="bar"></div><span id="scaletx">300 m</span></div>
  <div id="tip">拖动旋转 · 滚轮缩放 · 右键平移 · 单击桥梁构件 / 建筑查看属性</div>

  <div id="bottom">
    <div class="legend"><div class="row" id="legend"></div></div>
    <div class="tools">
      <label>高度剖切 <b id="cutv">不限</b></label>
      <input type="range" id="cut" min="0" max="100" value="100">
      <div style="margin-top:6px;font-size:9.5px;color:#6f8ba6">向下拖动逐层剖开，查看公路 / 铁路 / 桁架 / 墩台标高</div>
      <div class="sunrow"><label>日照方位 <b id="sunv">--</b></label>
        <input type="range" id="sun" min="0" max="100" value="36"></div>
    </div>
    <div class="search"><input id="q" placeholder="搜索构件 / 地名"><button id="go">定位</button></div>
  </div>
  <div id="loading">正在浇筑长江沙盘 …</div>
</div>

<script>__THREE__</script>
<script>window.__TWIN__=__DATA__;</script>
<script>
(function(){
'use strict';
if(!window.THREE){document.getElementById('loading').textContent='three.js 未加载';return;}
THREE.ColorManagement && (THREE.ColorManagement.enabled=false);
var D=window.__TWIN__, M=D.meta, BD=D.bridge, BM=M.bridge;
var W=M.w,H=M.h,ZEX=3.2,BEX=0.54,LAKEZ=BD.lakeZ;
var DECKZ=BD.deckZ, RAILZ=BD.railZ, HALF_W=W/2, HALF_H=H/2;
var AX=BD.axis, UX=AX.u[0], UY=AX.u[1], NX=-UY, NY=UX;
function V(x,y,h){return new THREE.Vector3(x-HALF_W,(h||0)*ZEX,-(y-HALF_H));}

var cv=document.getElementById('gl');
var renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));
renderer.setSize(innerWidth,innerHeight);
renderer.setClearColor(0x050b13,1);
renderer.localClippingEnabled=true;
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
var scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x050b13,0.00048);
var camera=new THREE.PerspectiveCamera(44,innerWidth/innerHeight,1,12000);
var clip=new THREE.Plane(new THREE.Vector3(0,-1,0),10000);
var clipped=[];
/* 写实光照：环境光 + 天空/地面双色半球光 + 主日方向光（带软阴影）+ 冷色补光 */
var amb=new THREE.AmbientLight(0xc4dcf4,1.00);scene.add(amb);
var hemi=new THREE.HemisphereLight(0xbcd9f2,0x172a20,0.48);scene.add(hemi);
var sun=new THREE.DirectionalLight(0xfff2dc,1.30);sun.position.set(-420,700,360);scene.add(sun);
sun.castShadow=true;
sun.shadow.mapSize.set(1024,1024);
var shc=sun.shadow.camera;
shc.left=-760;shc.right=760;shc.top=760;shc.bottom=-760;shc.near=20;shc.far=2600;
shc.updateProjectionMatrix();
sun.shadow.bias=-0.0006;sun.shadow.normalBias=0.9;sun.shadow.radius=2;
var fill=new THREE.DirectionalLight(0x77b4ff,0.40);fill.position.set(460,260,-420);scene.add(fill);

/* ---------- 0. 天空穹顶：天顶—地平线渐变 / 远山剪影 / 日轮与光晕 ---------- */
var skyU={uTop:{value:new THREE.Color(0x071a30)},uHor:{value:new THREE.Color(0x1b4e68)},
  uBot:{value:new THREE.Color(0x050d18)},uSunCol:{value:new THREE.Color(0xffe6b8)},
  uSunDir:{value:new THREE.Vector3(-0.5,0.75,0.42).normalize()},
  uSunI:{value:1.0},uHaze:{value:0.9}};
var skyMat=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,depthTest:false,
  uniforms:skyU,
  vertexShader:'varying vec3 vD;void main(){vD=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader:[
    'varying vec3 vD;uniform vec3 uTop,uHor,uBot,uSunCol,uSunDir;uniform float uSunI,uHaze;',
    'void main(){',
    '  vec3 d=normalize(vD);float h=d.y;',
    '  vec3 col=h>0.0?mix(uHor,uTop,pow(clamp(h,0.0,1.0),0.55))',
    '              :mix(uHor,uBot,pow(clamp(-h,0.0,1.0),0.5));',
    '  float ang=atan(d.z,d.x);',
    '  float ridge=0.014*sin(ang*5.0)+0.009*sin(ang*11.0+1.7)+0.005*sin(ang*23.0+0.4)+0.004;',
    '  float mt=smoothstep(ridge+0.003,ridge-0.003,h)*step(h,0.07);',
    '  col=mix(col,vec3(0.035,0.075,0.105),mt*0.62*uHaze);',
    '  float s=max(dot(d,normalize(uSunDir)),0.0);',
    '  col+=uSunCol*uSunI*(pow(s,320.0)*1.35+pow(s,18.0)*0.22+pow(s,4.0)*0.05);',
    '  col=mix(col,uHor,uHaze*exp(-abs(h)*11.0)*0.38);',
    '  gl_FragColor=vec4(col,1.0);',
    '}'].join('\n')});
var sky=new THREE.Mesh(new THREE.SphereGeometry(9000,32,20),skyMat);
sky.renderOrder=-1000;sky.frustumCulled=false;scene.add(sky);

/* ---------- 1. 地形（DEM 顶点色，江面 DEM<18m） ---------- */
var T=D.terrain,nx=T.nx,ny=T.ny;
var tp=[],tc=[],ti=[];
var LC={10:[0.20,0.52,0.30],20:[0.26,0.55,0.32],30:[0.33,0.54,0.34],40:[0.46,0.50,0.34],
        50:[0.31,0.34,0.38],60:[0.40,0.41,0.39],80:[0.07,0.24,0.36],90:[0.26,0.46,0.38],95:[0.29,0.49,0.43]};
for(var r=0;r<ny;r++)for(var c=0;c<nx;c++){
  var i=r*nx+c, px=c/(nx-1)*W, py=r/(ny-1)*H;
  var v=V(px,py,T.z[i]);tp.push(v.x,v.y,v.z);
  var col=LC[T.lc[i]]||LC[50];
  var sh=0.90+Math.min(T.z[i],13)/13*0.40;
  tc.push(col[0]*sh,col[1]*sh,col[2]*sh);
}
for(var r=0;r<ny-1;r++)for(var c=0;c<nx-1;c++){
  var a=r*nx+c,b=a+1,d=a+nx,e=d+1;ti.push(a,d,b,b,d,e);
}
var tg=new THREE.BufferGeometry();
tg.setAttribute('position',new THREE.Float32BufferAttribute(tp,3));
tg.setAttribute('color',new THREE.Float32BufferAttribute(tc,3));
tg.setIndex(ti);tg.computeVertexNormals();
var terrainMesh=new THREE.Mesh(tg,new THREE.MeshStandardMaterial({vertexColors:true,
  side:THREE.DoubleSide,roughness:0.96,metalness:0.0}));
terrainMesh.receiveShadow=true;scene.add(terrainMesh);
function terrainZ(px,py){
  var fx=Math.max(0,Math.min(nx-1.001,px/W*(nx-1)));
  var fy=Math.max(0,Math.min(ny-1.001,py/H*(ny-1)));
  var c0=Math.floor(fx),r0=Math.floor(fy),tx=fx-c0,ty=fy-r0;
  var i00=r0*nx+c0,i10=i00+1,i01=i00+nx,i11=i01+1;
  return (T.z[i00]*(1-tx)+T.z[i10]*tx)*(1-ty)+(T.z[i01]*(1-tx)+T.z[i11]*tx)*ty;
}

/* ---------- 2. 长江水面：顶点色（江心深 / 近岸浅 + 顺江流纹） ---------- */
var G=D.waterGrid,gnx=G.nx,gny=G.ny,wp=[],wc=[],wi=[];
function waterTone(x,y){
  var dx=x-AX.c[0],dy=y-AX.c[1];
  var nrm=dx*NX+dy*NY,along=dx*UX+dy*UY;
  var bank=Math.min(1,Math.abs(nrm)/190);
  var ripple=0.030*Math.sin(along*0.075+nrm*0.026)+0.018*Math.sin(along*0.19-nrm*0.055);
  var k=0.82+0.24*bank+ripple;
  return [0.10*k*1.05,0.46*k,0.68*k];
}
for(var r=0;r<gny;r++)for(var c=0;c<gnx;c++){
  if(!G.m[r*gnx+c])continue;
  var x0=c/(gnx-1)*W,x1=(c+1)/(gnx-1)*W,y0=r/(gny-1)*H,y1=(r+1)/(gny-1)*H;
  var base=wp.length/3;
  var a=V(x0,y0,LAKEZ+0.04),b=V(x1,y0,LAKEZ+0.04),
      d=V(x1,y1,LAKEZ+0.04),e=V(x0,y1,LAKEZ+0.04);
  wp.push(a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,e.x,e.y,e.z);
  wi.push(base,base+1,base+2,base,base+2,base+3);
  [[x0,y0],[x1,y0],[x1,y1],[x0,y1]].forEach(function(q){
    var t=waterTone(q[0],q[1]);wc.push(t[0],t[1],t[2]);});
}
var wg=new THREE.BufferGeometry();
wg.setAttribute('position',new THREE.Float32BufferAttribute(wp,3));
wg.setAttribute('color',new THREE.Float32BufferAttribute(wc,3));
wg.setIndex(wi);wg.computeVertexNormals();
/* 江面：自定义水面着色器（菲涅尔天空反射 + 流动波光 + 日轮高光 + 桥影 + 距离雾） */
var cW=new THREE.Vector2(AX.c[0]-HALF_W,-(AX.c[1]-HALF_H));
var uW=new THREE.Vector2(UX,-UY),nW=new THREE.Vector2(NX,-NY);
var waterU={uTime:{value:0},uTint:{value:new THREE.Color(0xffffff)},
  uSky:{value:new THREE.Color(0x2e7ba0)},uSunCol:{value:new THREE.Color(0xffe6b8)},
  uSunDir:{value:new THREE.Vector3(-0.5,0.75,0.42).normalize()},
  uFogCol:{value:new THREE.Color(0x050b13)},uFogD:{value:0.00042},
  uSunI:{value:1.0},uWave:{value:1.0},uShadowI:{value:1.0},
  uAxisC:{value:cW},uAxisU:{value:uW},uAxisN:{value:nW},
  uShadowW:{value:BD.deckW*1.05},uSpanLen:{value:(AX.main1-AX.main0)/8},
  uBridgeH:{value:DECKZ*ZEX}};
var wmat=new THREE.ShaderMaterial({uniforms:waterU,transparent:true,side:THREE.DoubleSide,
  vertexShader:[
    'attribute vec3 color;varying vec3 vC;varying vec3 vW;',
    'void main(){vC=color;vec4 w=modelMatrix*vec4(position,1.0);vW=w.xyz;',
    'gl_Position=projectionMatrix*viewMatrix*w;}'].join('\n'),
  fragmentShader:[
    'varying vec3 vC;varying vec3 vW;',
    'uniform float uTime,uFogD,uSunI,uWave,uShadowI,uShadowW,uSpanLen,uBridgeH;',
    'uniform vec3 uTint,uSky,uSunCol,uSunDir,uFogCol;',
    'uniform vec2 uAxisC,uAxisU,uAxisN;',
    'void main(){',
    '  vec2 p=vW.xz;float t=uTime;',
    /* 域扭曲：先用低频波打乱采样坐标，避免等间距平行波纹形成摩尔纹/雨丝 */
    '  vec2 w=p+vec2(8.0*sin(p.y*0.017+t*0.10),7.0*sin(p.x*0.021-t*0.13));',
    '  float a=sin(w.x*0.13+w.y*0.052+t*0.85)+0.6*sin(w.x*0.29-w.y*0.11-t*1.35);',
    '  float b=sin(w.x*0.061-w.y*0.17+t*0.52)+0.5*sin(w.y*0.23+w.x*0.09+t*1.1);',
    '  vec3 n=normalize(vec3(a*0.055*uWave,1.0,b*0.050*uWave));',
    '  vec3 V=normalize(cameraPosition-vW);vec3 L=normalize(uSunDir);vec3 H=normalize(L+V);',
    '  float fres=pow(1.0-max(dot(n,V),0.0),2.2);',
    '  vec3 col=vC*uTint*0.88;',
    /* 明暗完全跟随波形本身，幅度压低，只留含蓄的水光而不形成碎白斑 */
    '  float swell=0.018*sin(a*0.9+b*0.6)+0.010*sin(b*1.7-a*0.4);',
    '  col*=1.0+swell;col=mix(col,uSky,fres*0.55);',
    /* 桥体在江面的投影：按主光方位把桥面高度投影到水面，随日照滑块移动 */
    '  vec2 q=p-uAxisC;',
    '  vec2 off=clamp(-uSunDir.xz*(uBridgeH/max(uSunDir.y,0.45)),vec2(-110.0),vec2(110.0));',
    '  float nrmS=dot(q,uAxisN)-dot(off,uAxisN);',
    '  float alongS=dot(q,uAxisU)-dot(off,uAxisU);',
    '  float band=1.0-smoothstep(uShadowW*0.55,uShadowW*1.3,abs(nrmS));',
    '  float spanMask=step(-uSpanLen,alongS)*step(alongS,uSpanLen);',
    '  float shad=1.0-0.52*band*spanMask*uShadowI;',
    '  col*=shad;',
    '  float sh=max(dot(n,H),0.0);',
    '  float glint=pow(sh,26.0)*0.12+pow(sh,110.0)*0.38;',
    '  float streak=0.5+0.5*sin(a*2.3+b*1.7+t*1.6);',
    '  col+=uSunCol*glint*uSunI*(0.30+0.40*streak)*shad;',
    '  float d=length(cameraPosition-vW);',
    '  float fog=1.0-exp(-pow(d*uFogD,2.0));',
    '  col=mix(col,uFogCol,clamp(fog,0.0,1.0)*0.85);',
    '  gl_FragColor=vec4(col,0.97);',
    '}'].join('\n')});
var waterMesh=new THREE.Mesh(wg,wmat);scene.add(waterMesh);
/* 不加规则流线：等间距短线在斜向江面上会形成摩尔纹，改由着色器波光表达水体 */

/* ---------- 3. 路网 ---------- */
function buildRibbon(lines,widthFn,hFn,opacity){
  var vp=[],vc=[],vi=[],k=0;
  lines.forEach(function(o){
    var pts=o.p,wd=widthFn(o),col=o.col;
    for(var i=0;i<pts.length-1;i++){
      var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
      if(L<0.05)continue;
      var ox=-dy/L*wd/2,oy=dx/L*wd/2;
      var za=Math.max(hFn(a[0],a[1]),terrainZ(a[0],a[1])+0.06);
      var zb=Math.max(hFn(b[0],b[1]),terrainZ(b[0],b[1])+0.06);
      var P1=V(a[0]+ox,a[1]+oy,za),P2=V(a[0]-ox,a[1]-oy,za),
          P3=V(b[0]-ox,b[1]-oy,zb),P4=V(b[0]+ox,b[1]+oy,zb);
      var base=k;k+=4;
      vp.push(P1.x,P1.y,P1.z,P2.x,P2.y,P2.z,P3.x,P3.y,P3.z,P4.x,P4.y,P4.z);
      for(var q=0;q<4;q++)vc.push(col[0],col[1],col[2]);
      vi.push(base,base+1,base+2,base,base+2,base+3);
    }
  });
  var g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(vp,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(vc,3));
  g.setIndex(vi);g.computeVertexNormals();
  var m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,
    roughness:0.82,metalness:0.02,transparent:opacity<1,opacity:opacity}));
  m.receiveShadow=true;m.renderOrder=2;return m;
}
var RC={7:[0.54,0.62,0.68],6:[0.44,0.53,0.61],5:[0.39,0.47,0.55],4:[0.34,0.41,0.49],
        3:[0.30,0.37,0.44],2:[0.27,0.33,0.39],1:[0.26,0.35,0.34]};
D.roads.forEach(function(o){o.col=RC[o.k]||RC[2];});
var roadMesh=buildRibbon(D.roads,function(o){return {7:6,6:5.4,5:4.8,4:3.8,3:2.8,2:1.9,1:1.3}[o.k]||2;},
   function(){return LAKEZ+0.09;},1);
scene.add(roadMesh);

/* ---------- 4. 几何容器 ---------- */
function GeomBuilder(){this.p=[];this.c=[];this.i=[];this.f=0;this.hit=[];this._pid=-1;}
GeomBuilder.prototype.pid=function(v){this._pid=v;};
GeomBuilder.prototype.tri=function(a,b,c,col){
  var base=this.p.length/3;
  this.p.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
  for(var q=0;q<3;q++)this.c.push(col[0],col[1],col[2]);
  this.i.push(base,base+1,base+2);
  var prev=this.f;this.f++;
  if(this.hit.length && this.hit[this.hit.length-1].pid===this._pid){
    this.hit[this.hit.length-1].e=this.f;
  }else this.hit.push({s:prev,e:this.f,pid:this._pid});
};
GeomBuilder.prototype.quad=function(a,b,c,d,col){this.tri(a,b,c,col);this.tri(a,c,d,col);};
GeomBuilder.prototype.mesh=function(){
  var g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(this.p,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(this.c,3));
  g.setIndex(this.i);g.computeVertexNormals();
  var mat=new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,
    roughness:0.58,metalness:0.10});
  var m=new THREE.Mesh(g,mat);m.renderOrder=5;m.castShadow=true;m.receiveShadow=true;
  m.userData.hit=this.hit;m.userData.mat=mat;
  clipped.push(mat);return m;
};
/* 一根矩形截面杆（3 个可见面，a/b 为 Vector3） */
function bar(g,a,b,wd,col){
  /* 十字截面：水平面内两正交方向 + 垂直方向，任意视角都可见 */
  var s=[col[0]*0.72,col[1]*0.72,col[2]*0.72];
  var dirs=[[NX*wd,0,-NY*wd,1],[UX*wd,0,-UY*wd,1],[0,wd*0.85,0,0.72]];
  for(var k=0;k<dirs.length;k++){
    var q=dirs[k],c2=(q[3]===1?col:[col[0]*q[3],col[1]*q[3],col[2]*q[3]]);
    var A1=new THREE.Vector3(a.x+q[0],a.y+q[1],a.z+q[2]),
        A2=new THREE.Vector3(a.x-q[0],a.y-q[1],a.z-q[2]),
        B1=new THREE.Vector3(b.x+q[0],b.y+q[1],b.z+q[2]),
        B2=new THREE.Vector3(b.x-q[0],b.y-q[1],b.z-q[2]);
    g.quad(A1,A2,B2,B1,k===2?s:c2);
  }
}
/* 沿折线生成立体桥面带（顶面 + 两侧立面 + 底面），z 取点第三维 */
function deckBand(g,pts,width,zBotOff,col,pid){
  g.pid(pid);
  var side=[col[0]*0.66,col[1]*0.66,col[2]*0.66];
  for(var i=0;i<pts.length-1;i++){
    var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
    if(L<0.05)continue;
    var ox=-dy/L*width/2,oy=dx/L*width/2;
    var za=a[2],zb=b[2];
    var A=V(a[0]+ox,a[1]+oy,za),B=V(a[0]-ox,a[1]-oy,za),
        C=V(b[0]-ox,b[1]-oy,zb),Dd=V(b[0]+ox,b[1]+oy,zb);
    g.quad(A,B,C,Dd,col);
    var Ab=V(a[0]+ox,a[1]+oy,za-zBotOff),Bb=V(a[0]-ox,a[1]-oy,za-zBotOff),
        Cb=V(b[0]-ox,b[1]-oy,zb-zBotOff),Db=V(b[0]+ox,b[1]+oy,zb-zBotOff);
    g.quad(Ab,Db,Cb,Bb,side);
    g.quad(A,Ab,Bb,B,side);
    g.quad(A,Dd,Db,Ab,side);g.quad(B,Bb,Cb,C,side);
  }
}
function pillar(g,cx,cy,w,d,z0,z1,col,pid){
  g.pid(pid);
  var hx=UX*d/2,hy=UY*d/2,wx=NX*w/2,wy=NY*w/2;
  var P=[[cx-hx-wx,cy-hy-wy],[cx+hx-wx,cy+hy-wy],
         [cx+hx+wx,cy+hy+wy],[cx-hx+wx,cy-hy+wy]];
  var top=[],bot=[];
  for(var i=0;i<4;i++){top.push(V(P[i][0],P[i][1],z1));bot.push(V(P[i][0],P[i][1],z0));}
  for(var i=0;i<4;i++){
    var j=(i+1)%4,sh=0.72+0.26*Math.abs(Math.cos(i*1.2));
    g.quad(bot[i],bot[j],top[j],top[i],[col[0]*sh,col[1]*sh,col[2]*sh]);
  }
  g.quad(top[0],top[1],top[2],top[3],[col[0]*1.12,col[1]*1.12,col[2]*1.12]);
}

var STEEL=[0.74,0.82,0.89], GOLD=[1.00,0.82,0.46], TRUSS=[0.66,0.76,0.84],
    DECKC=[0.88,0.90,0.92], RAILC=[0.54,0.62,0.69], PIER=[0.66,0.72,0.77],
    TOWERC=[0.86,0.83,0.74], APPRC=[0.46,0.54,0.60], WHITE=[0.93,0.94,0.90],
    ROOFC=[0.92,0.72,0.34];

/* 索引范围：主桥 / 引桥 */
function idxOf(t){return Math.round((t-AX.t0)/AX.step);}
var I0=idxOf(AX.main0), I1=idxOf(AX.main1);
var mainA=BD.deckA.slice(I0,I1+1), mainB=BD.deckB.slice(I0,I1+1);
var apprA1=BD.deckA.slice(0,I0+1), apprB1=BD.deckB.slice(0,I0+1);
var apprA2=BD.deckA.slice(I1), apprB2=BD.deckB.slice(I1);

/* 4a. 上层公路桥面 + 下层铁路桥面 */
var deckG=new GeomBuilder();
deckBand(deckG,mainA,BD.deckW,0.42,DECKC,3);
deckBand(deckG,apprA1,BD.deckW*0.86,0.40,APPRC,16);
deckBand(deckG,apprA2,BD.deckW*0.86,0.40,APPRC,17);
var deckMesh=deckG.mesh();scene.add(deckMesh);
var railG=new GeomBuilder();
var railA=mainA.map(function(p){return [p[0],p[1],RAILZ];});
var railB=mainB.map(function(p){return [p[0],p[1],RAILZ];});
deckBand(railG,railA,BD.deckW*0.66,0.24,RAILC,4);
var railMesh=railG.mesh();scene.add(railMesh);

/* 车道标线（暖白虚线，双幅中心） */
var markG=new GeomBuilder();markG.pid(-1);
for(var i=I0;i<I1-2;i+=3){
  var a=BD.deck[i],b=BD.deck[i+1];
  if(!a||!b)continue;
  var p1=V(a[0],a[1],DECKZ+0.05),p2=V(b[0],b[1],DECKZ+0.05);
  bar(markG,p1,p2,0.11,WHITE,true);
}
var markMesh=markG.mesh();scene.add(markMesh);

/* 4b. 米字形钢桁架（两片主桁 + 上下弦 + 竖杆 + 菱形斜杆 + 横撑） */
var trussG=new GeomBuilder();
function panelPid(i){return i<I0+48?0:(i<I0+97?1:2);}
for(var side=0;side<2;side++){
  var P=(side===0)?mainA:mainB;
  for(var i=0;i<P.length-1;i++){
    var a=P[i],b=P[i+1];
    trussG.pid(panelPid(I0+i));
    var zt=a[2],zb=RAILZ;
    var At=V(a[0],a[1],zt),Bt=V(b[0],b[1],b[2]);
    var Ab=V(a[0],a[1],zb),Bb=V(b[0],b[1],zb);
    bar(trussG,At,Bt,0.42,TRUSS,true);          // 上弦
    bar(trussG,Ab,Bb,0.42,TRUSS,true);          // 下弦
    bar(trussG,Ab,At,0.34,STEEL,false);         // 竖杆
    /* 米字：中点 + 两条交叉斜杆（每 2 节点一大节间） */
    if(i%2===0 && i+2<P.length){
      var c=P[i+2];
      var Ct=V(c[0],c[1],c[2]),Cb=V(c[0],c[1],zb);
      var Mx=(b[0]+c[0])/2,My=(b[1]+c[1])/2;
      var Mtop=V(Mx,My,(b[2]+c[2])/2),Mbot=V(Mx,My,zb);
      bar(trussG,Ab,Bt,0.28,GOLD,true);
      bar(trussG,Bb,At,0.28,GOLD,true);
      bar(trussG,Bt,Cb,0.28,GOLD,true);
      bar(trussG,Bb,Ct,0.28,GOLD,true);
      bar(trussG,Mbot,Mtop,0.26,STEEL,false);
    }
  }
}
/* 横向联结（上/下平联），每 4 个节点一道 */
for(var i=0;i<mainA.length-1;i+=4){
  var a=mainA[i],b=mainB[i];
  if(!a||!b)continue;
  trussG.pid(panelPid(I0+i));
  bar(trussG,V(a[0],a[1],a[2]),V(b[0],b[1],b[2]),0.32,STEEL,true);
  bar(trussG,V(a[0],a[1],RAILZ),V(b[0],b[1],RAILZ),0.32,STEEL,true);
}
var trussMesh=trussG.mesh();scene.add(trussMesh);

/* 4c. 桥墩 + 管柱基础 */
var pierG=new GeomBuilder();
BD.piers.forEach(function(p){
  var x=p.p[0],y=p.p[1];
  pierG.pid(p.pid);
  pillar(pierG,x,y,4.2,5.0,LAKEZ-1.3,RAILZ-0.5,PIER,p.pid);
  /* 管柱示意（六根细柱） */
  for(var k=-2;k<=2;k++){
    var px=x+NX*k*0.95,py=y+NY*k*0.95;
    pillar(pierG,px,py,0.5,0.5,LAKEZ-1.6,LAKEZ+0.15,[0.50,0.58,0.64],-1);
  }
});
var pierMesh=pierG.mesh();scene.add(pierMesh);

/* 4d. 桥头堡（7 层 + 攒尖顶） + 引桥墩 */
var towerG=new GeomBuilder();
BD.towers.forEach(function(t){
  var x=t.p[0],y=t.p[1];
  towerG.pid(t.pid);
  var gz=Math.max(terrainZ(x,y),DECKZ-9.0);
  /* 左右两座（公路面两侧），中间留出行车通道 */
  for(var s=-1;s<=1;s+=2){
    var cx=x+NX*s*(BD.deckW*0.62),cy=y+NY*s*(BD.deckW*0.62);
    pillar(towerG,cx,cy,7.2,8.4,gz,gz+9.0,TOWERC,t.pid);
    /* 7 层窗带 + 金色挑檐交替，塔楼层次可辨 */
    for(var L=1;L<=6;L++){
      var z=gz+L*1.3;
      var q1=V(cx-NX*4.15-UX*4.65,cy-NY*4.15-UY*4.65,z),
          q2=V(cx+NX*4.15-UX*4.65,cy+NY*4.15-UY*4.65,z),
          q3=V(cx+NX*4.15+UX*4.65,cy+NY*4.15+UY*4.65,z),
          q4=V(cx-NX*4.15+UX*4.65,cy-NY*4.15+UY*4.65,z);
      towerG.quad(q1,q2,q3,q4,[0.24,0.28,0.32]);
      var e2=4.7;
      var r1=V(cx-NX*e2-UX*e2,cy-NY*e2-UY*e2,z+0.16),
          r2=V(cx+NX*e2-UX*e2,cy+NY*e2-UY*e2,z+0.16),
          r3=V(cx+NX*e2+UX*e2,cy+NY*e2+UY*e2,z+0.16),
          r4=V(cx-NX*e2+UX*e2,cy-NY*e2+UY*e2,z+0.16);
      towerG.quad(r1,r2,r3,r4,[0.94,0.80,0.52]);
    }
    /* 攒尖顶 */
    var apex=V(cx,cy,gz+12.4);
    var e=5.2;
    var c1=V(cx-NX*e-UX*e,cy-NY*e-UY*e,gz+9.0),
        c2=V(cx+NX*e-UX*e,cy+NY*e-UY*e,gz+9.0),
        c3=V(cx+NX*e+UX*e,cy+NY*e+UY*e,gz+9.0),
        c4=V(cx-NX*e+UX*e,cy-NY*e+UY*e,gz+9.0);
    towerG.tri(c1,c2,apex,ROOFC);towerG.tri(c2,c3,apex,ROOFC);
    towerG.tri(c3,c4,apex,ROOFC);towerG.tri(c4,c1,apex,ROOFC);
    pillar(towerG,cx,cy,0.55,0.55,gz+12.4,gz+14.0,[1.00,0.86,0.50],t.pid);
  }
});
/* 引桥墩（每 17.2 m 一孔，简化为每 4 节点一个） */
[apprA1,apprA2].forEach(function(seg,si){
  var pid=si===0?16:17;
  for(var i=2;i<seg.length-1;i+=4){
    var a=seg[i];
    towerG.pid(pid);
    pillar(towerG,a[0],a[1],1.5,1.8,terrainZ(a[0],a[1]),a[2]-0.55,PIER,pid);
  }
});
var towerMesh=towerG.mesh();scene.add(towerMesh);

/* 4e. 4 座民族形式桥亭 + 纪念碑 */
var annexG=new GeomBuilder();annexG.pid(-1);
[[AX.main0,1],[AX.main0,-1],[AX.main1,1],[AX.main1,-1]].forEach(function(q){
  var x=BD.axis.c[0]+q[0]*UX/4, y=BD.axis.c[1]+q[0]*UY/4;
  x+=NX*q[1]*(BD.deckW*0.52); y+=NY*q[1]*(BD.deckW*0.52);
  var z=DECKZ+0.1;
  pillar(annexG,x,y,1.1,1.1,z,z+1.6,TOWERC,-1);
  var apex=V(x,y,z+2.6),e=1.0;
  var c1=V(x-NX*e-UX*e,y-NY*e-UY*e,z+1.6),c2=V(x+NX*e-UX*e,y+NY*e-UY*e,z+1.6),
      c3=V(x+NX*e+UX*e,y+NY*e+UY*e,z+1.6),c4=V(x-NX*e+UX*e,y-NY*e+UY*e,z+1.6);
  annexG.tri(c1,c2,apex,ROOFC);annexG.tri(c2,c3,apex,ROOFC);
  annexG.tri(c3,c4,apex,ROOFC);annexG.tri(c4,c1,apex,ROOFC);
});
var memX=BD.axis.c[0]+(AX.main1+30)*UX/4,memY=BD.axis.c[1]+(AX.main1+30)*UY/4;
pillar(annexG,memX,memY,0.7,0.7,terrainZ(memX,memY),terrainZ(memX,memY)+4.2,[0.88,0.88,0.84],-1);
var annexMesh=annexG.mesh();scene.add(annexMesh);

/* ---------- 5. 建筑 ---------- */
var bp=[],bc=[],bi=[],hitB=[],fB=0;
var BCOL=[[0.30,0.48,0.62],[0.37,0.55,0.68],[0.44,0.61,0.73],[0.52,0.67,0.78],[0.62,0.72,0.76]];
var NAMED=[1.00,0.76,0.38];
/* 离桥越远越矮、越暗：把视线聚焦到桥梁本体 */
function bFade(x,y){
  var dx=x-AX.c[0],dy=y-AX.c[1];
  return 0.50+0.50*Math.exp(-Math.abs(dx*NX+dy*NY)/230);
}
function triB(a,b,c,col){
  var base=bp.length/3;
  bp.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
  for(var q=0;q<3;q++)bc.push(col[0],col[1],col[2]);
  bi.push(base,base+1,base+2);fB++;
}
D.buildings.forEach(function(b,idx){
  var poly=b.p.slice();
  if(poly.length>2){var p0=poly[0],pl=poly[poly.length-1];
    if(Math.abs(p0[0]-pl[0])<0.01&&Math.abs(p0[1]-pl[1])<0.01)poly=poly.slice(0,-1);}
  if(poly.length<3)return;
  var fd=bFade(b.c?b.c[0]:poly[0][0],b.c?b.c[1]:poly[0][1]);
  var h=Math.max(b.h*BEX*(0.86+0.14*fd),0.5),base=0;
  for(var i=0;i<poly.length;i++)base=Math.max(base,terrainZ(poly[i][0],poly[i][1]));
  base-=0.05;
  var ci=Math.min(BCOL.length-1,Math.floor(h/4));
  var col=b.n?NAMED:BCOL[ci];
  var dim=0.80+0.20*fd;
  col=[col[0]*dim,col[1]*dim,col[2]*dim];
  var top=[],bot=[];
  for(var i=0;i<poly.length;i++){
    top.push(V(poly[i][0],poly[i][1],base+h));bot.push(V(poly[i][0],poly[i][1],base));
  }
  for(var i=0;i<poly.length;i++){
    var j=(i+1)%poly.length,sh=0.72+0.28*Math.abs(Math.cos(i*1.1));
    var sc=[col[0]*sh,col[1]*sh,col[2]*sh];
    triB(bot[i],bot[j],top[j],sc);triB(bot[i],top[j],top[i],sc);
  }
  var contour=poly.map(function(p){return new THREE.Vector2(p[0],p[1]);});
  var faces=[];try{faces=THREE.ShapeUtils.triangulateShape(contour,[]);}catch(e){faces=[];}
  if(!faces.length){for(var i=1;i<poly.length-1;i++)faces.push([0,i,i+1]);}
  for(var i=0;i<faces.length;i++){
    var f=faces[i];triB(top[f[0]],top[f[1]],top[f[2]],[col[0]*1.08,col[1]*1.08,col[2]*1.08]);
  }
  hitB.push({s:hitB.length?hitB[hitB.length-1].e:0,e:fB,i:idx});
});
var bg=new THREE.BufferGeometry();
bg.setAttribute('position',new THREE.Float32BufferAttribute(bp,3));
bg.setAttribute('color',new THREE.Float32BufferAttribute(bc,3));
bg.setIndex(bi);bg.computeVertexNormals();
var bmat=new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,
  roughness:0.84,metalness:0.03});
clipped.push(bmat);
var buildingMesh=new THREE.Mesh(bg,bmat);buildingMesh.renderOrder=5;
buildingMesh.castShadow=true;buildingMesh.receiveShadow=true;scene.add(buildingMesh);

/* ---------- 6. 沙盘底座 + 网格刻度 ---------- */
var baseG=new THREE.BoxGeometry(W+26,13,H+26);
var baseM=new THREE.Mesh(baseG,new THREE.MeshStandardMaterial({color:0x0c1928,
  roughness:0.92,metalness:0.02}));
baseM.position.set(0,-7.0,0);baseM.receiveShadow=true;scene.add(baseM);
var edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(W+26,13,H+26)),
  new THREE.LineBasicMaterial({color:0x3b7fa8}));edge.position.copy(baseM.position);scene.add(edge);
var gridP=[];
for(var gx=0;gx<=W;gx+=50){gridP.push(gx-HALF_W,-0.28,-HALF_H-13,gx-HALF_W,-0.28,HALF_H+13);}
for(var gy=0;gy<=H;gy+=50){gridP.push(-HALF_W-13,-0.28,gy-HALF_H,HALF_W+13,-0.28,gy-HALF_H);}
var gridG=new THREE.BufferGeometry();
gridG.setAttribute('position',new THREE.Float32BufferAttribute(gridP,3));
var gridMesh=new THREE.LineSegments(gridG,new THREE.LineBasicMaterial({color:0x1d3f58,transparent:true,opacity:.55}));
scene.add(gridMesh);

/* ---------- 6.5 夜景灯带：桥面路灯 + 城市灯火（仅夜景模式显示） ---------- */
var lampP=[],lampC=[];
function putLamp(x,y,z,r,g,b){lampP.push(x-HALF_W,z*ZEX,-(y-HALF_H));lampC.push(r,g,b);}
for(var s=AX.t0+8;s<=AX.t1-8;s+=44){
  var lx=AX.c[0]+s*UX/4,ly=AX.c[1]+s*UY/4;
  var off=BD.deckW*0.46;
  putLamp(lx+NX*off,ly+NY*off,DECKZ+2.0,1.0,0.80,0.48);
  putLamp(lx-NX*off,ly-NY*off,DECKZ+2.0,1.0,0.80,0.48);
}
D.buildings.forEach(function(b,i){
  if(i%9!==0||!b.c)return;
  putLamp(b.c[0],b.c[1],b.h*BEX*1.03+0.8,0.95,0.72,0.42);
});
var lampG=new THREE.BufferGeometry();
lampG.setAttribute('position',new THREE.Float32BufferAttribute(lampP,3));
lampG.setAttribute('color',new THREE.Float32BufferAttribute(lampC,3));
var lampPts=new THREE.Points(lampG,new THREE.PointsMaterial({size:12,sizeAttenuation:true,
  vertexColors:true,transparent:true,opacity:0.42,depthWrite:false,
  blending:THREE.AdditiveBlending}));
lampPts.visible=false;lampPts.renderOrder=8;scene.add(lampPts);

/* ---------- 7. 标注 ---------- */
var labBox=document.getElementById('labels'),labels=[];
function addLabel(n,p,z,cls,bridge){
  var e=document.createElement('div');e.className='lab'+(cls?' '+cls:'');
  e.textContent=n;labBox.appendChild(e);
  labels.push({e:e,v:V(p[0],p[1],z),bridge:!!bridge});
}
D.poi.forEach(function(p){addLabel(p.n,p.p,p.z,p.hot?'hot':'',false);});
/* 每孔跨径标注（骨架模式隐藏） */
/* 每联一个跨径标注，避免 9 个标签互相重叠 */
[0,1,2].forEach(function(j){
  var t=AX.main0+(j+0.5)*3*AX.span;
  var x=AX.c[0]+t*UX/4,y=AX.c[1]+t*UY/4;
  addLabel('第'+(j+1)+'联 · 3×128 m',[x,y],DECKZ+2.6,'span',true);
});
addLabel('汉阳引桥 303 m',[AX.c[0]+(AX.t0+AX.main0)/2*UX/4,AX.c[1]+(AX.t0+AX.main0)/2*UY/4],
         DECKZ+1.0,'dim',true);
addLabel('武昌引桥 211 m',[AX.c[0]+(AX.t1+AX.t1+211)/2*UX/4,AX.c[1]+(AX.t1+AX.t1+211)/2*UY/4],
         DECKZ+1.0,'dim',true);

/* ---------- 8. 相机与交互 ---------- */
var BCX=BD.axis.c[0]-HALF_W, BCZ=-(BD.axis.c[1]-HALF_H);
var st={th:-0.40,ph:0.37,dist:980,tx:BCX,ty:DECKZ*ZEX*0.80,tz:BCZ};
/* 右上角「桥身细部」：同一场景、独立相机、双视口渲染 */
var INSET_ON=true, INSET_W=330, INSET_H=174, INSET_R=22, INSET_T=92;
var iCam=new THREE.PerspectiveCamera(32,INSET_W/INSET_H,1,12000);
function applyInsetCam(){
  var th=-0.12,ph=0.15,dist=360,ty=DECKZ*ZEX*1.00;
  iCam.position.set(BCX+dist*Math.cos(ph)*Math.sin(th),ty+dist*Math.sin(ph),
                    BCZ+dist*Math.cos(ph)*Math.cos(th));
  iCam.lookAt(BCX,ty,BCZ);iCam.updateProjectionMatrix();
}
applyInsetCam();
function setInset(on){
  INSET_ON=!!on;
  document.getElementById('inset').classList.toggle('hide',!INSET_ON);
}
function applyCam(){
  var cx=st.tx+st.dist*Math.cos(st.ph)*Math.sin(st.th);
  var cy=st.ty+st.dist*Math.sin(st.ph);
  var cz=st.tz+st.dist*Math.cos(st.ph)*Math.cos(st.th);
  camera.position.set(cx,cy,cz);camera.lookAt(st.tx,st.ty,st.tz);
}
applyCam();
var drag=null;
cv.addEventListener('pointerdown',function(e){drag={x:e.clientX,y:e.clientY,b:e.button};
  try{cv.setPointerCapture(e.pointerId);}catch(err){}});
cv.addEventListener('pointerup',function(e){
  if(drag&&Math.abs(e.clientX-drag.x)<3&&Math.abs(e.clientY-drag.y)<3&&drag.b===0)pick(e);
  drag=null;
});
cv.addEventListener('pointermove',function(e){
  if(!drag)return;
  var dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;
  if(drag.b===2||e.shiftKey){
    var sc=st.dist/900;
    var right=new THREE.Vector3().subVectors(camera.position,new THREE.Vector3(st.tx,st.ty,st.tz))
      .cross(camera.up).normalize();
    st.tx-=right.x*dx*sc;st.tz-=right.z*dx*sc;st.ty+=dy*sc;
  }else{st.th-=dx*0.005;st.ph=Math.max(0.08,Math.min(1.48,st.ph+dy*0.004));}
  applyCam();
});
cv.addEventListener('contextmenu',function(e){e.preventDefault();});
cv.addEventListener('wheel',function(e){e.preventDefault();
  st.dist=Math.max(200,Math.min(5000,st.dist*(1+Math.sign(e.deltaY)*0.11)));applyCam();},{passive:false});
addEventListener('resize',function(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);});

/* ---------- 9. 点选 ---------- */
var ray=new THREE.Raycaster(),ndc=new THREE.Vector2();
var rightPanel=document.getElementById('right'),rbody=document.getElementById('rbody');
var pickMeshes=[deckMesh,railMesh,trussMesh,pierMesh,towerMesh,buildingMesh];
var KIND={truss:'连续钢桁梁',deck:'上层公路桥面',rail:'下层铁路桥面',pier:'桥墩 / 基础',
          foundation:'管柱基础',tower:'桥头堡 / 桥台',pavilion:'桥亭',approach:'引桥',annex:'附属设施'};
function pick(e){
  ndc.x=e.clientX/innerWidth*2-1;ndc.y=-(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(ndc,camera);
  var its=ray.intersectObjects(pickMeshes,false);
  if(!its.length){rightPanel.classList.remove('show');return;}
  var o=its[0],fi=o.faceIndex,part=null;
  if(o.object===buildingMesh){
    for(var i=0;i<hitB.length;i++){if(fi>=hitB[i].s&&fi<hitB[i].e){showBuilding(D.buildings[hitB[i].i]);return;}}
    rightPanel.classList.remove('show');return;
  }
  var hh=o.object.userData.hit;
  for(var i=0;i<hh.length;i++){if(fi>=hh[i].s&&fi<hh[i].e&&hh[i].pid>=0){part=BD.parts[hh[i].pid];break;}}
  if(!part){rightPanel.classList.remove('show');return;}
  showPart(part);
}
function showPart(p){
  document.getElementById('deckcard').classList.remove('show');
  var kv=[['构件类型',KIND[p.k]||p.k],['构件编号','WHB-'+String(p.id+1).padStart(3,'0')],
    ['中心桩号',p.st],['里程范围','K'+(p.s/1000).toFixed(3)+' – K'+(p.e/1000).toFixed(3)],
    ['区段长度',p.l.toFixed(1)+' m'],['标高范围',(p.z0*4).toFixed(1)+' – '+(p.z1*4).toFixed(1)+' m（相对江面）'],
    ['材料 / 构造',p.mat||'—'],['技术规格',p.spec||'—'],['数据来源',p.src]];
  var rows=kv.map(function(x){return '<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';}).join('');
  rbody.innerHTML='<div class="rname">'+p.n+'</div><div class="rtype">BRIDGE ELEMENT · '+p.k.toUpperCase()+'</div>'+rows+
    (p.note?'<div class="divider"></div><div style="font-size:10px;color:#a9c9e4;line-height:1.7">'+p.note+'</div>':'')+
    '<div class="divider"></div><div style="font-size:10px;color:#e8b478;line-height:1.7">'+
    '桥梁几何按公开设计参数重建，非竣工 BIM，不含构件级应力 / 监测属性；不作量测。</div>';
  rightPanel.classList.add('show');
}
function showBuilding(b){
  document.getElementById('deckcard').classList.remove('show');
  var at=b.at||{};
  var kv=[['构件类型','示意地标 / 建筑体块'],['层数',b.lv+' 层'],
    ['模型高度',(b.h*4).toFixed(1)+' m'],['占地',b.a.toLocaleString()+' m²'],['高度来源',b.s]];
  var rows=kv.map(function(x){return '<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';}).join('');
  var tg='';Object.keys(at).forEach(function(k){tg+='<div class="kv"><k>'+k+'</k><v>'+at[k]+'</v></div>';});
  rbody.innerHTML='<div class="rname">'+(b.n||'未命名建筑')+'</div>'+
    '<div class="rtype">SCHEMATIC BUILDING</div>'+rows+
    (tg?'<div class="divider"></div><div class="ptitle">公开资料</div>'+tg:'');
  rightPanel.classList.add('show');
}
document.getElementById('rclose').onclick=function(){rightPanel.classList.remove('show');};

/* ---------- 10. 图层 / 模式 ---------- */
var LY=[['地形 · Copernicus DEM',terrainMesh,1,'#3d7a52'],['长江 · DEM 低地水面',waterMesh,1,'#16618c'],
  ['城市路网 · 示意',roadMesh,1,'#5b7080'],['上层公路桥面',deckMesh,1,'#c9cfd4'],
  ['下层铁路桥面',railMesh,1,'#6b808f'],['米字形钢桁架',trussMesh,1,'#e8c46a'],
  ['桥墩 · 管柱基础',pierMesh,1,'#8a99a6'],['桥头堡 · 引桥',towerMesh,1,'#d9cfb8'],
  ['桥亭 / 标线 / 纪念碑',annexMesh,1,'#e8d9a0'],['周边建筑 · 示意',buildingMesh,1,'#6ba8c8'],
  ['地名 / 跨径标注',null,1,'#dff1ff']];
var layBox=document.getElementById('layers');
LY.forEach(function(o,i){
  var d=document.createElement('label');d.className='ly';
  d.innerHTML='<input type="checkbox" checked data-i="'+i+'"><span class="sw" style="background:'+o[3]+'"></span>'+o[0];
  layBox.appendChild(d);
});
var bridgeLabelsHidden=false, SEP=0;
function setLayer(i,on){
  if(LY[i][1])LY[i][1].visible=on;
  else{
    bridgeLabelsHidden=!on||document.getElementById('btnSkel').classList.contains('on');
    labels.forEach(function(l){l.e.style.display=(on&&!(bridgeLabelsHidden&&l.bridge))?'':'none';});
  }
}
layBox.addEventListener('change',function(e){setLayer(+e.target.dataset.i,e.target.checked);});
function setMode(mode){
  ['btnAll','btnFloors','btnSkel','btnTop','btnWide'].forEach(function(id){
    document.getElementById(id).classList.remove('on');});
  document.getElementById(mode).classList.add('on');
  document.getElementById('deckcard').classList.toggle('show',mode==='btnFloors');
  if(mode==='btnFloors'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    bridgeLabelsHidden=false;
    st.th=-0.16;st.ph=0.30;st.dist=700;
    st.tx=BCX;st.ty=DECKZ*ZEX*0.90;st.tz=BCZ;applyCam();
    document.getElementById('tip').textContent='双层分解：上层公路面上移 / 下层铁路面下移 — 公铁两用结构一眼看清';
  }else if(mode==='btnSkel'){
    [3,4,5,6,7,8,9].forEach(function(i){setLayer(i,false);});
    [0,1,2,10].forEach(function(i){setLayer(i,true);});
    bridgeLabelsHidden=true;
    labels.forEach(function(l){if(l.bridge)l.e.style.display='none';});
    st.th=-0.48;st.ph=1.30;st.dist=1780;st.tx=BCX;st.ty=0;st.tz=BCZ;applyCam();
    document.getElementById('tip').textContent='地理骨架：长江江面 / 龟蛇二山 / 路网 — 先确认桥位与江岸线，再叠桥梁构件';
  }else if(mode==='btnTop'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    bridgeLabelsHidden=false;
    st.th=0;st.ph=1.47;st.dist=1800;st.tx=BCX;st.ty=0;st.tz=BCZ;applyCam();
    document.getElementById('tip').textContent='正射俯视：核对桥轴线、3 联 9 孔跨径分段与长江走向';
  }else if(mode==='btnWide'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    bridgeLabelsHidden=false;
    st.th=-0.10;st.ph=0.24;st.dist=640;
    st.tx=BCX;st.ty=DECKZ*ZEX*0.82;st.tz=BCZ;applyCam();
    document.getElementById('tip').textContent='桥身主视：米字形钢桁架 / 8 墩 9 孔 / 上层公路 + 下层铁路双线';
  }else{
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    bridgeLabelsHidden=false;
    st.th=-0.40;st.ph=0.37;st.dist=980;st.tx=BCX;st.ty=DECKZ*ZEX*0.80;st.tz=BCZ;applyCam();
    document.getElementById('tip').textContent='沙盘全景：右上角为桥身细部同步机位 · 拖动旋转 · 滚轮缩放 · 单击构件查看属性';
  }
  /* 骨架模式隐藏了桥梁构件，画中画同步收起；桥身模式主视已是特写 */
  setInset(mode==='btnAll'||mode==='btnTop');
  /* 图层都复位后再应用双层分解，避免 setLayer 把桁架重新打开 */
  applySep(mode==='btnFloors'?8:0);
  layBox.querySelectorAll('input').forEach(function(cb,i2){cb.checked=LY[i2][1]?LY[i2][1].visible:true;});
}
['btnAll','btnFloors','btnSkel','btnTop','btnWide'].forEach(function(id){
  document.getElementById(id).onclick=function(){setMode(id);};});

/* 双层分解：上层公路上移、下层铁路下移 */
function applySep(v){
  SEP=+v;
  deckMesh.position.y=SEP*ZEX*0.9;
  markMesh.position.y=SEP*ZEX*0.9;
  trussMesh.visible=SEP===0&&LY[5][1].visible;
  railMesh.position.y=-SEP*ZEX*0.35;
}

/* ---------- 11. 高度剖切 ---------- */
var cut=document.getElementById('cut'),cutv=document.getElementById('cutv');
cut.oninput=function(){
  var t=+cut.value/100;
  if(t>=0.999){clipped.forEach(function(m){m.clippingPlanes=[];});cutv.textContent='不限';}
  else{
    var maxh=(DECKZ+9.6)*ZEX+10;
    var yy=(0.04+0.96*t)*maxh;clip.constant=yy;
    clipped.forEach(function(m){m.clippingPlanes=[clip];m.needsUpdate=true;});
    cutv.textContent='≤ '+(yy/ZEX*4).toFixed(0)+' m（相对江面）';
  }
};

/* ---------- 12. 构件清单 / 搜索 ---------- */
var plist=document.getElementById('plist');
BD.parts.forEach(function(p){
  var e=document.createElement('div');e.className='pi';
  e.innerHTML='<span class="tag">'+(KIND[p.k]||p.k).slice(0,2)+'</span>'+
    '<span class="nm">'+p.n+'</span><span class="st">'+p.st+'</span>';
  e.onclick=function(){locatePart(p);};plist.appendChild(e);
});
function focus(x,y,z,dist,ph,th){
  st.tx=x-HALF_W;st.tz=-(y-HALF_H);st.ty=z*ZEX;st.dist=dist;st.ph=ph;st.th=th;applyCam();
}
function locatePart(p){
  focus(p.c[0],p.c[1],DECKZ*0.7,520,0.38,-0.12);
  document.getElementById('tip').textContent='已定位：'+p.n+' · '+p.st;
  showPart(p);
}
function locate(){
  var q=document.getElementById('q').value.trim();if(!q)return;
  for(var i=0;i<BD.parts.length;i++)if(BD.parts[i].n.indexOf(q)>=0){locatePart(BD.parts[i]);return;}
  for(var i=0;i<D.buildings.length;i++)if(D.buildings[i].n&&D.buildings[i].n.indexOf(q)>=0){
    var b=D.buildings[i];focus(b.c[0],b.c[1],4,380,0.60,-0.50);
    document.getElementById('tip').textContent='已定位：'+b.n;showBuilding(b);return;}
  for(var i=0;i<D.poi.length;i++)if(D.poi[i].n.indexOf(q)>=0){
    focus(D.poi[i].p[0],D.poi[i].p[1],D.poi[i].z,520,0.60,-0.50);
    document.getElementById('tip').textContent='已定位：'+D.poi[i].n;return;}
  document.getElementById('tip').textContent='未找到「'+q+'」，试试：钢桁梁 / 桥头堡 / 黄鹤楼 / 龟山';
}
document.getElementById('go').onclick=locate;
document.getElementById('q').addEventListener('keydown',function(e){if(e.key==='Enter')locate();});

/* ---------- 13. 统计 / 图例 / 说明 ---------- */
var K=[['全桥长',BM.total,'m'],['正桥',BM.main,'m'],['主孔',128,'m'],
  ['桥孔',BM.n_span,'孔'],['水中墩',BM.n_pier,'座'],['桥头堡',BM.n_tower,'座'],
  ['桁架高',BM.truss_h,'m'],['公路宽',BM.deck_w,'m'],['铁路宽',BM.rail_w,'m'],
  ['可点选',BM.n_part,'项'],['江面',BM.river_width,'m'],['DEM',M.dem_max,'m']];
document.getElementById('kpis').innerHTML=K.map(function(x){
  return '<div class="kpi"><b>'+x[1]+'<i>'+x[2]+'</i></b><span>'+x[0]+'</span></div>';}).join('');
var LEG=[['#3d7a52','龟山 / 蛇山'],['#16618c','长江水面'],['#5b7080','示意路网'],
  ['#c9cfd4','上层公路面'],['#6b808f','下层铁路面'],['#e8c46a','米字形钢桁架'],
  ['#8a99a6','桥墩 / 基础'],['#d9cfb8','桥头堡'],['#6ba8c8','示意建筑'],['#ffd98a','具名地标']];
document.getElementById('legend').innerHTML=LEG.map(function(x){
  return '<span class="it"><i class="box" style="background:'+x[0]+'"></i>'+x[1]+'</span>';}).join('');
document.getElementById('deckrows').innerHTML=
  '<div class="fr"><b>上层</b><span>公路 · 宽 22.5 m<i>双向四车道 + 双侧人行道各 2.25 m</i></span></div>'+
  '<div class="fr"><b>下层</b><span>铁路 · 双线宽 14.5 m<i>轨距中心间距 4.1 m · 净空 6.125 m</i></span></div>'+
  '<div class="fr"><b>主桁</b><span>平弦菱形（米字形）<i>桁高 16 m · 桁距 10 m · 8 个 16 m 大节间</i></span></div>'+
  '<div class="fr"><b>基础</b><span>大型管柱钻孔法<i>Φ1.55 m 管柱 · 世界首次用于深水基础</i></span></div>';
document.getElementById('srcbox').innerHTML=
  '<em>真实数据</em>：Copernicus DEM 30 m（'+M.dem_min+'–'+M.dem_max+' m）+ ESA WorldCover 10 m。'+
  '江面按 DEM &lt;18 m 低地判定（与 WorldCover 永久水体一致），实测跨江 1,150 m，'+
  '与公开「龟蛇锁江江面 1,126 m」吻合；桥轴线按江中心线拟合 + 垂直方向定位。<br>'+
  '<em>公开参数</em>：1957-10-15 通车 · 全桥 1,670.4 m · 正桥 1,155.5 m（3 联 9 孔 ×128 m）· '+
  '8 水中墩 · 2 座桥头堡（7 层 35 m）· 汉阳引桥 303.45 m / 武昌引桥 211.45 m · 公铁两用。<br>'+
  '<span class="warn">注意：本轮 Overpass / OSM 全镜像不可达（504 / 406 / 超时），'+
  '周边路网、'+M.n_building+' 栋建筑与地标均为<span class="warn">示意矢量</span>，非实测 OSM，不作量测；'+
  '桥梁构件按公开设计参数程序化重建，非竣工 BIM。为便于观察，垂直放大 '+ZEX.toFixed(1)+'×、'+
  '地形压缩 '+M.terrain_squeeze+'×、桥面横向放大 '+M.wvis+'×，均为可视化夸张。</span><br>'+
  '<em>视觉增强</em>：PBR 材质 + 软阴影 + 天空穹顶/远山剪影 + 江面菲涅尔反射、流动波光与日轮高光；'
  +'「光影氛围」可切科技蓝 / 写实黄昏 / 夜景灯光，「日照方位」可调主光角度；'
  +'右上角「桥身细部」为同一场景独立机位双视口渲染。江面按江心—近岸深浅渐变、'
  +'周边建筑按离桥距离降低亮度与高度，均为表达性渲染，不作量测。<br>'+
  '<em>合规</em>：WGS84，仅本地可视化；对外发布需 GCJ-02 转换与国内合规底图 / 审图号。';
function tick(){
  var d=new Date();
  document.getElementById('clk').textContent=d.toTimeString().slice(0,8);
  document.getElementById('date').textContent=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+
    String(d.getDate()).padStart(2,'0')+'  周'+'日一二三四五六'[d.getDay()];
}
tick();setInterval(tick,1000);

/* ---------- 13.5 光影氛围：三套可切换的天光 / 雾 / 江面 / 灯带 ---------- */
var MOOD={
 tech:{amb:0xc4dcf4,ambI:1.14,hemiSky:0xbcd9f2,hemiGnd:0x172a20,hemiI:0.55,
   sun:0xfff2dc,sunI:1.06,fill:0x77b4ff,fillI:0.45,
   fog:0x0a1826,fogD:0.00042,clear:0x050b13,
   top:0x071a30,hor:0x1b4e68,bot:0x050d18,disc:0xffe6b8,haze:0.9,
   tint:0xffffff,wsky:0x2e7ba0,wsun:1.0,wave:1.0,lamps:false,skySun:1.0,
   tip:'科技蓝：冷色天光 + 软阴影 + 江面镜面波光 · 拖动旋转 / 单击构件查看属性'},
 dusk:{amb:0xffd9ad,ambI:0.90,hemiSky:0xffc98a,hemiGnd:0x3a2a1c,hemiI:0.72,
   sun:0xffb45e,sunI:1.32,fill:0x6f8fd0,fillI:0.40,
   fog:0x2a2118,fogD:0.00052,clear:0x17120e,
   top:0x243a5c,hor:0xd08a52,bot:0x2b1a12,disc:0xffd08a,haze:1.25,
   tint:0xffd9b0,wsky:0xc08a62,wsun:1.30,wave:0.95,lamps:false,skySun:1.30,
   tip:'写实黄昏：低角度暖阳 / 大气暖雾 / 江面金色反光 — 更接近真实摄影观感'},
 night:{amb:0x5b7bb0,ambI:0.54,hemiSky:0x4e78b8,hemiGnd:0x0d1424,hemiI:0.42,
   sun:0x9db8ee,sunI:0.34,fill:0x35508c,fillI:0.25,
   fog:0x050b18,fogD:0.00058,clear:0x030711,
   top:0x020610,hor:0x122c50,bot:0x02050c,disc:0xaac6ff,haze:0.6,
   tint:0x9fc4e8,wsky:0x1b3b68,wsun:0.62,wave:0.6,lamps:true,skySun:0.22,
   tip:'夜景灯光：桥面路灯 / 桥头堡与城市窗光点亮，江面倒映冷色天光'}
};
var moodNow='tech';
function setMood(k){
  if(!MOOD[k])return;var m=MOOD[k];moodNow=k;
  amb.color.setHex(m.amb);amb.intensity=m.ambI;
  hemi.color.setHex(m.hemiSky);hemi.groundColor.setHex(m.hemiGnd);hemi.intensity=m.hemiI;
  sun.color.setHex(m.sun);sun.intensity=m.sunI;
  fill.color.setHex(m.fill);fill.intensity=m.fillI;
  scene.fog.color.setHex(m.fog);scene.fog.density=m.fogD;
  skyU.uTop.value.setHex(m.top);skyU.uHor.value.setHex(m.hor);skyU.uBot.value.setHex(m.bot);
  skyU.uSunCol.value.setHex(m.disc);skyU.uHaze.value=m.haze;skyU.uSunI.value=m.skySun;
  waterU.uTint.value.setHex(m.tint);waterU.uSky.value.setHex(m.wsky);
  waterU.uSunCol.value.setHex(m.disc);waterU.uFogCol.value.setHex(m.fog);
  waterU.uFogD.value=m.fogD;waterU.uSunI.value=m.wsun;waterU.uWave.value=m.wave;
  renderer.setClearColor(m.clear,1);
  /* 无头浏览器 innerHeight 常比截图窗口矮，根背景同步跟随清屏色才不会在底边露冷色带 */
  var bg='#'+('000000'+m.clear.toString(16)).slice(-6);
  document.documentElement.style.background=bg;
  document.body.style.background=bg;
  document.getElementById('app').style.background=bg;
  lampPts.visible=!!m.lamps;
  document.body.className='mood-'+k;
  [['moodTech','tech'],['moodDusk','dusk'],['moodNight','night']].forEach(function(p){
    document.getElementById(p[0]).classList.toggle('on',p[1]===k);
  });
  document.getElementById('tip').textContent=m.tip;
}
[['moodTech','tech'],['moodDusk','dusk'],['moodNight','night']].forEach(function(p){
  document.getElementById(p[0]).onclick=function(){setMood(p[1]);};
});
/* 日照方位：主光绕场景旋转，天空日轮与江面高光同步跟随 */
var sunSl=document.getElementById('sun'),sunv=document.getElementById('sunv');
function applySun(){
  var t=+sunSl.value/100,a=-Math.PI+t*2*Math.PI,R=780,H=660;
  sun.position.set(Math.sin(a)*R,H,Math.cos(a)*R);
  var dir=sun.position.clone().normalize();
  skyU.uSunDir.value.copy(dir);waterU.uSunDir.value.copy(dir);
  var deg=Math.round(t*360);
  var dt=(deg<45||deg>=315)?'偏北':deg<135?'偏东':deg<225?'偏南':'偏西';
  sunv.textContent=deg+'° · '+dt;
}
sunSl.oninput=applySun;applySun();setMood('tech');

/* ---------- 14. 渲染循环 ---------- */
var tmp=new THREE.Vector3();
function loop(){
  requestAnimationFrame(loop);
  waterU.uTime.value=performance.now()*0.001;
  labels.forEach(function(l){
    tmp.copy(l.v).project(camera);
    var vis=tmp.z<1&&tmp.z>-1&&!(bridgeLabelsHidden&&l.bridge);
    l.e.style.display=vis?'':'none';
    if(vis){l.e.style.left=(tmp.x*0.5+0.5)*innerWidth+'px';l.e.style.top=(-tmp.y*0.5+0.5)*innerHeight+'px';}
  });
  renderer.setScissorTest(false);
  renderer.setViewport(0,0,innerWidth,innerHeight);
  renderer.setClearColor(0x050b13,1);
  renderer.render(scene,camera);
  var blocked=document.getElementById('right').classList.contains('show')||
              document.getElementById('deckcard').classList.contains('show');
  if(INSET_ON&&!blocked){
    var ix=innerWidth-INSET_R-INSET_W,iy=innerHeight-INSET_T-INSET_H;
    if(ix>4&&iy>4){
      renderer.setScissorTest(true);
      renderer.setViewport(ix,iy,INSET_W,INSET_H);
      renderer.setScissor(ix,iy,INSET_W,INSET_H);
      renderer.setClearColor(0x081a2b,1);
      iCam.aspect=INSET_W/INSET_H;iCam.updateProjectionMatrix();
      /* 近距画中画里加性灯点会被 sizeAttenuation 放成一整条过曝白带，细部视口暂时关掉 */
      var lampWas=lampPts.visible;lampPts.visible=false;
      renderer.render(scene,iCam);
      lampPts.visible=lampWas;
      renderer.setScissorTest(false);
      renderer.setViewport(0,0,innerWidth,innerHeight);
    }
  }
}
loop();
window.__TDBG={scene:scene,camera:camera,st:st,applyCam:applyCam,setMode:setMode,
  setInset:setInset,iCam:iCam,insetOn:function(){return INSET_ON;},
  applyCut:function(v){cut.value=v;cut.oninput();},applySep:applySep,
  deckMesh:deckMesh,trussMesh:trussMesh,pierMesh:pierMesh,buildingMesh:buildingMesh,
  parts:BD.parts,THREE:THREE,labels:labels,SEP:function(){return SEP;},
  setMood:setMood,applySun:applySun,mood:function(){return moodNow;},
  skyU:skyU,waterU:waterU,lampPts:lampPts};
var ld=document.getElementById('loading');ld.style.opacity=0;setTimeout(function(){ld.remove();},600);
})();
</script>
</body>
</html>
'''
html = HTML.replace('__THREE__', three).replace('__DATA__', data)
outp = os.path.join(OUT, '武汉长江大桥_数字沙盘.html')
open(outp, 'w', encoding='utf-8').write(html)
print('OK ->', outp, '%.2f MB' % (os.path.getsize(outp) / 1024 / 1024))
