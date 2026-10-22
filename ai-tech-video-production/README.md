# AI Tech Video Production

将中文 AI 科技口播制作成高码率 MP4，支持横竖版布局、全屏章节页、真人显示切换、按需字幕与可编辑工程交接。

## 使用

```text
$ai-tech-video-production
口播视频：/path/to/talking-head.mp4
文案：可选，或从视频转写
要求：导出竖屏 MP4，保留使用的图片与预览检查图。
```

需要字幕或后续剪辑时，在请求中写明“烧录字幕并保留可编辑字幕数据”或“交付可编辑工程”。默认不额外添加字幕。

已剪好的口播可直接使用本 Skill。原始素材需要精剪时按 [video-use](../video-use/) 交接；复杂动效可按需读取 [video-talkcraft](../video-talkcraft/)，独立素材任务可用 [ai-tech-video-assets](../ai-tech-video-assets/)。安装与调用关系见 [视频制作与关联技能](../VIDEO_WORKFLOW.md)。

成片制作需要可用的转写方法、浏览器/Node.js 或 Remotion，以及 FFmpeg 或等价工具。图片生成工具可选，无法取得本地图片文件时可用已有图片、录屏或动效。安装 Skill 目录不会自动安装运行依赖。

执行约定与默认交付见 [SKILL.md](SKILL.md)。按任务读取：

- [可运行章节页、基础运动函数和真人切换组件](references/composition-components.md)
- [TalkCraft 按内容接入](references/talkcraft-integration.md)
- [真实时间线与字幕断句](references/timeline-workflow.md)
- [素材规划](references/asset-planning.md)
- [工程、编码、布局与清理](references/remotion-rules.md)
- [共用运行环境、修改缓冲期与缓存维护](references/runtime-cleanup-policy.md)
- [成片验收](references/quality-checks.md)

`agents/openai.yaml` 提供启动提示，`templates/` 用于剪辑交接。将完整 Skill 目录安装到运行环境实际支持的技能发现路径后使用；仓库源文件与安装副本分别维护。

组件位于 `assets/composition/`，无 npm 依赖。启动本地静态服务后打开 `example.html`，可切换横竖版、选择本地口播并预览；该示例不会修改视频文件，也不是成片导出器。运行 `node scripts/test-composition.mjs` 检查主时钟、章节覆盖和人物布局。
