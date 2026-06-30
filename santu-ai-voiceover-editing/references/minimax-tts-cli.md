# MiniMax 中国站 TTS CLI

默认使用本机全局命令：

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

## 固定参数

- CLI：`minimax-tts`
- 子命令：`tts`
- 中国站 API：`https://api.minimaxi.com`
- 模型：`speech-2.8-hd`
- 音色：`SantuVoice20260618B`
- 语言增强：`Chinese`
- 默认输出：`mp3`
- 默认开启：`--subtitle`

## 执行规则

- 先把清理后的口播稿保存为 `script.txt`，再用 `--text-file` 传入，避免长文本 shell 转义问题。
- 输出音频保存为 `public/media/audio/voice.mp3` 或项目内等价路径。
- CLI 会同时保存元数据 JSON，路径通常是 `voice.mp3.json`；保留它用于字幕或后续排查。
- 如果 CLI 返回字幕时间戳，优先用于时间线；否则按音频波形和句子停顿校准。
- 不要在 skill 文档或交付物里暴露 `MINIMAX_API_KEY`。
