# 画面、合成与编码规则

本规则支持横版与竖版；以下竖屏坐标仅为正文分屏示例，用户指定的画幅、品牌和已有工程配置优先。实现方案可调整，真实音频对齐、人物不变形、内容不遮挡和交付完整性必须成立。

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

从工程渲染时设置目标码率；原音轨可直接封装且用户要求纯人声时，优先 `-c:a copy`，保留源音质、时长与时间戳，不受重新编码的 128k 下限约束。如需混音或 FFmpeg 编码，使用高质量渲染输出作为输入。例如（路径替换为本任务文件）：

```bash
ffmpeg -i input.mp4 -c:v libx264 -preset slow -b:v 8M -maxrate 10M -bufsize 20M -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 128k final_hq.mp4
```

检查实际编码参数、码率和画质。目标码率不保证实际平均码率恰好相等；单纯增大已经有损文件的码率不能恢复细节。源渲染质量不足时从工程重渲，不靠重复转码制造大文件。

## Layering

原口播声音只播放一次，使用独立音轨或唯一原视频元素。画面按 `mode` 决定真人是否出现；`chapter/content` 隐藏所有真人层，包括底层原视频和 PIP。隐藏只控制画面，原视频时钟继续，回来时仍使用原视频全局时间。不得因隐藏人物而暂停、裁剪、循环或改变音频速度。

图层顺序为统一背景 → 内容或章节图示 → 可选真人 → 独立字幕。全屏章节保留不透明底色，不通过两层同时透明而漏出真人。字幕按用户请求持续显示，与章节标题分开，不能被转场遮挡。真人隐藏时内容占用完整可读区域，不能只删除人像而留下半屏空位。

HTML/SVG 可使用 [随包组件](composition-components.md)，Remotion 可读取同一状态计算器安排 `Sequence` 与视觉层。其他实现也须遵守同一时间线与可见性规则；不要求为了组件切换原工程的渲染器。

## Asset Layout Safe Area

以下是竖版 `1080x1920` 的默认版式（用户确认过的标准），全屏章节、横版与自定义布局使用各自保护区：

| 区域 | 用途 |
|---|---|
| `Y=0-110` | 背景氛围，不放核心文字 |
| `Y=120-1170` | 正文内容区：标题、截图、图示、标签 |
| `Y=1192-1304` | 字幕区，全片固定在中间偏下，便于短视频平台观看；不放最底部 |
| `X=380-700, Y=1350-1730` | 正文人物小窗（`320x380`，圆角约 26），居中在字幕下方 |
| `X>=940, Y=900-1650` | 平台右侧点赞/评论按钮区，不放小窗和核心信息 |

