#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""写实质感增强片段库（digital-twin-studio 可选增强层）。

把「界面更精美 / 更逼真」这一轮验证过的效果做成可直接复用的片段：
PBR 光照与软阴影、渐变天空穹顶 + 远山剪影 + 日轮、自定义水面着色器
（域扭曲波纹 / 菲涅尔 / 主角投影 / 日轮高光 / 距离雾）、三档光影氛围、
日照方位滑块、夜景灯点，以及大屏 UI 的入场动效与微光描边。

用法（在 make_*_html.py 里，把返回值内联进 HTML，保持单文件离线）：

    import sys; sys.path.insert(0, '$S/scripts')
    from visual_fx import inline_fx
    fx_css, fx_js = inline_fx({
        'water': {'center': [cx, cz], 'axis': [ux, uz], 'normal': [nx, nz],
                  'shadowWidth': deck_w * 1.05, 'spanLen': span,
                  'bridgeHeight': deck_z * zex, 'shadow': True},
        'lamps': lamp_positions,       # [[x, y, z, r, g, b], ...]
    })
    html = html.replace('</head>', '<style>' + fx_css + '</style></head>')
    html = html.replace('</body>', '<script>' + fx_js + '</script></body>')

页面初始化完成后调用一次：

    var fx = TwinFX.install({
        THREE: THREE, scene: scene, camera: camera, renderer: renderer,
        waterMesh: waterMesh,          // 可选：不传则只加天空/灯光，不换水面材质
        lights: true, sky: true, ui: true
    });

然后在渲染循环里 `fx.tick()`；需要切氛围 / 改日照时 `fx.setMood('dusk')` /
`fx.applySun(0.36)`。所有 DOM 绑定都是防御式的：页面没有对应按钮也不会报错。

