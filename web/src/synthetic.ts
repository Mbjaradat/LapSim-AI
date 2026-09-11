// Development/test-only deterministic acceptance driver. No public runtime import.
import fixtures from '../fixtures/native.json';
import {extract,type Raw} from './tracking';
import {Session} from './session';
import {inverseContact,neutral,limits,channels,sub,targetPose,type Pose,type Side,type V,type Target} from './core';
import {sources,targets} from './task';
export function asTarget(side:Side,p:Pose):Target{const t:Target={side,valid:true};for(const k of channels){const base=neutral[side][k];t[k]=k==='jaw'?p[k]:(p[k]-base)/(p[k]>=base?limits[k][1]-base:base-limits[k][0]);}return t;}
export function fixtureHands(phase=0):Raw[]{return (['Left','Right'] as const).map(s=>extract(fixtures.tracking[phase].points[s],s,1,false)!);}
export function syntheticTrial(s=new Session()){
 let time=0,ticks=0;for(let phase=0;phase<3;phase++)for(let i=0;i<42;i++){time+=.1;s.observe(fixtureHands(phase),time);s.tick(time);}
 for(let i=0;i<70&&!s.gate.started;i++){time+=.1;s.observe(fixtureHands(2),time);s.tick(time);}if(!s.gate.started)throw Error('Calibration did not enter LIVE');
 function move(side:Side,point:V,jaw:number){const p={...inverseContact(side,point),jaw},target=asTarget(side,p),desired=targetPose(target)!;let last='';
 for(let i=0;i<160;i++){time+=.05;s.stamp=time;s.targets=[target];s.tick(time);ticks++;
 if(s.collision.pairGap(s.poses)<-1e-9)throw Error('Instrument collision');const held=Object.fromEntries(Object.entries(s.task.owners).filter(([,o])=>o).map(([n,o])=>[o,s.task.offsets[n]]));for(const side of ['LEFT','RIGHT'] as Side[])if(s.collision.boardGap(side,s.poses[side],held)<-1e-9||s.collision.workspaceGap(side,s.poses[side],held)<-1e-9)throw Error('Containment');
 if(channels.every(k=>Math.abs(s.poses[side][k]-desired[k])<1e-7))return;
 const current=JSON.stringify(s.poses[side]);if(current===last&&[...s.collision.contacts].some(c=>c.startsWith(side)))return;last=current;
 }throw Error('Control did not converge');}
 function moveObject(n:string,side:Side,p:V,jaw:number){move(side,sub(p,s.task.offsets[n]??[0,0,0]),jaw);}
 for(const [n,source] of Object.entries(sources)){
 move('LEFT',source,1);move('LEFT',source,0);if(s.task.owners[n]!=='LEFT')throw Error(n+' pickup');
 moveObject(n,'LEFT',[source[0],source[1],source[2]+.025],0);moveObject(n,'LEFT',[0,.042,-.080],0);
 const p=s.task.positions[n],receiver=[p[0],p[1]-.006,p[2]-.003];move('RIGHT',receiver,1);move('RIGHT',receiver,0);
 if(s.task.owners[n]!=='LEFT')throw Error(n+' premature handoff');moveObject(n,'LEFT',[0,.042,-.080],1);if(String(s.task.owners[n])!=='RIGHT')throw Error(n+' handoff '+JSON.stringify({owners:s.task.owners,pending:s.task.pending,positions:s.task.positions,poses:s.poses,offsets:s.task.offsets}));
 const target=targets[n];moveObject(n,'RIGHT',[target[0],target[1],target[2]+.025],0);moveObject(n,'RIGHT',target,0);moveObject(n,'RIGHT',target,1);
 if(s.task.placements[n]!=='CORRECT')throw Error(n+' placement '+JSON.stringify(s.task.positions[n]));
 }
 if(s.task.completed!==6||s.state!=='COMPLETE')throw Error('Incomplete trial');return {ticks,result:s.telemetry.result};
}
