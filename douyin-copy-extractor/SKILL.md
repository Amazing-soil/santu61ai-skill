---
name: douyin-copy-extractor
description: 从抖音分享口令或分享链接解析作品，下载所需媒体，并提取作品基本信息、发布文案和经校对的完整口播文案。用户要求下载抖音视频、提取文案、字幕、逐字稿、口播稿或批量处理抖音链接时使用；不负责分类、查重、入库或决定保存位置。
---

# 抖音链接与文案提取

把抖音分享内容处理成通用的结构化文本。默认输出作品基本信息、发布文案和口播文案校正版；分类、查重、入库和长期保存由调用它的项目决定。

## 能力边界

本技能负责：

- 解析抖音分享口令、短链和标准作品链接。
- 获取作者昵称、视频时长、作品 ID、标准作品链接和发布文案。
- 下载提取所需的音频或视频。
- 使用 GPU 完成中文语音转写。
- 对纯画面文字视频或低置信度片段抽帧 OCR。
- 校正同音字、专有名词、数字、标点和断句。
- 返回通用 JSON 或人类可读文本。

本技能不负责：

- 后续分类、查重和入库。
- 更新项目索引、素材库或数据库。
- 自行决定长期保存目录和文件命名。

如果用户明确要求保存、分类或入库，先完成本技能的提取，再把提取结果交给用户指定的项目流程；不要把项目规则写回本技能。

## 运行位置

技能安装在全局目录。执行脚本前设置：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/douyin-copy-extractor"
```

所有脚本都从 `$SKILL_DIR/scripts/` 调用，不依赖当前项目目录。

## 硬约束

1. 严格单并发。每条视频开始前执行 `pipeline.py begin`；上一条没有 `finish` 或 `abort` 时，不得开始下一条。
2. GPU 是语音转写的硬门槛。Apple Silicon 使用 MLX/Metal；NVIDIA 使用 faster-whisper/CUDA FP16。检测失败时停止，不降级到 CPU。
3. 视频、音频、抽帧图片、浏览器状态和中间 JSON 只能写入 `begin` 返回的 `job_dir`。
4. 默认完成后删除全部临时文件。只有用户明确要求保留原视频或音频时，才在清理前复制到用户指定的位置。
5. 最终文本记录只允许 `basic_info`、`publish_copy`、`corrected_transcript` 三个顶层字段。
6. 失败时关闭浏览器并执行 `abort`，不得遗留任务锁或单条视频临时文件。

## 单条处理流程

### 1. 开始任务

```bash
python3 "$SKILL_DIR/scripts/pipeline.py" begin --source '<抖音分享文本或链接>'
python3 "$SKILL_DIR/scripts/pipeline.py" probe
```

保存输出中的 `token` 和 `job_dir`。

### 2. 解析、下载和 GPU 转写

批量任务仍然一次只处理一个链接：

```bash
python3 "$SKILL_DIR/scripts/extract_one.py" \
  --token '<token>' \
  --job-dir '<job_dir>' \
  --url '<抖音分享链接>' \
  --session '<本条视频独立会话名>'
```

助手会解析短链、读取页面信息、下载媒体、执行 GPU ASR，并在退出前关闭浏览器。页面与下载细节见 [references/workflow.md](references/workflow.md)。

输出中的 `raw_transcript` 是原始识别结果，必须校正后才能作为最终口播文案。

### 3. 校正口播文案

基于 ASR 分段、发布文案、上下文和必要的画面文字校正：

- 修正同音字、专有名词、数字、标点和明显断句。
- 删除纯口吃和无意义重复，但不删除观点、案例、步骤、转折或行动号召。
- 按语义分段，保留清单编号和顺序。
- 不确定处写 `[听不清]`，不得补写视频中没有的内容。
- 纯画面文字视频或低置信度片段，使用 `scripts/vision_ocr.swift` 对少量抽帧图片做 macOS Vision 中文 OCR。

OCR 图片必须放在 `job_dir`，不对正常口播视频全量抽帧。

### 4. 生成和校验结果

在 `job_dir` 内生成 `record.json`，遵循 [references/output-contract.md](references/output-contract.md)：

```bash
python3 "$SKILL_DIR/scripts/pipeline.py" validate \
  --token '<token>' \
  --record '<job_dir>/record.json'
```

### 5. 返回结果并清理

校验通过后执行：

```bash
python3 "$SKILL_DIR/scripts/pipeline.py" finish \
  --token '<token>' \
  --record '<job_dir>/record.json'
```

`finish` 会输出最终 JSON、删除整个 `job_dir` 并释放任务锁。默认直接把结果返回给用户，不写入任何项目。

如果用户明确要求保存原视频、音频或文本文件，必须在 `finish` 前复制到用户指定路径；不得自行选择目录。

## 失败与恢复

本条任务无法继续时，先关闭专用浏览器会话，再执行：

```bash
python3 "$SKILL_DIR/scripts/pipeline.py" abort --token '<token>'
```

上次进程异常退出时先用 `status` 检查。只有确认任务已经失效且超过两小时，才能执行：

```bash
python3 "$SKILL_DIR/scripts/pipeline.py" recover --older-than-seconds 7200
```

## 批量输入

链接按队列顺序处理。每条视频必须完成：

```text
begin → 解析和下载 → GPU转写 → 校正 → validate → finish
```

禁止批量下载后集中转写，禁止多进程、线程池或多个浏览器会话并行处理不同视频。
