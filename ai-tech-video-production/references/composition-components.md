# 章节页、运动与真人显示组件

随包目录 [assets/composition](../assets/composition/) 提供无 npm 依赖的 ES Modules。它实现原生横竖版章节页、四种画面布局、基础运动函数、真人显示切换和按帧画面导出。它是主工程可复用的画面组件，不替代 ASR、素材制作、音频混音或 MP4 编码器。

## 文件与使用

| 文件 | 用途 |
|---|---|
| [motion.mjs](../assets/composition/motion.mjs) | smooth、at、settle、vis、bezier、stroke；无全局 clamp/pr 依赖 |
| [chapter.mjs](../assets/composition/chapter.mjs) | 原创章节排版、编号与标题错峰入场、文字转义与换行 |
| [composition.mjs](../assets/composition/composition.mjs) | 配置检查、按全局帧取状态、横竖版布局、SVG 输出 |
| [player.mjs](../assets/composition/player.mjs) | 单个原视频元素负责真人与唯一声音；隐藏不暂停；按帧 seek 和 Canvas 导出 |
| [example.html](../assets/composition/example.html) | 10 秒交互示例，横竖版切换和本地视频选择 |
| [example.mjs](../assets/composition/example.mjs) | 示例配置及可替换内容绘制函数 |
| [SOURCES.md](../assets/composition/SOURCES.md) | 组件实现及外部依赖说明 |

在 Skill 目录运行 `python3 -m http.server 8768 --bind 127.0.0.1`，用当前任务允许的浏览器打开 `http://127.0.0.1:8768/assets/composition/example.html`。原生模块通过 HTTP 加载，不依赖 `file://`。示例需要不少于 10 秒的口播才能显示真人；未加载视频时只能查看章节和图示。示例不会改动源文件，也不会自动生成 MP4。

将需要的模块及 `SOURCES.md` 一起复制到工程。示例文案仅用于组件检查，生产时替换为本片真实内容。

## 统一时间线

```js
import {createPlayer} from './composition/player.mjs';
const player = createPlayer(document.querySelector('#stage'), {
  width:1920, height:1080, fps:30, totalFrames:300,
  theme:{background:'#101615',ink:'#F2EADB',accent:'#A8DDC3'},
  segments:[
    {id:'a',startFrame:0,endFrame:60,mode:'host'},
    {id:'b',startFrame:60,endFrame:120,mode:'chapter',index:'01',title:'AI工具'},
    {id:'c',startFrame:120,endFrame:300,mode:'split',title:'从一个任务开始'}
  ],
  subtitles:[]
}, {source:'./media/source.mp4',renderContent:({config,state,box}) => {
  // 返回本片编写的 SVG 图示，使用 box 的当前可读区域。
  return '';
}});
await player.ready;
await player.seek(120);              // 原片 4 秒，不是本段 0 秒
const canvas = await player.renderFrame(120); // 同时取到该时刻真人与图示
```

`startFrame` 包含，`endFrame` 不包含。段落必须连续覆盖 `totalFrames`；字幕可有空档，不得重叠。主时钟为原片全局帧号；`localFrame` 仅用于段内视觉动作。迁移现有秒数时间线时显式换算，不维护第二份独立时码。

`mode`：

- `host`：真人为主，可少量辅助文字。
- `split`：真人与图示分区；横版左右、竖版上下。
- `chapter`：不透明背景、大编号、标题，所有真人层关闭。
- `content`：图示使用完整内容区域，所有真人层关闭。

`host.visible=false` 可关闭其他模式的真人；全屏模式禁止设成 true。可用 `host.rect={x,y,width,height}` 覆盖默认人物位置，坐标为原生画布像素，必须避开字幕。原视频按居中等比例 cover 裁切；需要特殊脸部/手势构图时在主工程扩展裁切策略，不拉伸视频。

相邻可见真人段使用 `hostTransitionFrames` 平滑改变大小、位置；跨越隐藏段重新出现时直接对准原片当前时刻。生产中可增加视觉入场，但音频和源时钟始终不变。内容绘制函数读取 `box`，真人隐藏后获得全屏布局，不继续沿用分屏宽度。

## 运动和章节

`at(t,a,b)` 使用分段二次缓动，`settle(t,a,duration)` 使用三次到达曲线叠加多项式轻微回弹，`vis(t,a,b,fade)` 控制可见区间，`bezier(a,b,c,d,p)` 给出曲线路径点。`strokeValues(length,p)` 返回纯数值，可用于 React/SVG；`stroke(element,p)` 用于浏览器路径。所有时间须使用相同单位；不要把绝对秒数和段内帧号混用。

章节页按给定时长压缩入场、保留中间阅读时间并退场。底色保持不透明，防止最后几帧漏出人物。章节 `index/title` 必填，`label` 可选；过长标题会在三行及最小字号范围内处理，仍放不下则报错，要求精简或重新布局。没有读取时长自动保证：仍须结合口述验收。

章节默认同一主题，通过编号、标题、信息结构区分，不自动交替明暗。大标题缩成章节标签等额外承接可按 [TalkCraft 接入](talkcraft-integration.md) 实现，不必同时使用两套章节组件。

## 接入已有渲染工程

- HTML/SVG：使用 `createPlayer`，或只取 `compile/stateAt/renderSVG`。`renderContent` 是可信项目代码；普通文字先用 `escapeXML/textSVG`，不要拼接外部未转义内容。SVG 内图片用于帧导出时应嵌入可读 data URI，避免 Blob 图像中外部资源失效。
- Remotion：导入纯函数 `compile/stateAt` 与 motion；用 `useCurrentFrame()` 的全局帧号驱动状态。人物视觉层按 `state.host.visible` 决定，声音放单独的唯一原音轨；不能将整段音频随人物 `Sequence` 一起卸载。章节 SVG 可由 `renderSVG` 输出，或移植其排版到 React。随包提供 ES Modules；React 包装层由主工程适配并验证。
- FFmpeg 或其他合成：按同一配置关闭所有真人层；时间线由主工程维护。Canvas 帧可作为图像序列输入，导出阶段沿用主工程的色彩转换和媒体检查。浏览器 PNG 是 sRGB 画面，不能只贴 BT.709 标签代替实际转换。

`renderFrame(frame)` 会暂停预览并定位源视频；返回不含音轨的 Canvas。最终音频从原片只封装一次。纯人声能直接复制时比较音频包及时间戳；混音时检查完整人声、响度与峰值。组件示例通过不代表任意新视频已经验收。

## 验证

在 Skill 目录运行 `node scripts/test-composition.mjs`。用浏览器加载示例和一条测试视频，检查连续播放跨越 `host → chapter → split → content → host`，只有一个音视频元素，隐藏期间时钟递增，回归时仍与原片同步。调用 `renderFrame()` 导出章节、全屏内容和回归帧，检查横竖版字体、人物裁切和字幕。必要时取过渡前后多帧；不得把静帧检查写成完整声画审片。
