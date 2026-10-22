---
name: ai-tech-video-assets
description: 为中文 AI 科技口播规划或制作图片、HTML 动效和实操素材，提供逐段素材表与剪辑交接说明。适用于素材任务；完整视频剪辑使用成片制作流程。
---

# AI Tech Video Assets

将口播文案或真实口播转为可执行的素材方案；用户要求生成素材时继续完成文件与预览验收。只要规划表时交付规划表，不扩大为整片剪辑。

## 核心约定

- 用户要求和现有成片布局优先。独立规划默认 `1080x1920`、右下真人 PiP、底部字幕；若素材将交给其他剪辑工程，先从工程配置读取安全区，不能把两套 PIP 坐标混用。
- 原始音频可用时按实际语义时间点对齐；只有文案时标注估计时长，不能声称完成音频校准。
- 素材核心信息避开字幕和人像，背景可以铺满。每段表达一个意思，实操录屏保留关键操作，避免概念图覆盖真实 UI。
- 用户要求制作即继续制作，不固定等待规划表或动效说明的确认；用户明确要求先选方向时停在相应选择点。

## 按需读取

| 当前工作 | 参考 |
|---|---|
| 拆段与素材选择 | [脚本分段](references/script-segmentation.md)、[素材选择](references/asset-decision-tree.md) |
| 布局、字体、色彩 | [视觉规则](references/visual-rules.md) |
| HTML 动效 | [动效检索与实现](references/motion-search-workflow.md)；需要模式参考时读 [Anime.js patterns](references/animejs-patterns.md) |
| 生成图片 | [图片提示词](references/image-prompt-rules.md) |
| 交付 | [验收清单](references/acceptance-checklist.md) |

## 交付

规划表至少对应口播句子、核心意思、素材类型、画面方向、安全区及真实或估计时间。按需使用 [素材表](templates/asset-map-table.md)、[动效说明](templates/motion-brief.md)、[剪辑师说明](templates/editor-handoff.md)。

生成素材时将文件保存在任务媒体目录，提供实际路径与可查看的预览。缺少某类生成工具时，选用能表达同一意思的已有素材或可用工具；无法满足的要求明确列出。
