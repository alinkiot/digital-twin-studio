#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 three.js + 孪生数据 + 大屏 UI 拼成一个离线可用的单文件 HTML"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')

three = open(os.path.join(HERE, 'three.min.js'), encoding='utf-8').read().replace('</script', '<\\/script')
data = open(os.path.join(HERE, 'twin_data.json'), encoding='utf-8').read().replace('</script', '<\\/script')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>杭州西湖 · 城市数字孪生</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#070d15;color:#dce8f5;
  font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif;-webkit-font-smoothing:antialiased}
#app{position:relative;width:100%;height:100%}
canvas#gl{position:absolute;inset:0;display:block}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 42%,transparent 40%,rgba(3,8,16,.55) 100%)}
.scan{position:absolute;inset:0;pointer-events:none;opacity:.22;
  background:repeating-linear-gradient(0deg,transparent 0 3px,rgba(90,170,255,.045) 3px 4px)}

/* ---------- 顶部 ---------- */
header{position:absolute;top:0;left:0;right:0;height:74px;display:flex;align-items:center;
  padding:0 26px;background:linear-gradient(180deg,rgba(6,14,26,.96),rgba(6,14,26,0));
  border-bottom:1px solid rgba(96,168,232,.16);pointer-events:none;z-index:6}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:34px;height:34px;border:1.5px solid #4fd0e0;border-radius:8px;position:relative;
  box-shadow:0 0 18px rgba(79,208,224,.35) inset,0 0 12px rgba(79,208,224,.2)}
