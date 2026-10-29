#!/usr/bin/env python3
"""Install only this skill; never install the surrounding skills collection."""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SKILL = 'douyin-favorites-kb'
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', '.venv', '.git')


def digest_tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and
            '__pycache__' not in p.parts and p.suffix != '.pyc' and p.name != '.DS_Store'}


def install(source, destination, replace=False):
    source = source.resolve()
    destination = destination.expanduser().absolute()
    if destination.is_symlink():
        raise ValueError('目标是软链接；请自行检查其来源，安装器不会覆盖。')
    if destination.resolve() == source or destination.resolve().is_relative_to(source):
        raise ValueError('目标不能是安装源或安装源内部。')
    if destination.exists() and not replace:
        raise ValueError('目标已存在。先保留本地改动；确认更新时加 --replace，旧目录会自动备份。')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.skill-install-', dir=destination.parent))
    backup = None
    try:
        shutil.copytree(source, staging / SKILL, ignore=IGNORE)
        if digest_tree(source) != digest_tree(staging / SKILL):
            raise ValueError('安装内容校验失败。')
        if destination.exists():
            backup = destination.with_name(SKILL + '.backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            # Store backups outside the host's skills scan directory.
            backup_dir = destination.parent.parent / 'skill-backups'
            backup_dir.mkdir(exist_ok=True)
            backup = backup_dir / backup.name
            destination.rename(backup)
        try:
            (staging / SKILL).rename(destination)
        except OSError:
            if backup:
                backup.rename(destination)
            raise
        return {'installed': str(destination), 'backup': str(backup) if backup else None,
                'next': '重开对话并运行 scripts/doctor.py --full；安装完成不代表已登录或已通过采集验收。'}
    finally:
        shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=['codex', 'claude'], default='codex')
    parser.add_argument('--skills-dir', type=Path, help='宿主实际技能根目录，不含技能名；用于自定义位置')
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    root = args.skills_dir or Path.home() / ('.agents' if args.host == 'codex' else '.claude') / 'skills'
    result = install(Path(__file__).resolve().parents[1], root / SKILL, args.replace)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