设计约定见 references/visual_fx.md。片段本身只用 ES5 语法与 three.js r15x，
不依赖任何 CDN、构建工具或后处理库。
"""
import json

__all__ = ['CSS_CHROME', 'build_fx', 'inline_fx', 'required_dom_ids']

# ---------------------------------------------------------------- CSS 层
CSS_CHROME = r'''
/* ===== 大屏微质感：入场动效 / 面板微光 / 按钮扫光 / 大气辉光 ===== */
@keyframes tfxPanelIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
#left,#inset,#bottom>*{animation:tfxPanelIn .6s cubic-bezier(.2,.72,.2,1) both}
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
  animation:tfxSheen 6s linear infinite}
@keyframes tfxSheen{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
header::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,transparent,rgba(79,208,224,.55),transparent)}
.atm{position:absolute;inset:0;pointer-events:none;z-index:1;mix-blend-mode:screen;opacity:.9;
  background:radial-gradient(ellipse 68% 54% at 50% 34%,rgba(58,128,178,.16),transparent 72%),
             radial-gradient(ellipse 42% 36% at 16% 8%,rgba(92,180,224,.10),transparent 76%),
             radial-gradient(ellipse 40% 34% at 84% 12%,rgba(48,112,168,.10),transparent 76%)}
.vig{position:absolute;inset:0;pointer-events:none;z-index:2;
  background:radial-gradient(ellipse at 50% 42%,transparent 36%,rgba(2,6,12,.66) 100%)}
.scan{position:absolute;inset:0;pointer-events:none;z-index:2;opacity:.16;
  background:repeating-linear-gradient(0deg,transparent 0 3px,rgba(90,170,255,.05) 3px 4px)}
body.mood-dusk .panel{border-color:rgba(224,176,116,.28);background:rgba(24,18,13,.9)}
body.mood-dusk .ptitle{color:#d8b98c}
body.mood-dusk .ptitle::before{background:#e8b478;box-shadow:0 0 8px #e8b478}
body.mood-dusk .scan{opacity:.05}
body.mood-dusk .btn.on{background:rgba(232,180,120,.24);border-color:#e8b478;color:#ffe4b8}
body.mood-night .panel{background:rgba(5,11,24,.93);border-color:rgba(110,145,220,.26)}
body.mood-night .scan{opacity:.08}
'''.strip()

# ---------------------------------------------------------------- JS 层
_FX_JS = r'''
/* TwinFX v1.0 — 离线单文件 three.js 场景的写实质感增强层（ES5 / 无外部依赖） */
(function(){
'use strict';
var C=window.FXCFG||{};
function D(v,d){return v===undefined?d:v;}
function gid(id){return document.getElementById(id);}

var MOODS={
 tech:{amb:0xc4dcf4,ambI:1.14,hemiSky:0xbcd9f2,hemiGnd:0x172a20,hemiI:0.55,
   sun:0xfff2dc,sunI:1.06,fill:0x77b4ff,fillI:0.45,
   fog:0x0a1826,fogD:0.00042,clear:0x050b13,
   top:0x071a30,hor:0x1b4e68,bot:0x050d18,disc:0xffe6b8,haze:0.9,skySun:1.0,
   tint:0xffffff,wsky:0x2e7ba0,wsun:1.0,wave:1.0,lamps:false,
   tip:'科技蓝：冷色天光 + 软阴影 + 江面镜面波光 · 拖动旋转 / 单击构件查看属性'},
 dusk:{amb:0xffd9ad,ambI:0.90,hemiSky:0xffc98a,hemiGnd:0x3a2a1c,hemiI:0.72,
   sun:0xffb45e,sunI:1.32,fill:0x6f8fd0,fillI:0.40,
   fog:0x2a2118,fogD:0.00052,clear:0x17120e,
   top:0x243a5c,hor:0xd08a52,bot:0x2b1a12,disc:0xffd08a,haze:1.25,skySun:1.30,
   tint:0xffd9b0,wsky:0xc08a62,wsun:1.30,wave:0.95,lamps:false,
   tip:'写实黄昏：低角度暖阳 / 大气暖雾 / 江面金色反光 — 更接近真实摄影观感'},
 night:{amb:0x5b7bb0,ambI:0.54,hemiSky:0x4e78b8,hemiGnd:0x0d1424,hemiI:0.42,
   sun:0x9db8ee,sunI:0.34,fill:0x35508c,fillI:0.25,
   fog:0x050b18,fogD:0.00058,clear:0x030711,
   top:0x020610,hor:0x122c50,bot:0x02050c,disc:0xaac6ff,haze:0.6,skySun:0.22,
   tint:0x9fc4e8,wsky:0x1b3b68,wsun:0.62,wave:0.6,lamps:true,
   tip:'夜景灯光：桥面路灯 / 楼体窗光点亮，江面倒映冷色天光'}
};
if(C.moods){for(var mk in C.moods){if(C.moods.hasOwnProperty(mk)){MOODS[mk]=C.moods[mk];}}}

function skyUniforms(T){
  return {uTop:{value:new T.Color(0x071a30)},uHor:{value:new T.Color(0x1b4e68)},
    uBot:{value:new T.Color(0x050d18)},uSunCol:{value:new T.Color(0xffe6b8)},
    uSunDir:{value:new T.Vector3(-0.5,0.75,0.42).normalize()},
    uSunI:{value:1.0},uHaze:{value:0.9}};
}

function waterUniforms(T,W){
  W=W||{};
  return {uTime:{value:0},uTint:{value:new T.Color(0xffffff)},
    uSky:{value:new T.Color(0x2e7ba0)},uSunCol:{value:new T.Color(0xffe6b8)},
    uSunDir:{value:new T.Vector3(-0.5,0.75,0.42).normalize()},
    uFogCol:{value:new T.Color(0x050b13)},uFogD:{value:D(W.fogDensity,0.00042)},
    uSunI:{value:1.0},uWave:{value:1.0},uShadowI:{value:W.shadow===false?0.0:1.0},
    uAxisC:{value:new T.Vector2(W.center?W.center[0]:0,W.center?W.center[1]:0)},
    uAxisU:{value:new T.Vector2(W.axis?W.axis[0]:1,W.axis?W.axis[1]:0)},
    uAxisN:{value:new T.Vector2(W.normal?W.normal[0]:0,W.normal?W.normal[1]:1)},
    uShadowW:{value:D(W.shadowWidth,24)},uSpanLen:{value:D(W.spanLen,600)},
    uBridgeH:{value:D(W.bridgeHeight,45)}};
}

/* 水面片段：域扭曲波纹（避免摩尔纹）→ 菲涅尔 → 主角投影 → 收敛的日轮高光 → 距离雾 */
function waterFragment(){
  return [
    'varying vec3 vC;varying vec3 vW;',
    'uniform float uTime,uFogD,uSunI,uWave,uShadowI,uShadowW,uSpanLen,uBridgeH;',
    'uniform vec3 uTint,uSky,uSunCol,uSunDir,uFogCol;',
    'uniform vec2 uAxisC,uAxisU,uAxisN;',
    'void main(){',
    '  vec2 p=vW.xz;float t=uTime;',
    '  vec2 w=p+vec2(8.0*sin(p.y*0.017+t*0.10),7.0*sin(p.x*0.021-t*0.13));',
    '  float a=sin(w.x*0.13+w.y*0.052+t*0.85)+0.6*sin(w.x*0.29-w.y*0.11-t*1.35);',
    '  float b=sin(w.x*0.061-w.y*0.17+t*0.52)+0.5*sin(w.y*0.23+w.x*0.09+t*1.1);',
    '  vec3 n=normalize(vec3(a*0.055*uWave,1.0,b*0.050*uWave));',
    '  vec3 V=normalize(cameraPosition-vW);vec3 L=normalize(uSunDir);vec3 H=normalize(L+V);',
    '  float fres=pow(1.0-max(dot(n,V),0.0),2.2);',
    '  vec3 col=vC*uTint*0.88;',
    '  float swell=0.018*sin(a*0.9+b*0.6)+0.010*sin(b*1.7-a*0.4);',
    '  col*=1.0+swell;col=mix(col,uSky,fres*0.55);',
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
    '}'].join('\n');
}

function install(opt){
  opt=opt||{};
  var T=opt.THREE||window.THREE,scene=opt.scene;
  if(!T||!scene)throw new Error('TwinFX.install 需要 THREE 与 scene');
  var camera=opt.camera||window.camera,renderer=opt.renderer||window.renderer;
  var sunDir0=new T.Vector3(-0.5,0.75,0.42).normalize();
  var lights={},skyU=skyUniforms(T),waterU=waterUniforms(T,C.water);
  var lampPts=null,waterMat=null,moodNow='tech';

  /* 1) PBR 光照 + 软阴影。已有灯光的场景可传 lights:false 跳过。 */
  if(opt.lights!==false&&opt.lights!==null){
    lights.amb=new T.AmbientLight(0xc4dcf4,1.00);scene.add(lights.amb);
    lights.hemi=new T.HemisphereLight(0xbcd9f2,0x172a20,0.48);scene.add(lights.hemi);
    lights.sun=new T.DirectionalLight(0xfff2dc,1.30);scene.add(lights.sun);
    lights.fill=new T.DirectionalLight(0x77b4ff,0.40);
    lights.fill.position.set(460,260,-420);scene.add(lights.fill);
    var S=lights.sun;S.castShadow=true;S.shadow.mapSize.set(D(C.shadowMapSize,1024),D(C.shadowMapSize,1024));
    var shc=S.shadow.camera,e=D(C.shadowExtent,760);
    shc.left=-e;shc.right=e;shc.top=e;shc.bottom=-e;shc.near=20;shc.far=D(C.shadowFar,2600);
    shc.updateProjectionMatrix();
    S.shadow.bias=-0.0006;S.shadow.normalBias=0.9;S.shadow.radius=2;
    if(renderer){renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;}
  }else if(opt.lights&&opt.lights.amb){
    lights=opt.lights;
  }

  /* 2) 天空穹顶：天顶—地平线渐变 / 远山剪影 / 日轮与光晕 */
  if(opt.sky!==false){
    var skyMat=new T.ShaderMaterial({side:T.BackSide,depthWrite:false,depthTest:false,
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
    var sky=new T.Mesh(new T.SphereGeometry(D(C.skyRadius,9000),32,20),skyMat);
    sky.renderOrder=-1000;sky.frustumCulled=false;scene.add(sky);
  }

  /* 3) 水面：把传进来的水面 mesh 换成自定义 ShaderMaterial */
  if(opt.waterMesh){
    waterMat=new T.ShaderMaterial({uniforms:waterU,transparent:true,side:T.DoubleSide,
      vertexShader:[
        'attribute vec3 color;varying vec3 vC;varying vec3 vW;',
        'void main(){vC=color;vec4 w=modelMatrix*vec4(position,1.0);vW=w.xyz;',
        'gl_Position=projectionMatrix*viewMatrix*w;}'].join('\n'),
      fragmentShader:waterFragment()});
    opt.waterMesh.material=waterMat;
  }

  /* 4) 夜景灯点：坐标由调用方给出 [[x,y,z,r,g,b], ...] */
  var lamps=opt.lamps||C.lamps||[];
  if(lamps.length){
    var lp=[],lc=[];
    for(var i=0;i<lamps.length;i++){
      var q=lamps[i];lp.push(q[0],q[1],q[2]);
      lc.push(q.length>5?q[3]:1,q.length>5?q[4]:0.8,q.length>5?q[5]:0.48);
    }
    var lg=new T.BufferGeometry();
    lg.setAttribute('position',new T.Float32BufferAttribute(lp,3));
    lg.setAttribute('color',new T.Float32BufferAttribute(lc,3));
    lampPts=new T.Points(lg,new T.PointsMaterial({size:D(C.lampSize,12),sizeAttenuation:true,
      vertexColors:true,transparent:true,opacity:D(C.lampOpacity,0.42),
      depthWrite:false,blending:T.AdditiveBlending}));
    lampPts.visible=false;lampPts.renderOrder=8;scene.add(lampPts);
  }

  function setMood(k){
    if(!MOODS[k])return;var m=MOODS[k];moodNow=k;
    if(lights.amb){lights.amb.color.setHex(m.amb);lights.amb.intensity=m.ambI;}
    if(lights.hemi){lights.hemi.color.setHex(m.hemiSky);lights.hemi.groundColor.setHex(m.hemiGnd);lights.hemi.intensity=m.hemiI;}
    if(lights.sun){lights.sun.color.setHex(m.sun);lights.sun.intensity=m.sunI;}
    if(lights.fill){lights.fill.color.setHex(m.fill);lights.fill.intensity=m.fillI;}
    if(scene.fog){scene.fog.color.setHex(m.fog);scene.fog.density=m.fogD;}
    skyU.uTop.value.setHex(m.top);skyU.uHor.value.setHex(m.hor);skyU.uBot.value.setHex(m.bot);
    skyU.uSunCol.value.setHex(m.disc);skyU.uHaze.value=m.haze;skyU.uSunI.value=m.skySun;
    waterU.uTint.value.setHex(m.tint);waterU.uSky.value.setHex(m.wsky);
    waterU.uSunCol.value.setHex(m.disc);waterU.uFogCol.value.setHex(m.fog);
    waterU.uFogD.value=m.fogD;waterU.uSunI.value=m.wsun;waterU.uWave.value=m.wave;
    if(renderer)renderer.setClearColor(m.clear,1);
    /* 无头浏览器 innerHeight 常比截图窗口矮，根背景同步跟随清屏色才不会露冷色边 */
    var bg='#'+('000000'+m.clear.toString(16)).slice(-6);
    document.documentElement.style.background=bg;
    document.body.style.background=bg;
    var app=gid('app');if(app)app.style.background=bg;
    if(lampPts)lampPts.visible=!!m.lamps;
    document.body.className='mood-'+k;
    var ids=[['moodTech','tech'],['moodDusk','dusk'],['moodNight','night']];
    for(var j=0;j<ids.length;j++){
      var b=gid(ids[j][0]);if(b)b.classList.toggle('on',ids[j][1]===k);
    }
    var tip=gid('tip');if(tip)tip.textContent=m.tip;
  }

  /* 5) 日照方位：主光绕场景旋转，天空日轮 / 水面高光 / 主角投影同步移动 */
  function applySun(v){
    var t=(v===undefined?D(C.sun,0.36):v);
    var a=-Math.PI+t*2*Math.PI,R=D(C.sunRadius,780),H=D(C.sunHeight,660);
    if(lights.sun)lights.sun.position.set(Math.sin(a)*R,H,Math.cos(a)*R);
    var dir=lights.sun?lights.sun.position.clone().normalize():sunDir0;
    skyU.uSunDir.value.copy(dir);waterU.uSunDir.value.copy(dir);
    var deg=Math.round(t*360);
    var dt=(deg<45||deg>=315)?'偏北':deg<135?'偏东':deg<225?'偏南':'偏西';
    var lab=gid('sunv');if(lab)lab.textContent=deg+'° · '+dt;
    var sl=gid('sun');if(sl&&+sl.value!==Math.round(t*100))sl.value=Math.round(t*100);
  }

  if(opt.ui!==false){
    var pairs=[['moodTech','tech'],['moodDusk','dusk'],['moodNight','night']];
    for(var n=0;n<pairs.length;n++){
      (function(p){var b=gid(p[0]);if(b)b.onclick=function(){setMood(p[1]);};})(pairs[n]);
    }
    var slider=gid('sun');if(slider)slider.oninput=function(){applySun(+slider.value/100);};
  }
  applySun();setMood('tech');

  return {
    THREE:T,scene:scene,camera:camera,renderer:renderer,lights:lights,
    skyU:skyU,waterU:waterU,waterMaterial:waterMat,lampPts:lampPts,
    setMood:setMood,applySun:applySun,mood:function(){return moodNow;},
    tick:function(){waterU.uTime.value=performance.now()*0.001;}
  };
}

window.TwinFX={version:'1.0',install:install,moods:MOODS};
})();
'''.strip()


def build_fx(cfg=None):
    """返回 (css_text, js_text)。cfg 为可 JSON 序列化的配置字典。"""
    cfg = dict(cfg or {})
    prefix = 'var FXCFG=' + json.dumps(cfg, ensure_ascii=False, separators=(',', ':')) + ';\n'
    return CSS_CHROME, prefix + _FX_JS


def inline_fx(cfg=None):
    """返回可直接插入 HTML 的 (style_tag, script_tag)。"""
    css, js = build_fx(cfg)
    return '<style>\n' + css + '\n</style>\n', '<script>\n' + js + '\n</script>\n'


def required_dom_ids():
    """可选 UI 元素（全部是防御式绑定，缺失不影响 3D 效果）。"""
    return ['app', 'tip', 'sun', 'sunv', 'moodTech', 'moodDusk', 'moodNight']


if __name__ == '__main__':
    import sys
    css, js = inline_fx()
    sys.stdout.write(css + js)
