#!/usr/bin/env python3
"""Prepare, resume, align and render follow-reading media. One job per command."""
from pathlib import Path
import argparse, json, math, os, re, shutil, tempfile
from common import asset, digest, duration, ensure_new_output, ffmpeg, load, probe, record, save, stream, update
from layout import STYLE, draw_page, pages, tokenize

FOLDERS = {'source':'01-原始视频','extracted':'02-提取素材','avatar':'03-数字人视频','project':'04-制作工程','final':'05-成片'}


def init(a):
    library=Path(a.library).expanduser().resolve(); library.mkdir(parents=True,exist_ok=True)
    source=Path(a.source).expanduser().resolve(strict=True)
    if not re.fullmatch(r'GD-\d{3,}',a.id):raise ValueError('Use a stable ID such as GD-001')
    h=digest(source)
    # Scoped registry: all jobs in the supplied library. Never choose another project implicitly.
    for p in library.glob('*/素材记录.json'):
        r=load(p)
        if r['source']['sha256']==h or (a.source_id and r['source'].get('id')==a.source_id):
            print(json.dumps({'already_registered':str(p.parent),'state':r['state']},ensure_ascii=False));return
        if r['id']==a.id:raise ValueError(f'{a.id} already belongs to another source')
    safe_title=re.sub(r'[\\/:*?"<>|\x00-\x1f]','-',a.title).strip('. ')
    if not safe_title:raise ValueError('Title cannot be empty')
    job=library/f'{a.id}-{safe_title}';job.mkdir(exist_ok=False)
    dest=job/FOLDERS['source']/('source'+source.suffix.lower());dest.parent.mkdir()
    shutil.copyfile(source,dest)
    if digest(dest)!=h:raise ValueError('Source copy verification failed')
    stream(dest,'video');stream(dest,'audio')
    r={'schema_version':1,'id':a.id,'title':a.title,'day_label':a.day_label,'person_label':a.person_label,
       'state':'待提取','source':{'url':a.source_url,'id':a.source_id,'author':a.author,'day':a.source_day,
       'sha256':h,'film_provenance':'未核实'},'files':{'source':str(dest.relative_to(job))},'checks':{},'publication':'未安排、未提交'}
    update(job,r);print(job)


def frames(a):
    job=Path(a.job);r=record(job);src=asset(job,r,'source');length=duration(src)
    out=job/'检查/原片抽帧';out.mkdir(parents=True,exist_ok=True)
    for i,t in enumerate((0,length*.25,length*.5,length*.75,max(0,length-.12))):
        ffmpeg(['-ss',str(t),'-i',src,'-frames:v','1',out/f'{i+1:02d}-{t:.2f}s.png'])
    print(out)


def checked_plan(plan, src):
    if not all(plan.get('review',{}).get(k) for k in ('crop_checked','transcript_checked','emphasis_checked')):
        raise ValueError('Inspect frames, transcript and exact source highlights before setting the three review fields')
    if not plan['review'].get('evidence_frames'):raise ValueError('Record the actual inspected frame paths')
    info=stream(src,'video');w,h=int(info['width']),int(info['height'])
    # Display rotation complicates crop coordinates; normalize a separate copy explicitly first.
    if any(abs(float(x.get('rotation',0)))%360 for x in info.get('side_data_list',[])):
        raise ValueError('Rotated source: normalize display orientation in a separate file before choosing crop coordinates')
    c=plan['crop']
    if len(c)!=4 or any(type(n) is not int or n<0 or n%2 for n in c):raise ValueError('Crop is [x,y,width,height], nonnegative even integers')
    x,y,cw,ch=c
    if cw<2 or ch<2 or x+cw>w or y+ch>h:raise ValueError('Crop is outside source bounds')
    t=duration(src);start=float(plan.get('start',0));end=float(plan.get('end',t))
    if not (0<=start<end<=t+.01):raise ValueError('Invalid source time range')
    if not plan.get('rows'):raise ValueError('Missing complete transcript rows')
    for row in plan['rows']:tokenize(row)
    pages(plan,end-start)
    return start,end


def write_text(rows, folder):
    plain=[];marked=[];spans=[];offset=0
    for i,row in enumerate(rows):
        text='';mark=''
        for seg in row:
            value=seg['text'];text+=value
            if seg['emphasis']:
                spans.append({'row':i,'start':len(text)-len(value),'end':len(text),'text':value})
                mark+='“'+value+'”'
            else:mark+=value
        plain.append(text);marked.append(mark)
    (folder/'完整文案.txt').write_text('\n\n'.join(plain)+'\n')
    (folder/'跟读文案.txt').write_text('\n\n'.join(marked)+'\n')
    save(folder/'重点字.json',{'rows':rows,'spans':spans,'index_unit':'Unicode code points; row-local start inclusive, end exclusive'})


