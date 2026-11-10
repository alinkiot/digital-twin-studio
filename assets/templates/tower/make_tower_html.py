#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 three.js + 黄鹤楼孪生数据 + 楼阁大屏 UI 拼成离线单文件 HTML"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
three = open(os.path.join(HERE, 'three.min.js'), encoding='utf-8').read().replace('</script', '<\\/script')
data = open(os.path.join(HERE, 'tower_data.json'), encoding='utf-8').read().replace('</script', '<\\/script')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>武汉黄鹤楼 · 楼阁数字孪生</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#070d16;color:#dce8f5;
  font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif;-webkit-font-smoothing:antialiased}
#app{position:relative;width:100%;height:100%}
canvas#gl{position:absolute;inset:0;display:block}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 44%,transparent 38%,rgba(2,7,14,.60) 100%)}
.scan{position:absolute;inset:0;pointer-events:none;opacity:.18;
  background:repeating-linear-gradient(0deg,transparent 0 3px,rgba(90,170,255,.05) 3px 4px)}
header{position:absolute;top:0;left:0;right:0;height:76px;display:flex;align-items:center;
  padding:0 26px;background:linear-gradient(180deg,rgba(5,13,24,.97),rgba(5,13,24,0));
  border-bottom:1px solid rgba(96,168,232,.16);pointer-events:none;z-index:6}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:34px;height:34px;border:1.5px solid #e8c26a;border-radius:8px;position:relative;
  box-shadow:0 0 18px rgba(232,194,106,.35) inset,0 0 12px rgba(232,194,106,.2)}
