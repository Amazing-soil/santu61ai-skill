# santu61ai-skill

三土沉淀的 AI Agent Skills 合集。每个 skill 都作为独立子目录维护，可复制到 Codex、Claude Code 或其他兼容 `SKILL.md` 的 Agent 环境中使用。

## 抖音收藏知识库：单独安装入口

只想整理抖音收藏，请直接看 [安装与使用](douyin-favorites-kb/README.md)，或下载 [单技能 ZIP](https://github.com/Amazing-soil/santu61ai-skill/raw/refs/heads/main/downloads/douyin-favorites-kb.zip)。包内已包含所需提取运行时，不必安装其他技能。提供 Codex 安装器与 WorkBuddy 上传引导，包含依赖自检、使用协议、首次三条样本流程和故障处理；具体实机验证范围见 [兼容性](douyin-favorites-kb/references/compatibility.md)。

## Skills

| Skill | 用途 | 语言 |
|---|---|---|
| [douyin-favorites-kb](./douyin-favorites-kb/) | 本人抖音收藏转 Markdown 知识库，完整文案、分类、查重与失败重试；含独立安装包 | 中文 |
| [douyin-copy-extractor](./douyin-copy-extractor/) | 提取抖音作品信息、发布文案和经校对的完整口播，按需保留媒体；需要 GPU | 中文 |
| [bayarea-follow-reading](./bayarea-follow-reading/) | 提取跟读文案、重点字、音频和右侧素材，接收数字人视频后按湾区固定模板合成成片 | 中文 |
| [ai-tech-video-production](./ai-tech-video-production/) | 将已剪好的中文 AI 科技口播制作成横竖版 MP4，支持全屏章节页、真人显示切换、按需字幕和可编辑工程 | 中文 |
| [ai-tech-video-assets](./ai-tech-video-assets/) | 规划或制作口播图片、HTML 动效和实操素材，提供素材表与剪辑交接说明 | 中文 |
| [video-use](./video-use/) | 原始视频转写、精剪与剪后时间线交接，内置 manim-video | 英文 |
| [codex-imagegen](./codex-imagegen/) | Claude 通过本地 Codex 内置 GPT Image 2 生成图片并交接本地 PNG | 中文 |
| [video-talkcraft](./video-talkcraft/) | 按需提供口播分镜、动效卡、转场与组件；遵循独立许可 | 中文 / 英文 |
| [santu-ai-voiceover-editing](./santu-ai-voiceover-editing/) | 把中文文案做成“三土学AI”黑底头像声波竖屏口播，包含 MiniMax TTS、黑底插画、字幕安全带、Remotion 成片和封面 | 中文 |
| [santu-ai-voiceover-illustrations](./santu-ai-voiceover-illustrations/) | 把中文 AI/商业文案拆成黑底 gpt-image2 西装小人简笔画素材方案，并要求图片落盘和记录真实像素 | 中文 |

## 仓库结构

```text
santu61ai-skill/
├── README.md
├── LICENSE
└── <skill-name>/
    ├── SKILL.md
    ├── README.md
    ├── agents/
    ├── references/
    └── templates/
```

每个 skill 的核心说明位于对应目录的 `SKILL.md`，其余目录按需提供 Agent 配置、参考规则、模板或脚本。

## 安装

中文 AI 科技口播的关联技能、安装步骤和调用关系见 [视频制作与关联技能](VIDEO_WORKFLOW.md)。

### 安装单个 Skill

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git
mkdir -p ~/.codex/skills
cp -R santu61ai-skill/ai-tech-video-production ~/.codex/skills/
```

黑底头像声波口播建议同时安装主剪辑 skill 和配图 skill：

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git
mkdir -p ~/.codex/skills
cp -R santu61ai-skill/santu-ai-voiceover-editing ~/.codex/skills/
cp -R santu61ai-skill/santu-ai-voiceover-illustrations ~/.codex/skills/
```

### 每日跟读视频

同时安装 `bayarea-follow-reading` 与 `douyin-copy-extractor` 两个完整目录。前者负责素材归档、数字人回传和成片，后者负责抖音下载与 GPU 转写。使用说明见 [跟读制作 skill](bayarea-follow-reading/SKILL.md)。

```text
使用 $bayarea-follow-reading 处理这些抖音链接，准备跟读素材和数字人驱动音频。
使用 $bayarea-follow-reading 将回传的 GD-001 数字人视频匹配归档，并生成完整跟读视频。
```

数字人目前由用户手动制作；固定背景、蓝色重点字和人物完整缩放由随包脚本完成。Python、FFmpeg 和 MiSans 字体按技能中的运行条件准备。

### 使用软链接

适合希望通过 `git pull` 持续更新技能的用户：

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git ~/santu61ai-skill
mkdir -p ~/.codex/skills
ln -s ~/santu61ai-skill/ai-tech-video-production ~/.codex/skills/ai-tech-video-production
ln -s ~/santu61ai-skill/santu-ai-voiceover-editing ~/.codex/skills/santu-ai-voiceover-editing
ln -s ~/santu61ai-skill/santu-ai-voiceover-illustrations ~/.codex/skills/santu-ai-voiceover-illustrations
```

## 使用方式

在支持 skills 的 Agent 中直接点名调用：

```text
使用 $ai-tech-video-production 将这条已剪好的中文 AI 科技口播视频制作成竖屏 MP4。
口播视频：/path/to/talking-head.mp4
如需字幕或可编辑工程，请在请求中写明。
```

黑底头像声波口播：

```text
使用 $santu-ai-voiceover-editing 把这篇中文文案做成黑底头像声波竖屏口播，并生成 9:16 和 6:7 封面。
封面标题：AI超级团队 03
文案：……
```

只做配图素材：

```text
使用 $santu-ai-voiceover-illustrations 把这篇口播文案拆成黑底西装小人简笔画素材方案，并给出可直接用于 gpt-image2 的 prompt。
```

具体依赖、工作流和输出要求请阅读每个 skill 子目录内的 README。

## 初始化前必读

不同 skill 的依赖不一样，尤其是 `santu-ai-voiceover-editing` 默认带有三土个人定制配置。安装者需要在第一次使用前做一次选择：

- 直接使用三土默认配置：使用仓库内默认头像、固定“三土学AI”黑底风格、MiniMax 克隆音色 `SantuVoice20260618B`。
- 替换成自己的账号和形象：准备自己的 MiniMax API key、克隆音色 `voice_id`、圆形头像/主讲人形象，并按 skill README 修改 `agents/openai.yaml`、`SKILL.md` 或运行时参数。
- 跳过 TTS：如果已有成品音频，可以提供 `audioPath`，让剪辑流程从音频对齐、插画和 Remotion 工程开始。

敏感信息不要提交到仓库。MiniMax API key 应写在本机环境变量或本机 `.env` 中，参考 [MiniMax env 示例](./santu-ai-voiceover-editing/templates/minimax.env.example)。

## 贡献与反馈

欢迎通过 Issue 提交使用反馈、改进建议和新 skill 提案。

## License

三土维护的原创内容采用 [MIT](./LICENSE)。`video-use/` 保留原作者 MIT 声明；`video-talkcraft/` 使用 [PolyForm Noncommercial](video-talkcraft/LICENSE)，其许可注明商业使用需要作者事先授权。各目录内的第三方内容按其原许可分发，详见 [第三方来源与许可](THIRD_PARTY_NOTICES.md)。
