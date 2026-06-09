# santu61ai-skill

三土沉淀的 AI Agent Skills 合集。每个 skill 都作为独立子目录维护，可复制到 Codex、Claude Code 或其他兼容 `SKILL.md` 的 Agent 环境中使用。

## Skills

| Skill | 用途 | 语言 |
|---|---|---|
| [ai-tech-video-production](./ai-tech-video-production/) | 把中文 AI 科技口播视频和文案制作成可编辑 Remotion 工程与最终 MP4 | 中文 |

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

### 使用软链接

适合希望通过 `git pull` 持续更新技能的用户：

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git ~/santu61ai-skill
mkdir -p ~/.codex/skills
ln -s ~/santu61ai-skill/ai-tech-video-production ~/.codex/skills/ai-tech-video-production
```

## 使用方式

在支持 skills 的 Agent 中直接点名调用：

```text
Use $ai-tech-video-production to turn my talking-head video and script
into an editable Remotion project and final MP4.
```

具体依赖、工作流和输出要求请阅读每个 skill 子目录内的 README。

## 贡献与反馈

欢迎通过 Issue 提交使用反馈、改进建议和新 skill 提案。

## License

[MIT](./LICENSE)