def prepare(a):
    job=Path(a.job).resolve();r=record(job)
    if r['state']!='待提取':raise ValueError('Already prepared; use status to resume, do not apply pitch twice')
    src=asset(job,r,'source')
    if digest(src)!=r['source']['sha256']:raise ValueError('Original source changed after import')
    plan=load(a.plan);start,end=checked_plan(plan,src);length=end-start
    for p in plan['review']['evidence_frames']:
        if not (job/p).is_file():raise ValueError(f'Missing inspected frame: {p}')
    target=job/FOLDERS['extracted'];ensure_new_output(target)
    with tempfile.TemporaryDirectory(prefix='.prepare-',dir=job) as tmp:
        out=Path(tmp);master=out/'合成主音轨.wav'
        audio=stream(src,'audio');rate=int(audio['sample_rate']);pitch=0 if a.audio_already_processed else -0.5
        shifted=round(rate*2**(pitch/12))
        filters=f'asetrate={shifted},aresample={rate},atempo={rate/shifted:.10f},apad=whole_dur={length},atrim=duration={length}'
        filters+=f',afade=t=in:st=0:d=0.03,afade=t=out:st={max(0,length-.03)}:d=0.03'
        ffmpeg(['-ss',str(start),'-i',src,'-t',str(length),'-vn','-af',filters,'-ar','48000','-c:a','pcm_s16le',master])
        ffmpeg(['-i',master,'-c:a','libmp3lame','-b:a','192k',out/'数字人驱动音频.mp3'])
        x,y,w,h=plan['crop']
        ffmpeg(['-ss',str(start),'-i',src,'-i',master,'-t',str(length),'-vf',f'crop={w}:{h}:{x}:{y},setsar=1',
                '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',
                '-c:a','aac','-b:a','192k','-movflags','+faststart',out/'右侧素材.mp4'])
        if a.audio_mp4:ffmpeg(['-i',master,'-vn','-c:a','aac','-b:a','192k',out/'单独声音.mp4'])
        write_text(plan['rows'],out);save(out/'提取计划.json',plan)
        for p in out.iterdir():
            if p.suffix in ('.mp4','.mp3','.wav'):ffmpeg(['-i',p,'-f','null','-'])
        shutil.move(str(out),str(target))
    r.update({'state':'等待数字人','duration':length,'audio':{'pitch_semitones':pitch,'already_processed_input':a.audio_already_processed,
        'provenance':'下载视频既有混合音轨，未分离左右人声','master_sha256':digest(target/'合成主音轨.wav')}})
    r['files'].update({'right':str((target/'右侧素材.mp4').relative_to(job)),'master':str((target/'合成主音轨.wav').relative_to(job)),
        'driver':str((target/'数字人驱动音频.mp3').relative_to(job)),'plan':str((target/'提取计划.json').relative_to(job))})
    r['checks']['extraction']={'full_decode':'passed','visual_review':plan['review'],'crop':plan['crop'],'source_range':[start,end]}
    update(job,r);print(json.dumps({'job':str(job),'state':r['state'],'driver':str(asset(job,r,'driver'))},ensure_ascii=False))


def pcm(path, rate=8000):
    import numpy as np,subprocess
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar',str(rate),'-f','f32le','-'])
    x=np.frombuffer(raw,dtype=np.float32).astype(float)
    return x-x.mean()


def compare(master, avatar):
    import numpy as np
    from scipy.signal import correlate,correlation_lags
    ref=pcm(master);other=pcm(avatar);rate=8000
    c=correlate(other,ref,mode='full',method='fft');lags=correlation_lags(len(other),len(ref),mode='full')
    mask=np.abs(lags)<=rate*3
    lag=int(lags[mask][np.argmax(c[mask])])
    a=max(0,lag);b=max(0,-lag);n=min(len(other)-a,len(ref)-b)
    def score(x,y):
        den=float(np.linalg.norm(x)*np.linalg.norm(y))
        return float(np.dot(x,y)/den) if den else 0.0
    scores=[];residuals=[]
    for k in range(3):
        lo=k*n//3;hi=(k+1)*n//3
        x=other[a+lo:a+hi];y=ref[b+lo:b+hi]
        scores.append(score(x,y))
        local=correlate(x,y,mode='full',method='fft');ll=correlation_lags(len(x),len(y))
        m=np.abs(ll)<=rate//4
        residuals.append(float(ll[m][np.argmax(local[m])]/rate))
    return {'suggested_avatar_start':lag/rate,'correlation':score(other[a:a+n],ref[b:b+n]),
            'third_correlations':scores,'third_residual_seconds':residuals,
            'automatic_alignment_reliable':min(scores)>.8 and max(abs(v) for v in residuals)<=.04,
            'meaning':'Positive start means avatar has extra leading material. This is a measurement, not a visual lip-sync approval.'}


