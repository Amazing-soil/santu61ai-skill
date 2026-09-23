# AI Tech Video Production

将中文 AI 科技口播制作成高码率 MP4，支持素材规划、真人 PIP、按需字幕与可编辑工程交接。

## 使用

```text
$ai-tech-video-production
口播视频：/path/to/talking-head.mp4
文案：可选，或从视频转写
要求：导出竖屏 MP4，保留使用的图片与预览检查图。
```

需要字幕或后续剪辑时，在请求中写明“烧录字幕并保留可编辑字幕数据”或“交付可编辑工程”。默认不额外添加字幕。

本 Skill 不依赖其他自定义 Skill；成片制作需要可用的转写方法、Remotion/Node.js 与 FFmpeg 或等价工具。图片生成工具可选，无法取得本地图片文件时可用已有图片、录屏或动效。安装本目录不会自动安装运行依赖。

执行约定与默认交付见 [SKILL.md](SKILL.md)。按任务读取：

- [真实时间线与字幕断句](references/timeline-workflow.md)
- [素材规划](references/asset-planning.md)
- [工程、编码、布局与清理](references/remotion-rules.md)
- [共用运行环境、修改缓冲期与缓存维护](references/runtime-cleanup-policy.md)
- [成片验收](references/quality-checks.md)

`agents/openai.yaml` 提供启动提示，`templates/` 用于剪辑交接。将完整 Skill 目录安装到运行环境实际支持的技能发现路径后使用；仓库源文件与安装副本分别维护。
