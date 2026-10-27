---
name: codex-imagegen
description: Claude Code 通过本地 Codex CLI 的内置 image_gen 调用 GPT Image 2，生成或修改视频背景、插画和其他图片素材。用户要求 Claude 调 Codex 生图，或 AI 科技视频流程在 Claude 中需要 GPT Image 2 素材时使用；不直连图片 API，不索要 API Key。
---

# Claude 调本地 Codex 生图

Claude 负责素材方案、提示词、工程和验收；本地 Codex 只负责本次图片生成。使用 Codex 已有登录和内置 `image_gen`（GPT Image 2），不调用第三方 router，不调用 `scripts/image_gen.py` API 路线，不提取登录凭据。

## 执行

1. 用 Bash 检查 `codex` 与 Python 3，首次使用运行 `python3 <本技能目录>/scripts/generate.py --probe`。探测只说明 CLI 与开关情况，不能代替真实生图。
2. 把完整提示词写入任务目录的 UTF-8 文件，写清用途、比例、风格、主体位置、字幕/人物安全区、禁止生成的文字。真实截图保持原文件，不用生图伪造实测证据。
3. 解析本 SKILL.md 所在目录，运行脚本。使用绝对路径；提示词通过文件和 stdin 传递，不拼进 shell 命令。

```bash
python3 "<本技能目录>/scripts/generate.py" \
  --prompt-file "/absolute/project/work/image-prompt.txt" \
  --output "/absolute/project/public/media/images/search-background.png"
```

修改或参考图片时，重复添加 `--reference "/absolute/reference.png"`。脚本把图片交给 Codex，要求先查看参考，再使用内置生图工具。每次只生成一张；多张素材逐张执行并查看结果。

4. 等待进程结束。脚本会把请求、Codex JSONL 日志和交接结果放在输出目录的 `.codex-imagegen/<任务编号>/`，最终路径和实际像素写入 `result.json`。返回码非零或 `status != success` 时，不能继续按成功素材使用。
5. Claude 用 Read 查看实际图片，确认构图、文字、参考内容与安全区，再复制或接入媒体目录；工程内使用普通文件，避免渲染 bundle 无法读取外部软链。按需重新生成，不用空白占位图应付。

## 失败处理

- `codex` 缺失或未登录：报告本地缺失项，让用户在本机完成安装或 `codex login`；不要索要聊天中的密钥。
- `image_gen` 不可用、网络失败或输出未落盘：保留日志，报告失败步骤。不要自动切 API、第三方服务或其他模型，不绕过审批和沙箱。
- 非交互任务需要额外审批而停住时，保留现场并说明原因；不添加 `--dangerously-bypass-approvals-and-sandbox`。
- 超时按失败处理。进程结束或文字回复“已生成”都不等于图片成功，必须检查本地 PNG 和实际尺寸。

仅安装本技能不会把 Codex 生图工具加入 Claude。Claude 在本机通过 Bash 调 Codex；无本机终端的 Claude 网页会话不能直接使用这条路线。更多说明见 [运行与交接](references/runtime.md)。
