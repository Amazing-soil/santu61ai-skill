# AI Tech Video Production

AI 科技中文口播短视频的端到端剪辑 skill。输入口播视频和文案后，按真实语音时间线规划素材，生成或整理可读素材，产出可编辑 Remotion 工程、可选字幕轨、最终高码率 MP4 和关键帧检查图。

## Standalone

本 skill 可以单独安装和使用，不依赖 `ai-tech-video-assets` 或其他自定义 skill。

可选增强：

- 图片生成工具：用于生成 GPT Image/AI 图片素材。
- ASR/Whisper/faster-whisper：用于切真实语音时间线和字幕。
- Remotion/Node.js/FFmpeg：用于生成工程、渲染视频和做媒体检查。

如果环境里没有生图工具或生图工具无法提供本地图片路径，仍然可以使用本 skill：改用 HTML/Remotion 动效、用户提供的图片/截图/录屏，或先通过可落盘的 API/CLI 生成图片文件。

## What It Does

- 按真实口播切时间线，不按文案估算硬配素材。
- 规划素材类型：实操录屏/截图、HTML/Anime.js/Remotion 动效、GPT Image/AI 图片、无素材过渡。
- 生成或整理素材，并统一放进工程媒体目录。
- 创建可编辑 Remotion 工程，核心配置写入 `src/timeline.json`。
- 按需生成可编辑字幕轨，字幕以真实语音口述为准。
- 渲染最终高码率 MP4，并用 `ffprobe`、关键帧抽帧图做验收。

## Inputs

最少需要：

- 口播视频文件路径。
- 口播文案或大纲。

可选：

- 已有图片、截图、录屏素材目录。
- 是否需要字幕/烧录字幕。
- 品牌色、禁用风格、参考视频或封面要求。
- 输出目录或项目名。

示例请求：

```text
$ai-tech-video-production
口播视频：/path/to/talking-head.mp4
文案：……
要求：生成可编辑 Remotion 工程，导出 1080x1920 高码率 MP4，不烧字幕，给后期字幕留空间。
```

字幕示例：

```text
$ai-tech-video-production
基于这个口播视频生成剪辑工程和可编辑字幕轨，字幕按真实口播，不要直接照文案。
最终导出高码率 MP4，并给我关键帧检查图。
```

## Workflow

1. 读取口播视频和文案。
2. 用音频/ASR/人工核对切真实时间线。
3. 按语义段规划素材类型。
4. 先定视觉色彩策略，避免全片青绿/荧光绿。
5. 生成或整理素材到工程媒体目录。
6. 创建 Remotion 工程和 `src/timeline.json`。
7. 处理 PIP：开头居中放大、正文中间下方小 PIP、结尾回到居中。
8. 如需字幕，生成可编辑字幕轨，不只烧进 MP4。
9. 渲染高码率 MP4。
10. 抽关键帧检查素材时间、PIP 遮挡、字幕安全区、色彩占比和转场。

## Image Asset Rule

工程可引用的图片必须是本地可读文件，不能只存在于聊天界面。

推荐目录：

```text
public/media/images/
```

推荐引用：

```json
{
  "kind": "image",
  "asset": "media/images/scene-01.png"
}
```

如果内置生图工具只把图片返回到聊天界面、不给本地路径，处理方式是：

1. 优先从工具默认生成目录复制图片到 `public/media/images/`。
2. 如果没有可访问文件路径，改用可落盘的 API/CLI 重新生成。
3. 如果仍无法落盘，请用户保存/提供图片文件。
4. 在图片落盘之前，不要把该图片写入 `src/timeline.json`。

交付前必须确认：

```bash
file public/media/images/*.png
```

并通过 Remotion 渲染或抽帧确认图片没有空白、丢失或路径错误。

## Output Structure

推荐输出结构：

```text
project-name/
  package.json
  src/
    index.ts
    Video.tsx
    timeline.json
  public/
    media/
      source_talking.mp4
      images/
      videos/
  out/
    final.mp4
    final-checks/
  docs/
    README.md
```

## Final MP4 Encoding

默认交付高码率 MP4：

- `1080x1920`
- `30fps`
- H.264
- 视频目标码率默认 `8M`
- `maxrate 10M`
- `bufsize 20M`
- AAC 音频不低于 `128k`

运动素材多、录屏细节多或用户要求更清晰时，视频目标码率用 `10M-12M`。

不要把低码率预览版或单纯 CRF 压出来的小文件当成最终交付。

## Verification

建议至少运行：

```bash
npm run typecheck
npm run validate-layering
npm run render
ffprobe -hide_banner -v error -show_entries format=duration,bit_rate,size:stream=index,codec_type,codec_name,duration,bit_rate -of json out/final.mp4
```

还应抽关键帧检查：

- 开头钩子段是否有语义背景素材。
- 素材出现时间是否和真实口播对齐。
- 字幕安全区是否被占用。
- 中间下方 PIP 是否遮挡核心信息。
- 结尾人物是否回到居中强化出镜。
- 图片素材是否成功读取，没有黑屏/空白/路径丢失。

## Common Problems

素材提前或滞后：

- 不要按文案估时间。
- 重新用 ASR/音频波形切真实时间线。
- 更新 `src/timeline.json` 中每段 `start` / `end`。

图片在聊天里能看到，但视频里没有：

- 说明图片没有进入工程媒体目录。
- 将图片复制到 `public/media/images/`。
- 确认 timeline 引用的是 `media/images/...`。

最终 MP4 文件太小：

- 检查是否用了单纯 CRF/质量模式。
- 改用目标码率控制。
- 用 `ffprobe` 验证视频码率。

字幕和口播不一致：

- 用户文案只做语义参考。
- 最终字幕以 ASR/人工校准后的真实口播为准。

## Publishing Notes

发布到 GitHub 时，至少包含：

- `SKILL.md`
- `README.md`
- `references/`
- `templates/`
- `agents/`，如需要

安装者只要安装本 skill 目录，就能触发 `$ai-tech-video-production` 并按 README 执行。其他 skill 只能作为可选增强，不能作为必需依赖。
