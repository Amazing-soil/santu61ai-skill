"""Deterministic video typography. Full text is retained; overflow needs timed pages."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from common import load

STYLE = load(Path(__file__).resolve().parents[1] / 'assets/style.json')


def fonts(folder):
    folder = Path(folder).expanduser()
    for weight in ('Regular', 'Medium', 'Bold'):
        if not (folder / f'MiSans-{weight}.ttf').is_file():
            raise ValueError(f'Missing MiSans-{weight}.ttf in {folder}; install font or supply --font-dir')
    return lambda size, weight='Medium': ImageFont.truetype(str(folder / f'MiSans-{weight}.ttf'), size)


def tokenize(row):
    result = []
    for seg in row:
        if set(seg) != {'text', 'emphasis'} or not isinstance(seg['text'], str) or not isinstance(seg['emphasis'], bool):
            raise ValueError('Each segment needs text:string and emphasis:boolean')
        if any(ch in seg['text'] for ch in '\n\r'):
            raise ValueError('A text segment cannot contain a newline; use a new row')
        result.extend((ch, seg['emphasis']) for ch in seg['text'])
    if not result: raise ValueError('Empty row')
    return result


def wrap(rows, font):
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines = []
    for row in rows:
        line, width = [], 0
        for ch, strong in tokenize(row):
            w = d.textlength(ch, font=font(STYLE['body_size'], 'Bold' if strong else 'Medium'))
            if width + w > 944 and line:
                # Avoid isolated Chinese punctuation at the beginning of the next line.
                if ch in '，。；：！？、）》”' and len(line) > 1:
                    last = line.pop()
                    lines.append(line)
                    line = [last]
                    width = d.textlength(last[0], font=font(STYLE['body_size'], 'Bold' if last[1] else 'Medium'))
                else:
                    lines.append(line); line = []; width = 0
            line.append((ch, strong)); width += w
        if line: lines.append(line)
    return lines


def draw_page(data, rows, output, font_dir):
    s = STYLE; f = fonts(font_dir)
    lines = wrap(rows, f)
    if len(lines) > s['max_rows']:
        raise ValueError(f'Text needs {len(lines)} lines; supply timed pages in plan.json, do not omit text or shrink the font')
    im = Image.new('RGB', tuple(s['canvas']), s['background']); d = ImageDraw.Draw(im)
    def center(text, y, size, color=None, weight='Medium', max_width=944):
        font = f(size, weight)
        width = d.textlength(text, font=font)
        if width > max_width:
            raise ValueError(f'Text too wide at fixed size {size}: {text}; provide a concise title or label')
        d.text(((1080-width)/2, y), text, font=font, fill=color or s['body'])
    center(s['brand'], 74, 38)
    d.line((72,142,1008,142), fill='#D4DFE2', width=2)
    center('每日跟读',171,52,s['emphasis'],'Bold')
    center(data['title'],243,86,weight='Bold')
    center('  ·  '.join(x for x in (data['day_label'], data.get('person_label','')) if x),351,35,s['muted'])
    for x,y,w,h in s['slots']:
        d.rectangle((x-1,y-1,x+w,y+h),fill='#E9ECEA',outline='#CFD7D7',width=1)
    d.text((68,1008),'跟读文案',font=f(27),fill=s['muted'])
    d.text((822,1008),'蓝字重读',font=f(27),fill=s['emphasis'])
    for i,line in enumerate(lines):
        x=68
        for ch,strong in line:
            font=f(s['body_size'],'Bold' if strong else 'Medium')
            d.text((x,s['body_y']+i*s['line_height']),ch,font=font,fill=s['emphasis'] if strong else s['body'])
            x+=d.textlength(ch,font=font)
    c='#CCDADF'; fill='#E6ECEB'; base=1850
    for x,w,h in [(82,44,54),(136,55,87),(206,38,62),(696,48,88),(760,40,56),(927,53,64)]:
        d.rectangle((x,base-h,x+w,base),fill=fill,outline=c,width=2)
    d.line([(280,1799),(320,1812),(362,1820),(407,1812),(448,1799)],fill=c,width=4)
    d.line([(287,1806),(324,1822),(402,1822),(441,1806)],fill=c,width=3)
    for x in (316,340,364,388,412):d.line((x,1822,x,1850),fill=c,width=2)
    d.polygon([(814,1850),(823,1773),(842,1713),(860,1773),(869,1850)],fill=fill,outline=c)
    d.line((842,1713,842,1850),fill=c,width=2)
    d.polygon([(523,1850),(523,1770),(538,1740),(558,1725),(573,1740),(573,1850)],fill=fill,outline=c)
    d.line((550,1739,550,1850),fill=c,width=2)
    d.line((65,1851,1015,1851),fill=c,width=2)
    d.arc((75,1844,1040,1894),start=2,end=175,fill='#DBE4E4',width=2)
    center('深圳 · 大湾区',1880,24,s['muted'],'Regular')
    im.save(output)
    return len(lines)


def pages(plan, length):
    rows=plan['rows']
    p=plan.get('pages') or [{'start':0,'end':length,'rows':list(range(len(rows)))}]
    ordered=[]; end=0
    for page in p:
        if abs(float(page['start'])-end)>0.001 or float(page['end'])<=end:
            raise ValueError('Pages must be contiguous from 0, with increasing end times')
        end=float(page['end']); ordered+=page['rows']
    if abs(end-length)>0.04 or ordered!=list(range(len(rows))):
        raise ValueError('Pages must cover the full duration and each text row exactly once, in order')
    return p
