# Anime.js Patterns

用于选择动效模式。`anime.setDashoffset`、`anime.stagger` 等写法是 Anime.js 旧版 API 示例；先检查工程版本，按对应官方 API 实现，不直接套到新版。下列关键词与视觉方式可独立复用。

## Recommended Patterns

### SVG Line Drawing

适合：趋势、差距、轨迹、效率曲线。

关键词：

- curve
- gap
- growth
- path

常用 Anime.js 能力：

- `anime.setDashoffset`
- `strokeDashoffset`
- timeline

### Stagger Reveal

适合：少量节点、模块、关键词依次出现。

关键词：

- steps
- nodes
- chips
- modules

常用能力：

- `anime.stagger`
- `opacity`
- `translateY`
- `scale`

### Scale Punch

适合：观点、判断、核心大字。

关键词：

- big word
- impact
- reveal
- punch

常用能力：

- `scale: [.7, 1.05, 1]`
- `opacity`
- `translateY`

### Orbit / Radial Motion

适合：任务中心、工作台、协作、工具围绕任务。

关键词：

- orbit
- radial
- center task
- workbench

常用能力：

- `rotate`
- `scale`
- `stagger`
- SVG connector drawing

### Particle Field

适合：科技氛围、信号感。

规则：

- 只能做背景氛围。
- 不能承载信息。
- 不能进入底部后变成视觉噪音。

## Default Timing

4 秒动效：

| 时间 | 内容 |
|---|---|
| 0-0.6s | 背景/粒子启动 |
| 0.6-1.4s | 核心大字进入 |
| 1.4-2.8s | 主视觉动势展开 |
| 2.8-4.0s | 画面稳定，给剪辑停留 |
