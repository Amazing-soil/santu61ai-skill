# 动效检索与实现

先按口播选择表现方式。已有可复用组件能满足任务时直接制作；需要新视觉、用户指定参考，或不确定 API 时才检索。

## 选择与检索

| 意图 | 模式 | 可用检索词 |
|---|---|---|
| 差距、趋势 | 曲线、轨迹 | `animejs svg line drawing` |
| 观点、判断 | 大字出现 | `animejs text reveal` |
| 对比 | 分屏、切换 | `animejs split screen animation` |
| 流程 | 路径、节点 | `animejs path animation` |
| 协作 | 中心任务、环绕 | `animejs orbit animation` |
| 混乱收束 | 粒子或乱线聚拢 | `animejs particles converge` |

实现 API 以项目安装版本及对应官方文档为准；CodePen、Lottie 等示例可作视觉参考，复用代码或资源前确认许可与依赖，不直接执行陌生下载脚本。

## 制作

按 [视觉规则](visual-rules.md) 和目标工程实际安全区统一颜色、字体与布局。每段保留一个核心意思，避免大量小字和不稳定的复杂动效。独立素材默认右下 PiP；交给中下 PIP 工程时采用工程坐标。

用户要求规划时交付 [动效说明](../templates/motion-brief.md)；要求制作时按说明继续生成可运行素材，不增加第二次方向确认。完成后在浏览器或渲染器查看实际动画，检查可读时间、图层和安全区。
