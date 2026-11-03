# 口播剪辑预设

脚本 [talking_head_presets.py](../scripts/talking_head_presets.py) 生成 1080×1920 的 ASS、时间线 JSON，以及可选的透明 MOV 和 MP4 预览。动态字幕另输出独立的 48 kHz 双声道 WAV。渲染需要带 libass 的 FFmpeg 与 ffprobe，并安装所选中文字体。

| 预设 | 使用方式 |
|---|---|
| `typography` 字体和重点字 | 常规字幕默认 Noto Serif SC、白字、无描边、柔和黑影。提供 `focus` 时，第一行稍缩小，第二行用更大的金色字轻弹。可以用 `--font` 换成已安装的思源宋体。阴影由 ASS 单独一层绘制，使用模糊 9 与约 85% 不透明度。 |
| `safe-area` 全屏竖版安全区 | 透明导视包含眼睛参考线、钩子、重点字、常规字幕以及右侧和底部预留区。默认安全矩形 `[90,210,875,1510]`、眼睛 y=640、钩子 y=365、重点字 y=960、字幕 y=1320，单位为 px。导视用于构图预览，成片导出前隐藏。 |
| `dynamic` 动态字幕和音效 | 用语义选择场景，文字在相应位置做入场，配套 WAV 从现有素材库按稳定 ID 读取。动效按原片场景重新实现，使用 FFmpeg/libass 的变换与渐变。 |

安全区坐标是可调起点，导入全屏真人时间线后需用目标平台手机界面复核。对接已有 PiP 或字幕布局时，用目标工程的锚点和保护区，避免套用全屏真人坐标。脚本 `--layout` 可覆盖导出的 `timeline.json` 中 `layout` 对象的同名字段，传入对象本身。

口播项目指定收藏视频的「思源粗宋」时，剪映可直接选择同名素材，实测缓存字库为 `SourceHanSerifCN-Heavy`。独立渲染可传入 `--font "Source Han Serif SC Heavy"`，本机 FFmpeg/libass 已确认选中系统安装的 `SourceHanSerifSC-Heavy`。其他电脑可从 [Adobe 思源宋体项目](https://github.com/adobe-fonts/source-han-serif)安装简体 Heavy，或使用该电脑已有的 Noto Serif SC。

本机剪映字体入口为「文本 → 基础 → 字体」，输入名称后按回车提交。已下载并在测试草稿中选中「研宋体」（`AaYS`）和「汉仪玄宋」（选中后显示「玄宋」，`HYXuanSong-85J`，剪映面板有会员标记）。剪映缓存也已有「字由点字江湖体」和「阳煦体」。这些剪映字体按软件内入口选用。独立渲染用系统已安装、已验证的字库。

### 脱离剪映使用

从[私有仓库](https://github.com/Amazing-soil/ai-tech-video-presets)签出 `fonts` 目录。仓库内的 Adobe 思源宋体 CN Heavy 来自 Adobe 2.003R 发行版，与剪映「思源粗宋」同家族、同字重，剪映缓存为较早的 1.000 版。传字体文件即可渲染，无需安装到系统。

```powershell
python "<技能目录>\scripts\talking_head_presets.py" typography "<新输出目录>" --cues typography.json --font "Source Han Serif CN Heavy" --font-file "<仓库目录>\fonts\source-han-serif\SourceHanSerifCN-Heavy.otf" --overlay --preview
```

`--font-file` 支持 OTF、TTF、OTC 和 TTC，也可用来读取另行取得授权的字库。以字库实际家族名或全名传入 `--font`，试渲时检查 FFmpeg/libass 的 `fontselect`，确认未选到替代字体。ASS 交接时接收方也需要对应字库。其他四款的身份和获取渠道见仓库字体说明。

## 调用

在 Windows 先按技能说明激活共享环境。先按实际音频或字幕时间轴写 cue 数组，时间用相对片段开头的秒数，按顺序排列。普通句只填 `text`，有单独重点行时填 `focus`。

```json
[
  {"start": 0, "end": 1.8, "text": "先让观众看清楚"},
  {"start": 1.8, "end": 3.8, "text": "只强调一个词", "focus": "关键信息"}
]
```

动态字幕的 cue 例子。

```json
[
  {"start": 0.3, "end": 2.0, "text": "为什么总剪不快？", "scene": "hook"},
  {"start": 2.4, "end": 4.1, "text": "先标出真正的重点", "scene": "knowledge"}
]
```

```powershell
python "<技能目录>\scripts\talking_head_presets.py" typography "<新输出目录>" --cues typography.json --overlay --preview
python "<技能目录>\scripts\talking_head_presets.py" safe-area "<新输出目录>" --duration 6 --overlay --preview
python "<技能目录>\scripts\talking_head_presets.py" dynamic "<新输出目录>" --cues dynamic.json --sfx-library "<音效库目录>" --overlay --preview
```

把透明 `overlay.mov` 作为画面上层，从时间线同一起点放入 `sfx.wav`，试听人声与音效的平衡。也可把 `overlay.ass` 交给支持 ASS 的渲染流程，或按 `timeline.json` 在 NLE 重建。字幕 cue 只用短行，超过画幅时拆分。透明 MOV 使用 QuickTime Animation 编码，交接时先验证目标剪辑软件的导入支持。预览 MP4 用于查看样式和节奏。

## 动态字幕场景

| 场景键 | 用途 | 默认动作 | 素材 ID |
|---|---|---|---|
| `hook` | 开头钩子 | 翻入展开 | A-6aa4aac921b4 |
| `emphasis` | 注意重点 | 翻起 | A-95dcb57c5091 |
| `question` | 疑问 | 轻摆并弹出 | A-1e39cca5e2c4 |
| `turn` | 突然转折 | 快速震动 | A-fb35198a9fbf |
| `reveal` | 出现信息 | 折叠翻开 | A-fc9d1154aa6d |
| `data` | 数据相关 | 旋入放大 | A-e2fb7b7806a4 |
| `awkward` | 尴尬 | 放大回弹 | A-7616a68c58f6 |
| `knowledge` | 知识点 | 柔化显现 | A-fb34e5ff5986 |
| `shock` | 震惊 | 模糊溶解 | A-ff7f59e45a26 |
| `word-zoom` | 逐字放大 | 错时逐字缩放 | A-3adee630d553 |

默认将音效起点放在字幕入场，增益 -12 dB，超出 cue 时截短并淡出。原库 `data` 对应组合片段，含相邻示范音效。可以在 cue 中提供其他已就绪的 `asset_id`，或通过 `--gain-db` 调整音轨；交付前试听，检查人声是否清楚。字体与安全区预设可独立运行。动态模式依次读取显式的 `--sfx-library`、环境变量 `SANTU_SFX_DIR`、本机路径 `D:\矩阵获客\音效素材库`。跨设备获取音效库见[私有仓库安装说明](https://github.com/Amazing-soil/ai-tech-video-presets).

原视频参考见[字体设计](https://www.douyin.com/video/7691306368742339049)、[口播排版](https://www.douyin.com/video/7674985181892548593)和[动态字幕与音效](https://www.douyin.com/video/7670463055139427758)。
