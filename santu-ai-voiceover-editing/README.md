# 三土学AI黑底头像声波口播

把一篇中文口播文案做成竖屏视频：MiniMax 克隆声音朗读、按真实音频切字幕和时间线、生成黑底 gpt-image2 西装小人插画、用 Remotion 输出 `1080x1920` 黑底头像声波成片，并可继续生成 `9:16` 和 `6:7` 两版封面。

## 适合场景

- AI/商业观点口播，但没有真人视频，只想用头像、声波、字幕和插画完成成片。
- “三土学AI”黑底商业草图风格：黑底、白/灰线稿、少量蓝橙红强调。
- 需要把抽象观点拆成简笔画隐喻，并确保素材真的落盘进工程。
- 需要一套可复用 Remotion 工程，而不是一次性导出。

## 相关 Skill

建议同时安装：

- [`santu-ai-voiceover-editing`](./)：主流程，负责 TTS、时间线、Remotion、字幕、头像声波、封面和验收。
- [`../santu-ai-voiceover-illustrations`](../santu-ai-voiceover-illustrations/)：配图流程，负责把口播文案拆成黑底 gpt-image2 简笔画素材方案和 prompt。

## 默认三土配置

本 skill 仓库保留了三土当前生产环境的默认配置，方便直接复用：

| 项目 | 默认值 |
|---|---|
| TTS CLI | `minimax-tts` |
| MiniMax 模型 | `speech-2.8-hd` |
| 默认音色 | `SantuVoice20260618B` |
| 头像 | `assets/santu-avatar.png` |
| 插画人物 | 戴眼镜西装小人 |
| 背景 | `#050505` 近黑 |
| 输出画幅 | `1080x1920` |
| 字幕区 | `Y=960-1240`，头像上方 |
| 头像区 | 圆心约 `X=540, Y=1400` |
| 插画缩放 | 记录真实像素，按平台安全区 `0.90-0.95` 等比例轻缩 |

如果你就是要沿用三土账号的视觉系统，可以不改头像和人物设定；如果要给自己的账号使用，请按下面初始化步骤替换。

## 初始化选择

第一次使用前先选一种模式。

### A. 使用三土默认形象

适合复刻“三土学AI”风格。

需要准备：

- 本机可用 `minimax-tts` CLI。
- 本机 MiniMax API key 已配置。
- 允许使用仓库里的默认头像 `assets/santu-avatar.png`。
- 默认音色 `SantuVoice20260618B` 在你的 MiniMax 账号或运行环境中可用。

### B. 换成自己的声音和形象

适合把这套 skill 变成自己的账号模板。

需要准备：

- MiniMax API key。
- 你自己的 MiniMax 克隆音色 `voice_id`。
- 一张清晰头像或主讲人形象，建议先裁成正方形，再导出透明圆形 PNG。
- 你自己的固定插画人物设定，例如“戴眼镜衬衫创始人”“短发黑衣产品经理”等。

建议替换：

- `assets/santu-avatar.png`：替换为你的圆形头像。
- `assets/santu-avatar-original.jpg`：保留原始头像源文件，便于以后重裁。
- `references/minimax-tts-cli.md`：把默认 `voice_id` 改成你的音色。
- `references/timeline-workflow.md`：把默认音色记录字段改成你的音色。
- `../santu-ai-voiceover-illustrations/references/character-ip.md`：把“戴眼镜西装小人”改成你的固定人物 IP。
- `agents/openai.yaml`：把默认提示词里的账号名、音色和风格改成你的版本。

### C. 跳过 TTS，只用已有音频

适合你已经有录好的口播音频或配音文件。

请求时提供：

```text
已有音频：/path/to/voice.mp3
文案：……
要求：跳过 MiniMax TTS，从真实音频切时间线。
```

此时仍需要生成插画素材、字幕时间线、Remotion 工程和 MP4。

## MiniMax 准备

本 skill 默认调用本机命令：

```bash
minimax-tts tts \
  --text-file script.txt \
  --output public/media/audio/voice.mp3 \
  --model speech-2.8-hd \
  --voice-id SantuVoice20260618B \
  --language-boost Chinese \
  --format mp3 \
  --sample-rate 32000 \
  --bitrate 128000 \
  --channel 1 \
  --subtitle
```

`minimax-tts` 不是本仓库内置脚本，需要在本机先安装或提供等价 CLI。推荐环境变量：

```bash
mkdir -p ~/.config/minimax_tts
cp santu-ai-voiceover-editing/templates/minimax.env.example ~/.config/minimax_tts/.env
chmod 600 ~/.config/minimax_tts/.env
```

然后填入自己的 API key 和可用音色。不要把 `.env` 或 API key 提交到 GitHub。

## 工程输出结构

每次生产建议生成一个独立 Remotion 工程：

```text
project-name/
  script.txt
  package.json
  remotion.config.ts
  src/
    index.ts
    Root.tsx
    Video.tsx
    timeline.json
    audio-levels.json
  public/
    media/
      audio/
        voice.mp3
        voice.mp3.json
        voice.subtitle.raw
      avatar/
        santu-avatar.png
      images/
        img-01-hook.png
        prompts.json
        asset-manifest.json
      covers/
        cover-9x16.png
        cover-6x7.png
        cover-manifest.json
      checks/
  out/
    final.mp4
  docs/
    editor-handoff.md
```

## 关键规则

- 音频是真实时间线基准，不按文案字数硬切。
- 字幕按中文停顿拆成短段，每屏建议 `8-18` 个汉字，最多 2 行。
- 插画必须是 gpt-image2 生成并落盘的图片文件，不能用代码临时画主体。
- 图片要记录真实像素尺寸，剪辑层再做平台安全区内等比例显示。
- 字幕黑影安全带必须在插画层上、字幕层下。
- 头像和左右声波是剪辑层固定组件，不是插画素材的一部分。
- 封面标题默认由 gpt-image2 直接生成到图里，不用代码后期叠字，除非用户明确要求。

## 常用请求

```text
使用 $santu-ai-voiceover-editing 制作一条黑底头像声波口播。
封面标题：AI超级团队 03
文案：……
```

```text
使用 $santu-ai-voiceover-editing 制作口播，但跳过 TTS。
已有音频：/path/to/voice.mp3
封面标题：……
文案：……
```

```text
使用 $santu-ai-voiceover-editing，但把默认头像换成 /path/to/avatar.png，音色使用 MyVoiceId。
文案：……
```

## 初始化清单

见 [templates/init-checklist.md](./templates/init-checklist.md)。

## 验收

至少检查：

```bash
npm run build-timeline
npm run extract-audio-levels
npm run validate-layout
npm run typecheck
npm run render
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,avg_frame_rate,duration \
  -show_entries format=duration,size \
  -of json out/final.mp4
```

最终交付必须包含 MP4、音频、时间线、prompt 清单、图片素材清单、关键帧检查图；如果提供封面标题，还要包含两版封面和 `cover-manifest.json`。
