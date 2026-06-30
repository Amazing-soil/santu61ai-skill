# gpt-image2 图片资产落盘工作流

## 核心原则

一张 gpt-image2 图只有在项目目录里存在可读图片文件，才算生产完成。聊天界面里出现预览图、prompt 已写好、或时间线里有未来路径，都不算完成。

Codex 内置生图能力可以产出图片文件；不要因为聊天里只显示预览就判断“不能保存本地”。先查 `$CODEX_HOME/generated_images/...`，找到新增文件后复制进项目。

## 默认目录

```text
public/media/images/
├── img-01-hook.png
├── img-02-tool-trap.png
├── prompts.json
└── asset-manifest.json
```

命名用 `img-序号-语义.png`，不要用空格、中文文件名或临时下载名。

## 生成顺序

1. 先由 `santu-ai-voiceover-illustrations` 输出每张图的用途和 prompt。
2. 使用内置 gpt-image2 / image generation 能力逐张生成图片；不要先绕去找本地图片 CLI。
3. 内置生图默认会把图片保存在 `$CODEX_HOME/generated_images/...`。每生成一张，先找到该目录里的新增 PNG，再复制到 `public/media/images/` 的确定路径；保留原始生成文件，不要删除。
4. 保存到项目后马上校验文件，而不是等全部生成完再看：

```bash
file public/media/images/img-01-hook.png
sips -g pixelWidth -g pixelHeight public/media/images/img-01-hook.png
```

5. 把通过校验的真实路径和真实像素尺寸写入 `asset-manifest.json` 和 `src/timeline.json`。不要假设图片一定是 `1080x1920`；如果实际是 `941x1672`，就记录 `941x1672`，并让剪辑层按平台安全区等比例轻缩居中显示。

## 查找内置生图文件

生成图片前先记录目录状态，生成后查找最近文件：

```bash
find "${CODEX_HOME:-$HOME/.codex}/generated_images" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.webp" \) -mmin -30 -print
```

确认新增文件后复制到项目路径：

```bash
cp "/path/to/generated.png" public/media/images/img-01-hook.png
file public/media/images/img-01-hook.png
sips -g pixelWidth -g pixelHeight public/media/images/img-01-hook.png
```

如果找到了文件但读取失败，先用 `file`、`sips` 或图片查看工具定位格式问题；不要改用代码画图补位。

## 如果没有找到新增图片文件

如果当前生图能力只在聊天里显示图片，且 `$CODEX_HOME/generated_images/...` 中也找不到新增图片文件：

- 立即暂停任务，向用户确认如何把图片保存进项目。
- 不要继续生成后续图片。
- 不要用 Remotion、SVG、Canvas、PIL 或脚本补画主体插画。
- 不要把不存在的 `public/media/images/img-xx.png` 写进可交付时间线。
- 不要切换到外部生图工具，除非用户明确要求。

## prompts.json

建议保存为：

```json
[
  {
    "id": "img-01-hook",
    "segmentIds": ["seg-01-hook"],
    "purpose": "从追 AI 工具转向研究商业",
    "prompt": "...",
    "expectedPath": "public/media/images/img-01-hook.png"
  }
]
```

## asset-manifest.json

建议保存为：

```json
[
  {
    "id": "img-01-hook",
    "path": "public/media/images/img-01-hook.png",
    "source": "gpt-image2",
    "status": "ready",
    "width": 941,
    "height": 1672
  }
]
```

`status` 只能在文件真实存在并可读后写成 `ready`。
