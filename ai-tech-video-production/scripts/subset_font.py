"""按本片用字子集化字幕字体，输出可直接 import 的 base64 woff2 模块。

用法:
  python3 subset_font.py --font ~/.local/share/ai-tech-video-production/fonts/DouyinSansBold.ttf \
      --text-from work/src/Video.tsx work/src/timeline.json --out work/src/douyinFont.ts
需要 fonttools 与 brotli。改字幕文字后重新运行，否则新字会回退到系统字体。
"""
import argparse, base64, io
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ap = argparse.ArgumentParser()
ap.add_argument('--font', required=True)
ap.add_argument('--text-from', nargs='+', required=True, help='收集用字的源文件（工程代码、时间线、字幕数据）')
ap.add_argument('--out', required=True, help='输出 .ts 模块，导出 FONT_WOFF2 data URI')
ap.add_argument('--export', default='DOUYIN_WOFF2')
a = ap.parse_args()

chars = set(''.join(Path(f).expanduser().read_text(encoding='utf-8') for f in a.text_from))
chars |= {chr(c) for c in range(0x20, 0x7f)} | set('，。、：；！？“”‘’（）·—…￥¥')
font = TTFont(Path(a.font).expanduser())
for t in ('GSUB', 'GPOS', 'GDEF'):  # 抖音美好体 GSUB 表损坏会让子集化报错；中文字幕不依赖排版特性
	if t in font:
		del font[t]
opt = subset.Options(); opt.flavor = 'woff2'; opt.layout_features = []
sub = subset.Subsetter(opt); sub.populate(text=''.join(chars)); sub.subset(font)
buf = io.BytesIO(); font.flavor = 'woff2'; font.save(buf)
Path(a.out).write_text(f"// 自动生成：subset_font.py\nexport const {a.export} = 'data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}';\n", encoding='utf-8')
print(f'{len(chars)} chars, {len(buf.getvalue()) // 1024} KB -> {a.out}')
