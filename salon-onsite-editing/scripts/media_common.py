"""Small, standard-library helpers; all media paths come from the caller."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def executable(value):
    result = shutil.which(str(value))
    if not result:
        raise ValueError(f'找不到程序：{value}')
    return result


def probe(path, ffprobe='ffprobe'):
    run = subprocess.run([executable(ffprobe), '-v', 'error', '-show_streams',
                          '-show_format', '-of', 'json', str(path)],
                         capture_output=True, text=True, timeout=120)
    if run.returncode:
        raise ValueError(run.stderr.strip()[-2000:] or 'ffprobe失败')
    return json.loads(run.stdout)


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            result.update(data)
    return result.hexdigest()


def write_new_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write('\n')
