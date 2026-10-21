# 抖音链接与文案提取

从抖音分享链接或分享口令中提取作品基本信息、发布文案和经校对的完整口播文案，供支持 `SKILL.md` 的 Agent 调用。

## 能获取什么

| 内容 | 说明 |
|---|---|
| 基本信息 | 作者昵称、时长、作品 ID、标准作品链接 |
| 发布文案 | 创作者发布的正文和话题标签 |
| 口播文案 | GPU 语音转写后，由 Agent 根据上下文校对、断句和分段 |
| 媒体 | 默认下载转写所需音频；需要保留视频或音频时，在请求中指定保存目录 |
| 画面文字 | 必要时抽少量帧做 OCR；附带的 Vision OCR 脚本仅支持 macOS |

`extract_one.py` 默认优先下载音频，不提供单独的视频下载开关。需要完整视频时，Agent 要按 [页面提取与运行环境](references/workflow.md) 获取视频媒体，并检查画面、音轨与时长；不能把仅含音频的 `media.mp4` 当作完整视频交付。只有转写结果还不等于校对后的最终文案。

## 安装

在本地终端运行：

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git
mkdir -p ~/.codex/skills
cp -R santu61ai-skill/douyin-copy-extractor ~/.codex/skills/
```

若仓库已在本地，进入仓库更新后只复制技能目录即可。目标目录已存在时，先检查和保留自己的改动，避免合并出重复目录。其他兼容 Agent 可将整个 `douyin-copy-extractor` 目录放入其技能目录，并将 `SKILL_DIR` 指向实际安装路径。

## 运行环境

- Python 3.10 或以上、Node.js 和 npm（用于运行 `npx`）、FFmpeg（包含 `ffprobe`）。
- `agent-browser` 及其 Chromium 浏览器。首次运行前执行 `npx --yes agent-browser install`。
- Apple Silicon Mac：使用 MLX/Metal，安装 `mlx-whisper`。
- NVIDIA GPU：安装匹配的驱动、CUDA/cuDNN 和 `faster-whisper`，确保 CTranslate2 能使用 CUDA。
- 无可用 GPU 时会停止，不会自动改用 CPU。Intel Mac 和纯 CPU 环境不满足本技能的转写要求。
- 首次使用需要联网下载浏览器、依赖和模型；之后提取仍需要访问抖音。

Apple Silicon 示例：

```bash
brew install ffmpeg
python3 -m venv ~/.venvs/douyin-copy-extractor
source ~/.venvs/douyin-copy-extractor/bin/activate
python3 -m pip install mlx-whisper
npx --yes agent-browser install
python3 ~/.codex/skills/douyin-copy-extractor/scripts/pipeline.py probe
```

NVIDIA 环境在虚拟环境中安装 `faster-whisper` 后运行同一个 `probe` 命令。FFmpeg、Node.js 和 GPU 驱动需自行安装。运行提取的 Agent 必须使用安装了转写依赖的 Python；新开终端时重新激活虚拟环境，或直接使用其 Python 绝对路径。

不需要随技能分发 API key、Cookie 或登录状态。遇到登录、验证码、访问限制时交由用户在本机处理；本技能不保证每条链接都能成功提取。

## 使用示例

只提取文本：

```text
用 $douyin-copy-extractor 提取这个抖音链接的基本信息、发布文案和完整口播文案：
<粘贴抖音分享链接或分享口令>
```

需要保留视频和文本：

```text
用 $douyin-copy-extractor 提取这条抖音视频，保留完整视频、发布文案和校对后的口播文案。
链接：<抖音分享链接>
保存到：<你的完整目录路径>
```

批量输入按链接顺序逐条完成，不并行下载或转写。分类、查重和入库由用户另外指定，本技能不会自动执行。

## 输出和临时文件

最终文本只含三个顶层字段：

```json
{
  "basic_info": {
    "platform": "抖音",
    "author": "作者昵称",
    "duration": "01:30",
    "work_id": "作品数字ID",
    "source_url": "https://www.douyin.com/video/<作品数字ID>"
  },
  "publish_copy": "发布正文和话题标签",
  "corrected_transcript": "校对后的完整口播文案"
}
```

以上是格式示意，实际作品 ID 必须为数字。不确定的听写内容标记为 `[听不清]`，不补写视频中没有的观点或案例。具体约束见 [提取结果格式](references/output-contract.md)。

每条任务通过 `begin` 创建临时目录和全局锁，完成后通过 `finish` 删除临时文件；失败通过 `abort` 清理。用户要求保留的文件必须在清理前复制到指定目录。模型缓存可以复用。开始提取前可运行 `pipeline.py status` 检查任务状态，不要直接删除仍在使用的锁。

## 文件说明

- [SKILL.md](SKILL.md)：Agent 的工作步骤与约束。
- [scripts/pipeline.py](scripts/pipeline.py)：单任务锁、GPU 检测、转写、结果校验和清理。
- [scripts/extract_one.py](scripts/extract_one.py)：单条页面信息提取与媒体下载、转写。
- [scripts/vision_ocr.swift](scripts/vision_ocr.swift)：macOS 画面文字识别。
- [agents/openai.yaml](agents/openai.yaml)：Agent 展示配置。

代码适用仓库的 [MIT 许可证](../LICENSE)。下载内容的使用和再分发需取得相应授权。
