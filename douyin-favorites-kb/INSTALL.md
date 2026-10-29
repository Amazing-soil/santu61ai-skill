# 安装与第一次运行

这是一个给 Agent 使用的技能，不是双击后自动抓取收藏的软件。请先在本机安装 Codex、WorkBuddy 或其他支持 `SKILL.md` 且能运行本地命令的 Agent。

## 1. 只安装需要的技能

### Codex

已安装 Git 和 Python 3.10+ 的用户，在终端运行：

```bash
git clone https://github.com/Amazing-soil/santu61ai-skill.git
cd santu61ai-skill
python3 douyin-favorites-kb/scripts/install.py --host codex
```

Windows 将 `python3` 换成 `py -3`。安装器只复制 `douyin-favorites-kb`，默认放在 `~/.agents/skills/`，不安装合集中的其他技能。目标已存在时会停止，不会直接覆盖。

没有 Git 时下载 [单技能 ZIP](https://github.com/Amazing-soil/santu61ai-skill/raw/refs/heads/main/downloads/douyin-favorites-kb.zip)，解压后进入包含 `douyin-favorites-kb` 的目录，再执行最后一行安装命令。也可以完整复制该文件夹到 Codex 实际扫描的技能目录。

[Codex 官方目录说明](https://learn.chatgpt.com/docs/build-skills)支持项目 `.agents/skills` 和用户 `~/.agents/skills`。旧环境已有 `~/.codex/skills` 时可以显式指定 `--skills-dir <实际技能根目录>`；不要在多处重复安装同名技能。安装后重开对话；未出现时重启应用。

### WorkBuddy

1. 下载上面的单技能 ZIP，不要上传整个三土技能合集。
2. 按 [WorkBuddy 官方说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)，进入技能板块，选择“添加技能 → 上传技能”，选择 ZIP。
3. 在“已安装”中确认 `douyin-favorites-kb` 已启用，重开对话。
4. 请 WorkBuddy 读取该技能的 `INSTALL.md`，报告实际安装目录，并按下文检查本机依赖。不要假定它与 Codex 共用路径、Python 或浏览器权限。

本包按 `douyin-favorites-kb/SKILL.md` 的单技能目录打包，已在 macOS WorkBuddy 5.9.2 验证原生 ZIP 导入和已安装状态。上传后等待应用完成安全检测，不需要勾选自动安装或跳过检测。若你的 WorkBuddy 版本要求解压后的目录，按界面选择其中的完整文件夹；若拒绝包结构，先保留报错，不把整个合集导入作为替代。当前发布的 WorkBuddy 导入与实机采集验证范围见 [兼容性](references/compatibility.md)。

### Claude Code 或其他宿主

Claude Code 可运行 `python3 douyin-favorites-kb/scripts/install.py --host claude`。其他宿主用 `--skills-dir <宿主实际技能根目录>` 指定位置，或按其官方方式导入单技能 ZIP。仅能阅读 Markdown、不能运行命令或连接本机浏览器的云端聊天环境不能执行完整采集。

## 2. 准备 Python、FFmpeg 和 Ego

| 依赖 | 用途 | 安装 / 检查 |
|---|---|---|
| Python 3.10+，建议 3.11 或 3.12 | 管理知识库与调用转写 | [Python 官网](https://www.python.org/downloads/)，终端检查 `python3 --version`；Windows 为 `py -3 --version` |
| FFmpeg 与 ffprobe | 解码音轨、核对媒体时长 | [FFmpeg 下载](https://ffmpeg.org/download.html)；Mac 已装 Homebrew 可用 `brew install ffmpeg`；Windows 解压适合的构建并把含两个程序的 `bin` 加入 PATH |
| Ego lite 浏览器 | 读取本人已登录的抖音收藏 | 从 [Ego 官网](https://lite.ego.app/)安装对应系统版本，打开应用并完成初次设置 |
| 本机 GPU 与 ASR 包 | 完整音轨转写 | 按下节选择 MLX 或 NVIDIA 路线 |

安装 Ego 后重开终端和 Agent，使 PATH 生效，再检查：

```text
ego-browser skill
ego-browser nodejs -e "console.log('ego-browser ready')"
ffmpeg -version
ffprobe -version
```

Agent 应完整读取 `ego-browser skill` 的输出，以当前浏览器指南为准。若命令不存在，检查 Ego 是否完成初始化、命令是否在 PATH。macOS 常见命令目录为 `~/.local/bin`；Windows 修改 PATH 后需重启终端和应用。

收藏流程通过 Ego 获取媒体，**不需要额外安装 Node.js、npm 或 agent-browser**。随包提取器只负责锁、GPU 转写、验证和清理。

## 3. 安装 GPU 转写依赖

以下用 `$SKILL_DIR` 表示实际技能目录。Mac 代码块是 Bash/Zsh；Windows 是 PowerShell，不能互相照抄变量语法。

### Apple Silicon Mac（M 系列）

```bash
# Codex 默认位置；WorkBuddy 请改为它报告的实际安装路径。
SKILL_DIR="$HOME/.agents/skills/douyin-favorites-kb"
python3 -m venv "$HOME/.venvs/douyin-favorites-kb"
PYTHON="$HOME/.venvs/douyin-favorites-kb/bin/python"
"$PYTHON" -m pip install -r "$SKILL_DIR/requirements-mlx.txt"
"$PYTHON" "$SKILL_DIR/scripts/doctor.py" --full
```

MLX 需要原生 arm64 Python 和可访问的 Metal GPU。不要使用 Rosetta 的 x86 Python。`requirements-mlx.txt` 记录本次本机核验的直接依赖版本；其他依赖由 pip 解析。

### Windows + NVIDIA GPU

1. 安装 NVIDIA 驱动；`nvidia-smi` 应能显示显卡。
2. 根据 [faster-whisper 官方说明](https://github.com/SYSTRAN/faster-whisper#requirements)准备与 CTranslate2 匹配的 CUDA、cuBLAS、cuDNN。当前依赖范围面向 CUDA 12 / cuDNN 9；安装 Python 包不等于装好了驱动或 DLL。
3. 在 PowerShell 运行：

```powershell
# 将这里改为 Codex 或 WorkBuddy 实际的技能目录。
$SkillDir = "$HOME\.agents\skills\douyin-favorites-kb"
py -3 -m venv "$HOME\.venvs\douyin-favorites-kb"
$PythonExe = "$HOME\.venvs\douyin-favorites-kb\Scripts\python.exe"
& $PythonExe -m pip install -r "$SkillDir\requirements-cuda.txt"
& $PythonExe "$SkillDir\scripts\doctor.py" --full
```

NVIDIA 路线已提供安装入口，尚未在实体 NVIDIA 设备完成采集验收。显存不足时先停止并检查模型和设备要求，不暗中切换 CPU。Linux 的知识库脚本可用；完整采集还需能访问的 Ego 浏览器环境，本包不承诺 Linux 无人值守采集。

### 没有可用 GPU

可以管理已经存在的 Markdown 知识库，但不能执行本技能的音频转写。Intel Mac、只有 CPU 的电脑以及无法访问本机 GPU 的沙箱，不满足完整采集条件。`probe` 成功仅是 GPU 检测通过，首条转写还会验证模型下载和实际推理。

## 4. 检查后先做 3 条

`doctor.py` 不安装依赖、不读取收藏、不下载模型。普通检查列出文件、解释器和命令；加 `--full` 执行实际 GPU 检测。返回码 0 表示所检查的依赖通过，1 表示仍有缺项。

把自检输出中的 Python 绝对路径交给 Agent，后续 `library.py` 和 `pipeline.py` 都使用该解释器，不能只在一个终端激活虚拟环境就假定应用也能使用。

1. 在 Ego 里打开抖音并亲自登录，提供本人主页链接。
2. 发送 [README 的首次使用提示](README.md#第一次对-agent-说什么)，选择知识库目录。
3. Agent 核对账号、收藏入口，先处理 3 条。首次转写需要联网下载 Whisper 模型，耗时和空间取决于网络与模型；模型不随 ZIP 分发。
4. 检查三条的来源、作者、完整发布文案、口播开头与结尾、分类和索引。确认满意后再批量。

知识库初始化命令是 `library.py --root <知识库绝对路径> init`。它只建立规则和索引，不采集收藏。首次运行不创建定时任务。

## 5. 更新与卸载

更新前关闭正在运行的同步任务，保留自己改过的技能文件。Git 安装者先在仓库执行 `git pull --ff-only`，然后重新运行安装器并加 `--replace`。安装器把旧目录保存到技能根目录上一层的 `skill-backups/`，避免旧技能仍被宿主扫描；自定义改动需自行合并。ZIP 安装者下载新包后按相同方式更新。WorkBuddy 按“已安装”界面提供的更新/卸载操作处理，先备份本地修改再导入新包。

卸载只删除或卸载技能目录，不删除知识库、虚拟环境、模型缓存或浏览器登录状态。已有定时任务须在原宿主单独停用；删除技能文件不会自动取消定时任务。

## 常见问题

| 现象 | 处理 |
|---|---|
| 装好了但 Agent 看不到 | 重开对话；确认目录内直接存在 `SKILL.md`、技能已启用、没有多套同名入口 |
| 缺少 mlx-whisper / faster-whisper | 检查自检输出的 Python 路径，用同一解释器执行 `-m pip install` |
| `Metal device unavailable` | 核对 arm64 Python、Metal 权限和沙箱；请在能访问 GPU 的本机终端再检查，不直接推断显卡不存在 |
| CUDA DLL / cuDNN 报错 | 按上游说明核对库版本、PATH 和驱动，先让 `doctor.py --full` 通过 |
| 模型下载失败 | 检查模型站点连通性与磁盘空间；不能把空结果或摘要当作全文入库 |
| 找不到 Ego | 完成浏览器首次设置，检查 PATH，重启 Agent |
| 看不到收藏 / 需要验证 | 用户在本机浏览器处理；核对是否本人账号和“收藏”页，不能拿“喜欢”或公开作品替代 |
| 任务锁未释放 | `pipeline.py status` 查看；仅确认旧任务失效且超过两小时后用 `recover --older-than-seconds 7200` |
| 文案为空或过短 | 如实记录待处理，不填假文案通过校验 |
| 不会 PowerShell / 终端 | 将本说明和报错交给当前 Agent，让它先解释缺什么，再按宿主授权完成安装 |
