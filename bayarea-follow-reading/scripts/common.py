"""Shared local media operations; no network requests or platform publication."""
from pathlib import Path
import hashlib, json, os, subprocess, tempfile


def run(args):
    subprocess.run([str(x) for x in args], check=True)


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def stream(path, kind):
    for s in probe(path)['streams']:
        if s['codec_type'] == kind:
            return s
    raise ValueError(f'{path}: missing {kind} stream')


def duration(path):
    return float(probe(path)['format']['duration'])


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def load(path):
    return json.loads(Path(path).read_text())


def record(folder):
    return load(Path(folder) / '素材记录.json')


def update(folder, data):
    save(Path(folder) / '素材记录.json', data)


def ffmpeg(args):
    run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', *args])


def asset(folder, data, name):
    return Path(folder) / data['files'][name]


def ensure_new_output(path):
    # Never follow an archived symlink and silently modify shared media.
    if Path(path).exists() or Path(path).is_symlink():
        raise ValueError(f'Output already exists; keep it and choose a new content folder: {path}')