小窗外扩 `30px` 为人像保护区，核心素材与字幕不得进入。小窗要小：正文段人物不是重点，内容区才是。开头结尾的人物居中卡见 [Host Layout](#host-layout)。

## Subtitle Track

断句和文字来源以 [时间线规则](timeline-workflow.md#按需字幕) 为准。将每条字幕的 `start / end / text / hl`（需高亮的关键词）以及字体、位置、样式写入配置。

默认样式（有网感、科技博主常用）：

- 字体：**抖音美好体 DouyinSansBold**（字节官方 `bytedance/fonts` 仓库，SIL OFL 1.1，可免费商用）。共用副本放 `~/.local/share/ai-tech-video-production/fonts/DouyinSansBold.ttf` 与 `DouyinSans-OFL.txt`；缺失时从 `https://cdn.jsdelivr.net/gh/bytedance/fonts@main/DouyinSans/DouyinSansBold.ttf` 获取并保留许可文件。不要退回 PingFang 等系统黑体当字幕字体。
- 白字，`7px` 黑色外描边 + `0 6px 14px rgba(0,0,0,.6)` 投影。描边用 16 方向 `text-shadow` 模拟，不用 `-webkit-text-stroke`（会吃进笔画）。
- 每条 1–2 个关键词用黄色 `#ffe14d` 高亮：数字、价格、产品名、核心动作或结论词。
- 基础字号 `66px`，最小 `46px`，最大宽 `980px`，行高 `1.12`，字距 `1px`；按字符宽度动态缩字，仍过长则按语义拆条。
- 每条字幕 4 帧轻弹入（scale `0.88→1`），不做花哨逐字动画。
- 位置：竖版全片固定 `Y=1192-1304` 居中，不随段落跳动；人物居中卡、内容区和小窗都按这条带让位。

开头结尾大字、章节标题可同用该字体保持统一；正文说明文字仍用系统黑体。

### 字体加载（Remotion）

在 Remotion 并发渲染中，用 `FontFace(url)` + `delayRender` 异步加载会在后台标签页卡死超时（实测 28s/58s 均超时，单帧 still 却正常）。可靠做法：

1. 用 [scripts/subset_font.py](../scripts/subset_font.py) 按本片用字子集化为 woff2 并生成 base64 模块（DouyinSansBold 自带的 GSUB 表损坏，脚本会丢弃 GSUB/GPOS/GDEF，中文字幕不受影响）。
2. 在模块顶层用二进制构造并立即注册：`new FontFace('Douyin Sans', bytes.buffer, {weight:'700'})` → `document.fonts.add()`；仅当 `status !== 'loaded'` 时才 `delayRender` 等待。
3. 改字幕文字后重新运行子集化，否则新字会回退到系统字体。渲染后抽帧特写字幕确认字形。

## Text Label Components

默认不用发光小矩形框包短句，以免像后台按钮。对比采用分屏对照（`SplitCompare`），步骤或标准采用编号、细线的 HUD 坐标清单（`HudCoordinateList`），也可选择同样清晰的表达。

分屏每侧宜一个身份词和一个动作词；清单每屏宜 3–4 条，每条 2–6 个汉字。内容过多则拆屏，不挤成小字。以琥珀金或冷蓝强调主信息，弱化次要信息。

## Color System

色彩参数集中配置，默认：背景 `#05070d`、正文 `#f7fbff`、次要文字 `#9fb2c7`、琥珀金 `#f6d365`、冷蓝 `#69a8ff`、信号绿 `#1de58c`、警示红 `#ff565d`。

绿色用于扫描、信号、增长等语义，宜占高亮面积约 10%–20%；不要把背景、标题、粒子和图片同时做成青绿。不同 tone 的回退色也应不同。品牌色按用户指定执行。

## Host Layout

先选择 `host/split/chapter/content`，再计算人物和内容区域。

竖版默认（用户确认过的标准）：

- **开头、结尾 `host`**：人物居中缩放卡 `X=140, Y=280, 800x900`（圆角约 40），不用全屏人物。重点大字放卡片上方（`Y≈70-260`）和字幕带下方（`Y≈1390-1550`），字幕在卡片和下方大字之间。
- **正文 `split`**：内容区在上，人物小窗 `320x380` 居中在字幕下方。讲解、截图、指令卡、对比等正文段默认都带小窗，避免画面空；`content` 全屏隐藏人物只用于确需整屏的复杂图示。章节页仍隐藏人物。
- **居中卡 ↔ 小窗**：在两个位置原位交叉淡化约 10 帧（同一源视频时刻渲染两层画面，只改透明度），不做位置插值，避免人物划过字幕带遮住字幕。
- 卡片内 cover 裁切时让脸部（源画面约 `y=380-1240`）落在框中部：`offsetY = clamp(h/2 - 790*scale, h - vh, 0)`。随包 `layout()` 提供 1080×1920 与 1920×1080 的原生起点，也接受等比例其他尺寸；`host.rect` 可覆盖具体位置。构图按素材、脸部与手势调整，不把示例位置固定为所有视频的标准。

- 真人讲述可适当放大，正文配图可缩小或移动；使用原素材等比例裁切，不拉伸。
- 两个连续可见的人物段可平滑插值位置和大小；全屏章节与全屏内容必须完全隐藏真人。
- 真人回归时接上原视频当前时刻。需要入场动效时只改变视觉透明度或位置，不改变源视频起点。
- 横版一般左右分配，竖版一般上下分配；章节与全屏图示单独重排，不使用正文 PIP 留白。
- 检查转场中间帧：两个端点都安全不代表中间路径一定不遮字幕。

## Asset Transitions

相邻素材使用覆盖式淡入：上一层保持不透明，下一层在其上淡入；避免双透明交叉淡化露出口播底图。默认 `crossfadeFrames=10`，空档不超过 `bridgeMaxGapSeconds=2` 时可桥接。

外部无声素材可按原始时长与口播段时长调整播放速度；原口播视频和音频不得使用这一变速规则。素材太长或太短时简化、换静态图或禁用，不强塞播不完的内容。

## Sound Effects

默认在画面卡点加音效，节奏感来自"画面动作 + 对应声音"，不是堆数量。一条 30–40 秒口播约 25–35 个点位。

| 画面动作 | 音效（huashu-design 音效库） | 增益起点 |
|---|---|---|
| 钩子数字落下、章节大标题 | `impact/drop-thud` | -12 ~ -14 |
| 印章/结论盖章、结尾大字 | `impact/brand-stamp` | -9 ~ -12 |
| 切段、全屏页覆盖进入 | `transition/whoosh-fast`、`swipe-horizontal`、`whoosh`、`dissolve` | -14 ~ -17 |
| 标签/芯片弹出 | `feedback/notification-pop` | -14 ~ -15 |
| 流程节点逐个出现、复制按钮、截图强调框 | `ui/click-soft`、`ui/click` | -14 ~ -17 |
| 关键字段高亮 | `magic/sparkle` | -15 |
| 填写/输入 | `keyboard/type` | -15 |
| 自动配置进行中 / 完成 | `magic/ai-process`（-20）/ `progress/complete-done` | -19 |
| 划掉旧做法 | `keyboard/delete-key` | -14 ~ -19 |
| 关键数字结果、达成 | `feedback/achievement`、`feedback/success-chime` | -19 ~ -21 |

- 音效库：`~/.agents/skills/huashu-design/assets/sfx/<分类>/<名>.mp3`（ElevenLabs 生成，说明见该技能 `references/sfx-library.md`）。用到的文件复制进工程 `public/sfx/`，在 `timeline.json` 的 `sfx` 写 `{t, file, gainDb}`，`t` 与画面动作同一帧。
- 混音用 [scripts/mix_sfx.py](../scripts/mix_sfx.py)：每个音效先按峰值归一到 -1 dB，再加 `gainDb`；人声电平不变；`amix normalize=0` + `alimiter`；视频流 copy，音频 AAC 192k。调音效只需重混音，不重渲画面。
- 验收：用成片减原声得到音效残差，逐点比较 0.3 s 窗口内音效与人声电平。说话中的点位音效应低于人声约 3 dB 以上；盖住数字、产品名、结论词的必须降。停顿中的转场、钩子印章可与人声持平。工具无法听音时如实说明只做了电平核对，请用户试听。
- 不在每个字幕切换处都加音效；同一类音效连续出现时降低增益或隔一个点位。

## Deliverables And Cleanup

成片通过 [验收](quality-checks.md) 后，将最终 MP4、实际使用图片和验收图分别放入 `deliverables/final/`、`images/`、`previews/`；有字幕时将可编辑的字幕和样式数据另存 `subtitles/`。交接工程时保留 timeline、依赖配置、说明和所需全部素材。

清理按 [运行环境与清理策略](runtime-cleanup-policy.md) 执行。`bundle-*`、测试导出和验收中间视频在交付后立即清理；能加速近期修改的渲染分段默认保留 7 天，必要时延长至 14 天。共用 Node/Python 环境、转写模型、包管理器缓存、系统 FFmpeg/Chrome 以及已安装的其他 Skill 不属于单个项目，不随本项目清理。

清理前确认交付物没有指向待删除文件，并统计清理前后占用。不得清理源视频、用户素材、工程源码、时间线、依赖配置、工程实际引用的媒体、最终交付物、必要验收记录、其他任务、未知目录或用户要求保留的文件。验收失败或必要素材尚未导出时保留排查现场。

## Validation

读取实际 `package.json`，运行与改动有关、确实存在的检查命令。Skill 不附带 `validate-layering` 脚本，不假定工程有同名 npm 命令；已有检查可复用，否则通过时间线检查与最终渲染验证源视频引用、图层、音轨和遮挡。TypeScript 工程有配置时运行其类型检查。

导出后从最终 MP4 抽取关键与转场帧，检查码率、时长、尺寸、帧率、音轨和播放效果，按 [验收清单](quality-checks.md) 记录实际结果。
