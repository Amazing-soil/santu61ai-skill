#!/usr/bin/env python3
"""Hermetic checks for the Claude/Codex file handoff; no network or API calls."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

SCRIPT = Path(__file__).with_name("generate.py")
spec = importlib.util.spec_from_file_location("bridge", SCRIPT)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def sample_png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")) + chunk(b"IEND", b""))


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-image-test-")
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake = self.bin / "codex"
        fake.write_text(f"#!{sys.executable}\n" + '''import json, os, pathlib, sys
args=sys.argv[1:]
request=sys.stdin.read()
job=pathlib.Path(args[args.index('--output-last-message')+1])
output=pathlib.Path(os.environ['TEST_OUTPUT'])
output.write_bytes(pathlib.Path(os.environ['TEST_PNG']).read_bytes())
case=os.environ.get('TEST_CASE','success')
if case=='nonzero': sys.exit(3)
job.write_text(json.dumps({'status':'failed' if case=='failed' else 'success',
 'tool':'router' if case=='wrong-tool' else 'image_gen','image_path':str(output),'message':'test fixture'}))
print(json.dumps({'type':'turn.completed'}))
''')
        fake.chmod(0o755)
        self.output = self.root / "素材 空格.png"
        self.fixture = self.root / "fixture.png"
        self.fixture.write_bytes(sample_png())
        self.prompt = self.root / "prompt.txt"
        self.marker = self.root / "must-not-exist"
        self.prompt.write_text(f"Draw a search ring. $(touch {self.marker}) `touch {self.marker}`\n第二行", encoding="utf-8")
        self.env = dict(os.environ, PATH=str(self.bin)+os.pathsep+os.environ.get('PATH',''),
                        TEST_OUTPUT=str(self.output), TEST_PNG=str(self.fixture))

    def tearDown(self):
        self.temp.cleanup()

    def run_bridge(self, *extra):
        return subprocess.run([sys.executable,str(SCRIPT),'--prompt-file',str(self.prompt),
                               '--output',str(self.output),*extra],env=self.env,capture_output=True,text=True)

    def test_success_and_literal_prompt(self):
        result = self.run_bridge()
        self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
        data=json.loads(result.stdout)
        self.assertEqual((data['width'],data['height']), (1,1))
        self.assertFalse(self.marker.exists())
        request=(Path(data['job_dir'])/'request.txt').read_text()
        self.assertIn(self.prompt.read_text(),request)
        command=json.loads((Path(data['job_dir'])/'command.json').read_text())
        self.assertIn('--ignore-user-config',command)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',command)

    def test_existing_asset_is_preserved(self):
        self.output.write_bytes(b'keep existing asset')
        result=self.run_bridge()
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.output.read_bytes(),b'keep existing asset')

    def test_failed_status_wrong_tool_and_nonzero_are_rejected(self):
        for case in ['failed','wrong-tool','nonzero']:
            with self.subTest(case=case):
                self.env['TEST_CASE']=case
                result=self.run_bridge()
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(json.loads(result.stdout)['status'],'failed')
                self.output.unlink(missing_ok=True)

    def test_truncated_and_corrupt_png_are_rejected(self):
        for bad in [sample_png()[:24],sample_png()[:-1],sample_png()[:-5]+b'xxxxx']:
            with self.subTest(length=len(bad)):
                self.fixture.write_bytes(bad)
                result=self.run_bridge()
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(json.loads(result.stdout)['status'],'failed')
                self.output.unlink(missing_ok=True)

    def test_dry_run_never_invokes_codex(self):
        result=self.run_bridge('--dry-run')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'dry_run')
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
