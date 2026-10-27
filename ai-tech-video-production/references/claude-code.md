# Claude Code 运行说明

这套技能在本机 Claude Code 中使用。Claude 网页会话和无终端的云端会话不能仅靠安装 SKILL.md 调用本机工具。安装与调用关系见 [视频流程](../../VIDEO_WORKFLOW.md)。

## 工具对应

| 工作 | Claude Code 中使用 |
|---|---|
| 读取说明、源码、PNG/JPEG 验收图 | Read；文件列表和文本搜索用 Glob/Grep 或 Bash 的 rg |
| 改工程、提示词、时间线和字幕 | Write / Edit；文件写入后回读 |
| FFmpeg、ffprobe、转写、Node、Remotion、Manim | Bash，使用当前机器实际存在的程序和环境 |
| 打开/操作网页、录屏或截图 | 当前可用且已授权的浏览器工具或本地浏览器工作流；不得假定 Codex 的内置浏览器工具存在 |
| 生成或修改 GPT Image 2 图片 | `codex-imagegen` 脚本 → 本地 `codex exec` → 内置 `image_gen` → 项目 PNG |
| TalkCraft 独立评审 | 其 review-protocol 中的 Claude `Agent` 路线；工具不可用时按协议报告或使用已授权的替代方式 |

不把 `functions.exec`、`image_gen`、`spawn_agent`、`open_in_codex` 等 Codex 工具名当作 Claude 自带工具。Claude 可以读取和执行同一套本地 Python/Node/FFmpeg 脚本；不需要为两个 Agent 另建一套视频时间线。

## 路径和运行环境

- 从被加载的 SKILL.md 所在目录定位 `references/`、`scripts/`、`assets/`，软链需要解析真实路径。跨技能从安装目录或同一仓库查找，不写死 `/Users/.../.codex/skills`。
- 安装入口有：`/ai-tech-video-production`、`/ai-tech-video-assets`、`/video-use`、`/video-talkcraft`、`/manim-video` 和 `/codex-imagegen`。自动调用取决于本次任务与会话实际发现的技能。
- 首次检查 `ffmpeg -version`、`ffprobe -version`、`node --version`、`python3 --version`，再检查本次需要的转写与渲染环境。仅按用到的能力补依赖，复用主技能运行环境策略。
- `agents/openai.yaml` 是 Codex 界面元数据，Claude 按 SKILL.md 执行即可。不要因为 Claude 不使用它就删除其他 Agent 所需文件。
- 项目源码、真实截图、提示词、字幕数据和媒体留在项目目录。技能安装不包含运行环境、密钥、口播文件或个人素材。

## 图片与工程交付

Claude 先保存提示词，通过 `codex-imagegen/scripts/generate.py` 调本地 Codex。沿用本地 Codex 登录，内置工具负责 GPT Image 2；不得为方便改调 API、router 或其他模型。检查 JSON 结果、真实图片尺寸、构图和媒体文件可读性后接入工程。缺少登录、工具、网络或权限时，明确报告实际缺失项。

成片制作、素材制作的视觉要求保持一致：保留真实截图的关键内容，生成图只用于背景或解释，字幕按实际口播对齐且避开脸与截图重点，每段只表达一个核心意思。用户指定开头结尾居中缩放人物时，在主时间线上实现相应布局。

用户要求可编辑工程时，交付真实工程源文件、素材、时间线/字幕数据和可执行的启动方法。Remotion Studio 源码预览与拖拽式剪辑界面应按实际能力说明；不能用“可编辑”暗示未实现的界面。
