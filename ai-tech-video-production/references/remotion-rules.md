# Remotion Production Rules

用于 AI 科技口播视频的可编辑 Remotion 工程。

## Project Contract

推荐结构：

```text
remotion_project/
├── public/media/source_talking.mp4
├── public/media/motion/
├── public/media/images/
├── src/Video.tsx
├── src/timeline.json
├── scripts/validate-layering.mjs
├── docs/README.md
└── out/
```

`src/timeline.json` 是可编辑入口，至少包含：

- `fps`
- `width`
- `height`
- `durationSeconds`
- `source`
- `assetTransitions`
- `pip`
- `segments`

## Layering

工程必须保持三层：

1. 原口播视频底层：完整铺底。
2. 素材覆盖层：图片、动效、说明卡。
3. 原口播视频 PIP 层：只引用 `source_talking.mp4`。

禁止把素材文件放进 PIP 层。每次修改模板后运行图层校验脚本。

## Asset Layout Safe Area

非图片素材包括 HTML/Anime.js 动效、文字信息图、流程卡、图表、代码/窗口模拟。生成这些素材时必须预留顶部安全区：

- `Y=0-260`：只允许背景网格、光斑、粒子、弱装饰，不放可读文字、卡片、图标组、流程节点或主视觉。
- `Y=280-1080`：优先放核心标题、关键图形、流程节点、图表和主要动效。
- `Y=1080-1120`：缓冲区，只放非关键装饰，避免压到字幕安全区。
- `Y=1120-1360`：中间偏下字幕安全区；不放必须阅读的素材内容。
- 正文阶段右下 `X=720-1040, Y=1120-1660`：真人 PIP 保护区；素材核心信息不得进入。
- 开头前 `3 秒` 与结尾最后 `3 秒` 使用居中人物保护区，素材需要围绕人物重新排版；主标题优先放人物上方，短标签可放人物左右，不能压脸、胸口或字幕。

Remotion 实现时，不要让主内容容器从 `top: 0` 或 `top: 120` 开始。建议给非图片素材的主内容容器设置 `paddingTop >= 260`，或用明确的 `top: 280` / `translateY` 下移；抽帧时检查首个核心元素是否贴近上沿。

## Text Label Components

正文阶段禁止继续使用“发光小矩形框包文字”的短标签组件。该样式容易像后台按钮或表单控件，和 AI 科技口播的画面叙事冲突。

Remotion 模板应优先提供两类文本组件：

### SplitCompare

用于对比和反常识：

- 普通人 vs 超级个体
- 旧方式 vs 新方式
- 不是 A，而是 B
- 效率差距、认知差距、流程差距

实现建议：

- 左右或上下两栏，不使用卡片框；中间只用细线、光束、弱分割。
- 旧方式降亮、弱化或划线；新方式用信号绿/金色高亮。
- 每侧只放 `1` 个身份词 + `1` 个动作词，避免长句。
- 核心文字放在 `Y=280-1080`，右下 PIP 区保持干净。

### HudCoordinateList

用于步骤、特征、判断标准和执行顺序：

- `01 / 先给AI跑`
- `02 / 自己判断`
- `03 / 再做修正`

实现建议：

- 使用编号、1px 细线、坐标点、弱扫描光，不包矩形框。
- 每屏最多 `3-4` 条，单条 `2-6` 个汉字为宜。
- 坐标清单不要进入 `Y=1120-1360` 字幕区，不压右下 PIP。
- 如果内容超过容量，拆成下一段或删字，不缩成一堆小字。

## Dynamic PIP Defaults

默认使用三阶段动态 PIP：

1. `introHero`：开头前 `3 秒`，人物居中放大，但不全屏；背景继续展示钩子素材，人物周围可放 `2-4` 个短标签或一条钩子标题。
2. `bodyCorner`：正文阶段，人物平滑缩小并移动到右下角。
3. `outroHero`：最后 `3 秒`，人物平滑回到中央；背景继续展示结论素材，人物周围可放结论词、适用场景或提问辅助信息。

如果开头钩子或结尾收束的真实口播段不足 `3 秒`，使用真实时间线边界，不强行占满。居中强化出镜不能只剩人物，也不要直接使用全屏原口播。

推荐配置：

```json
{
  "pip": {
    "introHero": {"duration": 3, "x": 190, "y": 560, "width": 700, "height": 900, "radius": 42},
    "bodyCorner": {"x": 740, "y": 1340, "width": 300, "height": 400, "radius": 30},
    "outroHero": {"duration": 3, "x": 190, "y": 560, "width": 700, "height": 900, "radius": 42},
    "transitionFrames": 20
  }
}
```

正文右下 PIP：

```json
{
  "enabled": true,
  "x": 740,
  "y": 1340,
  "width": 300,
  "height": 400,
  "radius": 30,
  "borderWidth": 4,
  "borderColor": "rgba(255,255,255,0.72)"
}
```

规则：

- 开头和结尾居中人物建议占画面宽度约 `52%-68%`，保留背景素材和辅助信息，不做全屏纯人像。
- 居中人物周围的辅助信息必须短：最多一条主钩子/结论和 `2-4` 个短标签，不用满屏小字。
- 从居中到右下、从右下到居中的位移、尺寸和圆角变化必须连续插值，不能硬切。
- 近似 `3:4`，用 `object-fit: cover` 等比例裁切。
- 位置压低到右下角，给中间偏下字幕区让位。
- 不直接缩小 `9:16` 原视频。
- 上下可小范围裁剪，不能横向或纵向拉伸人像。

## Asset Transitions

相邻素材使用覆盖式淡入：

- 上一段素材保持 `opacity: 1` 到下一段开始覆盖。
- 下一段素材在上层淡入。
- 不做两段同时半透明的传统 crossfade，因为会漏出口播底图。

推荐配置：

```json
{
  "assetTransitions": {
    "crossfadeFrames": 10,
    "bridgeMaxGapSeconds": 2
  }
}
```

如果相邻素材之间空档小于等于 `bridgeMaxGapSeconds`，素材层应桥接空档，避免闪回原口播背景。

## Motion Playback

- `assetDuration` 存素材原始时长。
- 按口播段落时长计算 `playbackRate`，让素材尽量完整播放。
- 如果段落短到动效无法看懂，禁用该段素材或改成静态图。

## Validation

至少运行：

```bash
npm run validate-layering
npx tsc --noEmit
```

必要时抽帧：

```bash
npx remotion still src/index.ts CompositionId out/check.png --frame=159
```

导出后再从最终 MP4 抽过渡帧，确认成片没有闪屏。
