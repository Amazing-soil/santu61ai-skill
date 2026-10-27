"""把画面（无声 MP4）、原口播人声和卡点音效混成成片；只混一次。

用法:
  python3 mix_sfx.py --picture out/picture.mp4 --voice public/media/source.mp4 \
      --timeline src/timeline.json --public public --out ../deliverables/final/成片.mp4 [--check]
timeline.json 需含 durationSeconds 与 sfx: [{t, file, gainDb}]，file 相对 --public。
每个音效先按峰值归一到 -1 dB 再加 gainDb；人声电平不变。--check 输出每个点位音效残差与人声电平。
"""
import argparse, json, re, subprocess, tempfile
from pathlib import Path

ap = argparse.ArgumentParser()
for k in ('picture', 'voice', 'timeline', 'public', 'out'):
	ap.add_argument('--' + k, required=True)
ap.add_argument('--check', action='store_true')
a = ap.parse_args()
D = json.loads(Path(a.timeline).read_text(encoding='utf-8'))
pub = Path(a.public)

def peak(f):
	err = subprocess.run(['ffmpeg', '-i', str(f), '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
	return float(re.search(r'max_volume: (-?[\d.]+) dB', err).group(1))

peaks, chains, labels = {}, ['[1:a]aformat=sample_rates=48000:channel_layouts=mono[voice]'], ['[voice]']
args = ['ffmpeg', '-y', '-v', 'warning', '-i', a.picture, '-i', a.voice]
for i, c in enumerate(D['sfx']):
	f = pub / c['file']
	peaks.setdefault(f, peak(f))
	ms = round(c['t'] * 1000)
	args += ['-i', str(f)]
	chains.append(f'[{i + 2}:a]aformat=sample_rates=48000:channel_layouts=mono,volume={-1 - peaks[f] + c["gainDb"]:.2f}dB,adelay={ms}|{ms}[s{i}]')
	labels.append(f'[s{i}]')
chains.append(''.join(labels) + f'amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.89:level=false[mix]')
args += ['-filter_complex', ';'.join(chains), '-map', '0:v:0', '-map', '[mix]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
	'-t', str(D['durationSeconds']), '-movflags', '+faststart', a.out]
subprocess.run(args, check=True)
print(a.out)

if a.check:
	import numpy as np
	with tempfile.TemporaryDirectory() as tmp:
		raw = lambda src, n: (subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '48000', '-f', 'f32le', f'{tmp}/{n}'], check=True), np.fromfile(f'{tmp}/{n}', np.float32))[1]
		m, s = raw(a.out, 'm'), raw(a.voice, 's')
	n = min(len(m), len(s))
	# AAC 编码有起始延迟：先找成片与原声的对齐偏移，再相减得到音效残差
	seg = slice(48000, min(n, 144000))
	lag = max(range(-4096, 4097, 8), key=lambda k: float(np.dot(m[seg], np.roll(s, k)[seg])))
	r = m[:n] - np.roll(s, lag)[:n]
	db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
	for c in D['sfx']:
		w = slice(int(c['t'] * 48000), int((c['t'] + 0.3) * 48000))
		x, v = db(r[w]), db(s[w])
		flag = '  <-- 盖住人声，考虑降低' if v > -38 and x > v + 3 else ''
		print(f"{c['t']:6.2f} {c['file']:42s} sfx {x:6.1f} dB  voice {v:6.1f} dB{flag}")
