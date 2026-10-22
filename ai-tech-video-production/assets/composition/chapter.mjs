import {at,clamp} from './motion.mjs';
export const escapeXML = value => String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
export const units = text => [...text].reduce((n,c)=>n+(/[\u0000-\u00ff]/.test(c)?.62:1),0);
export function wrapText(text,maxUnits) {
  const lines=[]; let line='',size=0;
  for (const c of String(text)) {
    if(c==='\n'){lines.push(line);line='';size=0;continue;}
    const u=units(c);if(size+u>maxUnits&&line){lines.push(line);line='';size=0;}
    line+=c;size+=u;
  }
  if(line)lines.push(line);return lines;
}
export function fitLines(text,width,size,min=48,maxLines=3) {
  for(let f=size;f>=min;f-=2){const lines=wrapText(text,width/f);if(lines.length<=maxLines)return {lines,size:f};}
  throw new RangeError('Title too long: shorten the chapter title or provide a wider layout');
}
export function textSVG(text,x,y,size,color,extra='') {
  return `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" ${extra}>${escapeXML(text)}</text>`;
}
/** Original layout inspired by general editorial principles; no Riso code/assets. */
export function chapterMarkup(state,config) {
  const {width:w,height:h,theme:t}=config,portrait=h>w, s=state.segment;
  const length=(s.endFrame-s.startFrame)/config.fps, k=Math.min(1,length/1.5);
  const seconds=state.localFrame/config.fps;
  const numberIn=at(seconds,0,.34*k),titleIn=at(seconds,.15*k,.62*k);
  const end=Math.max(0,length-.22*k),out=1-at(seconds,end,length);
  const x=w*.075, titleX=portrait?x:w*.39, available=w*(portrait?.85:.54);
  const fitted=fitLines(s.title,available,portrait?108:120,48,3);
  const titleY=portrait?h*.50:h*.44;
  const label=s.label||'章节';
  return `<g data-chapter="true" opacity="${out}">
    ${textSVG(label,x,h*.13,portrait?30:28,t.muted)}
    <g opacity="${numberIn}" transform="translate(0 ${(1-numberIn)*35})">${textSVG(s.index,x,portrait?h*.40:h*.53,portrait?350:Math.min(420,w*.25/Math.max(1,units(String(s.index)))),t.accent,'font-weight="800"')}</g>
    <g opacity="${clamp(titleIn)}" transform="translate(0 ${(1-titleIn)*22})">
    ${fitted.lines.map((l,i)=>textSVG(l,titleX,titleY+i*fitted.size*1.22,fitted.size,t.ink,'font-weight="750"')).join('')}
    <path d="M${titleX} ${titleY+(fitted.lines.length-1)*fitted.size*1.22+38}h${100*titleIn}" stroke="${t.accent}" stroke-width="5"/>
    </g></g>`;
}
