#!/usr/bin/env python3
"""Build a deterministic single-skill ZIP containing only distribution files."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'douyin-favorites-kb'
DEST = ROOT / 'downloads/douyin-favorites-kb.zip'


def main():
    DEST.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(DEST, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(SKILL.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            if any(p.startswith('.') or p == '__pycache__' for p in path.relative_to(SKILL).parts):
                continue
            if path.suffix not in {'.md', '.py', '.swift', '.yaml', '.txt'} and path.name != 'LICENSE':
                continue
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
    DEST.with_suffix('.zip.sha256').write_text(digest + '  ' + DEST.name + '\n', encoding='utf-8')
    print(DEST)
    print(digest)


if __name__ == '__main__':
    main()
