# 视频制作与关联技能

这组技能用于中文 AI 科技口播，从原始素材精剪、素材规划到成片与工程交接。按当前任务调用对应技能。

## 调用关系

```text
原始视频 ── video-use 精剪 ── 剪好的口播 ── ai-tech-video-production ── MP4 / 工程
                                   │                 │
                                   │                 └─ 按需读取 video-talkcraft 分镜与动效
                                   └─ ai-tech-video-assets 独立规划或制作素材

video-use/skills/manim-video：需要数学或技术动画时按需调用
```

| 技能 | 使用时机 | 范围 |
|---|---|---|
| [ai-tech-video-production](ai-tech-video-production/SKILL.md) | 已剪好的真实口播需要成片 | 统一真实音频时间线、真人布局、章节页、B-roll、动效、按需字幕与导出 |
| [ai-tech-video-assets](ai-tech-video-assets/SKILL.md) | 只需要规划或制作素材 | 图片、HTML 动效、实操素材与剪辑交接 |
| [video-use](video-use/SKILL.md) | 原始口播尚未精剪 | 确认精剪策略后交接剪好的视频、媒体参数与剪后时间线 |
| [video-talkcraft](video-talkcraft/SKILL.md) | 重点段落需要复杂分镜或动效 | 按主技能接入规则选择组件，使用同一主时间线 |
| [manim-video](video-use/skills/manim-video/SKILL.md) | 需要数学、算法或技术动画 | Video Use 内置技能，包含脚本与参考文档 |
| [codex-imagegen](codex-imagegen/SKILL.md) | Claude 中需要 GPT Image 2 图片 | 调本地 Codex 内置生图，交回经过检查的本地 PNG |

主技能的接入约定见 [TalkCraft 接入说明](ai-tech-video-production/references/talkcraft-integration.md)。Video Use 在此次精剪交接中只做前置精剪；TalkCraft 的独立制作默认值按主技能接入规则适配。主技能自带无 npm 依赖的章节、运动与真人切换组件。

## Claude Code 安装与调用

将下列 6 个完整技能目录软链到 `~/.claude/skills/`，目标存在时先核对，不覆盖同名真实目录。软链指向稳定的仓库源文件，更新源文件后各入口使用同一份说明：

| Claude 入口 | 仓库路径 |
|---|---|
| `/ai-tech-video-production` | `ai-tech-video-production/` |
| `/ai-tech-video-assets` | `ai-tech-video-assets/` |
| `/video-use` | `video-use/` |
| `/video-talkcraft` | `video-talkcraft/` |
| `/manim-video` | `video-use/skills/manim-video/` |
| `/codex-imagegen` | `codex-imagegen/` |

例如首次安装单个入口：

```bash
mkdir -p ~/.claude/skills
ln -s "/absolute/path/to/santu61ai-skill/ai-tech-video-production" ~/.claude/skills/ai-tech-video-production
```

按表为其余入口建立软链，保留完整目录与第三方许可。新开 Claude Code 会话检查技能是否出现，按实际加载结果判断安装，不能只看目录存在。

Claude 使用方式：

```text
/ai-tech-video-production 将 /absolute/path/口播.mp4 做成竖屏视频。
按真实口播对齐中文字幕，保留真实截图，开头结尾用居中缩放人物。
需要背景图时调用本地 Codex 的 GPT Image 2；交付成片和可编辑工程。
```

本机能力与工具对应见 [Claude 运行说明](ai-tech-video-production/references/claude-code.md)。GPT Image 2 一律由 Claude 通过 [codex-imagegen](codex-imagegen/SKILL.md) 调本地 Codex 内置 `image_gen`，沿用 Codex 登录；不在 Claude 里索要图片 API Key，不直接调用第三方 router。首次检查后还要真实生图与查看成图，不能把功能开关当作成功证据。

## Codex 安装

首次克隆并安装全部关联目录：

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git ~/santu61ai-skill
mkdir -p ~/.codex/skills
for skill in ai-tech-video-production ai-tech-video-assets video-use video-talkcraft codex-imagegen; do
  cp -R ~/santu61ai-skill/"$skill" ~/.codex/skills/
