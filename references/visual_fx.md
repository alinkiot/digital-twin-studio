# 写实质感增强配方（可选增强层）

> 目标：把「能看的矢量沙盘」推到「像一张效果图」。这一层**不改变任何数据、坐标与构件**，
> 只换材质、光照、天空、水面与 UI 质感，因此对量测精度零影响，也随时可整层摘掉。
> 完整可运行的实现见 `assets/templates/sandbox/`（武汉长江大桥沙盘，四套模板里画质最完整的一套）。

## 0. 性价比排序（先做上面的）

| 优先级 | 措施 | 观感提升 | 代价 |
| --- | --- | --- | --- |
| ★★★ | `MeshLambertMaterial` → `MeshStandardMaterial` + `PCFSoftShadowMap` 软阴影 | 体积感、投影、材质分层 | 低；注意阴影相机范围 |
| ★★★ | 渐变天空穹顶（ShaderMaterial）+ 远山剪影 + 日轮 | 背景不再是死黑纯色 | 低 |
| ★★★ | 自定义水面着色器（菲涅尔 / 流动法线 / 桥影 / 距离雾） | 江面从色块变成水 | 中；要反复目检收敛 |
| ★★ | 三档光影氛围 + 日照方位滑块 | 一张场景出三种情绪，且能演示光照 | 中；需统一改所有颜色 |
| ★★ | 夜景点光 `THREE.Points` + 城市窗光 | 夜景档立刻有故事 | 低 |
| ★ | UI 入场动效 / 微光描边 / 按钮扫光 / 大气辉光 | 大屏「贵」一点 | 低，纯 CSS |
| ★ | SSAO / Bloom / ACES 色调映射 | 更接近离线渲染 | 高：需 EffectComposer，SwiftShader 下明显变慢 |
| ★ | 程序化贴图（沥青 / 钢轨 / 窗格） | 近景真实 | 中：需 UV 与纹理生成 |
| — | PMREM 环境贴图 / 平面反射 / 竣工 BIM / 倾斜摄影 | 真正可用于量测 | 高，属另一个量级 |

**结论**：最见效的是软阴影与天空/水面，而不是继续堆几何。别一上来就做后处理。

## 1. 两种接入方式

### A. 直接用片段库（推荐新项目）

`scripts/visual_fx.py` 返回可直接内联的 CSS / JS，保持单文件离线：

```python
import sys; sys.path.insert(0, '$S/scripts')
from visual_fx import inline_fx

fx_css, fx_js = inline_fx({
    'water': {'center': [cx, cz], 'axis': [ux, uz], 'normal': [nx, nz],
              'shadowWidth': deck_w * 1.05, 'spanLen': span,
              'bridgeHeight': deck_z * zex, 'shadow': True},
    'lamps': lamp_positions,             # [[x, y, z, r, g, b], ...]
    'shadowExtent': 760, 'skyRadius': 9000,
})
html = html.replace('</head>', fx_css + '</head>')
html = html.replace('</body>', fx_js + '</body>')
```

页面初始化完成后：

```javascript
var fx = TwinFX.install({
    THREE: THREE, scene: scene, camera: camera, renderer: renderer,
    waterMesh: waterMesh,       // 不传则只加天空/灯光，不换水面材质
    lamps: FX_LAMPS,            // 可选；也可写在 cfg.lamps 里
    lights: true, sky: true, ui: true
});
function loop(){ requestAnimationFrame(loop); fx.tick(); renderer.render(scene, camera); }
// fx.setMood('dusk') / fx.applySun(0.36) / fx.mood()
```

契约与开关：

- `THREE` / `scene` 必传；`camera` / `renderer` 可省（省略时取全局同名变量）。
- `lights:false` 跳过建灯（场景已有灯光时）；也可传 `lights:{amb,hemi,sun,fill}` 复用已有灯对象。
- `sky:false` 不加天空穹顶；`ui:false` 不绑定按钮与滑块。
- 所有 DOM 绑定**防御式**：`app / tip / sun / sunv / moodTech / moodDusk / moodNight`
  缺失也不会报错（清单见 `visual_fx.required_dom_ids()`）。
- `scene.fog` 存在才会被氛围调制；水面 mesh 需要 `color` 顶点属性（江心深 / 近岸浅渐变由
  `waterTone()` 一类的函数生成）。

自检（CI / 提交前）：

