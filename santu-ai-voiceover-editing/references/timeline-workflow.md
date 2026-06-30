# TTS 与时间线

## 输入

至少需要：

- `scriptText`：中文口播文案。
- `avatarPath`：默认 `assets/santu-avatar.png`。
- `audioPath`：可选。若用户已提供成品音频，跳过 TTS。

默认不再等待克隆声音配置：本机已配置 MiniMax 中国站 API CLI，固定用三土克隆音色生成音频。

## MiniMax TTS 默认命令

默认命令形状：

```bash
minimax-tts tts \
  --text-file script.txt \
  --output voice.mp3 \
  --model speech-2.8-hd \
  --voice-id SantuVoice20260618B \
  --language-boost Chinese \
  --format mp3 \
  --sample-rate 32000 \
  --bitrate 128000 \
  --channel 1 \
  --subtitle
```

记录这些字段：

- `voiceProvider`: `minimax-cn-cli`
- `cli`: `minimax-tts`
- `model`: `speech-2.8-hd`
- `voiceId`: `SantuVoice20260618B`
- `languageBoost`: `Chinese`
- `inputTextFile`
- `outputAudioPath`
- `metadataPath`
- `subtitleEnabled`: `true`

语速默认自然偏稳，不要过快。老板向观点内容更适合有停顿、有重音。

## 时间线原则

- 音频是真实时间线的唯一基准。
- 有词级/句级时间戳时，直接使用。
- 没有时间戳时，先按中文标点切句，再根据音频总时长估算，最后用波形或试听校准关键停顿。
- 字幕切分优先按语义和停顿，不按固定字数机械切。
- MiniMax 返回长句字幕时，继续按 `，。！？；：` 拆成短段，去掉末尾标点，再按字数权重分配原字幕时间。
- 逗号前后尽量分屏显示；每屏建议 `8-18` 个汉字，超过 `18` 个字再按 `、/因为/所以/不是/而是/让/把/到` 等软断点拆分。
- 拆成短段后写入 `timedSubtitles`，不要只把长句写进 `segments.subtitle`。

## 视觉单元

- 默认 `4-7 秒` 一个视觉单元。
- 反常识钩子、三类/三步、结论句可以单独成视觉单元。
- 一张插画只表达一个判断、流程、状态或隐喻。
- 太短的句子沿用上一张图，不强行换图。

## timeline.json 字段

```json
{
  "audio": {
    "path": "public/media/audio/voice.mp3",
    "duration": 72.4,
    "voiceProvider": "minimax-cn-cli",
    "cli": "minimax-tts",
    "model": "speech-2.8-hd",
    "voiceId": "SantuVoice20260618B",
    "metadataPath": "public/media/audio/voice.mp3.json"
  },
  "avatar": {
    "path": "public/media/avatar/santu-avatar.png",
    "shape": "circle",
    "diameter": 250,
    "center": {"x": 540, "y": 1400}
  },
  "layout": {
    "platformSafeMargin": {"x": 90, "top": 70, "bottom": 120},
    "illustration": {"x": 107, "y": 80, "width": 866, "height": 1538, "sourceWidth": 941, "sourceHeight": 1672, "scale": 0.92},
    "subtitleShadow": {"x": 0, "y": 890, "width": 1080, "height": 390},
    "subtitle": {"x": 110, "y": 980, "width": 860, "height": 260},
    "avatar": {"cx": 540, "cy": 1400, "diameter": 250},
    "waveLeft": {"x": 130, "y": 1320, "width": 260, "height": 160},
    "waveRight": {"x": 690, "y": 1320, "width": 260, "height": 160}
  },
  "timedSubtitles": [
    {
      "id": "sub-001",
      "start": 0,
      "end": 1.8,
      "text": "用 AI 赚钱的第一步",
      "lines": ["用 AI 赚钱的第一步"]
    }
  ],
  "segments": [
    {
      "id": "seg-01-hook",
      "start": 0,
      "end": 5.2,
      "text": "你团队里最聪明的人，可能最先掉队。",
      "subtitle": ["你团队里最聪明的人", "可能最先掉队"],
      "visualPromptId": "img-01",
      "imagePath": "public/media/images/img-01.png",
      "imageSource": "gpt-image2",
      "layout": "topIllustration",
      "subtitleZone": "middle",
      "avatarMode": "fixedCircle",
      "waveformMode": "leftRightAudioBars"
    }
  ]
}
```

## 素材匹配表

| 时间段 | 字幕 | 核心意思 | gpt-image2 图 | 头像/声波 | 风险 |
|---|---|---|---|---|---|

风险列重点检查：字幕是否太长、图是否太复杂、头像/声波是否挡字、语义是否需要换图。

## 布局校验

生成时间线后检查：

- `layout.subtitleShadow` 存在，并覆盖 `layout.subtitle` 的上下范围。
- `layout.illustration.sourceWidth/sourceHeight` 记录图片真实像素，`width/height` 记录安全区内的等比例显示尺寸。
- `layout.illustration.x >= 80`，`layout.illustration.y >= 60`，右侧也至少留 `80px`。
- `layout.illustration.scale` 通常在 `0.90-0.95`，不要为了遮字幕缩成小图。
- `layout.subtitle.y + layout.subtitle.height <= layout.avatar.cy - layout.avatar.diameter / 2 - 20`。
- `layout.subtitle.y + layout.subtitle.height <= min(layout.waveLeft.y, layout.waveRight.y) - 20`。
- 每个 `segment.imagePath` 对应文件存在且可读。
- `imageWidth/imageHeight` 或 manifest 中的图片尺寸来自 `sips`/图片文件，不是凭空填。