done
```

`manim-video` 随 `video-use` 一起复制，Video Use 通过目录内相对路径读取。需要在 Agent 中独立发现它时，可额外注册：

```bash
ln -s ~/.codex/skills/video-use/skills/manim-video ~/.codex/skills/manim-video
```

已有同名目录时先保留个人配置，再同步对应目录。希望持续跟随仓库更新时，可在首次安装时将 `cp -R` 换为 `ln -s`，之后在仓库中运行 `git pull --ff-only`。复制安装的目录需在拉取仓库后单独同步。安装后重新加载 Agent 的技能列表。

## 运行依赖

| 工作 | 运行条件 |
|---|---|
| 规划素材、阅读分镜 | Agent 可读取完整技能目录 |
| 主技能章节与真人示例 | Node.js 用于检查，浏览器用于预览，Python 静态服务可用于加载模块 |
| 视频探测、剪辑与导出 | FFmpeg / ffprobe；渲染器按具体工程配置 |
| Remotion 工程 | Node.js、项目匹配的 Remotion / React 与浏览器；不随 Skill 自动安装 |
| Video Use 精剪 | Python 3.10+，按 [安装说明](video-use/install.md) 安装；默认转写需自行配置 ElevenLabs API key |
| TalkCraft | 按其 [README](video-talkcraft/README.md) 检查 Node、Python、FFmpeg、字级对齐与组件依赖；仅按需使用的能力需要相应依赖 |
| Manim 动画 | Python 3.10+、Manim CE、FFmpeg，按动画内容安装 LaTeX 与字体，详见其 [README](video-use/skills/manim-video/README.md) |
| 图片与网页素材 | Codex 内置生图；Claude 经本地 Codex CLI 调用。另需可用的真实录屏或浏览器，生成示意图与真实证据分别标明 |

Python、Node、模型、浏览器与服务凭证均需在使用者的环境准备。仓库不包含虚拟环境、依赖缓存、模型、密钥或个人口播视频。TalkCraft 自带的演示媒体只用于其组件演示，遵循目录内的来源与使用说明。

## 使用示例

```text
使用 $ai-tech-video-production 将 /path/to/edited-talking-head.mp4 制作成竖屏 MP4。
需要按真实口播安排真人、全屏章节与素材，按需使用 TalkCraft 动效。
默认不加字幕；保留实际使用的图片与验收图。
```

```text
这条素材尚未精剪。先用 $video-use 提出精剪策略，确认后完成精剪，
再交给 $ai-tech-video-production；字幕与画面使用剪后时间线。
```

```text
使用 $ai-tech-video-assets 只为这篇口播规划素材，提供逐段素材表与画面方向。
文案：……
```

## 来源与许可

三土维护的两个 AI Tech 技能使用仓库 MIT 许可。Video Use 保留 Browser Use 的 MIT 声明。TalkCraft 保留 Vincent Wei 的 PolyForm Noncommercial 许可及第三方声明，其许可注明商业使用需作者事先授权。具体文件见 [第三方来源与许可](THIRD_PARTY_NOTICES.md)。

## 湾区每日跟读视频

```text
抖音链接 → douyin-copy-extractor → 下载视频与校对文案
本地视频 ────────────────────────┘
             ↓
bayarea-follow-reading：右侧视频＋驱动音频＋文案重点字
             ↓
用户手动生成数字人 → 回传对应 GD 编号 → 固定模板合成 MP4 与封面
```

该流程使用 [bayarea-follow-reading](bayarea-follow-reading/SKILL.md)，与 AI 科技口播的布局、字幕、音效默认值分开。读取素材记录即可跨会话继续；不会自动调用数字人服务或发布平台。安装时同时复制它和 `douyin-copy-extractor`，字体、FFmpeg 与 Python 依赖按 [操作说明](bayarea-follow-reading/references/commands.md) 检查。
