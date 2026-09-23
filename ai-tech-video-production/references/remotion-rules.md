# Remotion Production Rules

以下是中文竖屏口播的默认参数，用户指定的画幅、品牌和已有工程配置优先。实现方案可调整，真实音频对齐、人物不变形、内容不遮挡和交付完整性必须成立。

## Project Contract

建议将临时工程与交付物分开，避免清理时误删成品：

```text
project/
  work/
    package.json
    public/media/source_talking.mp4
    public/media/images/
    public/media/motion/
    src/index.ts
    src/Video.tsx
    src/timeline.json
    out/
  deliverables/
    final/
    images/
    previews/
    subtitles/          # 生成字幕时保留
```

`src/timeline.json` 包含 `fps`、`width`、`height`、`durationSeconds`、`source`、`assetTransitions`、`pip`、`segments`；用户要求字幕时增加 `subtitleStyle`、`subtitles`。路径引用本地可读媒体文件，字段由实际工程解析，不假定这些文件已由 Skill 提供。

## Render Quality Defaults

默认 `1080x1920 / 30fps / H.264`，视频目标码率 `8M`、`maxrate 10M`、`bufsize 20M`，AAC 音频至少 `128k`；复杂运动和录屏可用 `10M-12M`，相应提高 maxrate。低码率预览单独命名，不能替代用户要求的高码率成片。

从工程渲染时设置目标码率；如需 FFmpeg 编码，使用高质量渲染输出作为输入。例如（路径替换为本任务文件）：

```bash
ffmpeg -i input.mp4 -c:v libx264 -preset slow -b:v 8M -maxrate 10M -bufsize 20M -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 128k final_hq.mp4
```

检查实际编码参数、码率和画质。目标码率不保证实际平均码率恰好相等；单纯增大已经有损文件的码率不能恢复细节。源渲染质量不足时从工程重渲，不靠重复转码制造大文件。

## Layering

底层为原口播视频，中层为覆盖素材，上层为同一原口播视频的 PIP。PIP 不能引用素材文件；音频只播放一次，避免底层与 PIP 同时出声。

如有字幕，可在素材与 PIP 之间放局部阴影和字幕文本，布局仍应让人物、字幕互不遮挡。图片与非透明背景可铺满画幅。

## Asset Layout Safe Area

默认正文布局，坐标基于 `1080x1920`：

| 区域 | 用途 |
|---|---|
| `Y=0-260` | 背景氛围，不放核心文字、卡片或流程节点 |
| `Y=280-1080` | 非图片素材的主要可读信息 |
| `Y=1080-1120` | 缓冲装饰；不放必须阅读的内容 |
| `Y=1120-1360` | 为字幕预留，实际字幕还需避开 PIP |
| PIP 实际框外扩 `40px` | 人像保护区；随位置和尺寸更新 |

默认正文 PIP 框是 `X=360-720, Y=1320-1800`，外扩后的保护区是 `X=320-760, Y=1280-1840`。核心素材与字幕均不得进入保护区。开头、结尾人物居中时重新安排标题、背景和短标签，避开脸、嘴、手和胸口。

## Subtitle Track