.logo::before,.logo::after{content:"";position:absolute;background:#4fd0e0}
.logo::before{left:50%;top:6px;bottom:6px;width:1.5px;transform:translateX(-50%)}
.logo::after{top:50%;left:6px;right:6px;height:1.5px;transform:translateY(-50%)}
h1{font-size:19px;font-weight:600;letter-spacing:2px;color:#eaf5ff}
.sub{font-size:11px;color:#6f8aa6;letter-spacing:1.4px;margin-top:3px}
.hright{margin-left:auto;display:flex;align-items:center;gap:22px;text-align:right}
.clock{font-size:22px;font-weight:300;letter-spacing:1px;color:#bfe3ff;font-variant-numeric:tabular-nums}
.clock small{font-size:11px;color:#64809c;display:block;letter-spacing:1px}
.badge{font-size:11px;padding:5px 11px;border:1px solid rgba(79,208,224,.4);border-radius:20px;
  color:#7ee0e8;background:rgba(79,208,224,.07);letter-spacing:.5px}

/* ---------- 左侧面板 ---------- */
.panel{position:absolute;z-index:5;background:rgba(9,19,33,.86);border:1px solid rgba(90,150,210,.2);
  border-radius:10px;backdrop-filter:blur(14px);box-shadow:0 12px 40px rgba(0,0,0,.4)}
#left{top:92px;left:22px;width:262px;padding:16px 16px 14px}
.ptitle{font-size:12px;color:#8fb6d8;letter-spacing:2px;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.ptitle::before{content:"";width:3px;height:12px;background:#4fd0e0;border-radius:2px;box-shadow:0 0 8px #4fd0e0}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.kpi{background:rgba(30,58,88,.34);border:1px solid rgba(90,150,210,.13);border-radius:7px;padding:9px 10px}
.kpi b{display:block;font-size:20px;font-weight:500;color:#7fe3f0;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi b i{font-size:10px;font-style:normal;color:#7d9ab5;margin-left:2px}
.kpi span{font-size:10px;color:#7793ad;letter-spacing:.5px}
.divider{height:1px;background:rgba(90,150,210,.15);margin:14px 0 12px}
.src{font-size:10.5px;line-height:1.85;color:#7996b1}
.src em{font-style:normal;color:#a9c9e4}
.src .warn{color:#e8b478}
.layers{display:grid;gap:2px;margin-top:10px}
.ly{display:flex;align-items:center;gap:9px;font-size:11.5px;color:#a8c2da;padding:5px 6px;border-radius:5px;cursor:pointer}
.ly:hover{background:rgba(80,150,220,.09)}
.ly input{appearance:none;width:14px;height:14px;border:1px solid #4a7398;border-radius:3px;position:relative;cursor:pointer;flex:none}
.ly input:checked{background:#3fbdd2;border-color:#3fbdd2}
.ly input:checked::after{content:"";position:absolute;left:4px;top:1px;width:4px;height:8px;
  border:solid #06131f;border-width:0 2px 2px 0;transform:rotate(45deg)}
.sw{width:9px;height:9px;border-radius:2px;flex:none}
.btnrow{display:flex;gap:6px;margin-top:12px}
.btn{flex:1;text-align:center;font-size:11px;padding:8px 4px;border-radius:6px;cursor:pointer;
  border:1px solid rgba(90,160,220,.28);background:rgba(40,90,140,.16);color:#a9cbe6;transition:.18s}
.btn:hover{background:rgba(70,160,220,.3);color:#fff;border-color:#5ec8e0}
.btn.on{background:rgba(63,189,210,.24);border-color:#4fd0e0;color:#bff4fb}

/* ---------- 右侧属性 ---------- */
#right{top:92px;right:22px;width:268px;padding:16px;display:none}
#right.show{display:block}
#right .hint{display:block}
.hint{font-size:11px;color:#6f8ba6;line-height:1.8}
.rname{font-size:16px;color:#eaf7ff;font-weight:600;margin:2px 0 3px;letter-spacing:.5px}
.rtype{font-size:11px;color:#6fd3e2;margin-bottom:12px;letter-spacing:1px}
.kv{display:flex;justify-content:space-between;gap:10px;font-size:11.5px;padding:6px 0;
  border-bottom:1px dashed rgba(90,150,210,.14)}
.kv k{color:#7b98b3;flex:none}
.kv v{color:#d3e6f6;text-align:right;word-break:break-all}
.tags{margin-top:10px;max-height:150px;overflow:auto;font-size:10.5px;color:#8fadc6;line-height:1.8}
.tags div{display:flex;gap:8px}.tags span{color:#5f88a8;min-width:76px}
.close{position:absolute;right:12px;top:12px;cursor:pointer;color:#6f8ba6;font-size:16px;line-height:1}
.close:hover{color:#fff}

/* ---------- 底部 ---------- */
#bottom{position:absolute;left:22px;right:22px;bottom:20px;z-index:5;display:flex;align-items:flex-end;gap:14px;pointer-events:none}
#bottom>*{pointer-events:auto}
.legend{background:rgba(9,19,33,.86);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:11px 14px;backdrop-filter:blur(14px);font-size:10.5px;color:#91aec8}
.legend .row{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.legend .it{display:flex;align-items:center;gap:6px;white-space:nowrap}
.legend .box{width:11px;height:11px;border-radius:2px}
.tools{background:rgba(9,19,33,.86);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:11px 14px;backdrop-filter:blur(14px);min-width:290px}
.tools label{font-size:10.5px;color:#8fb0cc;display:flex;justify-content:space-between;margin-bottom:7px}
.tools label b{color:#7fe3f0;font-weight:500}
input[type=range]{width:100%;height:4px;appearance:none;background:linear-gradient(90deg,#3fbdd2,#2a5878);
  border-radius:3px;outline:none;cursor:pointer}
input[type=range]::-webkit-slider-thumb{appearance:none;width:13px;height:13px;border-radius:50%;
  background:#9ff0fa;box-shadow:0 0 8px #4fd0e0;cursor:pointer}
.search{margin-left:auto;display:flex;gap:6px;background:rgba(9,19,33,.86);border:1px solid rgba(90,150,210,.2);
  border-radius:9px;padding:7px 9px;backdrop-filter:blur(14px)}
.search input{background:transparent;border:0;outline:0;color:#dceaf7;font-size:11.5px;width:132px}
.search input::placeholder{color:#5c7893}
.search button{background:rgba(63,189,210,.2);border:1px solid rgba(79,208,224,.4);color:#9fe9f2;
  border-radius:5px;padding:4px 10px;font-size:11px;cursor:pointer}

/* ---------- 标注 / HUD ---------- */
#labels{position:absolute;inset:0;pointer-events:none;z-index:4;overflow:hidden}
.lab{position:absolute;transform:translate(-50%,-100%);font-size:11px;color:#dff1ff;white-space:nowrap;
  text-shadow:0 1px 5px #000,0 0 10px rgba(0,0,0,.9);letter-spacing:.5px;opacity:.92}
.lab::after{content:"";position:absolute;left:50%;top:100%;width:1px;height:12px;
  background:linear-gradient(rgba(160,220,255,.8),transparent)}
.lab.hot{color:#ffe0a8;font-weight:600;font-size:12px}
#north{position:absolute;right:26px;bottom:118px;z-index:5;width:52px;height:52px;border-radius:50%;
  border:1px solid rgba(90,150,210,.28);background:rgba(9,19,33,.7);text-align:center;pointer-events:none}
#north .ar{font-size:19px;color:#7fe3f0;line-height:30px}
#north .tx{font-size:9px;color:#7f9db8;letter-spacing:1px}
#scale{position:absolute;left:24px;bottom:96px;z-index:5;font-size:10px;color:#8fadc6;pointer-events:none}
#scale .bar{height:5px;border:1px solid #8fadc6;border-top:0;width:88px;margin-bottom:3px}
#tip{position:absolute;left:50%;top:82px;transform:translateX(-50%);z-index:7;font-size:11px;
  color:#9fc4dd;background:rgba(9,19,33,.8);border:1px solid rgba(90,150,210,.2);
  padding:6px 14px;border-radius:16px;letter-spacing:.5px;pointer-events:none}
#loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:20;
  background:#070d15;color:#7fe3f0;font-size:13px;letter-spacing:3px;transition:opacity .5s}
</style>
</head>
<body>
<div id="app">
  <canvas id="gl"></canvas>
  <div class="vig"></div><div class="scan"></div>
  <div id="labels"></div>

  <header>
    <div class="brand"><div class="logo"></div>
      <div><h1>杭州西湖 · 城市数字孪生</h1>
      <div class="sub">WEST LAKE DIGITAL TWIN &nbsp;·&nbsp; OSM VECTOR FOOTPRINT + COPERNICUS DEM</div></div>
    </div>
    <div class="hright">
      <div class="badge">WGS84 · cos(φ) 修正</div>
      <div class="clock"><span id="clk">--:--:--</span><small id="date">----</small></div>
    </div>
  </header>

  <div class="panel" id="left">
    <div class="ptitle">城市概览 · CITY STATS</div>
    <div class="kpis" id="kpis"></div>
    <div class="divider"></div>
    <div class="ptitle">图层控制 · LAYERS</div>
    <div class="layers" id="layers"></div>
    <div class="btnrow">
      <div class="btn on" id="btnAll">全量</div>
      <div class="btn" id="btnSkel">验收骨架</div>
      <div class="btn" id="btnTop">俯视</div>
    </div>
    <div class="divider"></div>
    <div class="src" id="srcbox"></div>
  </div>

  <div class="panel" id="right">
    <div class="close" id="rclose">✕</div>
    <div class="ptitle">构件属性 · ELEMENT</div>
    <div id="rbody"></div>
  </div>

  <div id="north"><div class="ar">▲</div><div class="tx">N</div></div>
  <div id="scale"><div class="bar"></div><span id="scaletx">200 m</span></div>
  <div id="tip">拖动旋转 · 滚轮缩放 · 右键平移 · 单击建筑查看属性</div>

  <div id="bottom">
    <div class="legend"><div class="row" id="legend"></div></div>
    <div class="tools">
      <label>楼层剖切高度 <b id="cutv">不限</b></label>
      <input type="range" id="cut" min="0" max="100" value="100">
      <div class="hint" style="margin-top:7px;font-size:10px">向下拖动可逐层剖开建筑，查看每层结构</div>
    </div>
    <div class="search"><input id="q" placeholder="搜索建筑名 / 地名"><button id="go">定位</button></div>
  </div>

  <div id="loading">正在铺设地理骨架 …</div>
</div>

<script>__THREE__</script>
<script>window.__TWIN__=__DATA__;</script>
<script>
(function(){
'use strict';
if(!window.THREE){document.getElementById('loading').textContent='three.js 未加载';return;}
THREE.ColorManagement && (THREE.ColorManagement.enabled=false);
var D=window.__TWIN__, M=D.meta;
var W=M.w,H=M.h,ZEX=2.0,LAKE=4.9/4*ZEX,BEX=3.0;
var HALF_W=W/2, HALF_H=H/2;

/* ---------- 渲染器 / 场景 ---------- */
var cv=document.getElementById('gl');
var renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));
renderer.setSize(innerWidth,innerHeight);
renderer.setClearColor(0x070d15,1);
renderer.localClippingEnabled=true;
var scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x070d15,0.00075);
var camera=new THREE.PerspectiveCamera(46,innerWidth/innerHeight,1,9000);
var clip=new THREE.Plane(new THREE.Vector3(0,-1,0),10000);

function V(x,y,h){return new THREE.Vector3(x-HALF_W,(h||0)*ZEX,-(y-HALF_H));}
function C(hex){return new THREE.Color(hex);}
/* 由降采样 DEM 网格双线性插值出任意点的地面高程（场景单位，未乘 ZEX） */
function terrainZ(px,py){
  var fx=Math.max(0,Math.min(nx-1.001,px/W*(nx-1)));
  var fy=Math.max(0,Math.min(ny-1.001,py/H*(ny-1)));
  var c0=Math.floor(fx),r0=Math.floor(fy),tx=fx-c0,ty=fy-r0;
  var i00=r0*nx+c0,i10=i00+1,i01=i00+nx,i11=i01+1;
  function z(i){return T.lc[i]===7?LAKE/ZEX:T.z[i];}
  return (z(i00)*(1-tx)+z(i10)*tx)*(1-ty)+(z(i01)*(1-tx)+z(i11)*tx)*ty;
}
scene.add(new THREE.AmbientLight(0xb8d4f0,0.85));
var sun=new THREE.DirectionalLight(0xfff0d8,1.15);sun.position.set(-380,620,300);scene.add(sun);
var fill=new THREE.DirectionalLight(0x66aaff,0.35);fill.position.set(420,220,-380);scene.add(fill);

/* ---------- 1. 地形骨架（DEM + 土地覆盖） ---------- */
var T=D.terrain,nx=T.nx,ny=T.ny;
var tg=new THREE.BufferGeometry(),tp=[],tc=[],ti=[];
var LC={0:[0.24,0.48,0.32],2:[0.42,0.50,0.28],3:[0.53,0.52,0.34],4:[0.33,0.38,0.43],
        5:[0.40,0.46,0.40],7:[0.09,0.27,0.40],8:[0.35,0.55,0.50]};
for(var r=0;r<ny;r++)for(var c=0;c<nx;c++){
  var i=r*nx+c;
  var px=c/(nx-1)*W, py=r/(ny-1)*H;
  var z=T.lc[i]===7?LAKE/ZEX:T.z[i];
  var v=V(px,py,z); tp.push(v.x,v.y,v.z);
  var col=LC[T.lc[i]]||LC[0];
  var sh=0.78+Math.min(T.z[i],40)/40*0.42;   // 高程提亮
  tc.push(col[0]*sh,col[1]*sh,col[2]*sh);
}
for(var r=0;r<ny-1;r++)for(var c=0;c<nx-1;c++){
  var a=r*nx+c,b=a+1,d=a+nx,e=d+1;
  ti.push(a,d,b,b,d,e);
}
tg.setAttribute('position',new THREE.Float32BufferAttribute(tp,3));
tg.setAttribute('color',new THREE.Float32BufferAttribute(tc,3));
tg.setIndex(ti);tg.computeVertexNormals();
var terrainMesh=new THREE.Mesh(tg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
scene.add(terrainMesh);

/* ---------- 2. 水面（WorldCover 水格，与 DEM 配准） ---------- */
var G=D.waterGrid,gnx=G.nx,gny=G.ny;
var wp=[],wi=[],widx=[];
var WR={};
for(var r=0;r<gny;r++)for(var c=0;c<gnx;c++){WR[r*gnx+c]=G.m[r*gnx+c];}
for(var r=0;r<gny;r++)for(var c=0;c<gnx;c++){
  if(!WR[r*gnx+c])continue;
  var x0=c/(gnx-1)*W,x1=(c+1)/(gnx-1)*W,y0=r/(gny-1)*H,y1=(r+1)/(gny-1)*H;
  var base=wp.length/3;
  var a=V(x0,y0,LAKE/ZEX+0.03),b=V(x1,y0,LAKE/ZEX+0.03),
      d=V(x1,y1,LAKE/ZEX+0.03),e=V(x0,y1,LAKE/ZEX+0.03);
  wp.push(a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,e.x,e.y,e.z);
  wi.push(base,base+1,base+2,base,base+2,base+3);
}
var wg=new THREE.BufferGeometry();
wg.setAttribute('position',new THREE.Float32BufferAttribute(wp,3));wg.setIndex(wi);wg.computeVertexNormals();
var waterMesh=new THREE.Mesh(wg,new THREE.MeshPhongMaterial({color:0x1a6f9c,shininess:90,
  specular:0x6fd8ff,transparent:true,opacity:.88,side:THREE.DoubleSide}));
scene.add(waterMesh);

/* ---------- 3. 道路（按等级条带） ---------- */
function ribbon(pts,width,h,geomArr,colorArr,col){
  for(var i=0;i<pts.length-1;i++){
    var a=pts[i],b=pts[i+1];
    var dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
    if(L<0.05)continue;
    var ox=-dy/L*width/2,oy=dx/L*width/2;
    var P1=V(a[0]+ox,a[1]+oy,h),P2=V(a[0]-ox,a[1]-oy,h),
        P3=V(b[0]-ox,b[1]-oy,h),P4=V(b[0]+ox,b[1]+oy,h);
    var base=geomArr.length/3;
    geomArr.push(P1.x,P1.y,P1.z,P2.x,P2.y,P2.z,P3.x,P3.y,P3.z,P4.x,P4.y,P4.z);
    colorArr.push(col[0],col[1],col[2],col[0],col[1],col[2],col[0],col[1],col[2],col[0],col[1],col[2]);
    // 索引稍后统一生成
  }
}
function buildRibbon(lines,widthFn,hFn,meshColor,opacity){
  var vp=[],vc=[],vi=[],k=0;
  var hf=typeof hFn==='function'?hFn:function(){return hFn;};
  lines.forEach(function(o){
    var pts=o.p,wd=widthFn(o),col=o.col||meshColor;
    for(var i=0;i<pts.length-1;i++){
      var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
      if(L<0.05)continue;
      var ox=-dy/L*wd/2,oy=dx/L*wd/2;
      // 逐点贴合 DEM，路随地形起伏（水域夹到湖面高程，避免扎进湖底）
      var za=Math.max(hf(a[0],a[1]),terrainZ(a[0],a[1])+0.08);
      var zb=Math.max(hf(b[0],b[1]),terrainZ(b[0],b[1])+0.08);
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
  var m=new THREE.Mesh(g,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide,
    transparent:opacity<1,opacity:opacity}));
  m.renderOrder=2;return m;
}
var RC={7:[0.55,0.62,0.68],6:[0.46,0.54,0.62],5:[0.40,0.48,0.56],4:[0.36,0.43,0.50],
        3:[0.32,0.39,0.46],2:[0.29,0.35,0.41],1:[0.30,0.40,0.38]};
D.roads.forEach(function(r){r.col=RC[r.k]||RC[2];});
var roadMesh=buildRibbon(D.roads,function(o){return {7:7,6:6,5:5,4:4,3:3.2,2:2,1:1.4}[o.k]||2;},
   function(){return LAKE/ZEX+0.10;},null,1);
scene.add(roadMesh);

/* ---------- 4. 白堤 / 苏堤（OSM 真实矢量，米白堤身 + 中心线） ---------- */
var dikeLines=D.dikes.map(function(d){return {p:d.p,col:[0.94,0.90,0.78]};});
var dikeMesh=buildRibbon(dikeLines,function(){return 7.5;},function(){return LAKE/ZEX+0.34;},null,1);
dikeMesh.renderOrder=3;scene.add(dikeMesh);
var centerLines=D.dikes.map(function(d){return {p:d.p,col:[0.80,0.60,0.34]};});
var centerMesh=buildRibbon(centerLines,function(){return 1.1;},function(){return LAKE/ZEX+0.40;},null,1);
centerMesh.renderOrder=4;scene.add(centerMesh);

/* ---------- 5. 建筑：真实 footprint 挤出，合并成一个可点选 mesh ---------- */
var bp=[],bc=[],bi=[],hit=[];
var BCOL=[[0.36,0.62,0.80],[0.44,0.70,0.86],[0.55,0.78,0.90],[0.66,0.83,0.91],[0.80,0.84,0.78]];
var namedCol=[1.00,0.72,0.34];
var fidx=0;
function pushTri(a,b,c,col,start){
  var base=bp.length/3;
  bp.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
  for(var q=0;q<3;q++)bc.push(col[0],col[1],col[2]);
  bi.push(base,base+1,base+2);
  fidx++;
}
D.buildings.forEach(function(b,idx){
  var poly=b.p.slice();
  if(poly.length>2){
    var p0=poly[0],pl=poly[poly.length-1];
    if(Math.abs(p0[0]-pl[0])<0.01&&Math.abs(p0[1]-pl[1])<0.01)poly=poly.slice(0,-1);
  }
  if(poly.length<3)return;
  var h=Math.max(b.h*BEX,0.6);
  // 基座取该楼占地内的最高地面，保证楼体不会被 DEM 埋掉，屋顶仍保持水平
  var base=b.bz||0;
  for(var i=0;i<poly.length;i++)base=Math.max(base,terrainZ(poly[i][0],poly[i][1]));
  base-=0.12;
  var ci=Math.min(BCOL.length-1,Math.floor(h/4));
  var col=b.n?namedCol:BCOL[ci];
  var top=[],bot=[];
  for(var i=0;i<poly.length;i++){
    top.push(V(poly[i][0],poly[i][1],base+h));
    bot.push(V(poly[i][0],poly[i][1],base));
  }
  // 侧面
  for(var i=0;i<poly.length;i++){
    var j=(i+1)%poly.length;
    var shade=0.72+0.28*Math.abs(Math.cos(i*1.1));
    var sc=[col[0]*shade,col[1]*shade,col[2]*shade];
    pushTri(bot[i],bot[j],top[j],sc);
    pushTri(bot[i],top[j],top[i],sc);
  }
  // 顶面（扇形三角化，凸/凹均可近似）
  var contour=poly.map(function(p){return new THREE.Vector2(p[0],p[1]);});
  var faces=[];
  try{faces=THREE.ShapeUtils.triangulateShape(contour,[]);}catch(e){faces=[];}
  if(!faces.length){
    for(var i=1;i<poly.length-1;i++)faces.push([0,i,i+1]);
  }
  for(var i=0;i<faces.length;i++){
    var f=faces[i];
    pushTri(top[f[0]],top[f[1]],top[f[2]],[col[0]*1.08,col[1]*1.08,col[2]*1.08]);
  }
  hit.push({s:hit.length?hit[hit.length-1].e:0,e:fidx,i:idx});
});
var bg=new THREE.BufferGeometry();
bg.setAttribute('position',new THREE.Float32BufferAttribute(bp,3));
bg.setAttribute('color',new THREE.Float32BufferAttribute(bc,3));
bg.setIndex(bi);bg.computeVertexNormals();
var bmat=new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide});
var buildingMesh=new THREE.Mesh(bg,bmat);
buildingMesh.renderOrder=5;scene.add(buildingMesh);
console.log('buildings mesh faces',fidx,'hit ranges',hit.length);

/* ---------- 6. 沙盘底座 ---------- */
var baseG=new THREE.BoxGeometry(W+18,9,H+18);
var baseM=new THREE.Mesh(baseG,new THREE.MeshLambertMaterial({color:0x101f30}));
baseM.position.set(0,-5.2,0);scene.add(baseM);
var edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(W+18,9,H+18)),
  new THREE.LineBasicMaterial({color:0x3b7fa8}));edge.position.copy(baseM.position);scene.add(edge);

/* ---------- 7. 标注 ---------- */
var labBox=document.getElementById('labels'),labels=[];
D.poi.forEach(function(p){
  var e=document.createElement('div');e.className='lab'+(p.n.indexOf('白堤')>=0?' hot':'');
  e.textContent=p.n;labBox.appendChild(e);
  labels.push({e:e,v:V(p.p[0],p.p[1],(p.z||0)+1.5)});
});
D.dikes.forEach(function(d){
  if(d.n.indexOf('白堤')<0)return;
  var m=d.p[Math.floor(d.p.length/2)],e=document.createElement('div');
  e.className='lab hot';e.textContent='白堤';labBox.appendChild(e);
  labels.push({e:e,v:V(m[0],m[1],LAKE/ZEX+2.4)});
});

/* ---------- 8. 相机与交互（自写轨道控制） ---------- */
var st={th:-0.62,ph:0.62,dist:1250,tx:0,ty:12,tz:0};
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
  var dx=e.clientX-drag.x,dy=e.clientY-drag.y;
  drag.x=e.clientX;drag.y=e.clientY;
  if(drag.b===2||e.shiftKey){
    var sc=st.dist/900;
    var right=new THREE.Vector3().subVectors(camera.position,new THREE.Vector3(st.tx,st.ty,st.tz))
      .cross(camera.up).normalize();
    st.tx-=right.x*dx*sc;st.tz-=right.z*dx*sc;st.ty+=dy*sc;
  }else{st.th-=dx*0.005;st.ph=Math.max(0.10,Math.min(1.48,st.ph+dy*0.004));}
  applyCam();
});
cv.addEventListener('contextmenu',function(e){e.preventDefault();});
cv.addEventListener('wheel',function(e){e.preventDefault();
  st.dist=Math.max(180,Math.min(3200,st.dist*(1+Math.sign(e.deltaY)*0.11)));applyCam();},{passive:false});
addEventListener('resize',function(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);});

/* ---------- 9. 点选构件 ---------- */
var ray=new THREE.Raycaster(),ndc=new THREE.Vector2();
var rightPanel=document.getElementById('right'),rbody=document.getElementById('rbody');
function pick(e){
  ndc.x=e.clientX/innerWidth*2-1;ndc.y=-(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(ndc,camera);
  var its=ray.intersectObject(buildingMesh,false);
  if(!its.length){rightPanel.classList.remove('show');return;}
  var fi=its[0].faceIndex,rec=null;
  for(var i=0;i<hit.length;i++){if(fi>=hit[i].s&&fi<hit[i].e){rec=hit[i];break;}}
  if(!rec){rightPanel.classList.remove('show');return;}
  showInfo(D.buildings[rec.i]);
}
function showInfo(b){
  var at=b.at||{},rows='';
  var NAME={name:'名称','name:en':'英文名',building:'建筑类型',amenity:'设施',historic:'文保',
    tourism:'旅游',office:'办公',shop:'商业','addr:street':'街道','addr:housenumber':'门牌',
    'roof:shape':'屋顶形式','building:levels':'标注层数',height:'标注高度'};
  var kv=[['构件类型','IfcBuildingElementProxy / OSM way'],['OSM ID','way/'+b.id],
    ['层数',b.lv+' 层'],['模型高度',(b.h*4).toFixed(1)+' m'],['占地',b.a.toLocaleString()+' m²'],
    ['高度来源',b.s],['坐标','WGS84 · cos(30.245°) 修正']];
  kv.forEach(function(x){rows+='<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';});
  var tg='';
  Object.keys(NAME).forEach(function(k){if(at[k])tg+='<div><span>'+NAME[k]+'</span>'+at[k]+'</div>';});
  rbody.innerHTML='<div class="rname">'+(b.n||'未命名建筑')+'</div>'+
    '<div class="rtype">OSM BUILDING · '+b.k.toUpperCase()+'</div>'+rows+
    (tg?'<div class="divider"></div><div class="ptitle">原始标签 · TAGS</div><div class="tags">'+tg+'</div>':'');
  rightPanel.classList.add('show');
}
document.getElementById('rclose').onclick=function(){rightPanel.classList.remove('show');};

/* ---------- 10. 图层 / 按钮 ---------- */
var LY=[['地形 · DEM',terrainMesh,1,'#3d7a52'],['水面 · 湖泊',waterMesh,1,'#1a6f9c'],
  ['道路 · 路网',roadMesh,1,'#5b7080'],['堤 · 白堤苏堤',dikeMesh,1,'#efe6c8'],
  ['建筑 · 构件',buildingMesh,1,'#6ba8c8'],['地名标注',null,1,'#dff1ff']];
var layBox=document.getElementById('layers');
LY.forEach(function(o,i){
  var d=document.createElement('label');d.className='ly';
  d.innerHTML='<input type="checkbox" checked data-i="'+i+'"><span class="sw" style="background:'+o[3]+'"></span>'+o[0];
  layBox.appendChild(d);
});
function setLayer(i,on){
  if(LY[i][1])LY[i][1].visible=on;
  else labels.forEach(function(l){l.e.style.display=on?'':'none';});
}
layBox.addEventListener('change',function(e){setLayer(+e.target.dataset.i,e.target.checked);});
function setMode(mode){
  ['btnAll','btnSkel','btnTop'].forEach(function(id){document.getElementById(id).classList.remove('on');});
  document.getElementById(mode).classList.add('on');
  if(mode==='btnSkel'){
    setLayer(4,false);
    [0,1,2,3,5].forEach(function(i){setLayer(i,true);});
    st.th=-0.62;st.ph=1.30;st.dist=1600;st.tx=0;st.ty=0;st.tz=0;applyCam();
    document.getElementById('tip').textContent='骨架验收：湖泊 / 山体 / 路网 / 白堤苏堤 — 确认比例与位置后再叠建筑';
  }else if(mode==='btnTop'){
    setLayer(4,true);
    st.th=0;st.ph=1.47;st.dist=1750;st.tx=0;st.ty=0;st.tz=0;applyCam();
    document.getElementById('tip').textContent='正射俯视：核对轮廓、路网与湖岸线';
  }else{
    setLayer(4,true);
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    st.th=-0.62;st.ph=0.62;st.dist=1250;st.tx=0;st.ty=12;st.tz=0;applyCam();
    document.getElementById('tip').textContent='拖动旋转 · 滚轮缩放 · 右键平移 · 单击建筑查看属性';
  }
  // 同步复选框
  layBox.querySelectorAll('input').forEach(function(cb,i2){
    cb.checked=LY[i2][1]?LY[i2][1].visible:true;
  });
}
document.getElementById('btnAll').onclick=function(){setMode('btnAll');};
document.getElementById('btnSkel').onclick=function(){setMode('btnSkel');};
document.getElementById('btnTop').onclick=function(){setMode('btnTop');};

/* ---------- 11. 楼层剖切 ---------- */
var cut=document.getElementById('cut'),cutv=document.getElementById('cutv');
cut.oninput=function(){
  var t=+cut.value/100;
  if(t>=0.999){bmat.clippingPlanes=[];cutv.textContent='不限';}
  else{
    var maxh=90/4*ZEX;
    var yy=(0.15+0.85*t)*maxh;
    clip.constant=yy;
    bmat.clippingPlanes=[clip];bmat.needsUpdate=true;
    cutv.textContent='≤ '+(yy/ZEX*4).toFixed(0)+' m（约 '+Math.round(yy/ZEX*4/3.2)+' 层）';
  }
};

/* ---------- 12. 搜索定位 ---------- */
function locate(){
  var q=document.getElementById('q').value.trim();if(!q)return;
  var hitb=null;
  for(var i=0;i<D.buildings.length;i++){if(D.buildings[i].n&&D.buildings[i].n.indexOf(q)>=0){hitb=D.buildings[i];break;}}
  if(!hitb){
    for(var i=0;i<D.poi.length;i++){if(D.poi[i].n.indexOf(q)>=0){hitb={p:D.poi[i].p,n:D.poi[i].n};break;}}
  }
  if(!hitb){document.getElementById('tip').textContent='未找到「'+q+'」，试试：楼外楼 / 白堤 / 孤山';return;}
  var cx=hitb.p[0],cy=hitb.p[1];
  // 对建筑用质心
  if(hitb.c){cx=(hitb.c[0]-M.bbox[0])*M.kx/M.scale;cy=(hitb.c[1]-M.bbox[1])*M.ky/M.scale;}
  st.tx=cx-HALF_W;st.tz=-(cy-HALF_H);st.ty=0;st.dist=430;st.ph=0.72;st.th=-0.55;applyCam();
  document.getElementById('tip').textContent='已定位：'+hitb.n;
  if(hitb.a)showInfo(hitb);
}
document.getElementById('go').onclick=locate;
document.getElementById('q').addEventListener('keydown',function(e){if(e.key==='Enter')locate();});

/* ---------- 13. 左栏统计 / 图例 / 说明 ---------- */
var K=[['建筑构件',M.n_building,'栋'],['具名建筑',M.named,'栋'],['道路里程',M.road_km,'km'],
  ['水域面积',M.water_km2,'km²'],['建筑占地',M.bld_km2,'km²'],['OSM 原始',(M.osm_bytes/1048576).toFixed(2),'MB']];
document.getElementById('kpis').innerHTML=K.map(function(x){
  return '<div class="kpi"><b>'+x[1]+'<i>'+x[2]+'</i></b><span>'+x[0]+'</span></div>';}).join('');
var LEG=[['#3d7a52','林地 / 山体'],['#1a6f9c','湖泊水面'],['#5b7080','道路'],
  ['#efe6c8','白堤 / 苏堤'],['#6ba8c8','一般建筑'],['#f7c86a','具名建筑']];
document.getElementById('legend').innerHTML=LEG.map(function(x){
  return '<span class="it"><i class="box" style="background:'+x[0]+'"></i>'+x[1]+'</span>';}).join('');
document.getElementById('srcbox').innerHTML=
  '<em>数据链路</em>：OpenStreetMap / Overpass API（真实矢量轮廓）→ 按 id 去重、校验坐标与闭合 → '+
  '经纬度转平面（经度 × cos 30.245° = 96,167 m/°）→ 1 场景单位 = 4 m → 先铺 DEM / 水面 / 路网骨架，再挤出建筑。<br>'+
  '<em>地形</em>：Copernicus DEM + ESA WorldCover（VoxCity 5 m 栅格降采样）。<br>'+
  '<span class="warn">注意：OSM 中国区 2,422 栋里仅 10 栋标注层数、1 栋标注高度；其余高度取自 VoxCity / Overture 并按用途推定，仅作体量示意，不是实测楼高。</span><br>'+
  '<em>合规</em>：WGS84，仅本地可视化；对外发布需 GCJ-02 转换与国内合规底图 / 审图号。';
function tick(){
  var d=new Date();
  document.getElementById('clk').textContent=d.toTimeString().slice(0,8);
  document.getElementById('date').textContent=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+
    String(d.getDate()).padStart(2,'0')+'  周'+'日一二三四五六'[d.getDay()];
}
tick();setInterval(tick,1000);

/* ---------- 14. 渲染循环 ---------- */
var tmp=new THREE.Vector3();
function loop(){
  requestAnimationFrame(loop);
  labels.forEach(function(l){
    tmp.copy(l.v).project(camera);
    var vis=tmp.z<1&&tmp.z>-1;
    l.e.style.display=vis?'':'none';
    if(vis){l.e.style.left=(tmp.x*0.5+0.5)*innerWidth+'px';l.e.style.top=(-tmp.y*0.5+0.5)*innerHeight+'px';}
  });
  renderer.render(scene,camera);
}
loop();
window.__TDBG={scene:scene,camera:camera,buildingMesh:buildingMesh,terrainMesh:terrainMesh,
  hit:hit,ray:ray,pick:pick,THREE:THREE,st:st,applyCam:applyCam};
var ld=document.getElementById('loading');ld.style.opacity=0;setTimeout(function(){ld.remove();},600);
})();
</script>
</body>
</html>
'''

html = HTML.replace('__THREE__', three).replace('__DATA__', data)
outp = os.path.join(OUT, '西湖_数字孪生.html')
open(outp, 'w', encoding='utf-8').write(html)
print('OK ->', outp, '%.2f MB' % (os.path.getsize(outp)/1024/1024))