def attach(a):
    job=Path(a.job).resolve();r=record(job)
    if r['state']!='等待数字人':raise ValueError('Use status; this job is not waiting for an avatar')
    src=Path(a.avatar).expanduser().resolve(strict=True);stream(src,'video')
    target=job/FOLDERS['avatar'];ensure_new_output(target);target.mkdir()
    dest=target/(r['id']+'-数字人'+src.suffix.lower());shutil.copyfile(src,dest)
    if digest(src)!=digest(dest):raise ValueError('Avatar copy mismatch')
    r['files']['avatar']=str(dest.relative_to(job));r['avatar_sha256']=digest(dest)
    try:stream(dest,'audio')
    except ValueError:measurement={'automatic_alignment_reliable':False,'reason':'数字人没有音轨，需根据画面人工核对起点'}
    else:measurement=compare(asset(job,r,'master'),dest)
    measurement['avatar_duration']=duration(dest);measurement['reference_duration']=r['duration']
    save(target/'音频对应检查.json',measurement)
    r['checks']['alignment_measurement']=measurement;r['state']='待核对数字人';update(job,r)
    print(json.dumps(measurement,ensure_ascii=False,indent=2))


def align(a):
    job=Path(a.job).resolve();r=record(job)
    if r['state']!='待核对数字人':raise ValueError('Attach a matching avatar before alignment')
    if not a.visual_checked or not a.content_checked or not a.note:raise ValueError('Verify matching content, first/last sentence and visual alignment, then record a note')
    if a.offset<0:raise ValueError('A negative start indicates missing leading content; supply a complete avatar')
    left=asset(job,r,'avatar');tail=duration(left)-a.offset-r['duration']
    if abs(tail)>.2:raise ValueError(f'Avatar duration differs by {tail:.3f}s after alignment; inspect and provide an aligned copy, do not stretch speech blindly')
    m=r['checks']['alignment_measurement']
    if m.get('automatic_alignment_reliable') and abs(a.offset-m['suggested_avatar_start'])>.05:
        raise ValueError('Chosen offset conflicts with reliable audio measurement')
    r['alignment']={'avatar_start':a.offset,'tail_difference':tail,'note':a.note,'visual_checked':True,'content_checked':True}
    r['state']='可合成';update(job,r);print(r['state'])


def fit(path, slot):
    info=stream(path,'video');w,h=int(info['width']),int(info['height'])
    sar=info.get('sample_aspect_ratio','1:1')
    if sar not in ('N/A','0:1'):
        n,d=map(int,sar.split(':'));w=w*n/d
    rotation=next((float(x['rotation']) for x in info.get('side_data_list',[]) if 'rotation'in x),0)
    if abs(rotation)%180==90:w,h=h,w
    x,y,bw,bh=slot;factor=min(bw/w,bh/h)
    fw=max(2,min(bw,round(w*factor/2)*2));fh=max(2,min(bh,round(h*factor/2)*2))
    return fw,fh,x+(bw-fw)//2,y+(bh-fh)//2


