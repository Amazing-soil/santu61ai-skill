#!/usr/bin/env python3
"""Report real prerequisites. Does not download software or read user accounts."""
import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true', help='执行实际 GPU probe；不下载模型，不读取收藏')
    args = parser.parse_args()
    skill = Path(__file__).resolve().parents[1]
    checks = []
    def check(name, ok, detail):
        checks.append({'name': name, 'ok': bool(ok), 'detail': detail})
    check('python', sys.version_info >= (3, 10), sys.executable + ' / ' + platform.python_version())
    for rel in ['SKILL.md', 'assets/分类规则.md', 'scripts/library.py', 'scripts/extractor/pipeline.py', 'references/output-contract.md']:
        check('file:' + rel, (skill / rel).is_file(), str(skill / rel))
    for exe in ['ffmpeg', 'ffprobe', 'ego-browser']:
        path = shutil.which(exe)
        check(exe, path, path or '未在当前 Agent 的 PATH 找到；见 INSTALL.md')
    mlx = platform.system() == 'Darwin' and platform.machine() == 'arm64'
    module = 'mlx_whisper' if mlx else 'faster_whisper'
    check('asr-package', importlib.util.find_spec(module) is not None, module + '；需安装到上面显示的 Python 中')
    if args.full:
        try:
            result = subprocess.run([sys.executable, str(skill / 'scripts/extractor/pipeline.py'), 'probe'],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
            check('gpu', result.returncode == 0, (result.stdout + result.stderr)[-5000:] or f'退出码 {result.returncode}')
        except (OSError, subprocess.TimeoutExpired) as exc:
            check('gpu', False, str(exc))
    ok = all(c['ok'] for c in checks)
    print(json.dumps({'prerequisites_ok': ok, 'gpu_tested': args.full, 'checks': checks,
                      'manual_checks': ['ego-browser skill 能完整输出当前指南', 'ego-browser nodejs -e "console.log(1)" 可运行',
                                        '本人登录并确认抖音账号与收藏入口', '首条全长转写及正文回读验收'],
                      'note': '检查通过只说明这些依赖就绪；不证明登录、媒体可读、模型下载或真实同步已成功。'},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
