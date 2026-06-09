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
- 右下 `X=720-1040, Y=1120-1660`：真人 PIP 保护区；素材核心信息不得进入。

Remotion 实现时，不要让主内容容器从 `top: 0` 或 `top: 120` 开始。建议给非图片素材的主内容容器设置 `paddingTop >= 260`，或用明确的 `top: 280` / `translateY` 下移；抽帧时检查首个核心元素是否贴近上沿。

## PIP Defaults

默认右下 PIP：

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
