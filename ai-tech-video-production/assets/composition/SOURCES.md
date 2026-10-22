# 组件实现与外部依赖

- `motion.mjs` 由本技能实现：分段二次缓动、多项式回弹、淡入淡出、de Casteljau 贝塞尔求值及 SVG 描边进度。所有函数由调用方传入时间或进度，不创建独立播放时钟。
- `chapter.mjs`、`composition.mjs`、`player.mjs` 和示例由本技能实现。章节页采用少色、字号层级、编号与标题分层等通用排版方法。
- TalkCraft 为按需接入的外部组件来源，本目录未捆绑其组件。实际调用时记录所用组件、适配内容和适用许可，见 [TalkCraft 接入说明](../../references/talkcraft-integration.md)。
