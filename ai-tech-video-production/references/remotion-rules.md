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
- `subtitleStyle`（用户要求字幕时）
- `subtitles`（用户要求字幕时）
- `segments`

## Render Quality Defaults

默认交付高码率 MP4。不要把 CRF/质量模式自动压缩出的低码率小文件当成最终版，尤其是静态图、截图、卡片素材较多时，CRF 会把文件压得很小。

`1080x1920/30fps/H.264` 默认参数：

- 视频目标码率：`8M`
- `maxrate`：`10M`
- `bufsize`：`20M`
- 音频：AAC，`128k` 或更高
- 快速运动、密集录屏、复杂动效较多：目标码率提高到 `10M-12M`

如果 Remotion 工程直接导出的 MP4 偏小，必须做最终高码率转码，例如：

```bash
ffmpeg -y -i input.mp4 \
  -c:v libx264 -preset slow -b:v 8M -maxrate 10M -bufsize 20M \
  -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 128k \
  final_hq.mp4
```

如果同时需要小文件预览版，命名为 `*_preview.mp4` 或 `*_low.mp4`；高码率版本必须命名清楚，例如 `*_final_hq.mp4`，并作为默认交付。

## Layering

工程基础必须保持三层：

1. 原口播视频底层：完整铺底。
2. 素材覆盖层：图片、动效、说明卡。
3. 原口播视频 PIP 层：只引用 `source_talking.mp4`。

禁止把素材文件放进 PIP 层。每次修改模板后运行图层校验脚本。

如果生成字幕，字幕不是素材层的一部分，推荐层级为：

1. 原口播视频底层。
2. 素材覆盖层。
3. 字幕可读性阴影/弱遮罩层（可选，只覆盖字幕文字背后）。
4. 字幕文本层。
5. 原口播视频 PIP 层。

PIP 层在字幕之上，是为了防止字幕误压人像；正确做法仍然是让字幕位置避开 PIP。

## Asset Layout Safe Area

非图片素材包括 HTML/Anime.js 动效、文字信息图、流程卡、图表、代码/窗口模拟。生成这些素材时必须预留顶部安全区：

- `Y=0-260`：只允许背景网格、光斑、粒子、弱装饰，不放可读文字、卡片、图标组、流程节点或主视觉。
- `Y=280-1080`：优先放核心标题、关键图形、流程节点、图表和主要动效。
- `Y=1080-1120`：缓冲区，只放非关键装饰，避免压到字幕安全区。
- `Y=1120-1360`：中间偏下字幕安全区；不放必须阅读的素材内容。
- 正文阶段中间下方 `X=330-750, Y=1280-1780`：真人 PIP 保护区；素材核心信息不得进入。若 PIP 尺寸变化，以人物框外扩 `40px` 作为保护区。
- 开头前 `3 秒` 与结尾最后 `3 秒` 使用居中人物保护区，素材需要围绕人物重新排版；主标题优先放人物上方，短标签可放人物左右，不能压脸、胸口或字幕。

Remotion 实现时，不要让主内容容器从 `top: 0` 或 `top: 120` 开始。建议给非图片素材的主内容容器设置 `paddingTop >= 260`，或用明确的 `top: 280` / `translateY` 下移；抽帧时检查首个核心元素是否贴近上沿。

## Subtitle Track

用户要求字幕或烧录字幕时，必须生成可编辑字幕轨。用户提供的口播文案、旧字幕或标题稿只做语义参考；如果它们和视频里的真实语音不一致，最终字幕以音频 ASR/人工校准后的真实口述为准，脚本文案只用于辅助断句、理解上下文和发现明显错听。

字幕配置建议写入 `src/timeline.json`：

```json
{
  "subtitleStyle": {
    "enabled": true,
    "fontWeight": 900,
    "color": "#ffffff",
    "textShadow": "0 3px 10px rgba(0,0,0,0.95), 0 1px 2px rgba(0,0,0,1)",
    "baseFontSize": 58,
    "minFontSize": 42,
    "maxWidth": 760,
    "lineHeight": 1.14,
    "preferSingleLine": true
  },
  "subtitles": [
    {
      "start": 3.12,
      "end": 5.84,
      "text": "如果AI能让一个人干掉一个团队的活",
      "position": "bodySafe"
    }
  ]
}
```

全局 CSS 字体栈优先使用 Mac 上的苹方：

```css
body {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
}
```

字幕组件继承全局 CSS 字体栈，不在组件内另写不一致的 `fontFamily`。字幕样式固定为 `fontWeight: 900`、白字、黑色阴影、动态字号，`letterSpacing` 保持 `0`。

动态字号建议：

