"""Check media parameters, decode to the end, and optionally export actual frame zero."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import tempfile
from media_common import executable, probe, sha256, write_new_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--first-frame', type=Path)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--height', type=int, default=1920)
    args = parser.parse_args()
    source = args.input.expanduser().resolve(strict=True)
    if args.report.exists() or (args.first_frame and args.first_frame.exists()):
        parser.error('检查输出已存在，请使用新的报告和抽帧文件名')
    ffmpeg = executable(args.ffmpeg)
    before = source.stat()
    info = probe(source, args.ffprobe)
    video = next(x for x in info['streams'] if x['codec_type'] == 'video')
    audio = [x for x in info['streams'] if x['codec_type'] == 'audio']
    failures = []
    if (video['width'], video['height']) != (args.width, args.height):
        failures.append('成片尺寸不符')
    try:
        if abs(float(Fraction(video.get('avg_frame_rate', '0'))) - 30) > 0.01:
            failures.append('帧率不是30fps')
    except (ValueError, ZeroDivisionError):
        failures.append('无法读取有效帧率')
    if video.get('codec_name') != 'h264':
        failures.append('视频不是H.264')
    if any(video.get(k) != 'bt709' for k in ('color_primaries', 'color_transfer', 'color_space')):
        failures.append('未标明完整BT709 SDR色彩信息')
    if not audio:
        failures.append('缺少音轨')
    elif any(x.get('codec_name') != 'aac' for x in audio):
        failures.append('音轨不是AAC')
    with tempfile.TemporaryFile(mode='w+b') as error_log:
        decoded = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(source),
                                  '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'],
                                 stdout=subprocess.DEVNULL, stderr=error_log)
        error_log.seek(0)
        decode_error = error_log.read(8000).decode('utf-8', errors='replace')
    if decoded.returncode:
        failures.append('完整解码失败')
    if args.first_frame:
        args.first_frame.parent.mkdir(parents=True, exist_ok=True)
        frame = subprocess.run([ffmpeg, '-n', '-v', 'error', '-i', str(source), '-map', '0:v:0',
                                '-frames:v', '1', '-update', '1', str(args.first_frame)], capture_output=True, text=True)
        if frame.returncode:
            failures.append('第0帧导出失败：' + frame.stderr[-1000:])
    digest = sha256(source)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        failures.append('检查期间输入发生变化')
    result = {'file': str(source), 'sha256': digest, 'duration': info.get('format', {}).get('duration'),
              'video': video, 'audio': audio, 'full_decode_passed': decoded.returncode == 0,
              'decode_error': decode_error, 'technical_passed': not failures, 'failures': failures,
              'first_frame': str(args.first_frame) if args.first_frame else None,
              'manual_review_required': ['第0帧完整封面并与独立封面核对', '每镜头与过渡画面', '字幕和称呼', '讲话清晰度与BGM', '完整叙事', '人物及外发限制']}
    write_new_json(args.report, result)
    print(json.dumps({'technical_passed': not failures, 'failures': failures, 'report': str(args.report)}, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
