# santu61ai-skill

三土沉淀的 AI Agent Skills 合集。每个 skill 都作为独立子目录维护，可复制到 Codex、Claude Code 或其他兼容 `SKILL.md` 的 Agent 环境中使用。

## Skills

| Skill | 用途 | 语言 |
|---|---|---|
| [ai-tech-video-production](./ai-tech-video-production/) | 把中文 AI 科技口播视频和文案制作成可编辑 Remotion 工程与最终 MP4 | 中文 |
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
Use $ai-tech-video-production to turn my talking-head video and script
into an editable Remotion project and final MP4.
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

[MIT](./LICENSE)