def render(a):
    job=Path(a.job).resolve();r=record(job)
    if r['state']!='可合成':raise ValueError('Complete avatar matching and alignment before rendering')
    left=asset(job,r,'avatar');right=asset(job,r,'right');master=asset(job,r,'master');plan=load(asset(job,r,'plan'))
    if digest(left)!=r['avatar_sha256'] or digest(master)!=r['audio']['master_sha256']:raise ValueError('An input changed after review')
    project=job/FOLDERS['project'];final=job/FOLDERS['final'];ensure_new_output(project);ensure_new_output(final)
    length=r['duration'];hold=STYLE['cover_hold_seconds'];total=length+hold;pp=pages(plan,length)
    with tempfile.TemporaryDirectory(prefix='.render-',dir=job) as tmp:
        tmp=Path(tmp);eng=tmp/FOLDERS['project'];out=tmp/FOLDERS['final'];eng.mkdir();out.mkdir()
        inputs=[];geometry=[]
        for i,page in enumerate(pp):
            png=eng/f'文字背景-{i+1:02d}.png'
            draw_page(r,[plan['rows'][j] for j in page['rows']],png,a.font_dir)
            inputs+=['-loop','1','-framerate','30','-i',str(png)]
        n=len(pp);inputs+=['-i',str(left),'-i',str(right),'-i',str(master)]
        fg=[];base='0:v'
        for i,page in enumerate(pp[1:],1):
            fg.append(f'[{base}][{i}:v]overlay=0:0:enable=\'gte(t,{page["start"]+hold})\'[page{i}]');base=f'page{i}'
        for i,(path,offset,sat) in enumerate(((left,r['alignment']['avatar_start'],.88),(right,0,.90))):
            w,h,x,y=fit(path,STYLE['slots'][i]);geometry.append({'fit':[w,h],'placement':[x,y],'crop':False})
            fg.append(f'[{n+i}:v]trim=start={offset}:duration={length},setpts=PTS-STARTPTS,fps=30,scale={w}:{h}:flags=lanczos,setsar=1,eq=saturation={sat},tpad=stop_mode=clone:stop_duration=0.2,trim=duration={length},tpad=start_mode=clone:start_duration={hold}[video{i}]')
            fg.append(f'[{base}][video{i}]overlay={x}:{y}:shortest=1[composite{i}]');base=f'composite{i}'
        fg.append(f'[{base}]format=yuv420p[v]')
        fg.append(f'[{n+2}:a]aresample=48000,adelay=600:all=1,apad=whole_dur={total},atrim=duration={total}[a]')
        args=[*inputs,'-filter_complex',';'.join(fg),'-map','[v]','-map','[a]','-t',str(total),'-r','30','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'每日跟读.mp4')]
        save(eng/'渲染参数.json',{'style':STYLE,'geometry':geometry,'pages':pp,'duration':total,'audio':'prepared master only','font_dir':str(Path(a.font_dir).expanduser()),'filters':fg})
        ffmpeg(args);ffmpeg(['-i',out/'每日跟读.mp4','-f','null','-'])
        ffmpeg(['-i',out/'每日跟读.mp4','-frames:v','1',out/'封面.png'])
        for name,t in [('首帧保持',.5),('正文开始',hold+.1),('中间',total/2),('结尾',max(0,total-.12))]:
            ffmpeg(['-ss',str(t),'-i',out/'每日跟读.mp4','-frames:v','1',eng/(name+'.png')])
        for i,page in enumerate(pp[1:],2):
            ffmpeg(['-ss',str(page['start']+hold+.05),'-i',out/'每日跟读.mp4','-frames:v','1',eng/f'换页-{i:02d}.png'])
        from PIL import Image,ImageChops,ImageStat
        diff=sum(ImageStat.Stat(ImageChops.difference(Image.open(out/'封面.png'),Image.open(eng/'首帧保持.png'))).mean)/3
        audio_test=compare(master,out/'每日跟读.mp4')
        info=probe(out/'每日跟读.mp4');v=next(x for x in info['streams'] if x['codec_type']=='video')
        if (v['width'],v['height'])!=(1080,1920) or abs(float(info['format']['duration'])-total)>.08:raise ValueError('Output geometry/duration mismatch')
        if diff>2 or abs(audio_test['suggested_avatar_start']-hold)>.04 or not audio_test['automatic_alignment_reliable']:
            raise ValueError('First-frame hold or output audio timing check failed')
        checks={'full_decode':'passed','media':info,'opening_hold_mean_difference':diff,'output_audio':audio_test,
                'visual_review':'待查看实际首帧、中间、结尾及分页处','listening_review':'待试听','emphasis_groups':sum(seg['emphasis'] for row in plan['rows'] for seg in row)}
        save(eng/'成片检查.json',checks)
        # Copy the precise renderer used; includes imports and style for reproducibility.
        (eng/'scripts').mkdir()
        for filename in ('follow_reading.py','common.py','layout.py'):
            shutil.copyfile(Path(__file__).parent/filename,eng/'scripts'/filename)
        (eng/'assets').mkdir();shutil.copyfile(Path(__file__).resolve().parents[1]/'assets/style.json',eng/'assets/style.json')
        # The saved script folder can be supplied as <root>/scripts on export; retain source provenance here.
        shutil.move(str(eng),str(project));shutil.move(str(out),str(final))
    r['files'].update({'final':str((final/'每日跟读.mp4').relative_to(job)),'cover':str((final/'封面.png').relative_to(job))})
    r['checks']['render']={'full_decode':'passed','audio_timing':'passed','cover_hold':'passed'}
    r['state']='待成片检查';update(job,r);print(asset(job,r,'final'))


def review(a):
    job=Path(a.job);r=record(job)
    if r['state']!='待成片检查':raise ValueError('Render and inspect the actual output first')
    if not a.frames_checked or not a.audio_checked or not a.note:raise ValueError('Record actual viewing and listening, not only automated checks')
    r['checks']['final_review']={'frames_checked':True,'audio_checked':True,'note':a.note};r['state']='成片完成';update(job,r)
    print(r['state'])


def archive(a):
    job=Path(a.job).resolve();root=Path(a.project_root).resolve();share=Path(a.share_root).resolve()
    job.relative_to(root)
    if not share.is_dir():raise ValueError('Shared folder is unavailable; retain local files')
    logs=[]
    for local in sorted(job.rglob('*')):
        if local.is_symlink() or not local.is_file() or local.suffix.lower() not in {'.mp4','.mov','.mp3','.wav','.png','.jpg','.jpeg'}:continue
        dest=share/local.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);h=digest(local);size=local.stat().st_size
        if dest.exists():
            if dest.stat().st_size!=size or digest(dest)!=h:raise ValueError(f'Archive conflict; preserving both files: {dest}')
        else:
            fd,temp=tempfile.mkstemp(dir=dest.parent,prefix='.'+dest.name);os.close(fd)
            try:
                shutil.copyfile(local,temp)
                if Path(temp).stat().st_size!=size or digest(temp)!=h:raise ValueError('Archive copy verification failed')
                os.replace(temp,dest)
            finally:
                if Path(temp).exists():Path(temp).unlink()
        link=local.with_name(local.name+'.archive-link');ensure_new_output(link);link.symlink_to(dest);os.replace(link,local)
        logs.append({'path':str(local.relative_to(root)),'archive':str(dest),'bytes':size,'sha256':h})
        # Journal each replacement so an interrupted transfer remains recoverable.
        logpath=root/'发布管理/素材迁移记录'/f'{record(job)["id"]}-每日跟读'/ '迁移记录.json'
        prior=load(logpath) if logpath.exists() else []
        save(logpath,prior+[logs[-1]])
    print(json.dumps({'archived':len(logs),'job':str(job)},ensure_ascii=False))


