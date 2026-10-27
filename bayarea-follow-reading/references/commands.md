# 操作命令与目录

## 环境

Python 3.10+、FFmpeg/ffprobe、Pillow、NumPy、SciPy。字体使用 MiSans Regular/Medium/Bold，需本机合法安装；不在仓库分发字体。默认字体路径为 `~/Library/Fonts`，其他系统通过 `--font-dir` 指定。

先检查实际依赖；缺包时在本机合适的虚拟环境安装 `Pillow numpy scipy`，不要把环境、模型和缓存提交到仓库。转写另依赖下载技能的 GPU 环境。此处的 FFmpeg 合成不强制 GPU。

以下 `SKILL_DIR`、`LIBRARY`、`SOURCE`、`JOB`、`PLAN`、`AVATAR`、`FONT_DIR` 均由 Agent 根据实际文件设置，不把示例占位文本直接执行。

```bash
python3 "$SKILL_DIR/scripts/follow_reading.py" init \
  --library "$LIBRARY" --source "$SOURCE" --id GD-001 \
  --title 轻舟已过万重山 --day-label 第一天 --person-label 王志文 \
  --source-id 7686459030587940794 --source-day Day81 \
  --source-url https://www.douyin.com/video/7686459030587940794
python3 "$SKILL_DIR/scripts/follow_reading.py" frames --job "$JOB"
python3 "$SKILL_DIR/scripts/follow_reading.py" prepare --job "$JOB" --plan "$PLAN"
```

`init` 返回内容目录；若检测到重复则返回既有目录，不覆盖。下一条先 `status --job "$LIBRARY"` 看当前编号和状态。采集原视频的作者昵称通过 `--author` 保存；人物名 `--person-label` 用于上方画面，与原作者分别记录。

```bash
python3 "$SKILL_DIR/scripts/follow_reading.py" attach --job "$JOB" --avatar "$AVATAR"
# 先实际核对，再把测量和查看得到的 offset、note 写入命令。
python3 "$SKILL_DIR/scripts/follow_reading.py" align --job "$JOB" \
  --offset 0 --visual-checked --content-checked --note '填写本条实际核对依据'
python3 "$SKILL_DIR/scripts/follow_reading.py" render --job "$JOB" --font-dir "$FONT_DIR"
# 实际看图和试听后执行，不把这两个标记当成检查动作。
python3 "$SKILL_DIR/scripts/follow_reading.py" review --job "$JOB" \
  --frames-checked --audio-checked --note '填写本条实际检查范围和结果'
python3 "$SKILL_DIR/scripts/follow_reading.py" status --job "$JOB"
```

数字人多了片头时，`offset` 是该文件中与主音轨 0 秒对应的时间。脚本只接受对齐后时长差不超过 0.2 秒；少量尾差以已查看的静止尾帧补足，不靠改变说话速度。较大差异先检查原因，保留原件，另做明确对齐的副本再接收。

状态：`待提取 → 等待数字人 → 待核对数字人 → 可合成 → 待成片检查 → 成片完成`。文件可用性与状态分别检查，共享盘离线会显示缺文件，不等于文件被删除。

## 目录

```text
GD-001-主题/
├── 01-原始视频/source.mp4
├── 02-提取素材/
│   ├── 右侧素材.mp4
│   ├── 数字人驱动音频.mp3
│   ├── 合成主音轨.wav
│   ├── 完整文案.txt
│   ├── 跟读文案.txt
│   ├── 重点字.json
│   └── 提取计划.json
├── 03-数字人视频/
├── 04-制作工程/          # 字幕背景、参数、检查图、所用脚本与模板
├── 05-成片/              # 每日跟读.mp4、封面.png
├── 检查/原片抽帧/
└── 素材记录.json
```

当前矩阵获客项目默认集合是账号下 `04-视频/每日跟读/`，目录完整归属 XHS-001；如需与 SP 编号关联，在内容记录中附 `account_content_id`，不要把 SP 编号改写成 GD 编号。此前 SP-038 保留，作为已确认样片，不移动或重新编号。

用户只给视频而没说天数时，可按本系列已确认顺序取下一天；已有冲突或无法确定时问一次。人物名未知时留空，不猜。

## 归档

在矩阵获客项目遵守媒体共享归档规则。读取当前项目规则确定路径，不把本机用户名或 SMB 地址固化到通用脚本。`--share-root` 应为已挂载共享盘的 `矩阵获客/素材归档`，不是 URL。

```bash
python3 "$SKILL_DIR/scripts/follow_reading.py" archive --job "$JOB" \
  --project-root "$PROJECT_ROOT" --share-root "$SHARE_ROOT"
```

脚本逐文件核对大小及 SHA-256，复制成功后用软链接替换项目内媒体，保留目录结构；文案、工程代码和元数据留本地。目标存在但内容不一致时停止该次迁移，不覆盖。每次替换保存迁移记录，重复归档跳过已有软链接。此命令不登记发布工作台、不设置排期。