```bash
python3 -c "import sys;sys.path.insert(0,'scripts');from visual_fx import build_fx;open('/tmp/fx.js','w').write(build_fx()[1])"
node --check /tmp/fx.js
```

### B. 抄参考实现（推荐深度定制）

`assets/templates/sandbox/make_wuhan_html.py` 里各段都有段号注释，可整段搬：

`0. 天空穹顶` / `水面 ShaderMaterial` / `MeshStandardMaterial` 各 mesh /
`MOOD` 三档参数表 / `setMood()` / `applySun()` / `lampPts` / `loop()` 里的 `uTime`。

## 2. 光照与阴影

```javascript
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
var amb  = new THREE.AmbientLight(0xc4dcf4, 1.00);
var hemi = new THREE.HemisphereLight(0xbcd9f2, 0x172a20, 0.48); // 天空色 / 地面色
var sun  = new THREE.DirectionalLight(0xfff2dc, 1.30);
var fill = new THREE.DirectionalLight(0x77b4ff, 0.40);            // 冷色补光，救暗部
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
var shc = sun.shadow.camera;
shc.left = -760; shc.right = 760; shc.top = 760; shc.bottom = -760;
shc.near = 20; shc.far = 2600; shc.updateProjectionMatrix();
sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.9; sun.shadow.radius = 2;
```

- 地形 / 建筑 / 桥体：`MeshStandardMaterial({vertexColors:true, roughness:0.58~0.96,
  metalness:0.0~0.10})`；地形与底座 `receiveShadow=true`，桥体与建筑再加 `castShadow=true`。
- 阴影正交相机的 `left/right/...` 必须覆盖主角范围，否则远处直接没有影子；
  但范围越大阴影越糊，1024 贴图配 ±760 场景单位是实测的平衡点。
- **ShaderMaterial 不会自动接阴影 / 雾 / tone mapping**：天空与水面要么手写距离雾与高光，
  要么确认它们本来就不需要接收阴影。

## 3. 天空穹顶

半径 9000 的 `SphereGeometry(9000,32,20)` + `BackSide` + `depthWrite:false,depthTest:false`，
`renderOrder=-1000`、`frustumCulled=false`（相机 `far` 要大于半径）。片元里：

- 天顶 / 地平线 / 地面三段颜色按 `d.y` 混合（`pow(h,0.55)` 让渐变更自然）；
- 远山剪影：`atan(d.z,d.x)` 的多频正弦叠加成山脊线，`smoothstep` 压出一条暗带；
- 日轮：`pow(max(dot(d,sunDir),0),320)*1.35 + pow(...,18)*0.22 + pow(...,4)*0.05`；
- 地平线暖雾：`uHaze*exp(-abs(h)*11.0)*0.38`。

**必须让 `uSunDir` 与主光方向一致**，否则「太阳在东、影子往东」一眼假。

## 4. 水面着色器（最容易翻车的一段）

片元顺序：域扭曲 → 波形 → 菲涅尔 → 主角投影 → 收敛的高光 → 距离雾。

```glsl
vec2 w = p + vec2(8.0*sin(p.y*0.017+t*0.10), 7.0*sin(p.x*0.021-t*0.13));
float a = sin(w.x*0.13+w.y*0.052+t*0.85)+0.6*sin(w.x*0.29-w.y*0.11-t*1.35);
float b = sin(w.x*0.061-w.y*0.17+t*0.52)+0.5*sin(w.y*0.23+w.x*0.09+t*1.1);
vec3 n = normalize(vec3(a*0.055,1.0,b*0.050));
float fres = pow(1.0-max(dot(n,V),0.0),2.2);
vec3 col = vC*uTint*0.88;
col *= 1.0 + 0.018*sin(a*0.9+b*0.6) + 0.010*sin(b*1.7-a*0.4);
col = mix(col,uSky,fres*0.55);
```

主角投影（低成本高收益）：把主角高度按主光方位投到水面，再沿主轴 / 法向做带状遮罩：

```glsl
vec2 off = clamp(-uSunDir.xz*(uBridgeH/max(uSunDir.y,0.45)), vec2(-110.0), vec2(110.0));
float nrmS = dot(q,uAxisN)-dot(off,uAxisN);
float band = 1.0-smoothstep(uShadowW*0.55,uShadowW*1.3,abs(nrmS));
float spanMask = step(-uSpanLen,alongS)*step(alongS,uSpanLen);
col *= 1.0-0.52*band*spanMask*uShadowI;
```

