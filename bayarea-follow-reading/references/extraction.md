# 提取计划

先抽帧并实际看图，后写计划。不能根据视频标题推断画面分区或红字；同一博主也可能换布局。源视频已有边框、文字、水印保持原样，不补造被原片截断的字幕。影视原声、剧名、集数未核实时明确记录未核实。

## 文案数据

`rows` 是完整段落的顺序列表，每段由普通和重点文字构成。每个字段 `emphasis` 必须是布尔值。正文中的真实引号放在 `text` 里；输出重点双引号由脚本生成，两者不要混淆。

示例只说明格式，绝不能当成所有视频的内容或裁剪位置：

```json
{
  "crop": [506, 346, 574, 572],
  "start": 0,
  "end": 30.8,
  "rows": [
    [
      {"text": "关关难过", "emphasis": false},
      {"text": "关关过", "emphasis": true},
      {"text": "，步步难行", "emphasis": false},
      {"text": "步步行", "emphasis": true},
      {"text": "。", "emphasis": false}
    ]
  ],
  "review": {
    "crop_checked": true,
    "transcript_checked": true,
    "emphasis_checked": true,
    "evidence_frames": ["检查/原片抽帧/01-0.00s.png"],
    "note": "写实际查看范围、文案依据及待确认情况"
  }
}
```

- `crop`：显示正向源视频中的 `[x,y,width,height]`，使用偶数像素，全部在画面内。该脚本支持整段固定区域；变化布局应先分段处理。带旋转标记的原片先复制并规范显示方向，再选择裁剪坐标。
- `start/end`：原片时间；默认保留全长。删片头等操作必须有明确依据，不截掉首句或末句。
- `rows` 必须填写全部文案，不能只照搬这个单行示例。文本跨度采用 Unicode 字符位置，不用字节位置。
- `review` 是实际检查记录，不能在查看前直接复制 true。裁剪、文案或红字仍不确定时不要 `prepare`，先把疑点处理清楚。
- `pages` 可省略。全文超过 9 行时，按语音分段换页，例如 `[{"start":0,"end":12.3,"rows":[0,1,2]},{"start":12.3,"end":30.8,"rows":[3,4,5]}]`。时间从裁剪后的素材 0 秒起，最后一页覆盖全部时长；每行恰好出现一次。不要按平均时长盲分，使用语音时间戳和实际段落。

## 下载技能交接

已安装 `douyin-copy-extractor` 时，读它的完整 SKILL.md，按 `begin → probe → extract_one → 校正 → validate → finish` 执行。`extract_one` 会调用浏览器和下载工具；遵守其当前说明。最终三字段文本结果与临时分段转写信息在 `finish` 前复制到本条内容的 `01-原始视频/`；用 `init` 从它的 `job_dir` 保存媒体。若 `init` 命中重复，沿用返回目录。不要在 `finish` 后才找已经被清理的原片。

下载失败时按原技能 `abort`，不能遗留单条任务锁。不要为批量处理启动多个下载任务。

## 本地视频转写

已有校对稿且可复核时直接复用。没有文案时：

1. 用下载技能的 `pipeline.py begin --source '<本地文件说明>'` 获取 token 和 job_dir，再 `probe` 检查 GPU。
2. 把本地视频复制进该 job_dir。
3. 调用 `pipeline.py transcribe --token '<token>' --media '<job_dir/视频.mp4>' --language zh`，输出也放 job_dir。
4. 校对后按该技能的三字段合同生成 record.json；无法得知的来源字段留空，不编作者或 URL。
5. 验证并将标准结果及分段时间信息复制到本条项目目录，再 `finish`；失败则 `abort`。

全过程遵守下载技能的临时目录和单任务锁。GPU 不可用时报告缺项，不能悄悄降级到 CPU。
