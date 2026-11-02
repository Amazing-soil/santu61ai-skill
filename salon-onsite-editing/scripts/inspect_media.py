"""Create a technical source inventory; this does not judge speech or narrative quality."""
import argparse
import json
from pathlib import Path
import sys
from media_common import probe, sha256, write_new_json

MEDIA = {'.mov', '.mp4', '.m4v', '.mkv', '.avi', '.mts', '.webm'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    root = args.input.expanduser().resolve(strict=True)
    if args.output.exists():
        parser.error('输出已存在，请另选本批清单文件，避免覆盖')
    candidates = [root] if root.is_file() else sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in MEDIA)
    if not candidates:
        parser.error('没有找到支持的视频文件')
    entries, errors = [], []
    for source in candidates:
        try:
            stat = source.stat()
            data = probe(source, args.ffprobe)
            video = next(x for x in data['streams'] if x['codec_type'] == 'video')
            audio = [x for x in data['streams'] if x['codec_type'] == 'audio']
            digest = sha256(source)
            current = source.stat()
            if (stat.st_size, stat.st_mtime_ns, stat.st_ino) != (current.st_size, current.st_mtime_ns, current.st_ino):
                raise ValueError('登记期间源文件发生变化')
            entries.append({
                'file': source.name, 'path': str(source), 'resolved_path': str(source.resolve()),
                'bytes': stat.st_size, 'sha256': digest, 'duration': data.get('format', {}).get('duration'),
                'creation_time': video.get('tags', {}).get('creation_time') or data.get('format', {}).get('tags', {}).get('creation_time'),
                'video': video, 'audio': audio,
                'hdr': video.get('color_transfer') in ('smpte2084', 'arib-std-b67') or any('DOVI' in x.get('side_data_type', '') for x in video.get('side_data_list', [])),
                'review': {'narrative': '待查看', 'speech_clarity': '待核听', 'people_and_permissions': '待核对', 'purpose': '待分类'}
            })
            print('已登记 ' + source.name, file=sys.stderr, flush=True)
        except Exception as exc:
            errors.append({'path': str(source), 'error': str(exc)})
    report = {'input': str(root), 'technical_inventory_only': True, 'files': entries, 'errors': errors}
    write_new_json(args.output, report)
    print(json.dumps({'files': len(entries), 'errors': len(errors), 'output': str(args.output)}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