.logo::before,.logo::after{content:"";position:absolute;background:#e8c26a}
.logo::before{left:50%;top:6px;bottom:6px;width:1.5px;transform:translateX(-50%)}
.logo::after{top:50%;left:6px;right:6px;height:1.5px;transform:translateY(-50%)}
h1{font-size:19px;font-weight:600;letter-spacing:2px;color:#f2f7ff}
.sub{font-size:10.5px;color:#8b9cb0;letter-spacing:1.2px;margin-top:3px}
.hright{margin-left:auto;display:flex;align-items:center;gap:20px;text-align:right}
.clock{font-size:22px;font-weight:300;letter-spacing:1px;color:#f0dcb4;font-variant-numeric:tabular-nums}
.clock small{font-size:11px;color:#7e8fa2;display:block;letter-spacing:1px}
.badge{font-size:11px;padding:5px 11px;border:1px solid rgba(232,194,106,.42);border-radius:20px;
  color:#e8c26a;background:rgba(232,194,106,.07);letter-spacing:.5px}
.panel{position:absolute;z-index:5;background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);
  border-radius:10px;backdrop-filter:blur(14px);box-shadow:0 12px 40px rgba(0,0,0,.45)}
#left{top:92px;left:22px;width:278px;padding:15px 15px 13px;max-height:calc(100% - 250px);
  display:flex;flex-direction:column;overflow-y:auto;scrollbar-width:thin}
#left::-webkit-scrollbar{width:5px}#left::-webkit-scrollbar-thumb{background:#3a6a8c;border-radius:3px}
.ptitle{font-size:11.5px;color:#a8c6dd;letter-spacing:2px;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.ptitle::before{content:"";width:3px;height:12px;background:#e8c26a;border-radius:2px;box-shadow:0 0 8px #e8c26a}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.kpi{background:rgba(30,58,88,.34);border:1px solid rgba(90,150,210,.13);border-radius:7px;padding:8px 9px}
.kpi b{display:block;font-size:16px;font-weight:500;color:#f0d394;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi b i{font-size:10px;font-style:normal;color:#8b9cb0;margin-left:2px}
.kpi span{font-size:9.5px;color:#8197ac;letter-spacing:.4px}
.divider{height:1px;background:rgba(90,150,210,.15);margin:12px 0 10px;flex:none}
.layers{display:grid;gap:1px}
.ly{display:flex;align-items:center;gap:8px;font-size:11px;color:#a8c2da;padding:3px 5px;border-radius:5px;cursor:pointer}
.ly:hover{background:rgba(80,150,220,.09)}
.ly input{appearance:none;width:13px;height:13px;border:1px solid #4a7398;border-radius:3px;position:relative;cursor:pointer;flex:none}
.ly input:checked{background:#d8b45c;border-color:#d8b45c}
.ly input:checked::after{content:"";position:absolute;left:4px;top:1px;width:3px;height:7px;
  border:solid #06131f;border-width:0 2px 2px 0;transform:rotate(45deg)}
.sw{width:9px;height:9px;border-radius:2px;flex:none}
.btnrow{display:flex;gap:5px;margin-top:10px;flex:none;flex-wrap:wrap}
.btn{flex:1;min-width:0;text-align:center;font-size:10.5px;padding:7px 2px;border-radius:6px;cursor:pointer;
  border:1px solid rgba(90,160,220,.28);background:rgba(40,90,140,.16);color:#a9cbe6;transition:.18s}
.btn:hover{background:rgba(70,160,220,.3);color:#fff;border-color:#e8c26a}
.btn.on{background:rgba(216,180,92,.24);border-color:#e8c26a;color:#ffe9bd}
.src{font-size:10px;line-height:1.7;color:#8197ac;overflow:auto;max-height:96px}
.src em{font-style:normal;color:#bdd5e8}
.src .warn{color:#e8b478}
#parts{flex:none}
#plist{overflow:auto;max-height:108px;border:1px solid rgba(90,150,210,.14);border-radius:6px;
  background:rgba(10,24,42,.5)}
.pi{display:flex;align-items:center;gap:7px;font-size:10.5px;color:#9fbad2;padding:5px 8px;
  cursor:pointer;border-bottom:1px solid rgba(90,150,210,.07)}
.pi:hover{background:rgba(216,180,92,.16);color:#fff4dc}
.pi .tag{font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(232,194,106,.16);color:#f0d394;flex:none}
.pi .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pi .st{margin-left:auto;color:#6a8ba6;font-size:9.5px;flex:none}
#right{top:92px;right:22px;width:280px;padding:16px;display:none;max-height:calc(100% - 250px);overflow:auto}
#right.show{display:block}
#floorcard{top:92px;right:22px;width:252px;padding:14px;display:none;max-height:calc(100% - 250px);overflow:auto}
#floorcard.show{display:block}
.fr{display:flex;justify-content:space-between;gap:8px;font-size:10.5px;padding:6px 0;
  border-bottom:1px dashed rgba(90,150,210,.14);color:#cde0f0}
.fr b{color:#f0d394;font-weight:500;flex:none}
.fr span{color:#8ca7bf;text-align:right}
.fr i{font-style:normal;color:#6d89a2;font-size:9.5px;display:block}
.rname{font-size:15px;color:#f5f8ff;font-weight:600;margin:2px 0 3px;letter-spacing:.4px;line-height:1.4}
.rtype{font-size:10.5px;color:#e8c26a;margin-bottom:11px;letter-spacing:1px}
.kv{display:flex;justify-content:space-between;gap:10px;font-size:11px;padding:5px 0;
  border-bottom:1px dashed rgba(90,150,210,.14)}
.kv k{color:#839cb2;flex:none}
.kv v{color:#dce9f6;text-align:right;word-break:break-all}
.close{position:absolute;right:12px;top:12px;cursor:pointer;color:#7f96ad;font-size:16px;line-height:1}
.close:hover{color:#fff}
#bottom{position:absolute;left:22px;right:22px;bottom:20px;z-index:5;display:flex;align-items:flex-end;gap:12px;pointer-events:none}
#bottom>*{pointer-events:auto}
.legend{background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:10px 13px;backdrop-filter:blur(14px);font-size:10px;color:#9aafc4;max-width:410px}
.legend .row{display:flex;gap:11px;flex-wrap:wrap;align-items:center}
.legend .it{display:flex;align-items:center;gap:5px;white-space:nowrap}
.legend .box{width:10px;height:10px;border-radius:2px}
.tools{background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:10px 13px;backdrop-filter:blur(14px);min-width:238px}
.tools label{font-size:10px;color:#9ab5cc;display:flex;justify-content:space-between;margin-bottom:6px}
.tools label b{color:#f0d394;font-weight:500}
input[type=range]{width:100%;height:4px;appearance:none;background:linear-gradient(90deg,#d8b45c,#2a5878);
  border-radius:3px;outline:none;cursor:pointer}
input[type=range]::-webkit-slider-thumb{appearance:none;width:13px;height:13px;border-radius:50%;
  background:#ffe9bd;box-shadow:0 0 8px #e8c26a;cursor:pointer}
.search{margin-left:auto;display:flex;gap:6px;background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);
  border-radius:9px;padding:6px 8px;backdrop-filter:blur(14px)}
.search input{background:transparent;border:0;outline:0;color:#dceaf7;font-size:11px;width:130px}
.search input::placeholder{color:#61809a}
.search button{background:rgba(216,180,92,.2);border:1px solid rgba(232,194,106,.4);color:#ffe0a4;
  border-radius:5px;padding:4px 10px;font-size:11px;cursor:pointer}
#labels{position:absolute;inset:0;pointer-events:none;z-index:4;overflow:hidden}
.lab{position:absolute;transform:translate(-50%,-100%);font-size:10.5px;color:#e2f0ff;white-space:nowrap;
  text-shadow:0 1px 5px #000,0 0 10px rgba(0,0,0,.9);letter-spacing:.4px;opacity:.94}
.lab::after{content:"";position:absolute;left:50%;top:100%;width:1px;height:9px;
  background:linear-gradient(rgba(220,220,200,.8),transparent)}
.lab.hot{color:#ffe1a1;font-weight:600;font-size:12px}
.lab.floor{color:#ffd98a;font-size:10.5px;opacity:.95}
#north{position:absolute;right:26px;bottom:126px;z-index:5;width:50px;height:50px;border-radius:50%;
  border:1px solid rgba(90,150,210,.28);background:rgba(8,18,32,.7);text-align:center;pointer-events:none}
#north .ar{font-size:19px;color:#f0d394;line-height:29px}
#north .tx{font-size:9px;color:#8ba0b5;letter-spacing:1px}
#scale{position:absolute;left:24px;bottom:100px;z-index:5;font-size:10px;color:#94abc0;pointer-events:none}
#scale .bar{height:5px;border:1px solid #94abc0;border-top:0;width:88px;margin-bottom:3px}
#tip{position:absolute;left:50%;top:84px;transform:translateX(-50%);z-index:7;font-size:11px;
  color:#a9c4da;background:rgba(8,18,32,.84);border:1px solid rgba(90,150,210,.2);
  padding:6px 14px;border-radius:16px;letter-spacing:.4px;pointer-events:none}
#loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:20;
  background:#070d16;color:#f0d394;font-size:13px;letter-spacing:3px;transition:opacity .5s}
</style>
</head>
<body>
<div id="app">
  <canvas id="gl"></canvas><div class="vig"></div><div class="scan"></div>
  <div id="labels"></div>
  <header>
    <div class="brand"><div class="logo"></div>
      <div><h1>武汉黄鹤楼 · 楼阁数字孪生</h1>
      <div class="sub">YELLOW CRANE TOWER DIGITAL TWIN &nbsp;·&nbsp; COPERNICUS DEM + 公开设计参数分层重建</div></div>
    </div>
    <div class="hright"><div class="badge">LOD2 · 逐层可点选</div>
      <div class="clock"><span id="clk">--:--:--</span><small id="date">WGS84 / 1 单位 = 4 m</small></div></div>
  </header>
  <div class="panel" id="left">
    <div class="ptitle">楼阁指标</div><div class="kpis" id="kpis"></div>
    <div class="divider"></div>
    <div class="ptitle">图层</div><div class="layers" id="layers"></div>
    <div class="btnrow" id="modes">
      <div class="btn on" id="btnAll">主视</div>
      <div class="btn" id="btnFloors">分层</div>
      <div class="btn" id="btnSkel">骨架</div>
      <div class="btn" id="btnTop">俯视</div>
      <div class="btn" id="btnWide">全景</div>
    </div>
    <div class="divider"></div>
    <div class="ptitle">构件 / 楼层清单 <span style="margin-left:auto;color:#6f8aa6;font-size:9.5px" id="pn"></span></div>
    <div id="plist"></div>
    <div class="divider"></div>
    <div class="ptitle">数据来源与限制</div>
    <div class="src" id="srcbox"></div>
  </div>
  <div class="panel" id="floorcard"><div class="ptitle">逐层剖面 · 五层</div><div id="floorrows"></div>
    <div style="font-size:10px;color:#e8b478;line-height:1.7;margin-top:10px">
      每层为独立构件：可单击查看属性，或用下方「楼层剖切」逐层显示。</div></div>
  <div class="panel" id="right"><div class="close" id="rclose">×</div><div id="rbody"></div></div>
  <div id="bottom">
    <div class="legend"><div class="row" id="legend"></div></div>
    <div class="tools">
      <label>楼层剖切 <b id="cutv">全部 5 层</b></label>
      <input type="range" id="cut" min="0" max="6" step="1" value="6">
      <label style="margin-top:9px">分层展开间距 <b id="sepv">0 m</b></label>
      <input type="range" id="sep" min="0" max="12" step="1" value="0">
    </div>
    <div class="search"><input id="q" placeholder="搜索楼层 / 构件 / 地名"><button id="go">定位</button></div>
  </div>
  <div id="north"><div class="ar">↑</div><div class="tx">N</div></div>
  <div id="scale"><div class="bar"></div><span>约 180 m</span></div>
  <div id="tip">拖动旋转 · 滚轮缩放 · 右键平移 · 单击楼层 / 构件 / 建筑查看属性</div>
  <div id="loading">正在构建黄鹤楼逐层模型 …</div>
</div>
<script>__THREE__</script>
<script>window.__TWIN__=__DATA__;</script>
<script>__JS__</script>
</body>
</html>
'''

JS = r'''
(function(){
'use strict';
if(!window.THREE){document.getElementById('loading').textContent='three.js 未加载';return;}
THREE.ColorManagement && (THREE.ColorManagement.enabled=false);
var D=window.__TWIN__, M=D.meta, TW=D.tower, PT=D.parts;
var W=M.w,H=M.h,ZEX=3.2,BEX=0.60,TVIS=1.38,LAKEZ=0.4;
var HALF_W=W/2,HALF_H=H/2,TX=TW.x,TY=TW.y,BZ=TW.basez;
var S=M.scale;
function V(x,y,h){return new THREE.Vector3(x-HALF_W,(h||0)*ZEX,-(y-HALF_H));}
/* 楼阁局部坐标：横向 / 纵向按 TVIS 放大（可视化夸张，标注于说明） */
function T(x,y,hm){return V(TX+(x-TX)*TVIS,TY+(y-TY)*TVIS,BZ+hm/S*TVIS);}
var cv=document.getElementById('gl');
var renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));
renderer.setSize(innerWidth,innerHeight);
renderer.setClearColor(0x070d16,1);
var scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x070d16,0.00048);
var camera=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,1,9000);
scene.add(new THREE.AmbientLight(0xc0d6ee,0.92));
var sun=new THREE.DirectionalLight(0xffe9c4,1.30);sun.position.set(-330,620,300);scene.add(sun);
var fill=new THREE.DirectionalLight(0x77aaff,0.42);fill.position.set(420,260,-380);scene.add(fill);
var warm=new THREE.PointLight(0xffd08a,0.55,900);warm.position.set(TX-HALF_W,100,-(TY-HALF_H));scene.add(warm);

/* ---------- 1. 真实 DEM 地形 ---------- */
var TT=D.terrain,nx=TT.nx,ny=TT.ny,tp=[],tc=[],ti=[];
var LC={10:[0.17,0.35,0.24],20:[0.22,0.38,0.26],30:[0.27,0.40,0.29],40:[0.40,0.42,0.30],
        50:[0.31,0.37,0.44],60:[0.40,0.40,0.38],80:[0.07,0.23,0.35],90:[0.30,0.44,0.38]};
for(var r=0;r<ny;r++)for(var c=0;c<nx;c++){
  var i=r*nx+c,px=c/(nx-1)*W,py=r/(ny-1)*H;
  var v=V(px,py,TT.lc[i]===80?LAKEZ:TT.z[i]);tp.push(v.x,v.y,v.z);
  var col=LC[TT.lc[i]]||LC[50],sh=0.78+Math.min(TT.z[i],20)/20*0.34;
  tc.push(col[0]*sh,col[1]*sh,col[2]*sh);
}
for(var r=0;r<ny-1;r++)for(var c=0;c<nx-1;c++){
  var a=r*nx+c,b=a+1,d=a+nx,e=d+1;ti.push(a,d,b,b,d,e);
}
var tg=new THREE.BufferGeometry();
tg.setAttribute('position',new THREE.Float32BufferAttribute(tp,3));
tg.setAttribute('color',new THREE.Float32BufferAttribute(tc,3));tg.setIndex(ti);tg.computeVertexNormals();
var terrainMesh=new THREE.Mesh(tg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
scene.add(terrainMesh);
function terrainZ(px,py){
  var fx=Math.max(0,Math.min(nx-1.001,px/W*(nx-1))),fy=Math.max(0,Math.min(ny-1.001,py/H*(ny-1)));
  var c0=Math.floor(fx),r0=Math.floor(fy),tx=fx-c0,ty=fy-r0,i00=r0*nx+c0;
  function z(i){return TT.lc[i]===80?LAKEZ:TT.z[i];}
  return (z(i00)*(1-tx)+z(i00+1)*tx)*(1-ty)+(z(i00+nx)*(1-tx)+z(i00+nx+1)*tx)*ty;
}
/* ---------- 2. 江面 ---------- */
var G=D.waterGrid,gnx=G.nx,gny=G.ny,wp=[],wi=[];
for(var r=0;r<gny;r++)for(var c=0;c<gnx;c++){
  if(!G.m[r*gnx+c])continue;
  var x0=c/(gnx-1)*W,x1=(c+1)/(gnx-1)*W,y0=r/(gny-1)*H,y1=(r+1)/(gny-1)*H;
  var base=wp.length/3;
  var a=V(x0,y0,LAKEZ+0.06),b=V(x1,y0,LAKEZ+0.06),
      d=V(x1,y1,LAKEZ+0.06),e=V(x0,y1,LAKEZ+0.06);
  wp.push(a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,e.x,e.y,e.z);
  wi.push(base,base+1,base+2,base,base+2,base+3);
}
var wg=new THREE.BufferGeometry();
wg.setAttribute('position',new THREE.Float32BufferAttribute(wp,3));wg.setIndex(wi);wg.computeVertexNormals();
var waterMesh=new THREE.Mesh(wg,new THREE.MeshPhongMaterial({color:0x1a6389,shininess:95,
  specular:0x7adcff,transparent:true,opacity:.9,side:THREE.DoubleSide}));
scene.add(waterMesh);
/* ---------- 3. 路网 ---------- */
function ribbon(lines,widthFn,hFn,opacity){
  var vp=[],vc=[],vi=[],k=0;
  lines.forEach(function(o){
    var pts=o.p,wd=widthFn(o),col=o.col;
    for(var i=0;i<pts.length-1;i++){
      var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
      if(L<0.05)continue;
      var ox=-dy/L*wd/2,oy=dx/L*wd/2;
      var za=Math.max(hFn(a[0],a[1]),terrainZ(a[0],a[1])+0.08),
          zb=Math.max(hFn(b[0],b[1]),terrainZ(b[0],b[1])+0.08);
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
  g.setAttribute('color',new THREE.Float32BufferAttribute(vc,3));g.setIndex(vi);g.computeVertexNormals();
  var m=new THREE.Mesh(g,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide,
    transparent:opacity<1,opacity:opacity}));m.renderOrder=2;return m;
}
var RC={7:[0.62,0.55,0.38],6:[0.50,0.57,0.64],5:[0.43,0.50,0.58],4:[0.37,0.44,0.51],
        3:[0.33,0.46,0.42],2:[0.30,0.37,0.44],1:[0.28,0.35,0.40]};
D.roads.forEach(function(o){o.col=RC[o.k]||RC[2];o.n=o.n||'';});
var roadOnly=D.roads.filter(function(o){return o.k!==7;});   // 大桥单独按桥面标高建模
var roadMesh=ribbon(roadOnly,function(o){return {7:6.2,6:5,5:4,4:3,3:2,2:1.6,1:1.2}[o.k]||2;},
  function(x,y){return terrainZ(x,y)+0.09;},1);
scene.add(roadMesh);
/* ---------- 4. 周边建筑（示意矢量） ---------- */
var bp=[],bc=[],bi=[],hitB=[],fB=0;
var BC=[[0.30,0.44,0.57],[0.36,0.51,0.63],[0.43,0.58,0.69],[0.51,0.64,0.73],[0.61,0.66,0.62]];
var GOLD=[0.93,0.72,0.35];
function triB(a,b,c,col){var n=bp.length/3;
  bp.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
  for(var q=0;q<3;q++)bc.push(col[0],col[1],col[2]);bi.push(n,n+1,n+2);fB++;}
D.buildings.forEach(function(b,idx){
  var poly=b.p.slice();if(poly.length<3)return;
  var base=-99;for(var i=0;i<poly.length;i++)base=Math.max(base,terrainZ(poly[i][0],poly[i][1]));
  base-=0.08;
  var h=Math.max(b.h*BEX,0.55),col=b.n?GOLD:BC[Math.min(4,Math.floor(h/3.5))];
  var top=[],bot=[];
  for(var i=0;i<poly.length;i++){top.push(V(poly[i][0],poly[i][1],base+h));bot.push(V(poly[i][0],poly[i][1],base));}
  for(var i=0;i<poly.length;i++){var j=(i+1)%poly.length,sh=0.70+0.28*Math.abs(Math.cos(i*1.1));
    var sc=[col[0]*sh,col[1]*sh,col[2]*sh];triB(bot[i],bot[j],top[j],sc);triB(bot[i],top[j],top[i],sc);}
  var contour=poly.map(function(p){return new THREE.Vector2(p[0],p[1]);});
  var faces=[];try{faces=THREE.ShapeUtils.triangulateShape(contour,[]);}catch(e){faces=[];}
  if(!faces.length){for(var i=1;i<poly.length-1;i++)faces.push([0,i,i+1]);}
  for(var i=0;i<faces.length;i++){var f=faces[i];
    triB(top[f[0]],top[f[1]],top[f[2]],[col[0]*1.08,col[1]*1.08,col[2]*1.08]);}
  hitB.push({s:hitB.length?hitB[hitB.length-1].e:0,e:fB,i:idx});
});
var bg=new THREE.BufferGeometry();
bg.setAttribute('position',new THREE.Float32BufferAttribute(bp,3));
bg.setAttribute('color',new THREE.Float32BufferAttribute(bc,3));bg.setIndex(bi);bg.computeVertexNormals();
var buildingMesh=new THREE.Mesh(bg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
buildingMesh.renderOrder=4;scene.add(buildingMesh);

/* ---------- 5. 几何构造器（楼阁构件） ---------- */
function GB(){this.p=[];this.c=[];this.i=[];this.f=0;}
GB.prototype.tri=function(a,b,c,col){var n=this.p.length/3;
  this.p.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
  for(var q=0;q<3;q++)this.c.push(col[0],col[1],col[2]);
  this.i.push(n,n+1,n+2);this.f++;};
GB.prototype.quad=function(a,b,c,d,col){this.tri(a,b,c,col);this.tri(a,c,d,col);};
GB.prototype.mesh=function(pid){var g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(this.p,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(this.c,3));g.setIndex(this.i);g.computeVertexNormals();
  var m=new THREE.Mesh(g,new THREE.MeshPhongMaterial({vertexColors:true,side:THREE.DoubleSide,
    shininess:28,specular:0x332a18}));
  m.renderOrder=6;m.userData.pid=pid;return m;};
/* 切角方形（四边套八边形，"四面八方"） */
function octagon(edge){
  var a=edge/2/S,t=a*0.25;
  return [[-a+t,-a],[a-t,-a],[a,-a+t],[a,a-t],[a-t,a],[-a+t,a],[-a,a-t],[-a,-a+t]];
}
function ring(edge,cx,cy,hm){return octagon(edge).map(function(q){return T(cx+q[0],cy+q[1],hm);});}
var RED=[0.66,0.20,0.15],REDD=[0.47,0.13,0.11],WALL=[0.86,0.80,0.66],
    GLASS=[0.16,0.24,0.30],GOLDW=[0.95,0.74,0.30],GOLDD=[0.70,0.49,0.17],
    RAIL=[0.72,0.23,0.17],STONE=[0.72,0.74,0.72],STONED=[0.53,0.56,0.56],
    DARK=[0.20,0.16,0.12];
/* 八棱柱（柱 / 台基侧墙） */
function prism(g,bot,top,col,shade){
  for(var i=0;i<bot.length;i++){
    var j=(i+1)%bot.length,sh=shade?0.72+0.26*Math.abs(Math.cos(i*0.9)):1;
    g.quad(bot[i],bot[j],top[j],top[i],[col[0]*sh,col[1]*sh,col[2]*sh]);
  }
}
function cap(g,pts,col){for(var i=1;i<pts.length-1;i++)g.tri(pts[0],pts[i],pts[i+1],col);}
/* 方形柱 */
function column(g,x,y,hm0,hm1,w,col){
  var w2=w/2/S,p=[[x-w2,y-w2],[x+w2,y-w2],[x+w2,y+w2],[x-w2,y+w2]];
  var bot=p.map(function(q){return T(q[0],q[1],hm0);}),top=p.map(function(q){return T(q[0],q[1],hm1);});
  prism(g,bot,top,col,true);cap(g,top,[col[0]*1.1,col[1]*1.1,col[2]*1.1]);
}
/* 每层：台明 + 柱网 + 门窗格栅 + 平座栏杆 + 腰檐（四角起翘） */
function buildFloor(f,pid){
  var g=new GB(),e=f.edge,z0=f.z0,z1=f.z1,ev=f.eave;
  /* 台明 / 平座：外扩 0.55×出檐 */
  var out=octagon(e+ev*1.1),inn=octagon(e);
  var b0=ring(e+ev*1.1,TX,TY,z0-0.55),b1=ring(e+ev*1.1,TX,TY,z0+0.25);
  prism(g,b0,b1,STONE,true);cap(g,b1,STONE);
  /* 12 根檐柱：8 角柱 + 4 条长边中点 */
  var cor=octagon(e-1.6);
  cor.forEach(function(q){column(g,TX+q[0],TY+q[1],z0+0.25,z1-0.35,0.72,RED);});
  var a=(e-1.6)/2/S;
  [[0,-a],[a,0],[0,a],[-a,0]].forEach(function(q){
    column(g,TX+q[0],TY+q[1],z0+0.25,z1-0.35,0.62,REDD);});
  /* 墙体 + 门窗格栅（每面） */
  for(var i=0;i<8;i++){
    var q1=inn[i],q2=inn[(i+1)%8];
    var dx=q2[0]-q1[0],dy=q2[1]-q1[1],L=Math.hypot(dx,dy);
    if(L<1.0)continue;
    var ux=dx/L,uy=dy/L,nx=-uy,ny=ux;
    var inset=0.55/S;
    var A=[q1[0]+nx*inset,q1[1]+ny*inset],B=[q2[0]+nx*inset,q2[1]+ny*inset];
    var zA=z0+0.95,zB=z1-0.62;
    var p1=T(TX+A[0],TY+A[1],zA),p2=T(TX+B[0],TY+B[1],zA),
        p3=T(TX+B[0],TY+B[1],zB),p4=T(TX+A[0],TY+A[1],zB);
    g.quad(p1,p2,p3,p4,WALL);
    /* 竖向格栅 */
    var n=6;
    for(var k=1;k<n;k++){
      var t=k/n,xx=A[0]+(B[0]-A[0])*t,yy=A[1]+(B[1]-A[1])*t;
      var w=0.10/S;
      var c1=T(TX+xx-ux*w,TY+yy-uy*w,zA+0.25),c2=T(TX+xx+ux*w,TY+yy+uy*w,zA+0.25),
          c3=T(TX+xx+ux*w,TY+yy+uy*w,zB-0.25),c4=T(TX+xx-ux*w,TY+yy-uy*w,zB-0.25);
      g.quad(c1,c2,c3,c4,GLASS);
    }
    /* 横楣 */
    var m1=T(TX+A[0],TY+A[1],zB-0.45),m2=T(TX+B[0],TY+B[1],zB-0.45),
        m3=T(TX+B[0],TY+B[1],zB-0.12),m4=T(TX+A[0],TY+A[1],zB-0.12);
    g.quad(m1,m2,m3,m4,REDD);
  }
  /* 平座栏杆：外沿一圈细柱 + 上下横带 */
  var rail=octagon(e+ev*0.92);
  for(var i=0;i<8;i++){
    var q1=rail[i],q2=rail[(i+1)%8];
    var lo1=T(TX+q1[0],TY+q1[1],z0+0.3),lo2=T(TX+q2[0],TY+q2[1],z0+0.3),
        hi1=T(TX+q1[0],TY+q1[1],z0+1.55),hi2=T(TX+q2[0],TY+q2[1],z0+1.55);
    g.quad(lo1,lo2,hi2,hi1,[RAIL[0]*0.85,RAIL[1]*0.85,RAIL[2]*0.85]);
    var seg=Math.max(2,Math.round(Math.hypot(q2[0]-q1[0],q2[1]-q1[1])/1.3));
    for(var k=0;k<=seg;k++){
      var t=k/seg,x=q1[0]+(q2[0]-q1[0])*t,y=q1[1]+(q2[1]-q1[1])*t;
      var c1=T(TX+x-0.09,TY+y-0.09,z0+0.35),c2=T(TX+x+0.09,TY+y+0.09,z0+0.35),
          c3=T(TX+x+0.09,TY+y+0.09,z0+1.5),c4=T(TX+x-0.09,TY+y-0.09,z0+1.5);
      g.quad(c1,c2,c3,c4,RAIL);
    }
  }
  /* 腰檐：内圈高、外圈低，四角起翘 */
  var inner=octagon(e+0.6),outer=octagon(e+ev*2);
  for(var i=0;i<8;i++){
    var j=(i+1)%8;
    var iA=T(TX+inner[i][0],TY+inner[i][1],z1+2.0),
        iB=T(TX+inner[j][0],TY+inner[j][1],z1+2.0),
        oA=T(TX+outer[i][0],TY+outer[i][1],z1+0.15+(i%2?1.45:0.30)),
        oB=T(TX+outer[j][0],TY+outer[j][1],z1+0.15+(j%2?1.45:0.30));
    g.quad(iA,iB,oB,oA,i%2?GOLDD:GOLDW);
    /* 檐口厚度 */
    var oA2=T(TX+outer[i][0],TY+outer[i][1],z1-0.25+(i%2?1.45:0.30)),
        oB2=T(TX+outer[j][0],TY+outer[j][1],z1-0.25+(j%2?1.45:0.30));
    g.quad(oA,oB,oB2,oA2,DARK);
  }
  /* 檐下斗拱（简化：内圈与柱间的一圈深色带） */
  var arch=octagon(e+0.6);
  for(var i=0;i<8;i++){
    var q1=arch[i],q2=arch[(i+1)%8];
    var A=T(TX+q1[0],TY+q1[1],z1-0.45),B=T(TX+q2[0],TY+q2[1],z1-0.45),
        Cc=T(TX+q2[0],TY+q2[1],z1+0.15),Dd=T(TX+q1[0],TY+q1[1],z1+0.15);
    g.quad(A,B,Cc,Dd,REDD);
  }
  return g.mesh(pid);
}
/* 台基：两级须弥座 + 正面台阶 */
function buildBase(pid){
  var g=new GB(),e=TW.floors[0].edge+5.0;
  var a=ring(e+3,TX,TY,-TW.base_m*0.55),b=ring(e+3,TX,TY,0);
  prism(g,a,b,STONED,true);cap(g,b,STONE);
  var c=ring(e,TX,TY,0),d=ring(e,TX,TY,TW.base_m);
  prism(g,c,d,STONE,true);cap(g,d,STONE);
  /* 南面台阶 */
  var y0=TY-(e+3)/2/S,sw=7/S;
  for(var k=0;k<6;k++){
    var yy=y0-k*0.42/S,zz=-TW.base_m*0.55+k*0.09;
    var s1=T(TX-sw/2,yy,zz),s2=T(TX+sw/2,yy,zz),
        s3=T(TX+sw/2,yy-0.42/S,zz),s4=T(TX-sw/2,yy-0.42/S,zz);
    g.quad(s1,s2,s3,s4,[0.80,0.81,0.79]);
  }
  return g.mesh(pid);
}
/* 攒尖顶：四/八坡到宝顶 + 垂脊 + 葫芦 */
function buildRoof(pid){
  var g=new GB(),f=TW.floors[4],z1=TW.roof_base,edge=f.edge+f.eave*1.4;
  var outer=octagon(edge),inner=octagon(edge*0.24);
  var apex=T(TX,TY,z1+TW.roof_m);
  for(var i=0;i<8;i++){
    var j=(i+1)%8;
    var oA=T(TX+outer[i][0],TY+outer[i][1],z1+(i%2?1.5:0.2)),
        oB=T(TX+outer[j][0],TY+outer[j][1],z1+(j%2?1.5:0.2));
    g.tri(oA,oB,apex,i%2?GOLDD:GOLDW);
    /* 檐口 */
    var oA2=T(TX+outer[i][0],TY+outer[i][1],z1-0.3+(i%2?1.5:0.2)),
        oB2=T(TX+outer[j][0],TY+outer[j][1],z1-0.3+(j%2?1.5:0.2));
    g.quad(oA,oB,oB2,oA2,DARK);
    /* 垂脊 */
    var rA=T(TX+outer[i][0]*1.005,TY+outer[i][1]*1.005,z1+(i%2?1.5:0.2)+0.18),
        rB=T(TX+outer[i][0]*0.985,TY+outer[i][1]*0.985,z1+(i%2?1.5:0.2)+0.18);
    g.tri(rA,rB,apex,[0.99,0.85,0.46]);
  }
  /* 宝顶：三段葫芦 */
  var zz=z1+TW.roof_m;
  var seg=[[zz,zz+0.9,0.85],[zz+0.9,zz+2.1,1.15],[zz+2.1,zz+TW.finial_m,0.35]];
  seg.forEach(function(s,k){
    var r0=s[2]/S,r1=k===2?0.12/S:(k===0?s[2]*1.15/S:s[2]*0.55/S);
    var bot=[],top=[],N=10;
    for(var i=0;i<N;i++){
      var ang=i/N*Math.PI*2;
      bot.push(T(TX+Math.cos(ang)*r0,TY+Math.sin(ang)*r0,s[0]));
      top.push(T(TX+Math.cos(ang)*r1,TY+Math.sin(ang)*r1,s[1]));
    }
    prism(g,bot,top,[1.0,0.82,0.38],true);
  });
  return g.mesh(pid);
}
/* 长江大桥：桥面 + 桁架 + 桥头堡 */
function buildBridge(pid){
  var g=new GB(),pts=D.roads[0].p,DECK=9.2;
  for(var i=0;i<pts.length-1;i++){
    var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
    if(L<0.1)continue;
    var ox=-dy/L*3.1,oy=dx/L*3.1;
    var A=V(a[0]+ox,a[1]+oy,DECK),B=V(a[0]-ox,a[1]-oy,DECK),
        C=V(b[0]-ox,b[1]-oy,DECK),Dd=V(b[0]+ox,b[1]+oy,DECK);
    g.quad(A,B,C,Dd,[0.52,0.58,0.62]);
    var A2=V(a[0]+ox,a[1]+oy,DECK-0.55),B2=V(a[0]-ox,a[1]-oy,DECK-0.55),
        C2=V(b[0]-ox,b[1]-oy,DECK-0.55),D2=V(b[0]+ox,b[1]+oy,DECK-0.55);
    g.quad(A,Dd,D2,A2,[0.36,0.42,0.47]);g.quad(B,B2,C2,C,[0.36,0.42,0.47]);
    /* 桁架斜杆 */
    var n=Math.max(2,Math.round(L/7));
    for(var k=0;k<n;k++){
      var t0=k/n,t1=(k+1)/n;
      var q0=[a[0]+(b[0]-a[0])*t0,a[1]+(b[1]-a[1])*t0],
          q1=[a[0]+(b[0]-a[0])*t1,a[1]+(b[1]-a[1])*t1];
      var u=V(q0[0]+ox*0.9,q0[1]+oy*0.9,DECK+0.1),v=V(q1[0]+ox*0.9,q1[1]+oy*0.9,DECK+2.6);
      var u2=V(q0[0]+ox*0.9+0.22,q0[1]+oy*0.9,DECK+0.1),
          v2=V(q1[0]+ox*0.9+0.22,q1[1]+oy*0.9,DECK+2.6);
      g.quad(u,v,v2,u2,[0.42,0.50,0.56]);
    }
  }
  /* 两座桥头堡 */
  [pts[0],pts[pts.length-1]].forEach(function(q){
    var w=2.4,p=[[q[0]-w,q[1]-w],[q[0]+w,q[1]-w],[q[0]+w,q[1]+w],[q[0]-w,q[1]+w]];
    var bot=p.map(function(o){return V(o[0],o[1],DECK-1);}),
        top=p.map(function(o){return V(o[0],o[1],DECK+8.5);});
    prism(g,bot,top,[0.74,0.68,0.55],true);cap(g,top,[0.86,0.76,0.55]);
  });
  return g.mesh(pid);
}
var towerMeshes=[],floorMeshes=[],pidFloor=[];
var pidBase=findPid('台基'),pidRoof=findPid('攒尖'),pidBal=findPid('平座'),pidBridge=findPid('桥面');
function findPid(s){for(var i=0;i<PT.length;i++)if(PT[i].n.indexOf(s)>=0)return i;return -1;}
var baseMesh=buildBase(pidBase);scene.add(baseMesh);towerMeshes.push(baseMesh);
TW.floors.forEach(function(f,i){
  var pid=findPid('第'+'一二三四五'[i]+'层');
  var m=buildFloor(f,pid);scene.add(m);towerMeshes.push(m);floorMeshes.push(m);pidFloor.push(pid);
});
var roofMesh=buildRoof(pidRoof);scene.add(roofMesh);towerMeshes.push(roofMesh);
var bridgeMesh=buildBridge(pidBridge);scene.add(bridgeMesh);
/* ---------- 6. 沙盘底座 ---------- */
var baseG=new THREE.BoxGeometry(W+18,10,H+18);
var baseM=new THREE.Mesh(baseG,new THREE.MeshLambertMaterial({color:0x0e1c2c}));
baseM.position.set(0,-5.7,0);scene.add(baseM);
var edge=new THREE.LineSegments(new THREE.EdgesGeometry(baseG),
  new THREE.LineBasicMaterial({color:0x4b7f9e}));edge.position.copy(baseM.position);scene.add(edge);
/* ---------- 7. 标注 ---------- */
var labBox=document.getElementById('labels'),labels=[];
function addLabel(n,p,z,cls,fl){
  var e=document.createElement('div');e.className='lab'+(cls?' '+cls:'');e.textContent=n;labBox.appendChild(e);
  labels.push({e:e,v:V(p[0],p[1],z),fl:fl===undefined?-1:fl,geo:false});
}
D.poi.forEach(function(p){addLabel(p.n,p.p,p.z,p.hot?'hot':'',-1);});
/* 楼层信息改用右侧「逐层剖面」卡片，避免 3D 浮动标签遮挡模型 */
document.getElementById('floorrows').innerHTML=TW.floors.map(function(f,i){
  return '<div class="fr"><b>第'+'一二三四五'[i]+'层</b><span>'+f.h+' m / '+f.edge+' m 见方'+
    '<i>'+f.name.split(' · ')[1]+'</i></span></div>';}).join('');
/* ---------- 8. 相机 / 交互 ---------- */
var st={th:-0.52,ph:0.30,dist:138,tx:TX-HALF_W,ty:(BZ+TW.total_m/S*TVIS)*ZEX*0.62,tz:-(TY-HALF_H)};
function applyCam(){
  camera.position.set(st.tx+st.dist*Math.cos(st.ph)*Math.sin(st.th),
    st.ty+st.dist*Math.sin(st.ph),st.tz+st.dist*Math.cos(st.ph)*Math.cos(st.th));
  camera.lookAt(st.tx,st.ty,st.tz);
}
applyCam();
var drag=null;
cv.addEventListener('pointerdown',function(e){drag={x:e.clientX,y:e.clientY,b:e.button};
  try{cv.setPointerCapture(e.pointerId);}catch(err){}});
cv.addEventListener('pointerup',function(e){
  if(drag&&Math.abs(e.clientX-drag.x)<3&&Math.abs(e.clientY-drag.y)<3&&drag.b===0)pick(e);drag=null;});
cv.addEventListener('pointermove',function(e){
  if(!drag)return;var dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;
  if(drag.b===2||e.shiftKey){
    var sc=st.dist/900,right=new THREE.Vector3().subVectors(camera.position,
      new THREE.Vector3(st.tx,st.ty,st.tz)).cross(camera.up).normalize();
    st.tx-=right.x*dx*sc;st.tz-=right.z*dx*sc;st.ty+=dy*sc;
  }else{st.th-=dx*0.005;st.ph=Math.max(0.06,Math.min(1.48,st.ph+dy*0.004));}
  applyCam();});
cv.addEventListener('contextmenu',function(e){e.preventDefault();});
cv.addEventListener('wheel',function(e){e.preventDefault();
  st.dist=Math.max(70,Math.min(3600,st.dist*(1+Math.sign(e.deltaY)*0.11)));applyCam();},{passive:false});
addEventListener('resize',function(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);});
/* ---------- 9. 点选 ---------- */
var ray=new THREE.Raycaster(),ndc=new THREE.Vector2();
var rightPanel=document.getElementById('right'),rbody=document.getElementById('rbody');
var KIND={base:'台基 / 月台',floor:'楼层',balcony:'平座 / 回廊',roof:'攒尖屋顶',
          finial:'宝顶',annex:'附属建筑',bridge:'桥梁构件'};
function pick(e){
  ndc.x=e.clientX/innerWidth*2-1;ndc.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(ndc,camera);
  var its=ray.intersectObjects(towerMeshes.concat([bridgeMesh,buildingMesh]),false);
  if(!its.length){rightPanel.classList.remove('show');return;}
  var o=its[0];
  if(o.object===buildingMesh){
    for(var i=0;i<hitB.length;i++)if(o.faceIndex>=hitB[i].s&&o.faceIndex<hitB[i].e){
      showBuilding(D.buildings[hitB[i].i]);return;}
    rightPanel.classList.remove('show');return;
  }
  var pid=o.object.userData.pid;
  if(pid===undefined||pid<0){rightPanel.classList.remove('show');return;}
  showPart(PT[pid]);
}
function showPart(p){
  var kv=[['构件类型',KIND[p.k]||p.k],['构件编号','HCL-'+String(p.id+1).padStart(3,'0')],
    ['标高范围',(p.z0===0&&p.z1===0)?'见技术规格':(p.z0.toFixed(1)+' – '+p.z1.toFixed(1)+' m')],
    ['技术规格',p.spec],
    ['材料 / 构造',p.mat],['数据来源',p.src]];
  if(p.note)kv.push(['功能 / 展陈',p.note]);
  var rows=kv.map(function(x){return '<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';}).join('');
  document.getElementById('floorcard').classList.remove('show');
  rbody.innerHTML='<div class="rname">'+p.n+'</div><div class="rtype">TOWER ELEMENT · '+p.k.toUpperCase()+'</div>'+rows+
    '<div class="divider"></div><div style="font-size:10px;color:#e8b478;line-height:1.7">'+
    '楼阁按公开设计参数与形制程序化重建，非竣工 BIM；柱网、格栅、起翘为可视化表达，不含构件级结构属性。</div>';
  rightPanel.classList.add('show');
}
function showBuilding(b){
  var kv=[['要素类型',b.k==='landmark'?'具名地标（示意）':'周边建筑（示意）'],
    ['层数',b.lv+' 层'],['模型高度',(b.h*S).toFixed(1)+' m'],['占地',b.a.toLocaleString()+' m²'],
    ['高度来源',b.s]];
  var rows=kv.map(function(x){return '<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';}).join('');
  var tg='';if(b.at)Object.keys(b.at).forEach(function(k){tg+='<div class="kv"><k>'+k+'</k><v>'+b.at[k]+'</v></div>';});
  document.getElementById('floorcard').classList.remove('show');
  rbody.innerHTML='<div class="rname">'+(b.n||'未命名建筑')+'</div>'+
    '<div class="rtype">SCHEMATIC BUILDING</div>'+rows+
    (tg?'<div class="divider"></div><div class="ptitle">标签</div>'+tg:'')+
    '<div class="divider"></div><div style="font-size:10px;color:#e8b478;line-height:1.7">'+
    '本轮 OSM 服务不可达，周边建筑与路网为示意矢量，不作量测依据。</div>';
  rightPanel.classList.add('show');
}
document.getElementById('rclose').onclick=function(){rightPanel.classList.remove('show');};
/* ---------- 10. 图层 / 模式 ---------- */
var LY=[['地形 · Copernicus DEM',terrainMesh,1,'#3d7a52'],['长江 · DEM 低地水面',waterMesh,1,'#1a6389'],
  ['道路 / 路网（示意）',roadMesh,1,'#6b7b89'],['周边建筑（示意）',buildingMesh,1,'#6ba8c8'],
  ['武汉长江大桥（示意）',bridgeMesh,1,'#8a8f80'],['楼阁 · 台基',baseMesh,1,'#b0b4b0'],
  ['楼阁 · 五层主体',null,1,'#a8392a'],['楼阁 · 攒尖顶 / 宝顶',roofMesh,1,'#e8c26a'],
  ['地名 / 楼层标注',null,1,'#dff1ff']];
var layBox=document.getElementById('layers');
LY.forEach(function(o,i){
  var d=document.createElement('label');d.className='ly';
  d.innerHTML='<input type="checkbox" checked data-i="'+i+'"><span class="sw" style="background:'+o[3]+'"></span>'+o[0];
  layBox.appendChild(d);
});
var labelsHidden=false;
function setLayer(i,on){
  if(i===6){floorMeshes.forEach(function(m){m.visible=on;});}
  else if(LY[i][1])LY[i][1].visible=on;
  else{labelsHidden=!on;labels.forEach(function(l){l.e.style.display=(on?'':'none');});}
}
layBox.addEventListener('change',function(e){setLayer(+e.target.dataset.i,e.target.checked);});
function setMode(mode){
  ['btnAll','btnFloors','btnSkel','btnTop','btnWide'].forEach(function(id){
    document.getElementById(id).classList.remove('on');});
  document.getElementById(mode).classList.add('on');
  document.getElementById('floorcard').classList.toggle('show',mode==='btnFloors');
  if(mode==='btnFloors'){
    for(var i=0;i<LY.length;i++)setLayer(i,i!==3);
    document.getElementById('sep').value=7;applySep(7);
    st.th=-0.42;st.ph=0.28;st.dist=205;
    st.tx=TX-HALF_W;st.ty=(BZ+TW.total_m/S*TVIS)*ZEX*0.62+18;st.tz=-(TY-HALF_H);applyCam();
    document.getElementById('tip').textContent='分层展开：逐层上移，可单击任一楼层查看层高 / 平面 / 展陈功能';
  }else if(mode==='btnSkel'){
    for(var i=0;i<LY.length;i++)setLayer(i,i<5||i===8);
    document.getElementById('sep').value=0;applySep(0);
    st.th=-0.55;st.ph=1.32;st.dist=1250;st.tx=0;st.ty=0;st.tz=0;applyCam();
    document.getElementById('tip').textContent='地形骨架：真实 DEM 蛇山 / 长江低地 / 示意路网，先核地理关系再叠楼阁';
  }else if(mode==='btnTop'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    document.getElementById('sep').value=0;applySep(0);
    st.th=0;st.ph=1.47;st.dist=1150;st.tx=0;st.ty=0;st.tz=0;applyCam();
    document.getElementById('tip').textContent='正射俯视：核对八边形「四面八方」平面、层层收分与出檐';
  }else if(mode==='btnWide'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    document.getElementById('sep').value=0;applySep(0);
    st.th=-0.55;st.ph=0.58;st.dist=940;st.tx=0;st.ty=30;st.tz=0;applyCam();
    document.getElementById('tip').textContent='全景沙盘：蛇山 — 黄鹤楼 — 长江大桥 — 长江 — 武昌城区的空间关系';
  }else{
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    document.getElementById('sep').value=0;applySep(0);
    st.th=-0.52;st.ph=0.30;st.dist=138;
    st.tx=TX-HALF_W;st.ty=(BZ+TW.total_m/S*TVIS)*ZEX*0.62;st.tz=-(TY-HALF_H);applyCam();
    document.getElementById('tip').textContent='拖动旋转 · 滚轮缩放 · 右键平移 · 单击楼层 / 构件 / 建筑查看属性';
  }
  layBox.querySelectorAll('input').forEach(function(cb,i2){
    cb.checked=LY[i2][1]?LY[i2][1].visible:(i2===6?floorMeshes[0].visible:!labelsHidden);});
}
['btnAll','btnFloors','btnSkel','btnTop','btnWide'].forEach(function(id){
  document.getElementById(id).onclick=function(){setMode(id);};});
/* ---------- 11. 楼层剖切 / 分层展开 ---------- */
var SEP=0,CUT=6;
function applySep(v){
  SEP=+v;
  floorMeshes.forEach(function(m,i){m.position.y=i*SEP*ZEX*0.62;});
  roofMesh.position.y=4*SEP*ZEX*0.62;
  document.getElementById('sepv').textContent=(SEP*S).toFixed(0)+' m';
}
function applyCut(v){
  CUT=+v;
  floorMeshes.forEach(function(m,i){m.visible=floorVisible&&(i<CUT);});
  roofMesh.visible=(CUT>=6)&&roofVisible;
  baseMesh.visible=baseVisible;
  document.getElementById('cutv').textContent=CUT>=6?'全部 5 层':(CUT===0?'仅台基':'显示至第'+'一二三四五'[CUT-1]+'层');
}
var floorVisible=true,roofVisible=true,baseVisible=true;
/* 图层开关与剖切联动：由 setLayer 维护三个标志 */
var _setLayer=setLayer;
setLayer=function(i,on){
  if(i===6)floorVisible=on;if(i===7)roofVisible=on;if(i===5)baseVisible=on;
  _setLayer(i,on);
  applyCut(CUT);
};
document.getElementById('sep').oninput=function(){applySep(this.value);
  if(+this.value>0&&!document.getElementById('btnFloors').classList.contains('on')){
    document.getElementById('tip').textContent='分层展开：每层独立上移，便于逐层观察柱网 / 平座 / 腰檐';}};
document.getElementById('cut').oninput=function(){applyCut(this.value);};
applySep(0);applyCut(6);
/* ---------- 12. 清单 / 搜索 ---------- */
var plist=document.getElementById('plist');
PT.forEach(function(p){
  var e=document.createElement('div');e.className='pi';
  e.innerHTML='<span class="tag">'+(KIND[p.k]||p.k).slice(0,2)+'</span>'+
    '<span class="nm">'+p.n+'</span><span class="st">'+(p.z1?p.z1.toFixed(1)+'m':'—')+'</span>';
  e.onclick=function(){locatePart(p);};plist.appendChild(e);
});
document.getElementById('pn').textContent=PT.length+' 项';
function focus(x,y,z,dist,ph,th){st.tx=x-HALF_W;st.tz=-(y-HALF_H);st.ty=z*ZEX;
  st.dist=dist;st.ph=ph;st.th=th;applyCam();}
function locatePart(p){
  var fl=-1;
  for(var i=0;i<TW.floors.length;i++)if(p.n.indexOf('第'+'一二三四五'[i]+'层')>=0)fl=i;
  var hm=fl>=0?TW.floors[fl].z1:TW.total_m;
  focus(TX,TY,BZ+hm/S*TVIS,150,0.32,-0.55);
  document.getElementById('tip').textContent='已定位：'+p.n;showPart(p);
}
function locate(){
  var q=document.getElementById('q').value.trim();if(!q)return;
  for(var i=0;i<PT.length;i++)if(PT[i].n.indexOf(q)>=0){locatePart(PT[i]);return;}
  for(var i=0;i<D.poi.length;i++)if(D.poi[i].n.indexOf(q)>=0){
    focus(D.poi[i].p[0],D.poi[i].p[1],D.poi[i].z,300,0.55,-0.5);
    document.getElementById('tip').textContent='已定位：'+D.poi[i].n;return;}
  for(var i=0;i<D.buildings.length;i++)if(D.buildings[i].n&&D.buildings[i].n.indexOf(q)>=0){
    var b=D.buildings[i];focus(b.c[0],b.c[1],4,220,0.55,-0.5);
    document.getElementById('tip').textContent='已定位：'+b.n;showBuilding(b);return;}
  document.getElementById('tip').textContent='未找到「'+q+'」，试试：第三层 / 攒尖 / 宝顶 / 白云阁 / 长江大桥';
}
document.getElementById('go').onclick=locate;
document.getElementById('q').addEventListener('keydown',function(e){if(e.key==='Enter')locate();});
/* ---------- 13. 指标 / 图例 / 说明 ---------- */
var K=[['总高',M.tower_h,'m'],['楼层',M.n_floor,'层'],['底层平面',30,'m'],['檐柱',TW.n_col,'根'],
  ['点选构件',M.n_part,'项'],['周边建筑',M.n_building,'栋'],['示意路网',M.road_km,'km'],
  ['DEM 高程',M.dem_min+'–'+M.dem_max,'m'],['江面',M.water_km2,'km²']];
document.getElementById('kpis').innerHTML=K.map(function(x){
  return '<div class="kpi"><b>'+x[1]+'<i>'+x[2]+'</i></b><span>'+x[0]+'</span></div>';}).join('');
var LEG=[['#3d7a52','蛇山 / 林地'],['#1a6389','长江水面'],['#6b7b89','道路'],
  ['#6ba8c8','周边建筑'],['#f0c46a','具名地标'],['#a8392a','檐柱 / 栏杆'],
  ['#e8c26a','金色琉璃瓦 / 腰檐'],['#b0b4b0','台基'],['#ffe1a1','宝顶']];
document.getElementById('legend').innerHTML=LEG.map(function(x){
  return '<span class="it"><i class="box" style="background:'+x[0]+'"></i>'+x[1]+'</span>';}).join('');
document.getElementById('srcbox').innerHTML=
  '<em>地形</em>：Copernicus DEM 30 m 真实高程（本区域 '+M.dem_min+'–'+M.dem_max+' m），'+
  'DEM &lt; 20 m 低地判定长江水面，1 场景单位 = 4 m，垂直放大 '+ZEX.toFixed(1)+'×。<br>'+
  '<em>楼阁</em>：'+TW.built+'，'+TW.style+'；'+TW.height_src+'。'+
  '五层逐层独立建模（切角八边形平面、12 根檐柱、门窗格栅、平座栏杆、四角起翘腰檐、攒尖顶、葫芦宝顶），'+
  '可逐层剖切、分层展开、点选查看层高与功能。<br>'+
  '<span class="warn">注意：本轮 Overpass / OSM API 均不可达（000 / 406 / 504），'+
  '周边路网、建筑、长江大桥为按公开地理轮廓绘制的示意矢量，非实测 OSM，不作量测依据；'+
  '楼阁为按公开参数程序化重建，非竣工 BIM / Scan-to-BIM；'+
  '为便于逐层观察，楼阁横向与纵向放大 '+TVIS.toFixed(2)+'×，均为可视化夸张。</span><br>'+
  '<em>合规</em>：WGS84，仅本地可视化；对外发布需 WGS84 → GCJ-02 转换与国内合规底图 / 审图号。';
function tick(){var d=new Date();
  document.getElementById('clk').textContent=d.toTimeString().slice(0,8);
  document.getElementById('date').textContent=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+
    String(d.getDate()).padStart(2,'0')+'  周'+'日一二三四五六'[d.getDay()];}
tick();setInterval(tick,1000);
/* ---------- 14. 渲染 ---------- */
var tmp=new THREE.Vector3();
function loop(){
  requestAnimationFrame(loop);
  labels.forEach(function(l){
    tmp.copy(l.v);
    if(l.fl>=0)tmp.y+=l.fl*SEP*ZEX*0.62;
    tmp.project(camera);
    var vis=tmp.z<1&&tmp.z>-1&&!labelsHidden&&SEP===0;
    l.e.style.display=vis?'':'none';
    if(vis){l.e.style.left=(tmp.x*0.5+0.5)*innerWidth+'px';l.e.style.top=(-tmp.y*0.5+0.5)*innerHeight+'px';}
  });
  renderer.render(scene,camera);
}
loop();
window.__TDBG={scene:scene,camera:camera,st:st,applyCam:applyCam,applySep:applySep,
  applyCut:applyCut,setMode:setMode,floorMeshes:floorMeshes,roofMesh:roofMesh,
  labels:labels,parts:PT,THREE:THREE};
var ld=document.getElementById('loading');ld.style.opacity=0;setTimeout(function(){ld.remove();},600);
})();
'''

html = (HTML.replace('__THREE__', three)
            .replace('__DATA__', data)
            .replace('__JS__', JS))
for d in (HERE, OUT):
    with open(os.path.join(d, '黄鹤楼_数字孪生.html'), 'w', encoding='utf-8') as f:
        f.write(html)
print('html bytes', len(html))