def status(a):
    root=Path(a.job)
    files=[root/'素材记录.json'] if (root/'素材记录.json').is_file() else sorted(root.glob('*/素材记录.json'))
    for p in files:
        r=load(p);missing=[k for k,v in r['files'].items() if not (p.parent/v).is_file()]
        print(json.dumps({'id':r['id'],'title':r['title'],'state':r['state'],'folder':str(p.parent),'missing_files':missing},ensure_ascii=False))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('init');q.add_argument('--library',required=True);q.add_argument('--source',required=True);q.add_argument('--id',required=True);q.add_argument('--title',required=True);q.add_argument('--day-label',required=True)
    for n in ('person-label','source-url','source-id','author','source-day'):q.add_argument('--'+n,default='')
    for name in ('frames','prepare','attach','align','render','review','archive','status'):
        q=sub.add_parser(name);q.add_argument('--job',required=True)
        if name=='prepare':q.add_argument('--plan',required=True);q.add_argument('--audio-already-processed',action='store_true');q.add_argument('--audio-mp4',action='store_true')
        if name=='attach':q.add_argument('--avatar',required=True)
        if name=='align':
            q.add_argument('--offset',type=float,required=True);q.add_argument('--note',required=True);q.add_argument('--visual-checked',action='store_true');q.add_argument('--content-checked',action='store_true')
        if name=='render':q.add_argument('--font-dir',default=str(Path.home()/'Library/Fonts'))
        if name=='review':
            q.add_argument('--frames-checked',action='store_true');q.add_argument('--audio-checked',action='store_true');q.add_argument('--note',required=True)
        if name=='archive':q.add_argument('--project-root',required=True);q.add_argument('--share-root',required=True)
    a=p.parse_args()
    try:globals()[a.command](a)
    except (ValueError,KeyError,FileNotFoundError) as e:p.exit(2,f'{e}\n')

if __name__=='__main__':main()
