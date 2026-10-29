import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
LIB = SKILL / 'scripts/library.py'
PIPE = SKILL / 'scripts/extractor/pipeline.py'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / '有空格的 知识库'
        self.env = dict(os.environ, PYTHONUTF8='1', DOUYIN_COPY_EXTRACTOR_STATE_DIR=str(Path(self.temp.name) / 'state'))

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, script, *args, ok=True):
        r = subprocess.run([sys.executable, str(script), *map(str, args)], env=self.env,
                           capture_output=True, encoding='utf-8', timeout=20)
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr)
            return json.loads(r.stdout)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        return r

    def lib(self, *args, **kwargs):
        return self.run_cmd(LIB, '--root', self.root, *args, **kwargs)

    def fixture(self):
        self.lib('init')
        rec = {'basic_info': {'platform': '抖音', 'author': '离线测试作者', 'duration': '00:30',
               'work_id': '1000000000000000001', 'source_url': 'https://www.douyin.com/video/1000000000000000001'},
               'publish_copy': '测试发布文案，不对应真实作品。',
               'corrected_transcript': '这是一条离线测试文本，用来检查完整正文在保存和移动时没有丢失，不对应真实的视频。'}
        note = {'title': '测试标题', 'category': '99-待分类', 'uses': [], 'tags': ['测试'],
                'text_source': '音频转写', 'quality': '已校对', 'analysis': '仅用于验证文件操作。'}
        paths = []
        for name, value in [('record.json', rec), ('note.json', note), ('items.json', [dict(work_id=rec['basic_info']['work_id'], source_url=rec['basic_info']['source_url'])])]:
            p = Path(self.temp.name) / name
            p.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
            paths.append(p)
        return rec, paths

    def test_init_preserves_custom_rules(self):
        self.lib('init')
        p = self.root / '分类规则.md'
        p.write_text(p.read_text(encoding='utf-8') + '\n自定义规则\n', encoding='utf-8')
        before = p.read_bytes()
        self.lib('init')
        self.assertEqual(before, p.read_bytes())

    def test_add_deduplicate_move_preserves_full_text(self):
        rec, (rp, np, qp) = self.fixture()
        self.lib('queue', '--items', qp)
        saved = self.lib('add', '--record', rp, '--note', np)
        doc = Path(saved['path']).read_text(encoding='utf-8')
        for key in ['publish_copy', 'corrected_transcript']:
            self.assertIn(rec[key], doc)
        duplicate = self.lib('add', '--record', rp, '--note', np)
        self.assertEqual(duplicate['status'], 'already_exists')
        moved = self.lib('move', '--id', rec['basic_info']['work_id'], '--category', '02-知识收藏/AI工具与应用')
        text = Path(moved['path']).read_text(encoding='utf-8')
        self.assertEqual(doc.split('\n## 发布文案全文')[1], text.split('\n## 发布文案全文')[1])
        self.assertFalse(Path(saved['path']).exists())
        status = self.lib('status')
        self.assertEqual(len(status['saved']), 1)
        self.assertEqual(status['pending'], {})

    def test_pause_retry_scan_and_path_boundary(self):
        rec, (rp, np, qp) = self.fixture()
        wid = rec['basic_info']['work_id']
        self.lib('queue', '--items', qp)
        for _ in range(3):
            result = self.lib('fail', '--id', wid, '--reason', '离线测试')
        self.assertEqual(result['status'], 'paused')
        self.assertEqual(self.lib('retry', '--id', wid)['attempts'], 0)
        self.lib('scan', '--result', 'partial', '--reason', '尚未扫完')
        self.assertEqual(self.lib('status')['last_scan']['result'], 'partial')
        note = json.loads(np.read_text(encoding='utf-8'))
        note['category'] = '../outside'
        np.write_text(json.dumps(note), encoding='utf-8')
        self.lib('add', '--record', rp, '--note', np, ok=False)
        self.assertFalse((self.root.parent / 'outside').exists())

    def test_lock_excludes_second_process_and_releases(self):
        self.lib('init')
        module = load('library', LIB)
        with module.library_lock(self.root / '.同步锁'):
            self.lib('index', ok=False)
        self.lib('index')

    def test_installer_isolated_and_backup(self):
        module = load('installer', SKILL / 'scripts/install.py')
        dest = Path(self.temp.name) / 'skills' / SKILL.name
        module.install(SKILL, dest)
        self.assertTrue((dest / 'scripts/extractor/pipeline.py').is_file())
        self.assertEqual([x.name for x in dest.parent.iterdir()], [SKILL.name])
        local = dest / 'my-change.txt'
        local.write_text('keep me', encoding='utf-8')
        with self.assertRaises(ValueError):
            module.install(SKILL, dest)
        result = module.install(SKILL, dest, replace=True)
        self.assertEqual((Path(result['backup']) / local.name).read_text(), 'keep me')
        self.assertFalse(Path(result['backup']).is_relative_to(dest.parent))
        self.assertFalse(local.exists())

    def test_pipeline_job_contract_and_cleanup(self):
        rec, (rp, _, _) = self.fixture()
        started = self.run_cmd(PIPE, 'begin', '--source', rec['basic_info']['source_url'])
        token = started['token']
        job = Path(started['job_dir'])
        try:
            self.run_cmd(PIPE, 'begin', '--source', 'another', ok=False)
            record = job / 'record.json'
            record.write_text(json.dumps(rec, ensure_ascii=False), encoding='utf-8')
            self.run_cmd(PIPE, 'validate', '--token', token, '--record', record)
            self.run_cmd(PIPE, 'finish', '--token', token, '--record', record)
            self.assertFalse(job.exists())
        finally:
            if job.exists():
                self.run_cmd(PIPE, 'abort', '--token', token)


if __name__ == '__main__':
    unittest.main()
