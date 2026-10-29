#!/usr/bin/env python3
"""Manage a small Markdown library. Browser collection and ASR are coordinated by the host agent."""
import argparse
from contextlib import contextmanager
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


@contextmanager
def library_lock(path):
    # Keep the inode/file in place; deleting it would allow independent locks.
    with path.open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
                lock.write(b'\0')
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.kb-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        if path.read_text(encoding='utf-8') != content:
            raise ValueError('文件回读不一致')
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_state(root, state):
    write(root / '.同步状态.json', json.dumps(state, ensure_ascii=False, indent=2) + '\n')


def work_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{10,25}', value):
        raise ValueError('作品 ID 必须是 10 至 25 位数字字符串')
    return value


def validate_url(wid, url):
    work_id(wid)
    if url != 'https://www.douyin.com/video/' + wid:
        raise ValueError('来源必须是与作品 ID 一致的标准视频 URL')


def categories(root):
    text = (root / '分类规则.md').read_text(encoding='utf-8')
    result = set()
    in_table = False
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if line.startswith('|') and cells[0] == '目录':
            in_table = True
        elif in_table and line.startswith('|'):
            c = cells[0]
            if c and not set(c) <= set('-: '):
                if c.startswith('.') or any(p in ('', '.', '..') for p in c.split('/')) or '\\' in c:
                    raise ValueError('分类目录不可使用绝对路径或父目录')
                result.add(c)
        elif in_table:
            break
    if not result:
        raise ValueError('分类规则缺少目录表')
    return result


def destination(root, category):
    if category not in categories(root):
        raise ValueError('分类不在分类规则的目录表中')
    path = root / category
    if not path.resolve().is_relative_to(root):
        raise ValueError('分类目录越界')
    return path


def split_doc(text):
    if not text.startswith('---\n'):
        return {}, text
    head, body = text[4:].split('\n---\n', 1)
    meta = {}
    for line in head.splitlines():
        key, value = line.split(':', 1)
        meta[key] = json.loads(value.strip())
    return meta, body


def document(meta, body):
    return '---\n' + '\n'.join(k + ': ' + json.dumps(v, ensure_ascii=False) for k, v in meta.items()) + '\n---\n' + body


def entries(root):
    result = {}
    for p in sorted(root.rglob('*.md')):
        if not p.resolve().is_relative_to(root):
            raise ValueError('知识库中存在指向外部的 Markdown 链接')
        text = p.read_text(encoding='utf-8')
        if not text.startswith('---\n'):
            continue
        meta, body = split_doc(text)
        if '作品ID' not in meta:
            continue
        wid = work_id(meta['作品ID'])
        if wid in result:
            raise ValueError('作品 ID 重复，请保留正文后处理：' + wid)
        result[wid] = (p, meta, body)
    return result


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def rebuild(root, state):
    items = entries(root)
    lines = ['# 抖音收藏知识库索引', '', '完整文案保存在分类目录中；分类标准见 [分类规则](分类规则.md)。', '',
             '| 入库日期 | 分类 | 用途 | 标题 | 作者 |', '|---|---|---|---|---|']
    for p, meta, _ in sorted(items.values(), key=lambda e: (e[1]['入库日期'], e[1]['作品ID']), reverse=True):
        rel = quote(p.relative_to(root).as_posix(), safe='/')
        title = cell(meta['标题']).replace('[', '\\[').replace(']', '\\]')
        lines.append(f"| {cell(meta['入库日期'])} | {cell(meta['主分类'])} | {cell('、'.join(meta['用途']))} | [{title}]({rel}) | {cell(meta['作者'])} |")
    if not items:
        lines.extend(['', '尚未入库视频。'])
    write(root / '索引.md', '\n'.join(lines) + '\n')
    state['pending'] = {k: v for k, v in state['pending'].items() if k not in items}
    save_state(root, state)
    return items


