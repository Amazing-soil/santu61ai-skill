"""Offline behavioral checks with synthetic media; never uses personal source files."""
import argparse, contextlib, io, json, tempfile, unittest, wave
from pathlib import Path
import numpy as np
from common import digest, ffmpeg, load, record, save
from follow_reading import init, prepare, attach, align, archive, compare, fit, render
from layout import draw_page, fonts, pages, tokenize, wrap

SCRIPTS=Path(__file__).parent
FONTS=Path.home()/'Library/Fonts'

def ns(**kw):return argparse.Namespace(**kw)

def row(text='测试文字',emphasis=False):return [{'text':text,'emphasis':emphasis}]

class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        sr=8000;t=np.arange(sr*2)/sr
        # Non-periodic chirp with envelope so cross-correlation has a unique peak.
        cls.signal=.3*np.sin(2*np.pi*(230*t+170*t*t))*(.6+.3*np.sin(2*np.pi*3.7*t))
        cls.wav=cls.root/'original.wav';cls.write_wave(cls.wav,cls.signal)
        cls.source=cls.root/'source.mp4'
        ffmpeg(['-f','lavfi','-i','testsrc2=s=320x240:r=30:d=2','-i',cls.wav,'-c:v','libx264','-c:a','aac','-shortest',cls.source])
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    @staticmethod
    def write_wave(path,signal):
        with wave.open(str(path),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes((signal*32767).astype('<i2').tobytes())
    def plan(self):
        return {'crop':[160,0,160,240],'rows':[row('你好'),row('重点',True)],'review':{'crop_checked':True,'transcript_checked':True,'emphasis_checked':True,'evidence_frames':['检查/fixture.png'],'note':'Synthetic fixture; not a production review'}}
    def newjob(self,name):
        library=self.root/name
        a=ns(library=str(library),source=str(self.source),id='GD-001',title='测试',day_label='第一天',person_label='',source_url='',source_id='fixture',author='',source_day='')
        with contextlib.redirect_stdout(io.StringIO()):init(a)
        job=library/'GD-001-测试';(job/'检查').mkdir()
        from PIL import Image
        Image.new('RGB',(320,240)).save(job/'检查/fixture.png')
        return job,a
    def test_duplicate_does_not_create_or_modify(self):
        job,a=self.newjob('duplicate');before=digest(job/'素材记录.json')
        a.id='GD-009'
        with contextlib.redirect_stdout(io.StringIO()):init(a)
        self.assertEqual(len(list(job.parent.glob('GD-*'))),1);self.assertEqual(before,digest(job/'素材记录.json'))
    def test_crop_failure_keeps_job_resumable(self):
        job,_=self.newjob('crop');p=self.plan();p['crop']=[160,0,322,240];path=job/'plan.json';save(path,p)
        with self.assertRaises(ValueError):prepare(ns(job=str(job),plan=str(path),audio_already_processed=False,audio_mp4=False))
        self.assertEqual(record(job)['state'],'待提取');self.assertFalse((job/'02-提取素材').exists())
    def test_source_changed_rejected(self):
        job,_=self.newjob('changed');(job/'01-原始视频/source.mp4').write_bytes(b'changed');path=job/'plan.json';save(path,self.plan())
        with self.assertRaisesRegex(ValueError,'changed'):prepare(ns(job=str(job),plan=str(path),audio_already_processed=False,audio_mp4=False))
    def test_alignment_measurement_detects_delay_and_drift(self):
        delayed=self.root/'delayed.wav';self.write_wave(delayed,np.concatenate([np.zeros(1600),self.signal]))
        m=compare(self.wav,delayed);self.assertAlmostEqual(m['suggested_avatar_start'],.2,places=3);self.assertTrue(m['automatic_alignment_reliable'])
        drifted=self.root/'drifted.wav';self.write_wave(drifted,np.interp(np.arange(17000)/1.06,np.arange(len(self.signal)),self.signal))
        self.assertFalse(compare(self.wav,drifted)['automatic_alignment_reliable'])
    def test_full_text_pages_and_emphasis(self):
        rows=[row('普通')+row('重点',True),row('结束')]
        plan={'rows':rows,'pages':[{'start':0,'end':1,'rows':[0]},{'start':1,'end':2,'rows':[1]}]}
        self.assertEqual(len(pages(plan,2)),2)
        bad=json.loads(json.dumps(plan));bad['pages'][1]['rows']=[0]
        with self.assertRaises(ValueError):pages(bad,2)
        if (FONTS/'MiSans-Medium.ttf').exists():
            longrows=[row('完整文案内容'*60,True)]
            wrapped=wrap(longrows,fonts(FONTS))
            self.assertEqual(''.join(c for line in wrapped for c,_ in line),longrows[0][0]['text'])
            self.assertTrue(all(mark for line in wrapped for _,mark in line))
            with self.assertRaises(ValueError):draw_page({'title':'测试','day_label':'第一天'},longrows,self.root/'overflow.png',FONTS)
    def test_complete_two_page_media_and_archive(self):
        if not (FONTS/'MiSans-Medium.ttf').exists():self.skipTest('MiSans not installed')
        job,_=self.newjob('endtoend');plan=self.plan();plan['pages']=[{'start':0,'end':1,'rows':[0]},{'start':1,'end':2,'rows':[1]}]
        path=job/'plan.json';save(path,plan)
        with contextlib.redirect_stdout(io.StringIO()):prepare(ns(job=str(job),plan=str(path),audio_already_processed=True,audio_mp4=True))
        self.assertEqual(record(job)['state'],'等待数字人');h=digest(job/'02-提取素材/合成主音轨.wav')
        with self.assertRaises(ValueError):prepare(ns(job=str(job),plan=str(path),audio_already_processed=False,audio_mp4=False))
        self.assertEqual(h,digest(job/'02-提取素材/合成主音轨.wav'))
        avatar=self.root/'avatar.mp4'
        ffmpeg(['-i',self.source,'-i',job/'02-提取素材/合成主音轨.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac',avatar])
        with contextlib.redirect_stdout(io.StringIO()):attach(ns(job=str(job),avatar=str(avatar)))
        with self.assertRaises(ValueError):align(ns(job=str(job),offset=.3,visual_checked=True,content_checked=True,note='Synthetic fixture'))
        with contextlib.redirect_stdout(io.StringIO()):
            align(ns(job=str(job),offset=0,visual_checked=True,content_checked=True,note='Synthetic fixture'))
            render(ns(job=str(job),font_dir=str(FONTS)))
        self.assertEqual(record(job)['state'],'待成片检查')
        from PIL import Image
        c=Image.open(job/'05-成片/封面.png');second=Image.open(job/'04-制作工程/换页-02.png')
        self.assertNotEqual(c.crop((68,1071,1000,1160)).tobytes(),second.crop((68,1071,1000,1160)).tobytes())
        self.assertEqual(load(job/'04-制作工程/渲染参数.json')['geometry'][0]['crop'],False)
        with self.assertRaises(ValueError):render(ns(job=str(job),font_dir=str(FONTS)))
        share=self.root/'share';share.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):archive(ns(job=str(job),project_root=str(job.parent),share_root=str(share)))
        output=job/'05-成片/每日跟读.mp4';self.assertTrue(output.is_symlink());self.assertTrue(output.exists())
        before=digest(output)
        with contextlib.redirect_stdout(io.StringIO()):archive(ns(job=str(job),project_root=str(job.parent),share_root=str(share)))
        self.assertEqual(digest(output),before)
    def test_archive_conflict_preserves_original(self):
        job,_=self.newjob('conflict');share=self.root/'conflict-share';dest=share/job.name/'01-原始视频/source.mp4';dest.parent.mkdir(parents=True);dest.write_bytes(b'conflict')
        with self.assertRaises(ValueError):archive(ns(job=str(job),project_root=str(job.parent),share_root=str(share)))
        self.assertFalse((job/'01-原始视频/source.mp4').is_symlink());self.assertEqual(dest.read_bytes(),b'conflict')

if __name__=='__main__':unittest.main()