断句和文字来源以 [时间线规则](timeline-workflow.md#按需字幕) 为准。将每条字幕的 `start / end / text / position` 以及字体、位置、样式写入配置。

默认样式：白字、`fontWeight: 900`、黑色阴影、`letterSpacing: 0`，基础字号 `58px`、最小 `42px`、容器最大宽 `760px`、行高 `1.14`。采用可配置动态字号，保证可读，不用缩字掩盖句子过长。

Mac 字体栈优先 `"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`，字幕组件继承全局字体。黑色阴影可用 `0 3px 10px rgba(0,0,0,0.95), 0 1px 2px rgba(0,0,0,1)`。

正文单行字幕可放 `Y=1120-1260`，多行或侧置时按实际边界检查；不得侵入 PIP 保护区。开头、结尾字幕放人物旁侧或空白区域，不压脸和胸口。用户未要求字幕时只留空间。

## Text Label Components

默认不用发光小矩形框包短句，以免像后台按钮。对比采用分屏对照（`SplitCompare`），步骤或标准采用编号、细线的 HUD 坐标清单（`HudCoordinateList`），也可选择同样清晰的表达。

分屏每侧宜一个身份词和一个动作词；清单每屏宜 3–4 条，每条 2–6 个汉字。内容过多则拆屏，不挤成小字。以琥珀金或冷蓝强调主信息，弱化次要信息。

## Color System

色彩参数集中配置，默认：背景 `#05070d`、正文 `#f7fbff`、次要文字 `#9fb2c7`、琥珀金 `#f6d365`、冷蓝 `#69a8ff`、信号绿 `#1de58c`、警示红 `#ff565d`。

绿色用于扫描、信号、增长等语义，宜占高亮面积约 10%–20%；不要把背景、标题、粒子和图片同时做成青绿。不同 tone 的回退色也应不同。品牌色按用户指定执行。

## Dynamic PIP Defaults

| 阶段 | 位置与大小 | 内容 |
|---|---|---|
| `introHero` | `x=190, y=560, width=700, height=900, radius=42` | 开头约 3 秒，保留钩子背景和少量辅助信息 |
| `bodyBottomCenter` | `x=360, y=1320, width=360, height=480, radius=34` | 正文口播；边框默认 `4px rgba(255,255,255,0.72)` |
| `outroHero` | 与 introHero 相同 | 结尾约 3 秒，保留结论或提问背景 |

默认 `transitionFrames=20`，连续插值位置、大小和圆角；采用等比例裁切，不把原 `9:16` 视频拉伸。开头和结尾的真实边界短于 3 秒时缩短；人物与核心文字互不遮挡，不默认切成全屏纯人像。

## Asset Transitions

相邻素材使用覆盖式淡入：上一层保持不透明，下一层在其上淡入；避免双透明交叉淡化露出口播底图。默认 `crossfadeFrames=10`，空档不超过 `bridgeMaxGapSeconds=2` 时可桥接。

按素材原始时长 `assetDuration` 和口播段时长计算 `playbackRate`；素材太长或太短时简化、换静态图或禁用，不强塞播不完的内容。

## Deliverables And Cleanup

成片通过 [验收](quality-checks.md) 后，将最终 MP4、实际使用图片和验收图分别放入 `deliverables/final/`、`images/`、`previews/`；有字幕时将可编辑的字幕和样式数据另存 `subtitles/`。交接工程时保留 timeline、依赖配置、说明和所需全部素材。

清理按 [运行环境与清理策略](runtime-cleanup-policy.md) 执行。`bundle-*`、测试导出和验收中间视频在交付后立即清理；能加速近期修改的渲染分段默认保留 7 天，必要时延长至 14 天。共用 Node/Python 环境、转写模型、包管理器缓存、系统 FFmpeg/Chrome 以及已安装的其他 Skill 不属于单个项目，不随本项目清理。

清理前确认交付物没有指向待删除文件，并统计清理前后占用。不得清理源视频、用户素材、工程源码、时间线、依赖配置、工程实际引用的媒体、最终交付物、必要验收记录、其他任务、未知目录或用户要求保留的文件。验收失败或必要素材尚未导出时保留排查现场。

## Validation

读取实际 `package.json`，运行与改动有关、确实存在的检查命令。Skill 不附带 `validate-layering` 脚本，不假定工程有同名 npm 命令；已有检查可复用，否则通过时间线检查与最终渲染验证源视频引用、图层、音轨和遮挡。TypeScript 工程有配置时运行其类型检查。

导出后从最终 MP4 抽取关键与转场帧，检查码率、时长、尺寸、帧率、音轨和播放效果，按 [验收清单](quality-checks.md) 记录实际结果。