```ts
const fontSize = Math.max(
  subtitleStyle.minFontSize,
  subtitleStyle.baseFontSize - Math.max(0, text.length - 14) * 1.4
);
```

布局规则：

- 字幕优先单行显示，先动态缩小字号，再按语义拆成下一条字幕，最后才允许两行。
- 不按固定字数机械断句；按真实口播的自然句、语义短句和停顿切分。
- 正文阶段放在中间偏下安全区时必须避开中间下方 PIP。优先使用 `Y=1080-1260` 的单行字幕，或移动到 PIP 左右侧安全空位。
- 开头/结尾居中人物阶段，字幕不得覆盖脸、嘴、手和胸口；优先放到人物旁侧或下方安全空位，仍冲突时临时缩短或降低字号。
- 字幕容器不能进入正文中间下方 PIP 保护区 `X=330-750, Y=1280-1780`。

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
- 旧方式降亮、弱化或划线；新方式优先用琥珀金或冷蓝高亮，只有 AI 识别、扫描、信号、增长语义才少量使用信号绿。
- 每侧只放 `1` 个身份词 + `1` 个动作词，避免长句。
- 核心文字放在 `Y=280-1080`，中间下方 PIP 区保持干净。

### HudCoordinateList

用于步骤、特征、判断标准和执行顺序：

- `01 / 先给AI跑`
- `02 / 自己判断`
- `03 / 再做修正`

实现建议：

- 使用编号、1px 细线、坐标点、弱扫描光，不包矩形框。
- 每屏最多 `3-4` 条，单条 `2-6` 个汉字为宜。
- 坐标清单不要进入 `Y=1120-1360` 字幕区，不压中间下方 PIP。
- 如果内容超过容量，拆成下一段或删字，不缩成一堆小字。

## Color System

Remotion 模板必须先定义可替换的色彩系统，不要把绿色写成全局默认。

默认推荐：

```ts
const palette = {
  bg: "#05070d",
  text: "#f7fbff",
  muted: "#9fb2c7",
  amber: "#f6d365",
  blue: "#69a8ff",
  signalGreen: "#1de58c",
  danger: "#ff565d",
};
```

规则：

- 背景以深炭黑/近黑为主，正文用冷白，主强调优先用琥珀金或冷蓝。
- `signalGreen` 只用于 AI 识别、扫描、信号、增长、雷达、激活等语义，建议占画面高亮面积约 `10%-20%`。
- 不要让 `blue`、`warm` 等 tone 的 fallback 仍然返回绿色 RGB；每个 tone 必须有真实不同的主色。
- 不要让背景、标题、粒子、描边、进度条、图片提示词同时使用绿色，否则整条视频会变成单一青绿色科技风。
- 如果用户有品牌色或行业色，品牌色优先；没有品牌色时使用上述默认体系。

## Dynamic PIP Defaults

默认使用三阶段动态 PIP：

1. `introHero`：开头前 `3 秒`，人物居中放大，但不全屏；背景继续展示钩子素材，人物周围可放 `2-4` 个短标签或一条钩子标题。
2. `bodyBottomCenter`：正文阶段，人物平滑缩小并移动到中间下方。
3. `outroHero`：最后 `3 秒`，人物平滑回到中央；背景继续展示结论素材，人物周围可放结论词、适用场景或提问辅助信息。

如果开头钩子或结尾收束的真实口播段不足 `3 秒`，使用真实时间线边界，不强行占满。居中强化出镜不能只剩人物，也不要直接使用全屏原口播。

推荐配置：

```json
{
  "pip": {
    "introHero": {"duration": 3, "x": 190, "y": 560, "width": 700, "height": 900, "radius": 42},
    "bodyBottomCenter": {"x": 360, "y": 1320, "width": 360, "height": 480, "radius": 34},
    "outroHero": {"duration": 3, "x": 190, "y": 560, "width": 700, "height": 900, "radius": 42},
    "transitionFrames": 20
  }
}
```

正文中间下方 PIP：

```json
{
  "enabled": true,
  "x": 360,
  "y": 1320,
  "width": 360,
  "height": 480,
  "radius": 34,
  "borderWidth": 4,
  "borderColor": "rgba(255,255,255,0.72)"
}
```

规则：

- 开头和结尾居中人物建议占画面宽度约 `52%-68%`，保留背景素材和辅助信息，不做全屏纯人像。
- 居中人物周围的辅助信息必须短：最多一条主钩子/结论和 `2-4` 个短标签，不用满屏小字。
- 从居中到中间下方、从中间下方到居中的位移、尺寸和圆角变化必须连续插值，不能硬切。
- 近似 `3:4`，用 `object-fit: cover` 等比例裁切。
- 位置压低到中间下方，字幕和素材应主动避开人物框。
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
