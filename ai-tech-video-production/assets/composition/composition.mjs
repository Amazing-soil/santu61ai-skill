import {at,lerp} from './motion.mjs';
import {chapterMarkup,escapeXML,textSVG,fitLines,units} from './chapter.mjs';
export const MODES=Object.freeze(['host','split','chapter','content']);
const defaultTheme={background:'#101615',ink:'#F2EADB',muted:'#AAB9B0',accent:'#A8DDC3',line:'#43564D'};
const copy=x=>JSON.parse(JSON.stringify(x));
export function compile(input) {
  const c=copy(input);
  for(const key of ['width','height','fps','totalFrames'])if(!Number.isInteger(c[key])||c[key]<=0)throw Error(`Positive integer ${key} required`);
  if(!Array.isArray(c.segments)||!c.segments.length)throw Error('Segments required');
  c.theme={...defaultTheme,...c.theme};
  for(const v of Object.values(c.theme))if(!/^#[\da-f]{6}$/i.test(v))throw Error('Theme colors must be #RRGGBB');
  c.fontFamily=c.fontFamily||'PingFang SC, Noto Sans CJK SC, Arial, sans-serif';
  c.hostTransitionFrames=c.hostTransitionFrames??Math.round(c.fps*.5);
  if(!Number.isInteger(c.hostTransitionFrames)||c.hostTransitionFrames<0)throw Error('Invalid hostTransitionFrames');
  const ids=new Set();let cursor=0;
  for(const s of c.segments){
    if(typeof s.id!=='string'||ids.has(s.id))throw Error('Segment IDs must be unique strings');ids.add(s.id);
    if(!Number.isInteger(s.startFrame)||!Number.isInteger(s.endFrame)||s.startFrame!==cursor||s.endFrame<=cursor)throw Error(`Gap, overlap or invalid frame range at ${s.id}`);
    if(!MODES.includes(s.mode))throw Error(`Unknown display mode ${s.mode}`);
    if(['chapter','content'].includes(s.mode)&&s.host?.visible===true)throw Error(`${s.mode} must hide ALL host layers`);
    if(s.host?.visible!==undefined&&typeof s.host.visible!=='boolean')throw Error('host.visible must be boolean');
    if(s.host?.rect){const r=s.host.rect;if(!['x','y','width','height'].every(k=>Number.isFinite(r[k]))||r.x<0||r.y<0||r.width<=0||r.height<=0||r.x+r.width>c.width||r.y+r.height>c.height*.87)throw Error('Host rect outside canvas/subtitle-safe area');}
    if(s.mode==='chapter'){
      if(!String(s.index??'').trim()||[...String(s.index)].length>4||!String(s.title??'').trim())throw Error('Chapter needs a short index and title');
      fitLines(s.title,c.width*(c.height>c.width?.85:.54),c.height>c.width?108:120,48,3);
    }
    cursor=s.endFrame;
  }
  if(cursor!==c.totalFrames)throw Error('Segments must cover the complete original timeline');
  c.subtitles=c.subtitles||[];cursor=0;
  for(const s of c.subtitles){
    if(!Number.isInteger(s.startFrame)||!Number.isInteger(s.endFrame)||s.startFrame<cursor||s.endFrame<=s.startFrame||s.endFrame>c.totalFrames||typeof s.text!=='string'||!s.text.trim())throw Error('Invalid or overlapping subtitles');
    cursor=s.endFrame;
  }
  return c;
}
export function layout(config,mode) {
  const {width:w,height:h}=config,p=h>w;
  const host=mode==='host'?(p?{x:.12*w,y:.12*h,width:.76*w,height:.69*h}:{x:.34*w,y:.18*h,width:.32*w,height:.67*h}):(p?{x:.31*w,y:.62*h,width:.38*w,height:.245*h}:{x:.70*w,y:.20*h,width:.25*w,height:.65*h});
  const content=mode==='split'?(p?{x:.07*w,y:.12*h,width:.86*w,height:.45*h}:{x:.06*w,y:.18*h,width:.57*w,height:.62*h}):{x:.075*w,y:.18*h,width:.85*w,height:.61*h};
  return {host,content,caption:{x:w/2,y:.95*h,width:.88*w,fontSize:p?58:50}};
}
const visible=s=>!['chapter','content'].includes(s.mode)&&s.host?.visible!==false;
export function stateAt(c,frame) {
  if(!Number.isInteger(frame)||frame<0||frame>=c.totalFrames)throw RangeError('Frame outside original timeline');
  const i=c.segments.findIndex(s=>frame>=s.startFrame&&frame<s.endFrame),segment=c.segments[i];
  const localFrame=frame-segment.startFrame,show=visible(segment);
  const boxes=layout(c,show?segment.mode:(segment.mode==='chapter'?'chapter':'content'));
  let rect=segment.host?.rect||boxes.host;
  const previous=c.segments[i-1];
  if(show&&previous&&visible(previous)&&c.hostTransitionFrames>0){
    const from=previous.host?.rect||layout(c,previous.mode).host;
    const duration=Math.min(c.hostTransitionFrames,segment.endFrame-segment.startFrame);
    const p=at(localFrame,0,duration);rect=Object.fromEntries(Object.keys(rect).map(k=>[k,lerp(from[k],rect[k],p)]));
  }
  return {frame,sourceTime:frame/c.fps,segment,localFrame,host:{visible:show,rect},content:boxes.content,caption:boxes.caption,subtitle:c.subtitles.find(s=>frame>=s.startFrame&&frame<s.endFrame)||null};
}
export function captionMarkup(c,state) {
  if(!state.subtitle)return '';
  const b=state.caption,text=state.subtitle.text;
  const size=Math.min(b.fontSize,b.width/Math.max(1,units(text)));
  if(size<(c.height>c.width?42:36))throw Error('Subtitle too long; split it at a semantic boundary');
  return textSVG(text,b.x,b.y,size,'#FFFFFF','text-anchor="middle" font-weight="700" stroke="#000000" stroke-width="4" paint-order="stroke fill"');
}
/** renderContent is trusted project code; never interpolate unescaped external text. */
export function renderSVG(c,frame,{renderContent,caption=true}={}) {
  const s=stateAt(c,frame),t=c.theme;
  let body=s.segment.mode==='chapter'?chapterMarkup(s,c):'';
  if(s.segment.mode!=='chapter'){
    if(s.segment.title)body+=textSVG(s.segment.title,c.width*.075,c.height*.10,Math.min(c.height>c.width?56:60,c.width*.85/Math.max(1,units(s.segment.title))),t.ink,'font-weight="700"');
    if(renderContent)body+=renderContent({config:c,state:s,box:s.content})||'';
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${c.width}" height="${c.height}" viewBox="0 0 ${c.width} ${c.height}" font-family="${escapeXML(c.fontFamily)}"><rect width="100%" height="100%" fill="${t.background}"/>${body}${caption?captionMarkup(c,s):''}</svg>`;
}
