# AI Tech Video Production

面向中文 AI 科技口播短视频的端到端生产 skill。输入口播视频与文案后，指导 Agent 先切真实时间线，再配置混合素材，生成可编辑 Remotion 工程、导出 MP4，并检查 PIP、字幕安全区、转场和图层。

适合 AI 工具、AI 工作流、GEO、科技观点、产品实操等知识型竖屏短视频。

## 核心能力

- 基于真实口播视频切时间线，不按文案长度猜时长
- 为每个语义段匹配实操录屏、HTML/Anime.js 动效、AI 图片或留白
- 生成以 `src/timeline.json` 为快速修改入口的 Remotion 工程
- 保证原口播视频底层、素材覆盖层、真人 PIP 层的图层关系
- 检查顶部安全区、中下字幕区和右下 PIP 保护区
- 使用覆盖式淡入，避免素材切换时闪回口播底图
- 导出最终 MP4、关键帧检查图和剪辑师交付说明

## 默认成片规范

- 画幅：`1080x1920`
- 默认不烧录字幕，为后期字幕保留空间
- 字幕安全区：约 `Y=1120-1360`
- 非图片素材核心区：约 `Y=280-1080`
- 右下真人 PIP：仅引用原口播视频，使用等比例裁切
- 每 30 秒至少安排 1 张 AI 图片素材，最好 1-2 张，实操录屏段可例外

## 工作流

1. 检查口播视频规格、时长和已有素材。
2. 依据字幕时间戳、语音停顿或人工校准切分真实时间线。
3. 按语义选择素材类型，并检查素材密度。
4. 生成或整理素材，统一放入工程媒体目录。
5. 创建可编辑 Remotion 工程，并维护三层图层结构。
6. 抽取关键帧检查布局、PIP 和安全区。
7. 运行图层校验和 TypeScript 检查。
8. 导出 MP4，并抽查转场帧是否闪屏。

详细规则见：

- [真实时间线工作流](./references/timeline-workflow.md)
- [Remotion 工程规则](./references/remotion-rules.md)
- [交付前验收清单](./references/quality-checks.md)

## 使用示例

```text
Use $ai-tech-video-production.

口播视频：/path/to/talking-head.mp4
口播文案：<粘贴文案>

请完成素材配置和剪辑，生成可编辑 Remotion 工程、最终 MP4 和关键帧检查图。
```

## 推荐输入

- 一条完整的竖屏口播视频
- 与视频一致的口播文案
- 已有截图、实操录屏或品牌素材目录（可选）
- 是否需要烧录字幕、目标平台和风格偏好（可选）

## 标准交付物

```text
remotion_project/
├── public/media/source_talking.mp4
├── public/media/images/
├── public/media/motion/
├── src/Video.tsx
├── src/timeline.json
├── scripts/validate-layering.mjs
├── docs/README.md
└── out/
```

## 环境依赖

- Node.js
- Remotion
- FFmpeg / FFprobe
- 支持读取视频、生成图片和执行本地命令的 Agent 环境

本 skill 提供生产规则和模板，不内置完整 Remotion 项目脚手架，也不会上传用户的视频或私有素材。

## Skill 文件

- `SKILL.md`：Agent 核心指令
- `agents/openai.yaml`：OpenAI/Codex 展示与调用配置
- `references/`：时间线、Remotion 和验收规则
- `templates/`：时间线表与剪辑师交付模板

## License

本 skill 随仓库使用 [MIT License](../LICENSE) 发布。
