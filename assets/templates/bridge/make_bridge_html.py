#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 three.js + 江东大桥孪生数据 + 桥梁大屏 UI 拼成离线单文件 HTML"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out')
three = open(os.path.join(HERE,'three.min.js'), encoding='utf-8').read().replace('</script','<\\/script')
data  = open(os.path.join(HERE,'bridge_data.json'), encoding='utf-8').read().replace('</script','<\\/script')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>杭州江东大桥 · 桥梁数字孪生</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#060d16;color:#dce8f5;
  font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif;-webkit-font-smoothing:antialiased}
#app{position:relative;width:100%;height:100%}
canvas#gl{position:absolute;inset:0;display:block}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 44%,transparent 38%,rgba(2,7,14,.62) 100%)}
.scan{position:absolute;inset:0;pointer-events:none;opacity:.20;
  background:repeating-linear-gradient(0deg,transparent 0 3px,rgba(90,170,255,.05) 3px 4px)}
header{position:absolute;top:0;left:0;right:0;height:76px;display:flex;align-items:center;
  padding:0 26px;background:linear-gradient(180deg,rgba(5,13,24,.97),rgba(5,13,24,0));
  border-bottom:1px solid rgba(96,168,232,.16);pointer-events:none;z-index:6}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:34px;height:34px;border:1.5px solid #4fd0e0;border-radius:8px;position:relative;
  box-shadow:0 0 18px rgba(79,208,224,.35) inset,0 0 12px rgba(79,208,224,.2)}
