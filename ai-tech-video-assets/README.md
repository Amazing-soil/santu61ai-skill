# AI Tech Video Assets

为中文 AI 科技口播规划或制作图片、HTML 动效和实操素材。只需要素材表时提供规划；要求生成素材时完成文件与预览验收。

## 安装与依赖

复制完整目录到 Agent 支持的技能目录，例如 `~/.codex/skills/ai-tech-video-assets`。关联技能安装见 [视频制作与关联技能](../VIDEO_WORKFLOW.md)。

规划任务不需要额外运行依赖。制作图片需要可用的图片生成工具或已有图片；HTML 动效需要浏览器与适用的 JavaScript 运行环境；导出视频素材需要 FFmpeg 或所选渲染工具。Anime.js 按实际项目版本使用，不随本目录安装。

## 使用

```text
使用 $ai-tech-video-assets 为以下中文口播规划素材。
文案：……
目标：1080x1920 竖屏，提供逐段素材表。
```

需要文件时明确“继续生成图片和 HTML 动效，并提供预览”；完整成片使用 [ai-tech-video-production](../ai-tech-video-production/)。原始音频可用时按真实语义时间点对齐，只有文案时标明估计时长。

执行规则与各项参考资料见 [SKILL.md](SKILL.md)。素材规划包含原句、核心意思、素材类型、画面方向、安全区与时间；实际制作交付素材文件、来源记录、预览及剪辑说明。
