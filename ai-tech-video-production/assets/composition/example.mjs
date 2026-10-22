import {textSVG} from './chapter.mjs';
import {at} from './motion.mjs';
export function exampleConfig(portrait=false) {
  return {width:portrait?1080:1920,height:portrait?1920:1080,fps:30,totalFrames:300,hostTransitionFrames:15,
    segments:[
      {id:'intro',startFrame:0,endFrame:60,mode:'host',title:'从真人进入章节'},
      {id:'chapter',startFrame:60,endFrame:120,mode:'chapter',index:'01',label:'第一阶段',title:'AI工具'},
      {id:'explain',startFrame:120,endFrame:180,mode:'split',title:'把一个任务交给AI'},
      {id:'diagram',startFrame:180,endFrame:240,mode:'content',title:'让观众专心看内容'},
      {id:'return',startFrame:240,endFrame:300,mode:'host',title:'回到真人，口播时钟保持连续'}],
    subtitles:[{startFrame:60,endFrame:120,text:'章节页覆盖画面，原声继续播放'}, {startFrame:240,endFrame:300,text:'人物回来时接上原视频当前时间'}]};
}
export function exampleContent({config:c,state:s,box:b}) {
  if(s.segment.mode==='host')return '';
  const p=at(s.localFrame,0,Math.min(20,s.segment.endFrame-s.segment.startFrame)),x=b.x+b.width*.12,y=b.y+b.height*.40;
  const font=c.height>c.width?42:46;
  return `<g opacity="${p}">${textSVG('输入',x,y,font,c.theme.ink)}${textSVG('结果',x+b.width*.65,y,font,c.theme.ink)}<path d="M${x+b.width*.19} ${y-15}h${b.width*.36*p}" stroke="${c.theme.accent}" stroke-width="5"/>${textSVG('同一套素材，按真人是否出现调整版面',b.x,b.y+b.height*.76,c.height>c.width?26:28,c.theme.muted)}</g>`;
}