.logo::before,.logo::after{content:"";position:absolute;background:#4fd0e0}
.logo::before{left:50%;top:6px;bottom:6px;width:1.5px;transform:translateX(-50%)}
.logo::after{top:50%;left:6px;right:6px;height:1.5px;transform:translateY(-50%)}
h1{font-size:19px;font-weight:600;letter-spacing:2px;color:#eaf5ff}
.sub{font-size:10.5px;color:#6f8aa6;letter-spacing:1.3px;margin-top:3px}
.hright{margin-left:auto;display:flex;align-items:center;gap:20px;text-align:right}
.clock{font-size:22px;font-weight:300;letter-spacing:1px;color:#bfe3ff;font-variant-numeric:tabular-nums}
.clock small{font-size:11px;color:#64809c;display:block;letter-spacing:1px}
.badge{font-size:11px;padding:5px 11px;border:1px solid rgba(79,208,224,.4);border-radius:20px;
  color:#7ee0e8;background:rgba(79,208,224,.07);letter-spacing:.5px}
.panel{position:absolute;z-index:5;background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);
  border-radius:10px;backdrop-filter:blur(14px);box-shadow:0 12px 40px rgba(0,0,0,.45)}
#left{top:92px;left:22px;width:274px;padding:15px 15px 13px;max-height:calc(100% - 190px);
  display:flex;flex-direction:column}
.ptitle{font-size:11.5px;color:#8fb6d8;letter-spacing:2px;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.ptitle::before{content:"";width:3px;height:12px;background:#4fd0e0;border-radius:2px;box-shadow:0 0 8px #4fd0e0}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.kpi{background:rgba(30,58,88,.34);border:1px solid rgba(90,150,210,.13);border-radius:7px;padding:8px 9px}
.kpi b{display:block;font-size:19px;font-weight:500;color:#7fe3f0;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi b i{font-size:10px;font-style:normal;color:#7d9ab5;margin-left:2px}
.kpi span{font-size:9.5px;color:#7793ad;letter-spacing:.4px}
.divider{height:1px;background:rgba(90,150,210,.15);margin:12px 0 10px;flex:none}
.layers{display:grid;gap:1px}
.ly{display:flex;align-items:center;gap:8px;font-size:11px;color:#a8c2da;padding:4px 5px;border-radius:5px;cursor:pointer}
.ly:hover{background:rgba(80,150,220,.09)}
.ly input{appearance:none;width:13px;height:13px;border:1px solid #4a7398;border-radius:3px;position:relative;cursor:pointer;flex:none}
.ly input:checked{background:#3fbdd2;border-color:#3fbdd2}
.ly input:checked::after{content:"";position:absolute;left:4px;top:1px;width:3px;height:7px;
  border:solid #06131f;border-width:0 2px 2px 0;transform:rotate(45deg)}
.sw{width:9px;height:9px;border-radius:2px;flex:none}
.btnrow{display:flex;gap:5px;margin-top:10px;flex:none}
.btn{flex:1;text-align:center;font-size:10.5px;padding:7px 2px;border-radius:6px;cursor:pointer;
  border:1px solid rgba(90,160,220,.28);background:rgba(40,90,140,.16);color:#a9cbe6;transition:.18s}
.btn:hover{background:rgba(70,160,220,.3);color:#fff;border-color:#5ec8e0}
.btn.on{background:rgba(63,189,210,.24);border-color:#4fd0e0;color:#bff4fb}
.src{font-size:10px;line-height:1.75;color:#7996b1;overflow:auto;max-height:112px}
.src em{font-style:normal;color:#a9c9e4}
.src .warn{color:#e8b478}
#parts{flex:none}
#plist{overflow:auto;max-height:150px;border:1px solid rgba(90,150,210,.14);border-radius:6px;
  background:rgba(10,24,42,.5)}
.pi{display:flex;align-items:center;gap:7px;font-size:10.5px;color:#9fbad2;padding:5px 8px;
  cursor:pointer;border-bottom:1px solid rgba(90,150,210,.07)}
.pi:hover{background:rgba(70,160,220,.16);color:#eaf7ff}
.pi .tag{font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(79,208,224,.14);color:#7fd9e6;flex:none}
.pi .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pi .st{margin-left:auto;color:#5f88a8;font-size:9.5px;flex:none}

#right{top:92px;right:22px;width:272px;padding:16px;display:none;max-height:calc(100% - 190px);overflow:auto}
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
.legend{background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:10px 13px;backdrop-filter:blur(14px);font-size:10px;color:#91aec8;max-width:520px}
.legend .row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.legend .it{display:flex;align-items:center;gap:5px;white-space:nowrap}
.legend .box{width:10px;height:10px;border-radius:2px}
.tools{background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);border-radius:9px;
  padding:10px 13px;backdrop-filter:blur(14px);min-width:250px}
.tools label{font-size:10px;color:#8fb0cc;display:flex;justify-content:space-between;margin-bottom:6px}
.tools label b{color:#7fe3f0;font-weight:500}
input[type=range]{width:100%;height:4px;appearance:none;background:linear-gradient(90deg,#3fbdd2,#2a5878);
  border-radius:3px;outline:none;cursor:pointer}
input[type=range]::-webkit-slider-thumb{appearance:none;width:13px;height:13px;border-radius:50%;
  background:#9ff0fa;box-shadow:0 0 8px #4fd0e0;cursor:pointer}
.search{margin-left:auto;display:flex;gap:6px;background:rgba(8,18,32,.88);border:1px solid rgba(90,150,210,.2);
  border-radius:9px;padding:6px 8px;backdrop-filter:blur(14px)}
.search input{background:transparent;border:0;outline:0;color:#dceaf7;font-size:11px;width:136px}
.search input::placeholder{color:#5c7893}
.search button{background:rgba(63,189,210,.2);border:1px solid rgba(79,208,224,.4);color:#9fe9f2;
  border-radius:5px;padding:4px 10px;font-size:11px;cursor:pointer}
#labels{position:absolute;inset:0;pointer-events:none;z-index:4;overflow:hidden}
.lab{position:absolute;transform:translate(-50%,-100%);font-size:10.5px;color:#dff1ff;white-space:nowrap;
  text-shadow:0 1px 5px #000,0 0 10px rgba(0,0,0,.9);letter-spacing:.4px;opacity:.93}
.lab::after{content:"";position:absolute;left:50%;top:100%;width:1px;height:10px;
  background:linear-gradient(rgba(160,220,255,.8),transparent)}
.lab.hot{color:#ffd98a;font-weight:600;font-size:11.5px}
.lab.span{color:#a9d8ea;font-size:10px;opacity:.85}
#north{position:absolute;right:26px;bottom:120px;z-index:5;width:50px;height:50px;border-radius:50%;
  border:1px solid rgba(90,150,210,.28);background:rgba(8,18,32,.7);text-align:center;pointer-events:none}
#north .ar{font-size:19px;color:#7fe3f0;line-height:29px}
#north .tx{font-size:9px;color:#7f9db8;letter-spacing:1px}
#scale{position:absolute;left:24px;bottom:98px;z-index:5;font-size:10px;color:#8fadc6;pointer-events:none}
#scale .bar{height:5px;border:1px solid #8fadc6;border-top:0;width:88px;margin-bottom:3px}
#tip{position:absolute;left:50%;top:84px;transform:translateX(-50%);z-index:7;font-size:11px;
  color:#9fc4dd;background:rgba(8,18,32,.82);border:1px solid rgba(90,150,210,.2);
  padding:6px 14px;border-radius:16px;letter-spacing:.4px;pointer-events:none}
#loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:20;
  background:#060d16;color:#7fe3f0;font-size:13px;letter-spacing:3px;transition:opacity .5s}
</style>
</head>
<body>
<div id="app">
  <canvas id="gl"></canvas><div class="vig"></div><div class="scan"></div>
  <div id="labels"></div>
  <header>
    <div class="brand"><div class="logo"></div>
      <div><h1>杭州江东大桥 · 桥梁数字孪生</h1>
      <div class="sub">JIANGDONG BRIDGE DIGITAL TWIN &nbsp;·&nbsp; OSM VECTOR + COPERNICUS DEM + 设计参数构件重建</div></div>
    </div>
    <div class="hright">
      <div class="badge">钱江九桥 · 自锚式空间缆悬索桥</div>
      <div class="clock"><span id="clk">--:--:--</span><small id="date">----</small></div>
    </div>
  </header>

  <div class="panel" id="left">
    <div class="ptitle">桥梁概览 · BRIDGE STATS</div>
    <div class="kpis" id="kpis"></div>
    <div class="divider"></div>
    <div class="ptitle">图层控制 · LAYERS</div>
    <div class="layers" id="layers"></div>
    <div class="btnrow">
      <div class="btn on" id="btnAll">桥梁主视</div>
      <div class="btn" id="btnSkel">验收骨架</div>
      <div class="btn" id="btnTop">俯视</div>
      <div class="btn" id="btnWide">全景沙盘</div>
    </div>
    <div class="divider"></div>
    <div class="ptitle" id="parts">构件清单 · ELEMENTS</div>
    <div id="plist"></div>
    <div class="divider"></div>
    <div class="src" id="srcbox"></div>
  </div>

  <div class="panel" id="right">
    <div class="close" id="rclose">✕</div>
    <div class="ptitle">构件属性 · ELEMENT</div>
    <div id="rbody"></div>
  </div>

  <div id="north"><div class="ar">▲</div><div class="tx">N</div></div>
  <div id="scale"><div class="bar"></div><span id="scaletx">500 m</span></div>
  <div id="tip">拖动旋转 · 滚轮缩放 · 右键平移 · 单击桥构件 / 建筑查看属性</div>

  <div id="bottom">
    <div class="legend"><div class="row" id="legend"></div></div>
    <div class="tools">
      <label>高度剖切 <b id="cutv">不限</b></label>
      <input type="range" id="cut" min="0" max="100" value="100">
      <div style="margin-top:6px;font-size:9.5px;color:#6f8ba6">向下拖动逐层剖开，查看桥面 / 主缆 / 墩台标高关系</div>
    </div>
    <div class="search"><input id="q" placeholder="搜索构件 / 建筑 / 地名"><button id="go">定位</button></div>
  </div>
  <div id="loading">正在铺设钱塘江地理骨架 …</div>
</div>

<script>__THREE__</script>
<script>window.__TWIN__=__DATA__;</script>
<script>
(function(){
'use strict';
if(!window.THREE){document.getElementById('loading').textContent='three.js 未加载';return;}
THREE.ColorManagement && (THREE.ColorManagement.enabled=false);
var D=window.__TWIN__, M=D.meta, BD=D.bridge, BM=M.bridge;
var W=M.w,H=M.h,ZEX=3.2,BEX=2.0,WVIS=1.7;
var LAKEZ=0.4;                               // 江面场景高程（DEM 江面约 1.5 m / 4）
var DECKZ=BD.deckZ, HALF_W=W/2, HALF_H=H/2;
function V(x,y,h){return new THREE.Vector3(x-HALF_W,(h||0)*ZEX,-(y-HALF_H));}

var cv=document.getElementById('gl');
var renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));
renderer.setSize(innerWidth,innerHeight);
renderer.setClearColor(0x060d16,1);
renderer.localClippingEnabled=true;
var scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x060d16,0.00062);
var camera=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,1,9000);
var clip=new THREE.Plane(new THREE.Vector3(0,-1,0),10000);
var clipped=[];
scene.add(new THREE.AmbientLight(0xb8d4f0,0.9));
var sun=new THREE.DirectionalLight(0xfff0d8,1.2);sun.position.set(-380,640,320);scene.add(sun);
var fill=new THREE.DirectionalLight(0x66aaff,0.38);fill.position.set(430,240,-400);scene.add(fill);

/* ---------- 1. 地形骨架（DEM + WorldCover 配色，江面用 DEM<3m 判定） ---------- */
var T=D.terrain,nx=T.nx,ny=T.ny;
var tp=[],tc=[],ti=[];
var LC={10:[0.20,0.42,0.29],20:[0.30,0.48,0.30],30:[0.42,0.50,0.32],40:[0.46,0.47,0.33],
        50:[0.33,0.38,0.43],60:[0.40,0.40,0.38],80:[0.07,0.22,0.34],90:[0.30,0.44,0.38],95:[0.32,0.46,0.42]};
for(var r=0;r<ny;r++)for(var c=0;c<nx;c++){
  var i=r*nx+c, px=c/(nx-1)*W, py=r/(ny-1)*H;
  var z=T.lc[i]===80?LAKEZ:T.z[i];
  var v=V(px,py,z);tp.push(v.x,v.y,v.z);
  var col=LC[T.lc[i]]||LC[50];
  var sh=0.80+Math.min(T.z[i],40)/40*0.40;
  tc.push(col[0]*sh,col[1]*sh,col[2]*sh);
}
for(var r=0;r<ny-1;r++)for(var c=0;c<nx-1;c++){
  var a=r*nx+c,b=a+1,d=a+nx,e=d+1;ti.push(a,d,b,b,d,e);
}
var tg=new THREE.BufferGeometry();
tg.setAttribute('position',new THREE.Float32BufferAttribute(tp,3));
tg.setAttribute('color',new THREE.Float32BufferAttribute(tc,3));
tg.setIndex(ti);tg.computeVertexNormals();
var terrainMesh=new THREE.Mesh(tg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
scene.add(terrainMesh);

/* 地形高程插值（未乘 ZEX） */
function terrainZ(px,py){
  var fx=Math.max(0,Math.min(nx-1.001,px/W*(nx-1)));
  var fy=Math.max(0,Math.min(ny-1.001,py/H*(ny-1)));
  var c0=Math.floor(fx),r0=Math.floor(fy),tx=fx-c0,ty=fy-r0;
  var i00=r0*nx+c0,i10=i00+1,i01=i00+nx,i11=i01+1;
  function z(i){return T.lc[i]===80?LAKEZ:T.z[i];}
  return (z(i00)*(1-tx)+z(i10)*tx)*(1-ty)+(z(i01)*(1-tx)+z(i11)*tx)*ty;
}

/* ---------- 2. 江面（DEM 低地水格，与地形配准） ---------- */
var G=D.waterGrid,gnx=G.nx,gny=G.ny,wp=[],wi=[];
for(var r=0;r<gny;r++)for(var c=0;c<gnx;c++){
  if(!G.m[r*gnx+c])continue;
  var x0=c/(gnx-1)*W,x1=(c+1)/(gnx-1)*W,y0=r/(gny-1)*H,y1=(r+1)/(gny-1)*H;
  var base=wp.length/3;
  var a=V(x0,y0,LAKEZ+0.05),b=V(x1,y0,LAKEZ+0.05),
      d=V(x1,y1,LAKEZ+0.05),e=V(x0,y1,LAKEZ+0.05);
  wp.push(a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,e.x,e.y,e.z);
  wi.push(base,base+1,base+2,base,base+2,base+3);
}
var wg=new THREE.BufferGeometry();
wg.setAttribute('position',new THREE.Float32BufferAttribute(wp,3));wg.setIndex(wi);wg.computeVertexNormals();
var waterMesh=new THREE.Mesh(wg,new THREE.MeshPhongMaterial({color:0x16618c,shininess:95,
  specular:0x7adcff,transparent:true,opacity:.9,side:THREE.DoubleSide}));
scene.add(waterMesh);

/* ---------- 3. 次要水系 + 路网 ---------- */
function buildRibbon(lines,widthFn,hFn,meshColor,opacity){
  var vp=[],vc=[],vi=[],k=0;
  var hf=typeof hFn==='function'?hFn:function(){return hFn;};
  lines.forEach(function(o){
    var pts=o.p,wd=widthFn(o),col=o.col||meshColor;
    for(var i=0;i<pts.length-1;i++){
      var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
      if(L<0.05)continue;
      var ox=-dy/L*wd/2,oy=dx/L*wd/2;
      var za=Math.max(hf(a[0],a[1]),terrainZ(a[0],a[1])+0.07);
      var zb=Math.max(hf(b[0],b[1]),terrainZ(b[0],b[1])+0.07);
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
var RC={7:[0.52,0.60,0.67],6:[0.44,0.53,0.61],5:[0.39,0.47,0.55],4:[0.35,0.42,0.50],
        3:[0.31,0.38,0.45],2:[0.28,0.34,0.40],1:[0.27,0.36,0.35]};
D.roads.forEach(function(r){r.col=RC[r.k]||RC[2];});
var roadMesh=buildRibbon(D.roads,function(o){return {7:6,6:5.5,5:5,4:4,3:3,2:2,1:1.3}[o.k]||2;},
   function(){return LAKEZ+0.10;},null,1);
scene.add(roadMesh);
var wlines=D.waterPoly.map(function(w){return {p:w.p,col:[0.16,0.48,0.62]};});
var wpolyMesh=wlines.length?buildRibbon(wlines,function(){return 0.1;},function(){return LAKEZ+0.12;},null,1):null;
if(wpolyMesh){wpolyMesh.renderOrder=2;scene.add(wpolyMesh);}

/* ---------- 4. 桥梁构件：统一几何容器 ---------- */
function GeomBuilder(){
  this.p=[];this.c=[];this.i=[];this.f=0;this.hit=[];this._pid=-1;
}
GeomBuilder.prototype.pid=function(v){this._pid=v;};
GeomBuilder.prototype.tri=function(a,b,c,col){
  var base=this.p.length/3;
  this.p.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
  for(var q=0;q<3;q++)this.c.push(col[0],col[1],col[2]);
  this.i.push(base,base+1,base+2);
  var prev=this.f; this.f++;
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
  var mat=new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide});
  var m=new THREE.Mesh(g,mat);m.renderOrder=5;
  m.userData.hit=this.hit;m.userData.mat=mat;
  clipped.push(mat);return m;
};
/* 沿折线的立体带（顶面 + 两侧立面） */
function deckBand(g,pts,width,zTop,zBot,col,pid){
  g.pid(pid);
  var side=[col[0]*0.68,col[1]*0.68,col[2]*0.68];
  for(var i=0;i<pts.length-1;i++){
    var a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
    if(L<0.05)continue;
    var ox=-dy/L*width/2,oy=dx/L*width/2;
    var A=V(a[0]+ox,a[1]+oy,zTop),B=V(a[0]-ox,a[1]-oy,zTop),
        Cc=V(b[0]-ox,b[1]-oy,zTop),Dd=V(b[0]+ox,b[1]+oy,zTop);
    g.quad(A,B,Cc,Dd,col);
    var Ab=V(a[0]+ox,a[1]+oy,zBot),Bb=V(a[0]-ox,a[1]-oy,zBot),
        Cb=V(b[0]-ox,b[1]-oy,zBot),Db=V(b[0]+ox,b[1]+oy,zBot);
    g.quad(Ab,Db,Cb,Bb,side);                       // 底面
    g.quad(A,Ab,Bb,B,side);                         // 端侧（可省，保持立体）
    g.quad(A,Dd,Db,Ab,side);g.quad(B,Bb,Cb,Cc,side);
  }
}
/* 细带（主缆 / 吊索 / 标线） */
function thinBand(g,pts,width,col,pid,zFixed){
  g.pid(pid);
  for(var i=0;i<pts.length-1;i++){
    var a=pts[i],b=pts[i+1];
    var za=zFixed?a[2]:0, zb=zFixed?b[2]:0;
    var dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy);
    if(L<0.02)continue;
    var ox=-dy/L*width/2,oy=dx/L*width/2;
    var A=V(a[0]+ox,a[1]+oy,za),B=V(a[0]-ox,a[1]-oy,za),
        Cc=V(b[0]-ox,b[1]-oy,zb),Dd=V(b[0]+ox,b[1]+oy,zb);
    g.quad(A,B,Cc,Dd,col);
    // 侧面加一点厚度，避免从侧面看不见
    var A2=V(a[0]+ox,a[1]+oy,za-0.12),B2=V(a[0]-ox,a[1]-oy,za-0.12),
        C2=V(b[0]-ox,b[1]-oy,zb-0.12),D2=V(b[0]+ox,b[1]+oy,zb-0.12);
    g.quad(A,A2,D2,Dd,col);
  }
}
/* 矩形柱（桥塔 / 桥墩） */
function pillar(g,cx,cy,ux,uy,nx,ny,w,d,z0,z1,col,pid){
  g.pid(pid);
  var hx=ux*d/2,hy=uy*d/2,wx=nx*w/2,wy=ny*w/2;
  var P=[[cx-hx-wx,cy-hy-wy],[cx+hx-wx,cy+hy-wy],
         [cx+hx+wx,cy+hy+wy],[cx-hx+wx,cy-hy+wy]];
  var top=[],bot=[];
  for(var i=0;i<4;i++){top.push(V(P[i][0],P[i][1],z1));bot.push(V(P[i][0],P[i][1],z0));}
  for(var i=0;i<4;i++){
    var j=(i+1)%4,sh=0.72+0.26*Math.abs(Math.cos(i*1.2));
    var sc=[col[0]*sh,col[1]*sh,col[2]*sh];
    g.quad(bot[i],bot[j],top[j],top[i],sc);
  }
  g.quad(top[0],top[1],top[2],top[3],[col[0]*1.1,col[1]*1.1,col[2]*1.1]);
}
function pidAt(d){
  for(var i=0;i<BD.spanPids.length;i++){
    var s=BD.spanPids[i];if(d>=s.s&&d<=s.e)return s.pid;
  }
  for(var i=0;i<BD.apprPids.length;i++){
    var s=BD.apprPids[i];if(d>=s.s&&d<=s.e)return s.pid;
  }
  return -1;
}
/* 桥面折线按里程切片 */
function slice(pts,d0,d1){
  var out=[];
  for(var i=0;i<pts.length;i++){
    var d=i*15;
    if(d>=d0&&d<=d1)out.push(pts[i]);
  }
  return out;
}

var deck=new GeomBuilder(), cablesG=new GeomBuilder(), piersG=new GeomBuilder();
var GOLD=[0.98,0.76,0.38], STEEL=[0.62,0.72,0.80], BEAM=[0.44,0.56,0.66],
    APPR=[0.40,0.50,0.58], CABLE=[1.00,0.80,0.42], HANG=[0.78,0.87,0.94],
    TOWER=[0.88,0.92,0.96], PIER=[0.50,0.58,0.64], WHITE=[0.92,0.94,0.90];

/* 4a. 桥面（分离式双幅钢箱梁）按桥型分色 */
BD.spans.concat([]).forEach(function(sp,i){
  var col=sp.k==='susp'?GOLD:(sp.k==='rigid'?STEEL:BEAM);
  var A=slice(BD.deckA,sp.s,sp.e),B=slice(BD.deckB,sp.s,sp.e);
  var dw=4.7*WVIS;
  if(A.length>1)deckBand(deck,A,dw,DECKZ,DECKZ-0.88,col,sp.pid!==undefined?sp.pid:pidAt((sp.s+sp.e)/2));
  if(B.length>1)deckBand(deck,B,dw,DECKZ,DECKZ-0.88,col,sp.pid!==undefined?sp.pid:pidAt((sp.s+sp.e)/2));
});
/* 引桥桥面：从岸边渐降到地面 */
BD.apprPids.forEach(function(ap){
  var A=slice(BD.deckA,ap.s,ap.e),B=slice(BD.deckB,ap.s,ap.e);
  var head=ap.s===0;
  var zs=A.map(function(p,i){
    var d=ap.s+i*15,t=(d-ap.s)/(ap.e-ap.s);
    return head?LAKEZ+1.2+(DECKZ-LAKEZ-1.2)*t:DECKZ-(DECKZ-LAKEZ-1.2)*t;
  });
  deck.pid(ap.pid);
  for(var i=0;i<A.length-1;i++){
    var ptsA=[A[i],A[i+1]],ptsB=[B[i],B[i+1]];
    thinBand(deck,ptsA.map(function(p,k){return [p[0],p[1],zs[k]];}),4.7*WVIS,APPR,ap.pid,true);
    thinBand(deck,ptsB.map(function(p,k){return [p[0],p[1],zs[k]];}),4.7*WVIS,APPR,ap.pid,true);
  }
});
/* 桥面车道标线（每幅中心线，暖白虚线） */
BD.deck.forEach(function(p,i){});
(function(){
  var A=BD.deckA,B=BD.deckB;
  deck.pid(-1);
  for(var i=0;i<A.length-1;i+=2){
    thinBand(deck,[[A[i][0],A[i][1],DECKZ+0.04],[A[i+1][0],A[i+1][1],DECKZ+0.04]],0.18,WHITE,-1,true);
    thinBand(deck,[[B[i][0],B[i][1],DECKZ+0.04],[B[i+1][0],B[i+1][1],DECKZ+0.04]],0.18,WHITE,-1,true);
  }
})();
var deckMesh=deck.mesh();scene.add(deckMesh);

/* 4b. 桥塔（独柱）+ 主缆 + 吊索 + 锚碇 */
BD.towers.forEach(function(t){
  pillar(cablesG,t.p[0],t.p[1],t.ux,t.uy,t.nx,t.ny,1.15*WVIS,1.05*WVIS,
         DECKZ-1.0,DECKZ+BM.tower_h,TOWER,t.pid);
  cablesG.pid(t.pid);
  var a=V(t.p[0]-t.nx*0.8,t.p[1]-t.ny*0.8,DECKZ+BM.tower_h),
      b=V(t.p[0]+t.nx*0.8,t.p[1]+t.ny*0.8,DECKZ+BM.tower_h),
      c=V(t.p[0]+t.nx*0.8,t.p[1]+t.ny*0.8,DECKZ+BM.tower_h+0.35),
      d=V(t.p[0]-t.nx*0.8,t.p[1]-t.ny*0.8,DECKZ+BM.tower_h+0.35);
  cablesG.quad(a,b,c,d,GOLD);
});
BD.cables.forEach(function(cb){thinBand(cablesG,cb.p,0.95,CABLE,cb.pid,true);});
BD.hangers.forEach(function(h){thinBand(cablesG,[h.a,h.b],0.24,HANG,h.pid,true);});
BD.anchors.forEach(function(a){
  pillar(cablesG,a.p[0],a.p[1],1,0,0,1,2.0,1.6,DECKZ-2.6,DECKZ-0.2,STEEL,a.pid);
});
var cableMesh=cablesG.mesh();scene.add(cableMesh);

/* 4c. 桥墩 */
BD.piers.forEach(function(p){
  var z0=Math.min(terrainZ(p.p[0],p.p[1]),LAKEZ)-0.2;
  var w=p.main?2.2:1.15,d=p.main?2.6:1.3;
  pillar(piersG,p.p[0],p.p[1],1,0,0,1,w,d,z0,DECKZ-1.0,p.main?STEEL:PIER,p.pid);
});
var pierMesh=piersG.mesh();scene.add(pierMesh);

/* ---------- 5. 建筑：真实 footprint 挤出 ---------- */
var bp=[],bc=[],bi=[],hitB=[],fB=0;
var BCOL=[[0.34,0.58,0.76],[0.42,0.66,0.82],[0.52,0.74,0.87],[0.64,0.80,0.89],[0.78,0.82,0.76]];
var NAMED=[1.00,0.72,0.34];
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
  var h=Math.max(b.h*BEX,0.6),base=b.bz||0;
  for(var i=0;i<poly.length;i++)base=Math.max(base,terrainZ(poly[i][0],poly[i][1]));
  base-=0.1;
  var ci=Math.min(BCOL.length-1,Math.floor(h/4)),col=b.n?NAMED:BCOL[ci];
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
var bmat=new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide});
clipped.push(bmat);
var buildingMesh=new THREE.Mesh(bg,bmat);buildingMesh.renderOrder=5;scene.add(buildingMesh);

/* ---------- 6. 沙盘底座 ---------- */
var baseG=new THREE.BoxGeometry(W+18,10,H+18);
var baseM=new THREE.Mesh(baseG,new THREE.MeshLambertMaterial({color:0x0e1c2c}));
baseM.position.set(0,-5.7,0);scene.add(baseM);
var edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(W+18,10,H+18)),
  new THREE.LineBasicMaterial({color:0x3b7fa8}));edge.position.copy(baseM.position);scene.add(edge);

/* ---------- 7. 标注 ---------- */
var labBox=document.getElementById('labels'),labels=[];
function addLabel(n,p,z,cls,bridge){
  var e=document.createElement('div');e.className='lab'+(cls?' '+cls:'');
  e.textContent=n;labBox.appendChild(e);
  labels.push({e:e,v:V(p[0],p[1],z),bridge:!!bridge});
}
D.poi.forEach(function(p){addLabel(p.n,p.p,p.z,p.hot?'hot':'',false);});
BD.spans.forEach(function(sp,i){
  var p=BD.deck[Math.round((sp.s+sp.e)/2/15)];
  if(p)addLabel(sp.n.replace('跨江','').replace('自锚式','')+' '+Math.round(sp.l)+'m',p,
    DECKZ-5.2+(i%2)*1.4,'span',true);
});
BD.towers.forEach(function(t){addLabel(t.n.split('·').pop().trim(),t.p,DECKZ+BM.tower_h+2.0,'',true);});

/* ---------- 8. 相机与交互 ---------- */
var st={th:-0.39,ph:0.35,dist:560,tx:-69,ty:DECKZ*ZEX*0.62,tz:4};
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
  }else{st.th-=dx*0.005;st.ph=Math.max(0.09,Math.min(1.48,st.ph+dy*0.004));}
  applyCam();
});
cv.addEventListener('contextmenu',function(e){e.preventDefault();});
cv.addEventListener('wheel',function(e){e.preventDefault();
  st.dist=Math.max(140,Math.min(3600,st.dist*(1+Math.sign(e.deltaY)*0.11)));applyCam();},{passive:false});
addEventListener('resize',function(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);});

/* ---------- 9. 点选构件 / 建筑 ---------- */
var ray=new THREE.Raycaster(),ndc=new THREE.Vector2();
var rightPanel=document.getElementById('right'),rbody=document.getElementById('rbody');
var pickMeshes=[deckMesh,cableMesh,pierMesh,buildingMesh];
function pick(e){
  ndc.x=e.clientX/innerWidth*2-1;ndc.y=-(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(ndc,camera);
  var its=ray.intersectObjects(pickMeshes,false);
  if(!its.length){rightPanel.classList.remove('show');return;}
  var o=its[0],fi=o.faceIndex,rec=null,part=null;
  if(o.object===buildingMesh){
    for(var i=0;i<hitB.length;i++){if(fi>=hitB[i].s&&fi<hitB[i].e){showBuilding(D.buildings[hitB[i].i]);return;}}
    rightPanel.classList.remove('show');return;
  }
  var hh=o.object.userData.hit;
  for(var i=0;i<hh.length;i++){if(fi>=hh[i].s&&fi<hh[i].e&&hh[i].pid>=0){part=BD.parts[hh[i].pid];break;}}
  if(!part){rightPanel.classList.remove('show');return;}
  showPart(part);
}
var KIND={girder:'主梁 / 加劲梁',tower:'桥塔',cable:'主缆 / 锚固',hanger:'吊索',
          pier:'墩台 / 基础',approach:'引桥'};
function showPart(p){
  var kv=[['构件类型',KIND[p.k]||p.k],['构件编号','BRG-'+String(p.id+1).padStart(3,'0')],
    ['中心桩号',p.st],['里程范围','K'+(p.s/1000).toFixed(3)+' – K'+(p.e/1000).toFixed(3)],
    ['区段长度',p.l.toFixed(0)+' m'],['材料 / 构造',p.mat||'—'],['技术规格',p.spec||'—'],
    ['数据来源',p.src]];
  var rows=kv.map(function(x){return '<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';}).join('');
  rbody.innerHTML='<div class="rname">'+p.n+'</div><div class="rtype">BRIDGE ELEMENT · '+p.k.toUpperCase()+'</div>'+rows+
    '<div class="divider"></div><div style="font-size:10px;color:#e8b478;line-height:1.7">'+
    '桥梁几何按公开设计参数重建，可点选、可剖切、可定位；非竣工 BIM，不含构件级应力/监测属性。</div>';
  rightPanel.classList.add('show');
}
function showBuilding(b){
  var at=b.at||{};
  var kv=[['构件类型','OSM building / way'],['OSM ID','way/'+b.id],['层数',b.lv+' 层'],
    ['模型高度',(b.h*4).toFixed(1)+' m'],['占地',b.a.toLocaleString()+' m²'],['高度来源',b.s]];
  var rows=kv.map(function(x){return '<div class="kv"><k>'+x[0]+'</k><v>'+x[1]+'</v></div>';}).join('');
  var tg='';Object.keys(at).forEach(function(k){tg+='<div class="kv"><k>'+k+'</k><v>'+at[k]+'</v></div>';});
  rbody.innerHTML='<div class="rname">'+(b.n||'未命名建筑')+'</div>'+
    '<div class="rtype">OSM BUILDING · '+b.k.toUpperCase()+'</div>'+rows+
    (tg?'<div class="divider"></div><div class="ptitle">原始标签</div>'+tg:'');
  rightPanel.classList.add('show');
}
document.getElementById('rclose').onclick=function(){rightPanel.classList.remove('show');};

/* ---------- 10. 图层 / 模式 ---------- */
var LY=[['地形 · DEM',terrainMesh,1,'#3d7a52'],['钱塘江 · 水面',waterMesh,1,'#16618c'],
  ['次要水系',wpolyMesh,1,'#2a7a9e'],['道路 · 路网',roadMesh,1,'#5b7080'],
  ['桥面 · 双幅箱梁',deckMesh,1,'#d8b45c'],['缆索系统 · 塔/缆/吊索',cableMesh,1,'#ffcc6a'],
  ['墩台 · 基础',pierMesh,1,'#8a99a6'],['建筑 · 构件',buildingMesh,1,'#6ba8c8'],
  ['地名 / 跨径标注',null,1,'#dff1ff']];
var layBox=document.getElementById('layers');
LY.forEach(function(o,i){
  var d=document.createElement('label');d.className='ly';
  d.innerHTML='<input type="checkbox" checked data-i="'+i+'"><span class="sw" style="background:'+o[3]+'"></span>'+o[0];
  layBox.appendChild(d);
});
var bridgeLabelsHidden=false;
function setLayer(i,on){
  if(LY[i][1])LY[i][1].visible=on;
  else{
    bridgeLabelsHidden=!on||document.getElementById('btnSkel').classList.contains('on');
    labels.forEach(function(l){
      l.e.style.display=(on&&!(bridgeLabelsHidden&&l.bridge))?'':'none';
    });
  }
}
layBox.addEventListener('change',function(e){setLayer(+e.target.dataset.i,e.target.checked);});
function setMode(mode){
  ['btnAll','btnSkel','btnTop','btnWide'].forEach(function(id){document.getElementById(id).classList.remove('on');});
  document.getElementById(mode).classList.add('on');
  if(mode==='btnSkel'){
    [4,5,6,7].forEach(function(i){setLayer(i,false);});
    [0,1,2,3,8].forEach(function(i){setLayer(i,true);});
    st.th=-0.55;st.ph=1.32;st.dist=1750;st.tx=0;st.ty=0;st.tz=0;applyCam();
    document.getElementById('tip').textContent='骨架验收：钱塘江江面 / 两岸地形 / 路网 — 确认江岸线与比例后再叠桥梁构件';
  }else if(mode==='btnTop'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    st.th=0;st.ph=1.47;st.dist=2000;st.tx=0;st.ty=0;st.tz=0;applyCam();
    document.getElementById('tip').textContent='正射俯视：核对桥轴线、跨径分段与江岸线';
  }else if(mode==='btnWide'){
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    st.th=-0.55;st.ph=0.62;
    st.dist=1750;st.tx=40;st.ty=12;st.tz=20;applyCam();
    document.getElementById('tip').textContent='全景沙盘：钱塘江两岸地形 / 436 km 路网 / 455 栋建筑与 4,332 m 桥梁的关系';
  }else{
    for(var i=0;i<LY.length;i++)setLayer(i,true);
    st.th=-0.39;st.ph=0.35;st.dist=560;st.tx=-69;st.ty=DECKZ*ZEX*0.62;st.tz=4;applyCam();
    document.getElementById('tip').textContent='拖动旋转 · 滚轮缩放 · 右键平移 · 单击桥构件 / 建筑查看属性';
  }
  layBox.querySelectorAll('input').forEach(function(cb,i2){cb.checked=LY[i2][1]?LY[i2][1].visible:true;});
}
['btnAll','btnSkel','btnTop','btnWide'].forEach(function(id){
  document.getElementById(id).onclick=function(){setMode(id);};});

/* ---------- 11. 高度剖切 ---------- */
var cut=document.getElementById('cut'),cutv=document.getElementById('cutv');
cut.oninput=function(){
  var t=+cut.value/100;
  if(t>=0.999){clipped.forEach(function(m){m.clippingPlanes=[];});cutv.textContent='不限';}
  else{
    var maxh=(BM.deck_z+BM.tower_h)*ZEX+8;
    var yy=(0.06+0.94*t)*maxh;clip.constant=yy;
    clipped.forEach(function(m){m.clippingPlanes=[clip];m.needsUpdate=true;});
    cutv.textContent='≤ '+(yy/ZEX*4).toFixed(0)+' m（椭球高基准）';
  }
};

/* ---------- 12. 构件清单 / 搜索定位 ---------- */
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
  focus(p.c[0],p.c[1],DECKZ*0.7,430,0.40,-0.70);
  document.getElementById('tip').textContent='已定位：'+p.n+' · '+p.st;
  showPart(p);
}
function locate(){
  var q=document.getElementById('q').value.trim();if(!q)return;
  for(var i=0;i<BD.parts.length;i++)if(BD.parts[i].n.indexOf(q)>=0){locatePart(BD.parts[i]);return;}
  for(var i=0;i<D.buildings.length;i++)if(D.buildings[i].n&&D.buildings[i].n.indexOf(q)>=0){
    var b=D.buildings[i],cx=(b.c[0]-M.bbox[0])*M.kx/M.scale,cy=(b.c[1]-M.bbox[1])*M.ky/M.scale;
    focus(cx,cy,4,330,0.62,-0.55);
    document.getElementById('tip').textContent='已定位：'+b.n;showBuilding(b);return;}
  for(var i=0;i<D.poi.length;i++)if(D.poi[i].n.indexOf(q)>=0){
    focus(D.poi[i].p[0],D.poi[i].p[1],D.poi[i].z,430,0.62,-0.55);
    document.getElementById('tip').textContent='已定位：'+D.poi[i].n;return;}
  document.getElementById('tip').textContent='未找到「'+q+'」，试试：主塔 / 主缆 / 悬索桥 / 江东大道';
}
document.getElementById('go').onclick=locate;
document.getElementById('q').addEventListener('keydown',function(e){if(e.key==='Enter')locate();});

/* ---------- 13. 左栏统计 / 图例 / 说明 ---------- */
var K=[['全长',BM.total,'m'],['跨江桥梁',BM.river,'m'],['主跨',260,'m'],
  ['独柱主塔',BM.n_tower,'座'],['吊索',BM.n_hanger,'根'],['桥墩',BM.n_pier,'座'],
  ['可点选构件',BM.n_part,'个'],['建筑',M.n_building,'栋'],['路网',M.road_km,'km'],
  ['江面',M.water_km2,'km²']];
document.getElementById('kpis').innerHTML=K.map(function(x){
  return '<div class="kpi"><b>'+x[1]+'<i>'+x[2]+'</i></b><span>'+x[0]+'</span></div>';}).join('');
var LEG=[['#3d7a52','地形 / 绿地'],['#16618c','钱塘江'],['#5b7080','道路'],
  ['#d8b45c','悬索桥主梁'],['#8a99a6','连续梁 / 刚构'],['#ffcc6a','主缆 / 吊索'],
  ['#e8eaf2','独柱主塔'],['#6ba8c8','一般建筑'],['#f7c86a','具名建筑']];
document.getElementById('legend').innerHTML=LEG.map(function(x){
  return '<span class="it"><i class="box" style="background:'+x[0]+'"></i>'+x[1]+'</span>';}).join('');
document.getElementById('srcbox').innerHTML=
  '<em>数据链路</em>：Overpass 拉取 OSM 真实矢量（1.21 MB，1,810 要素，按 id 去重、校验闭合）→ '+
  '经纬度转平面（经度 × cos 30.32° = 96,094 m/°）→ 1 场景单位 = 4 m → '+
  '先铺 Copernicus DEM / 江面 / 路网骨架，再叠桥梁构件与建筑。<br>'+
  '<em>江面判定</em>：ESA WorldCover 10 m 在强涌潮河段把江面误判为建成区，改用 DEM 低地（&lt;3 m）判定，'+
  '实测跨江段 2,060 m，与公开资料 2,248 m 吻合。<br>'+
  '<span class="warn">注意：桥面轴线长 2,925 m 取自 OSM 真实矢量；两端引桥按设计全长 4,332 m 示意延伸。'+
  '桥塔、空间主缆、吊索、墩台按公开设计参数重建，非竣工 BIM；443 栋建筑高度按用途推定。'+
  '为便于观察，垂直放大 '+ZEX.toFixed(1)+'×、桥面横向放大 '+WVIS.toFixed(1)+'×，均为可视化夸张，不作量测。</span><br>'+
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
    var vis=tmp.z<1&&tmp.z>-1&&!(bridgeLabelsHidden&&l.bridge);
    l.e.style.display=vis?'':'none';
    if(vis){l.e.style.left=(tmp.x*0.5+0.5)*innerWidth+'px';l.e.style.top=(-tmp.y*0.5+0.5)*innerHeight+'px';}
  });
  renderer.render(scene,camera);
}
loop();
window.__TDBG={scene:scene,camera:camera,deckMesh:deckMesh,cableMesh:cableMesh,
  pierMesh:pierMesh,buildingMesh:buildingMesh,ray:ray,st:st,applyCam:applyCam,
  parts:BD.parts,THREE:THREE,labels:labels};
var ld=document.getElementById('loading');ld.style.opacity=0;setTimeout(function(){ld.remove();},600);
})();
</script>
</body>
</html>
'''
html = HTML.replace('__THREE__', three).replace('__DATA__', data)
outp = os.path.join(OUT, '江东大桥_数字孪生.html')
open(outp,'w',encoding='utf-8').write(html)
print('OK ->', outp, '%.2f MB' % (os.path.getsize(outp)/1024/1024))
