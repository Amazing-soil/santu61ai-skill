# 三土学AI黑底简笔画配图

把中文 AI/商业口播文案拆成黑底 gpt-image2 简笔画素材方案和 prompt。它可以独立使用，也可以作为 [`santu-ai-voiceover-editing`](../santu-ai-voiceover-editing/) 的配图子流程。

## 适合场景

- 只想先规划口播配图，不立刻剪成视频。
- 需要为黑底头像声波口播生成上方视觉区插画。
- 需要把抽象观点转成“一眼能懂”的商业隐喻图。
- 需要强制图片落盘，而不是只停留在聊天预览。

## 默认视觉系统

- 竖屏 `9:16`。
- 纯黑或近黑背景 `#050505`。
- 白色/浅灰线稿，少量蓝色 AI 信号、橙色行动强调、红色风险提示。
- 固定人物：戴眼镜西装小人。
- 重要内容集中在上方插画区，给字幕、圆形头像和左右声波留干净黑底。

## 如果你要自定义人物

修改这些文件：

- `references/character-ip.md`：固定人物外形、动作和禁忌。
- `references/prompt-template.md`：生成 prompt 时的固定描述。
- `agents/openai.yaml`：默认触发提示词。

建议保留这些原则：

- 人物必须承担核心动作，不要站在角落当装饰。
- 不要变成真人肖像、吉祥物、Q 版卡通或豪华 CEO 海报。
- 一张图只讲一个判断、流程、状态或隐喻。

## 常用请求

```text
使用 $santu-ai-voiceover-illustrations 把这篇文案拆成 12 张黑底简笔画配图方案，给出每张图的用途和 gpt-image2 prompt。
文案：……
```

```text
使用 $santu-ai-voiceover-illustrations 直接生成图片，并保存到项目 public/media/images/，记录真实像素尺寸和校验结果。
文案：……
```

## 输出要求

策略阶段至少输出：

- 图片 `id`
- 对应口播片段
- 核心意思
- 构图说明
- gpt-image2 prompt
- 建议文件名

直接生成图片时必须输出：

- 已保存文件路径
- 文件是否可读
- 真实像素尺寸
- 是否通过 QA

## 图片落盘规则

图片必须从生成目录复制进项目，例如：

```text
public/media/images/img-01-hook.png
public/media/images/prompts.json
public/media/images/asset-manifest.json
```

每张图片都要校验：

```bash
file public/media/images/img-01-hook.png
sips -g pixelWidth -g pixelHeight public/media/images/img-01-hook.png
```

如果只在聊天界面看到图，但本地没有文件路径，不能把它写进时间线；必须先找到 `$CODEX_HOME/generated_images/...` 里的新增文件并复制。

## 与主剪辑 skill 的关系

`santu-ai-voiceover-editing` 会负责：

- TTS 音频。
- 字幕和真实时间线。
- Remotion 工程。
- 头像、声波、字幕黑影安全带。
- 最终 MP4 和封面。

本 skill 只负责：

- 配图策略。
- gpt-image2 prompt。
- 图片落盘与素材清单。
- 插画 QA。
