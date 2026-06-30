# Remotion 规则

用于生成黑底头像声波竖屏视频。核心是音频驱动，不依赖真人视频。

## 工程结构

```text
remotion_project/
├── public/media/audio/voice.mp3
├── public/media/avatar/santu-avatar.png
├── public/media/images/
├── public/media/checks/
├── src/Video.tsx
├── src/timeline.json
├── scripts/extract-audio-levels.mjs
├── scripts/validate-layout.mjs
└── out/
```

## 图层顺序

1. 黑色背景层。
2. gpt-image2 简笔画图片层。
3. 字幕黑影安全带层。
4. 字幕层。
5. 声波层。
6. 圆形头像层。
7. 可选的轻品牌文字层。

代码只生成第 1、3、4、5、6、7 层，以及第 2 层的淡入/轻微位移动效；第 2 层的简笔画主体必须来自图片文件。

## 固定布局

```json
{
  "width": 1080,
  "height": 1920,
  "style": {
    "background": "#050505",
    "line": "#f5f5f5",
    "muted": "#8a8a8a",
    "accentBlue": "#58a6ff",
    "accentOrange": "#f59e0b",
    "accentRed": "#ef4444"
  },
  "layout": {
    "platformSafeMargin": {"x": 90, "top": 70, "bottom": 120},
    "illustration": {"x": 107, "y": 80, "width": 866, "height": 1538, "sourceWidth": 941, "sourceHeight": 1672, "scale": 0.92},
    "subtitleShadow": {"x": 0, "y": 890, "width": 1080, "height": 390},
    "subtitle": {"x": 110, "y": 980, "width": 860, "height": 260},
    "avatar": {"cx": 540, "cy": 1400, "diameter": 250},
    "waveLeft": {"x": 130, "y": 1320, "width": 260, "height": 160},
    "waveRight": {"x": 690, "y": 1320, "width": 260, "height": 160}
  }
}
```

把 `sourceWidth/sourceHeight` 写成图片真实像素，把 `width/height` 写成剪辑显示尺寸。显示尺寸按平台安全区等比例计算，不要假写素材尺寸。

推荐计算：

```js
const safe = {left: 90, right: 90, top: 70, bottom: 120};
const maxW = 1080 - safe.left - safe.right;
const maxH = 1580;
const scale = Math.min(0.95, maxW / sourceWidth, maxH / sourceHeight);
const displayW = Math.round(sourceWidth * scale);
const displayH = Math.round(sourceHeight * scale);
const x = Math.round((1080 - displayW) / 2);
const y = Math.max(safe.top, Math.round((1670 - displayH) / 2));
```

对常见 `941x1672` 图片，推荐 `scale=0.92`、显示约 `866x1538`、`x=107`、`y=80`，左右和顶部都留出安全空余。

## 组件建议

### IllustrationFrame

- 渲染 gpt-image2 图片。
- 只引用 `public/media/images/` 中已经存在、可读、校验过的图片文件。
- `objectFit: contain`。
- 素材尺寸记录真实像素，画面显示可以为平台安全区做等比例轻缩。
- 不要把正常图片缩到小框里；推荐 `0.90-0.95` 轻缩，左右至少留 `80px`，顶部至少留 `60px`。
- 只做淡入和轻微 `translateY`，不要再叠加会改变大小感的动态 `scale`。
- 如果图片不是黑底，先要求重生成，不要靠遮罩硬修。
- 不要引用尚未生成的占位路径；缺图时先回到图片资产落盘工作流。

### SubtitleSafetyBand

- 放在插画层之上、字幕层之下。
- 使用黑色或近黑色柔边渐变，覆盖字幕可能出现的位置。
- 宽度建议覆盖全屏，避免长字幕左右边缘被图像线条干扰。

示例样式：

```tsx
const band = timeline.layout.subtitleShadow;
<div
  style={{
    position: "absolute",
    left: band.x,
    top: band.y,
    width: band.width,
    height: band.height,
    background:
      "linear-gradient(180deg, rgba(5,5,5,0) 0%, rgba(5,5,5,0.84) 16%, rgba(5,5,5,0.96) 46%, rgba(5,5,5,0.96) 58%, rgba(5,5,5,0.84) 84%, rgba(5,5,5,0) 100%)",
    boxShadow: "0 -34px 92px rgba(0,0,0,0.7), 0 34px 92px rgba(0,0,0,0.78)",
  }}
/>
```

### SubtitleBlock

- 每段 1-2 行。
- 居中，字重高，行距紧。
- 关键词可局部高亮，但每屏最多 3 个词。
- 字幕位置要在阴影安全带中间，常用 `Y=960-1010`，底部必须离头像和声波至少 `20px`。

### CircularAvatar

- 使用 `border-radius: 50%` 或 SVG/Canvas mask 圆裁。
- 默认头像文件：`public/media/avatar/santu-avatar.png`，这是一张已裁剪好的透明圆形头像。
- 可加 2-4px 半透明浅色描边。
- 不做大幅弹跳或旋转。

### AudioWaveform

- 左右对称分布在头像两侧。
- 用音频振幅驱动条形、折线或圆点波。
- 振幅变化要平滑，避免抽搐。
- 声波不得进入字幕区。

## 校验命令

至少运行：

```bash
npx tsc --noEmit
npm run validate-layout
```

`validate-layout` 至少检查：

- `layout.subtitleShadow` 存在并覆盖字幕区。
- `layout.illustration.x >= 80`，`layout.illustration.y >= 60`，且 `1080 - (x + width) >= 80`。
- `layout.illustration.sourceWidth/sourceHeight` 来自真实图片文件；`layout.illustration.width/height` 是等比例显示尺寸。
- `layout.illustration.scale` 不大于 `0.95`，通常不小于 `0.88`，除非用户明确要求更小。
- `subtitle.y + subtitle.height <= avatar.cy - avatar.diameter / 2 - 20`。
- `subtitle.y + subtitle.height <= min(waveLeft.y, waveRight.y) - 20`。
- 每个 `segment.imagePath` 文件存在且可读，`imageStatus=ready` 不允许引用缺失文件。

必要时抽关键帧：

```bash
npx remotion still src/index.ts CompositionId public/media/checks/frame-001.png --frame=120
```

最终从 MP4 抽帧检查，不只看预览。
