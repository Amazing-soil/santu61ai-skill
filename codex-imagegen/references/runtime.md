# 运行与交接

需要 Python 3.10+、本地 Codex CLI、Codex 已登录、内置 `image_generation` 能力可用及网络。脚本使用 `--ignore-user-config` 隔离桌面版专属模型名、第三方 provider 与无关 MCP 配置，认证仍沿用本机 Codex 登录；使用当前 CLI 的默认文本模型，不锁定模型名，也不修改全局配置；每次请求启用内置生图功能，采用 `workspace-write` 沙箱，不绕过权限检查。

`--dry-run` 只生成请求与命令清单，不发起生图。`--probe` 读取 CLI 版本、登录状态和功能开关；均不能证明服务器当前可生图。真实生成需检查 `result.json`、JSONL 工具记录和 PNG 文件，再由 Claude 查看成图。

输出路径若已存在，脚本拒绝覆盖；改用新的文件名。参考图片只读。图片默认先由 Codex 保存到自己的生成目录，再由 Codex 复制为请求的 PNG 输出。父目录下的 `.codex-imagegen/` 是任务记录，不写进技能安装目录。项目公开发布前检查记录是否含未公开提示词与素材路径。

脚本使用 argv 数组和 stdin，不执行提示词中的 shell 内容。不要把密钥写进提示词或生成日志。脚本不读取凭据文件，不修改 Claude/Codex 的权限配置。Codex 和 Claude 的运行权限仍由各自环境决定。

上游说明：[Codex 内置图片生成](https://learn.chatgpt.com/docs/image-generation)、[Codex CLI 参数](https://learn.chatgpt.com/docs/cli/reference)。本技能使用内置 `image_gen`，调用 Codex CLI 本身不表示选择图片 API fallback。