高光务必收敛：`pow(sh,26)*0.12 + pow(sh,110)*0.38`，再乘 `(0.30+0.40*streak)*shad`。
指数太低会糊成一片，幅度太大会变成满江碎白斑；俯视机位下 `pow(sh,900)` 级别几乎看不见。

### 收敛记录（踩过的坑）

| 现象 | 原因 | 修复 |
| --- | --- | --- |
| 斜向江面出现等间距平行横条 / 雨丝 | 规则正弦或 `LineSegments` 流线阵列 → 摩尔纹 | 先做**域扭曲**再采样；删掉所有规则流线 |
| 黄昏档满江白色碎斑 | 低频涌浪幅度 0.06、高光系数过大 | 明暗只跟随波形本身，幅度降到 0.018 / 0.010；高光 ×0.3 |
| 陆地/建筑也有白碎斑 | 一度误判成阴影，实测关阴影后仍存在 → 是水面高光穿帮 | 隐藏水面 mesh 诊断，锁定来源再改 |
| 画中画里一条过曝白色横带 | 独立相机近距下日轮 + `Points` 灯点被放大 | 画中画渲染前临时 `lampPts.visible=false` 并压低日轮强度 |
| 无头截图底边露冷色带 | `innerHeight` 比窗口矮，根背景仍是旧清屏色 | `setMood()` 同步改 `html/body/#app` 的 background |

**不要**在水面加等间距短线流线；江心—近岸顶点色渐变 + 着色器波光已经足够。

## 5. 三档氛围与日照方位

`MOOD` 表按场景统一改：环境光、半球光、主日、补光、`scene.fog.color/density`、
`renderer.setClearColor`、天空 `uTop/uHor/uBot/uSunCol/uHaze/uSunI`、
水面 `uTint/uSky/uSunCol/uFogCol/uFogD/uSunI/uWave`、灯点显隐、`body.className`。

| 档 | 主日 | 雾 | 江面 tint | 灯点 | 用途 |
| --- | --- | --- | --- | --- | --- |
| 科技蓝 `tech` | `0xfff2dc / 1.06` | `0x0a1826 / 0.00042` | `0xffffff` | 关 | 默认大屏 |
| 写实黄昏 `dusk` | `0xffb45e / 1.32` | `0x2a2118 / 0.00052` | `0xffd9b0` | 关 | 出图 / 汇报 |
| 夜景灯光 `night` | `0x9db8ee / 0.34` | `0x050b18 / 0.00058` | `0x9fc4e8` | 开 | 氛围展示 |

日照滑块 `t∈[0,1]` → 主光绕 Y 轴一圈，同步 `skyU.uSunDir` 与 `waterU.uSunDir`，
于是日轮、江面高光、桥影一起移动。夜景档把 `uSunI` 压到 0.62、`skySun` 到 0.22，
避免「半夜出太阳」。

**新增 UI 行要同步放宽左侧面板 `max-height`**（本轮从 `calc(100% - 254px)` 改到
`calc(100% - 196px)`），否则构件清单被挤到滚动区外。

## 6. UI 微质感

`visual_fx.CSS_CHROME` 里是纯 CSS：面板入场（`translateY+opacity`）、
`.panel::before` 顶部微光、`.kpi` 金色描边、`.btn::after` 斜向扫光、
画中画 `sheen` 流光、`.atm` 大气辉光（`mix-blend-mode:screen`）、
黄昏 / 夜景两套面板配色。全部 `pointer-events:none`，不影响点选与拖拽。

DOM 层级建议：`.atm` z-index 1、`.vig` / `.scan` z-index 2、UI 面板 ≥5。

## 7. 验证清单

1. `node --check` 抽出的业务 JS；
2. `render_views.py` 全模式截图，抓 `Uncaught` 与 shader 编译告警；
3. `smoke_check.py` 11 项；
4. **三档氛围各出一张图目检**（科技蓝 / 黄昏 / 夜景），重点看江面碎斑、
   画中画过曝、面板是否被截断；
5. 纯净沙盘图（隐藏 UI + `.lab`、关画中画）再出黄昏版，检查底座四角是否全部入画、
   底边无冷色带。

## 8. 边界

这些全是**表达性渲染**，必须在页面数据来源块与说明文档里写明「不作量测」。
程序化材质 ≠ 竣工 BIM，平面投影桥影 ≠ 阴影贴图真值，顶点色渐变 ≠ 水深。
对外发布仍需 WGS84 → GCJ-02 转换与国内合规底图 / 审图号。
