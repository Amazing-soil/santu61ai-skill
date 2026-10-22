import {compile,stateAt,renderSVG,captionMarkup} from './composition.mjs';
import {escapeXML} from './chapter.mjs';
function waitFor(video,event,predicate,action=()=>{}) {
  return new Promise((resolve,reject)=>{
    let timer;
    const done=()=>{if(!predicate())return;clean();resolve();};
    const fail=()=>{clean();reject(Error(video.error?.message||`Video ${event} failed`));};
    const clean=()=>{clearTimeout(timer);video.removeEventListener(event,done);video.removeEventListener('error',fail);};
    video.addEventListener(event,done);video.addEventListener('error',fail);
    timer=setTimeout(()=>{clean();reject(Error(`Timed out waiting for ${event}`));},15000);
    try{action();done();}catch(e){clean();reject(e);}
  });
}
export function createPlayer(root,input,{source,renderContent}={}) {
  const config=compile(input);
  root.replaceChildren();root.style.cssText=`position:relative;aspect-ratio:${config.width}/${config.height};overflow:hidden;background:${config.theme.background}`;
  const background=document.createElement('div'),video=document.createElement('video'),captions=document.createElement('div');
  for(const el of [background,captions])el.style.cssText='position:absolute;inset:0;pointer-events:none';
  video.preload='auto';video.playsInline=true;video.style.cssText='position:absolute;object-fit:cover';
  video.setAttribute('aria-label','原口播，唯一声音来源');root.append(background,video,captions);
  let frame=0,raf=0,disposed=false,busy=false,hasSource=false;
  function paint(next) {
    frame=next;const s=stateAt(config,frame),r=s.host.rect;
    background.innerHTML=renderSVG(config,frame,{renderContent,caption:false});
    background.firstElementChild.style.cssText='width:100%;height:100%;display:block';
    Object.assign(video.style,{left:`${r.x/config.width*100}%`,top:`${r.y/config.height*100}%`,width:`${r.width/config.width*100}%`,height:`${r.height/config.height*100}%`,visibility:s.host.visible&&hasSource?'visible':'hidden',clipPath:`inset(0 round ${18/r.width*100}% / ${18/r.height*100}%)`});
    video.dataset.visible=String(s.host.visible&&hasSource);
    captions.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${config.width} ${config.height}" width="100%" height="100%" font-family="${escapeXML(config.fontFamily)}">${captionMarkup(config,s)}</svg>`;
    return s;
  }
  function syncClock(){
    if(disposed||video.paused||!hasSource)return;
    const next=Math.min(config.totalFrames-1,Math.floor(video.currentTime*config.fps));
    if(next!==frame)paint(next);
    if(video.currentTime>=config.totalFrames/config.fps)video.pause();
  }
  function tick(){if(disposed)return;syncClock();raf=requestAnimationFrame(tick);}
  // Keep preview clock responsive when a browser delays its first animation frame.
  const clockTimer=setInterval(syncClock,1000/config.fps);
  async function setSource(url) {
    if(busy)throw Error('Player operation in progress');busy=true;video.pause();hasSource=false;
    try{
      await waitFor(video,'loadeddata',()=>video.readyState>=2,()=>{video.src=url;video.load();});
      if(video.duration+1/config.fps<config.totalFrames/config.fps)throw Error('Source is shorter than the timeline');
      hasSource=true;paint(frame);
    }catch(e){video.removeAttribute('src');video.load();paint(frame);throw e;}finally{busy=false;}
    await seek(frame);return stateAt(config,frame);
  }
  async function seek(next) {
    stateAt(config,next);if(busy)throw Error('Player operation in progress');busy=true;video.pause();
    try{
      const t=next/config.fps;
      if(hasSource&&(Math.abs(video.currentTime-t)>1e-6||video.readyState<2))await waitFor(video,'seeked',()=>!video.seeking&&video.readyState>=2&&Math.abs(video.currentTime-t)<.5/config.fps,()=>{video.currentTime=t;});
      await document.fonts.ready;return paint(next);
    }finally{busy=false;}
  }
  async function svgImage(svg) {
    const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml;charset=utf-8'}));
    try{const im=new Image();im.src=url;await im.decode();return im;}finally{URL.revokeObjectURL(url);}
  }
  async function renderFrame(next) {
    const s=await seek(next),c=document.createElement('canvas');c.width=config.width;c.height=config.height;
    const ctx=c.getContext('2d',{colorSpace:'srgb'});
    ctx.drawImage(await svgImage(renderSVG(config,next,{renderContent,caption:false})),0,0);
    if(s.host.visible){
      if(!hasSource)throw Error('Visible host requires an actual source video');
      const r=s.host.rect,sw=video.videoWidth,sh=video.videoHeight,ratio=Math.max(r.width/sw,r.height/sh);
      const cw=r.width/ratio,ch=r.height/ratio;
      ctx.save();ctx.beginPath();ctx.roundRect(r.x,r.y,r.width,r.height,18);ctx.clip();
      ctx.drawImage(video,(sw-cw)/2,(sh-ch)/2,cw,ch,r.x,r.y,r.width,r.height);ctx.restore();
    }
    ctx.drawImage(await svgImage(`<svg xmlns="http://www.w3.org/2000/svg" width="${config.width}" height="${config.height}" font-family="${escapeXML(config.fontFamily)}">${captionMarkup(config,s)}</svg>`),0,0);
    return c;
  }
  paint(0);tick();
  const ready=source?setSource(source):Promise.resolve();
  return {config,video,ready,setSource,seek,renderFrame,getState:()=>({...stateAt(config,frame),hasSource,currentTime:video.currentTime,paused:video.paused}),
    play:async()=>{if(busy||!hasSource)throw Error('Load a source and finish seeking before playback');if(frame===config.totalFrames-1)await seek(0);await video.play();},
    pause:()=>video.pause(),destroy:()=>{disposed=true;cancelAnimationFrame(raf);clearInterval(clockTimer);video.pause();video.removeAttribute('src');video.load();root.replaceChildren();}};
}
