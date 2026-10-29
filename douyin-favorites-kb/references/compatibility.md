# 兼容性与验证范围

## 宿主与系统分开判断

| 层级 | 条件 |
|---|---|
| 识别技能 | 宿主能读取标准 `SKILL.md`；Codex 另提供 `agents/openai.yaml` 展示信息 |
| 管理知识库 | Python 3.10+；macOS/Linux 使用 flock，Windows 使用 msvcrt 字节锁 |
| 采集本人收藏 | 当前 Agent 能执行 Ego CLI，Ego 可连接且本人登录有效 |
| 音频转写 | Apple Silicon + MLX/Metal，或 NVIDIA + CUDA/faster-whisper；不降级 CPU |
| OCR | 随包 Swift/Vision 脚本仅支持 macOS；其他系统需宿主实际提供的图像识别能力 |
| 定时 | 由宿主的调度功能另行配置，本包没有常驻进程或自动安装的定时器 |

## 已知验证范围

- 原收藏流程在 macOS、Codex、Ego 与 MLX/Metal 环境中完成过三条真实收藏提取。该结果不代表每台电脑、每个账号或每条内容都可提取。
- 发布包的 6 项离线测试在 macOS、Windows、Linux 的 GitHub Actions 环境均已通过（[测试记录](https://github.com/Amazing-soil/santu61ai-skill/actions/runs/40878102664)），检查单技能安装、已有文件保护、知识库初始化、查重、改分类、重试、文件锁和提取器任务清理。离线测试不连接抖音，不证明浏览器登录或完整采集可用。
- Codex 安装目录按官方文档配置。本机 WorkBuddy 5.9.2（macOS）已通过原生“上传技能”导入 ZIP，技能出现在“已安装”列表且已启用。WorkBuddy 应用内完整采集、Windows/NVIDIA 全链路仍需在相应环境中验收；安装成功不等于真实同步成功。
- 本机 Apple M4 上，发布包的 `doctor.py --full` 已通过 Python、FFmpeg、Ego 命令和 MLX/Metal GPU 自检。
- CUDA 依赖提供范围约束，未生成跨平台全量依赖锁。升级底层驱动或 Python 后应重新运行自检和一条真实视频测试。

## 提取运行时来源

`scripts/extractor/pipeline.py`、`scripts/extractor/vision_ocr.swift` 及 `references/output-contract.md` 随本技能一起发布，来源是同仓库的 `douyin-copy-extractor`，遵循 MIT。这样安装收藏技能时无需再装全局提取技能，也不会因项目中另一个同名技能写入其他素材库。

更新这些文件时须核对三字段结果契约与独立提取技能，运行包内测试。此技能不调用独立提取技能的 `extract_one.py`，因此不需要其 agent-browser 依赖。

## 安装入口依据

- [Codex：Build skills](https://learn.chatgpt.com/docs/build-skills)
- [WorkBuddy：技能](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)
- [Ego lite](https://lite.ego.app/)
- [faster-whisper 环境要求](https://github.com/SYSTRAN/faster-whisper#requirements)
