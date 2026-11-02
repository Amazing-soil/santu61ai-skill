"""Read-only checks. Does not install packages, import GPU runtimes, or download models."""
import argparse
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    parser.add_argument('--font-dir', type=Path)
    args = parser.parse_args()
    commands = {name: shutil.which(name) for name in [args.ffmpeg, args.ffprobe, 'node', 'npm', 'clang', 'cmake']}
    fonts = []
    if args.font_dir and args.font_dir.is_dir():
        fonts = [str(p) for p in sorted(args.font_dir.rglob('*')) if p.is_file() and p.suffix.lower() in ('.ttf', '.otf', '.woff', '.woff2')]
    result = {
        'python': sys.executable, 'python_version': platform.python_version(),
        'system': platform.system(), 'machine': platform.machine(),
        'commands': commands, 'font_files': fonts,
        'optional_python_packages': {name: importlib.util.find_spec(name) is not None for name in ['mlx_whisper', 'faster_whisper']},
        'apple_avfoundation_route': platform.system() == 'Darwin',
        'ready_for_basic_inspection': sys.version_info >= (3, 10) and bool(commands[args.ffmpeg] and commands[args.ffprobe]),
        'not_verified': ['字体真实加载与字重', 'GPUPixel运行程序及GPU权限', 'HDR视觉效果', '转写模型与GPU推理', 'HyperFrames/GSAP渲染', '共享盘读写', '人物和外发限制']
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ready_for_basic_inspection'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