def nonempty(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError('缺少非空文字字段：' + key)
    return value


def add(root, state, record, note):
    if set(record) != {'basic_info', 'publish_copy', 'corrected_transcript'}:
        raise ValueError('提取结果必须保持三字段契约')
    basic = record['basic_info']
    if set(basic) != {'platform', 'author', 'duration', 'work_id', 'source_url'}:
        raise ValueError('基本信息字段不符合契约')
    for key in basic:
        nonempty(basic, key)
    wid = work_id(basic['work_id'])
    validate_url(wid, basic['source_url'])
    if basic['platform'] != '抖音':
        raise ValueError('平台必须是抖音')
    existing = entries(root)
    if wid in existing:
        rebuild(root, state)
        return {'status': 'already_exists', 'path': str(existing[wid][0])}
    publish = nonempty(record, 'publish_copy')
    transcript = nonempty(record, 'corrected_transcript')
    if len(transcript.strip()) < 20:
        raise ValueError('转写不足 20 字，请按提取器规则检查，不得补造文案')
    title = nonempty(note, 'title')
    analysis = nonempty(note, 'analysis')
    folder = destination(root, note['category'])
    uses = note.get('uses')
    tags = note.get('tags')
    if not isinstance(uses, list) or any(u not in ('自媒体对标', '知识收藏') for u in uses):
        raise ValueError('用途只能是自媒体对标、知识收藏或空数组')
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        raise ValueError('标签必须是字符串数组')
    if note.get('text_source') not in ('音频转写', '画面文字') or note.get('quality') not in ('已校对', '有听不清片段'):
        raise ValueError('需填写正确的文字来源与校对状态')
    if '[听不清]' in transcript and note['quality'] != '有听不清片段':
        raise ValueError('含听不清片段，请如实标记质量')
    meta = {'标题': title, '作品ID': wid, '来源': basic['source_url'], '作者': basic['author'], '时长': basic['duration'],
            '入库日期': now()[:10], '主分类': note['category'], '用途': list(dict.fromkeys(uses)), '标签': tags,
            '文字来源': note['text_source'], '校对状态': note['quality']}
    body = '\n## 发布文案全文\n\n' + publish + '\n\n## 口播或画面文字全文\n\n' + transcript + '\n\n## 理解与使用\n\n' + analysis + '\n'
    short = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '-', title).strip(' .')[:48] or '未命名'
    path = folder / (wid + '-' + short + '.md')
    if path.exists():
        raise ValueError('目标路径已存在，拒绝覆盖')
    write(path, document(meta, body))
    rebuild(root, state)
    return {'status': 'saved', 'path': str(path)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('init', 'status', 'index'):
        sub.add_parser(name)
    q = sub.add_parser('queue'); q.add_argument('--items', required=True)
    s = sub.add_parser('scan'); s.add_argument('--result', choices=('complete', 'partial', 'blocked'), required=True); s.add_argument('--reason', required=True)
    a = sub.add_parser('add'); a.add_argument('--record', required=True); a.add_argument('--note', required=True)
    f = sub.add_parser('fail'); f.add_argument('--id', required=True); f.add_argument('--reason', required=True)
    r = sub.add_parser('retry'); r.add_argument('--id', required=True)
    m = sub.add_parser('move'); m.add_argument('--id', required=True); m.add_argument('--category', required=True)
    args = p.parse_args()
    root = Path(args.root).expanduser().resolve()
    if args.command == 'init':
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise ValueError('请先运行 init')
    # Persistent zero-byte lock avoids races caused by unlinking an open lock file.
    with library_lock(root / '.同步锁'):
        rules = root / '分类规则.md'
        if args.command == 'init' and not rules.exists():
            write(rules, (Path(__file__).resolve().parents[1] / 'assets' / '分类规则.md').read_text(encoding='utf-8'))
        state_path = root / '.同步状态.json'
        if not state_path.exists() and args.command != 'init':
            raise ValueError('同步状态不存在，请运行 init；已存正文不会被覆盖')
        state = read_json(state_path) if state_path.exists() else {'pending': {}, 'last_scan': None}
        found = entries(root)
        if args.command in ('init', 'index'):
            found = rebuild(root, state)
            result = {'saved': len(found), 'root': str(root)}
        elif args.command == 'status':
            pending = {k: v for k, v in state['pending'].items() if k not in found}
            result = {'saved': {k: str(v[0].relative_to(root)) for k, v in found.items()}, 'pending': pending, 'last_scan': state['last_scan']}
        elif args.command == 'queue':
            rows = read_json(args.items)
            if not isinstance(rows, list):
                raise ValueError('采集清单必须是数组')
            for item in rows:
                validate_url(item['work_id'], item['source_url'])
            for item in rows:
                wid = item['work_id']
                if wid not in found:
                    state['pending'].setdefault(wid, {'source_url': item['source_url'], 'attempts': 0, 'reason': '', 'status': 'pending'})
            rebuild(root, state)
            result = {'pending': len(state['pending'])}
        elif args.command == 'scan':
            state['last_scan'] = {'at': now(), 'result': args.result, 'reason': args.reason}
            save_state(root, state)
            result = state['last_scan']
        elif args.command in ('fail', 'retry'):
            wid = work_id(args.id)
            if wid in found:
                rebuild(root, state)
                result = {'status': 'already_saved', 'path': str(found[wid][0])}
            else:
                if wid not in state['pending']:
                    raise ValueError('作品尚未排队，请先 queue')
                item = state['pending'][wid]
                if args.command == 'fail':
                    item['attempts'] += 1
                    item['reason'] = args.reason[:300]
                    item['status'] = 'paused' if item['attempts'] >= 3 else 'pending'
                else:
                    item.update(attempts=0, reason='', status='pending')
                save_state(root, state)
                result = item
        elif args.command == 'add':
            result = add(root, state, read_json(args.record), read_json(args.note))
        elif args.command == 'move':
            wid = work_id(args.id)
            old, meta, body = found[wid]
            target = destination(root, args.category) / old.name
            if target != old and target.exists():
                raise ValueError('目标已存在，拒绝覆盖')
            target.parent.mkdir(parents=True, exist_ok=True)
            if target != old:
                old.rename(target)
            meta['主分类'] = args.category
            write(target, document(meta, body))
            rebuild(root, state)
            result = {'status': 'moved', 'path': str(target)}
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        print('操作未完成：' + str(exc), file=sys.stderr)
        sys.exit(1)
