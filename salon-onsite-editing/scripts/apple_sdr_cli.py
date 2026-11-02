#!/usr/bin/env python3
"""Apple AVFoundation HDR-to-SDR, then temporal normalization only. Beauty always off."""
import argparse,json,subprocess,tempfile,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FF='ffmpeg'
FFPROBE='ffprobe'
def probe(p):return json.loads(subprocess.check_output([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(p)]))
def main():
 global FF,FFPROBE
 p=argparse.ArgumentParser(description='原生 Apple HDR→SDR：输入、输出、起点、时长；默认无美颜，无额外调色')
 p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('--start',type=float,default=0);p.add_argument('--duration',type=float)
 p.add_argument('--ffmpeg',default='ffmpeg');p.add_argument('--ffprobe',default='ffprobe');p.add_argument('--native-bin',type=Path,default=ROOT/'apple_sdr_export')
 a=p.parse_args();FF=shutil.which(a.ffmpeg);FFPROBE=shutil.which(a.ffprobe)
 if not FF or not FFPROBE:p.error('需要可执行的FFmpeg和ffprobe')
 if not a.native_bin.is_file():p.error('先编译apple_sdr_export.m，或用--native-bin指定本机程序')
 if a.output.exists() or a.output.with_suffix('.color.json').exists():p.error('输出已存在，拒绝覆盖')
 a.input=a.input.resolve();a.output=a.output.resolve()
 if a.input==a.output:p.error('不能覆盖原文件')
 source=probe(a.input);total=float(source['format']['duration']);duration=a.duration if a.duration is not None else total-a.start
 if not math.isfinite(a.start) or not math.isfinite(duration) or a.start<0 or duration<=0 or a.start+duration>total+0.05:p.error('起点或时长超出原片')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='apple-sdr-',dir=a.output.parent) as tmp:
  native=Path(tmp)/'native.mp4';cfr=Path(tmp)/'cfr-video.mp4'
  subprocess.run([str(a.native_bin.resolve()),str(a.input),str(native),str(a.start),str(duration),'AVAssetExportPreset1920x1080'],check=True)
  info=probe(native);v=next(s for s in info['streams'] if s['codec_type']=='video')
  if any(v.get(k)!='bt709' for k in ('color_primaries','color_transfer','color_space')):raise RuntimeError('原生输出并非BT709，停止')
  # Apple preset scales the preferredTransform composition into native portrait1080; only fallback size reduction if needed.
  vf='fps=30,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.2'
  target_size=(1920,1080) if v['width']>v['height'] else (1080,1920)
  if (v['width'],v['height'])!=target_size: vf+=f',scale={target_size[0]}:{target_size[1]}'
  frames=round(duration*30)
  subprocess.run([FF,'-y','-v','error','-hwaccel','videotoolbox','-i',str(native),'-map','0:v:0','-an','-vf',vf,'-frames:v',str(frames),'-r','30','-c:v','h264_videotoolbox','-b:v','12M','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-map_metadata','-1',str(cfr)],check=True)
  subprocess.run([FF,'-y','-v','error','-i',str(cfr),'-i',str(native),'-map','0:v:0','-map','1:a:0?','-c','copy','-map_metadata','-1','-movflags','+faststart',str(a.output)],check=True)
  final=probe(a.output);fv=next(s for s in final['streams'] if s['codec_type']=='video')
  if any(fv.get(k)!='bt709' for k in ('color_primaries','color_transfer','color_space')):raise RuntimeError('最终输出非完整BT709标记，请检查本机编码器，勿用于批量')
  (a.output.with_suffix('.color.json')).write_text(json.dumps({'source':str(a.input),'start':a.start,'duration':duration,'native_preset':'AVAssetExportPreset1920x1080','native_video':{k:v.get(k) for k in ('width','height','nb_frames','avg_frame_rate','color_primaries','color_transfer','color_space')},'normalization':'30fps; pad final frame at boundary if needed; no second tone map; native audio copied','beauty':'off','output_streams':final['streams']},ensure_ascii=False,indent=2))
 print(a.output)
if __name__=='__main__':main()
