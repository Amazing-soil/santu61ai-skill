#!/usr/bin/env node
import test from 'node:test';
import assert from 'node:assert/strict';
import {compile,stateAt,renderSVG} from '../assets/composition/composition.mjs';
import {exampleConfig,exampleContent} from '../assets/composition/example.mjs';
import {at,smooth,settle,vis,bezier,strokeValues,stroke} from '../assets/composition/motion.mjs';
for(const portrait of [false,true]) {
  test(`${portrait?'portrait':'landscape'}: complete timeline, source clock, hidden host and full content`,()=>{
    const c=compile(exampleConfig(portrait));
    for(let f=0;f<300;f++){
      const s=stateAt(c,f);assert.equal(s.sourceTime,f/30);
      assert.equal(s.host.visible,!(f>=60&&f<120||f>=180&&f<240));
      const r=s.host.rect;assert.ok(r.x>=0&&r.y>=0&&r.x+r.width<=c.width&&r.y+r.height<c.height*.9);
      assert.equal(renderSVG(c,f,{renderContent:exampleContent}),renderSVG(c,f,{renderContent:exampleContent}));
    }
    assert.ok(stateAt(c,200).content.width>stateAt(c,140).content.width||portrait);
    assert.ok(stateAt(c,200).content.height>stateAt(c,140).content.height||!portrait);
    assert.equal(stateAt(c,240).sourceTime,8);
    assert.ok(stateAt(c,240).host.rect.y>c.height*.10+12, "Host must not cover the header");
  });
}
test('invalid timeline and conflicting host state are rejected',()=>{
  for(const mutate of [c=>c.segments[1].startFrame++,c=>c.segments[1].host={visible:true},c=>c.totalFrames++,c=>c.segments[0].mode='bad',c=>c.segments[2].host={rect:{x:-1,y:0,width:20,height:20}}]){
    const c=exampleConfig();mutate(c);assert.throws(()=>compile(c));
  }
});
test('captions and arbitrary text cannot escape SVG',()=>{
  const c=exampleConfig();c.segments[1].title='<script>&"';c.subtitles[0].text='<img onerror=x>';
  const svg=renderSVG(compile(c),90);assert.ok(!svg.includes('<script>'));assert.ok(svg.includes('&lt;script&gt;'));assert.ok(svg.includes('&lt;img onerror=x&gt;'));
});
test('short chapter has finite motion and does not change total duration',()=>{
  const c=compile({width:1920,height:1080,fps:30,totalFrames:1,segments:[{id:'one',startFrame:0,endFrame:1,mode:'chapter',index:'1',title:'短章'}]});
  assert.ok(!/NaN|Infinity/.test(renderSVG(c,0)));assert.equal(stateAt(c,0).host.visible,false);assert.throws(()=>stateAt(c,1));
});
test('visible-to-visible host movement reaches both geometric endpoints',()=>{
  const c=exampleConfig();c.segments[1]={id:'s',startFrame:60,endFrame:120,mode:'split'};const x=compile(c);
  assert.deepEqual(stateAt(x,60).host.rect,stateAt(x,59).host.rect);
  assert.notDeepEqual(stateAt(x,68).host.rect,stateAt(x,60).host.rect);
  assert.deepEqual(stateAt(x,90).host.rect,stateAt(x,119).host.rect);
});
test('Motion functions are self-contained, endpoint-correct and repeatable',()=>{
  assert.equal(at(-1,0,1),0);assert.equal(at(2,0,1),1);assert.equal(at(.5,0,1),.5);
  assert.equal(vis(-1,0,1),0);assert.equal(vis(2,0,1),0);assert.equal(vis(.5,0,1),1);
  assert.deepEqual(bezier([0,0],[1,2],[2,3],[4,5],0),[0,0]);assert.deepEqual(bezier([0,0],[1,2],[2,3],[4,5],1),[4,5]);
  assert.deepEqual(strokeValues(20,.25),{strokeDasharray:20,strokeDashoffset:15});assert.throws(()=>at(0,1,1));
});
test('easing stays monotonic, arrival settles and fade envelopes are symmetric',()=>{
  let previous=0;const arrivals=[];
  for(let i=0;i<=100;i++){
    const p=i/100,ease=smooth(p);assert.ok(ease>=previous&&ease<=1);previous=ease;
    assert.ok(Math.abs(vis(p,0,1,.4)-vis(1-p,0,1,.4))<1e-12);
    arrivals.push(settle(p,0,1));
  }
  assert.equal(settle(-1,0,1),0);assert.equal(settle(2,0,1),1);
  assert.ok(Math.max(...arrivals)>1&&Math.max(...arrivals)<1.06);
  assert.equal(vis(.5,0,1,2),1);
  for(const call of [()=>smooth(NaN),()=>settle(1,0,0),()=>vis(0,0,1,Infinity),()=>strokeValues(-1,0)])assert.throws(call);
});
test('curve midpoint and browser stroke adapter match geometric expectations',()=>{
  assert.deepEqual(bezier([0,0],[0,2],[2,2],[2,0],.5),[1,1.5]);
  const path={getTotalLength:()=>80,style:{}};
  assert.deepEqual(stroke(path,.25),{strokeDasharray:80,strokeDashoffset:60});
  assert.deepEqual(path.style,{strokeDasharray:'80',strokeDashoffset:'60'});
  assert.throws(()=>bezier([0],[0,2],[2,2],[2,0],.5));
});
