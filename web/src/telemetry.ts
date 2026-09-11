import {dist,type Side,type V} from './core';
import type {PegTransfer} from './task';
export type Counts=Record<'grasps'|'releases'|'handoffs'|'drops'|'incorrect_placements'|'successful_placements',number>;
export class Telemetry {
 clock=0;active=0;pausedSeconds=0;started:number|null=null;ended:number|null=null;pauseStart:number|null=null;
 paths:Record<Side,number>={LEFT:0,RIGHT:0};anchors:Record<string,V>={};owners:Record<string,Side|null>={};
 counts:Counts={grasps:0,releases:0,handoffs:0,drops:0,incorrect_placements:0,successful_placements:0};
 events:Record<string,unknown>[]=[];samples:Record<string,unknown>[]=[];pauses:Record<string,unknown>[]=[];
 truncated={events:false,samples:false,pauses:false};nextSample=0;result:Record<string,any>|null=null;
 reset(){Object.assign(this,new Telemetry());}
 append(key:'events'|'samples'|'pauses',value:Record<string,unknown>){const cap={events:4096,samples:600,pauses:1024}[key];if(this[key].length===cap){this[key].shift();this.truncated[key]=true;}this[key].push(value);}
 event(type:string,fields:Record<string,unknown>={},time=this.clock){this.append('events',{type,time_seconds:time,...fields});}
 observe(dt:number,paused:boolean,task:Pick<PegTransfer,'state'|'owners'|'placements'|'completed'>,tips:Record<Side,V>){if(!Number.isFinite(dt)||dt<0||Object.values(tips).some(p=>p.length!==3||!p.every(Number.isFinite)))throw Error('Invalid telemetry sample');if(this.result)return;this.clock+=dt;
 if(this.started===null){if(paused||!['RUNNING','COMPLETE'].includes(task.state)){this.owners={...task.owners};return;}this.started=this.clock-dt;this.event('session_start',{},this.started);this.anchors=structuredClone(tips);}
 if(paused){if(this.pauseStart===null){this.pauseStart=this.clock-dt;this.event('pause_start',{},this.pauseStart);}this.anchors=structuredClone(tips);return;}
 if(this.pauseStart!==null){this.pausedSeconds+=this.clock-dt-this.pauseStart;this.append('pauses',{start_seconds:this.pauseStart,end_seconds:this.clock-dt});this.pauseStart=null;this.event('pause_end',{},this.clock-dt);this.anchors=structuredClone(tips);}
 this.active+=dt;for(const s of ['LEFT','RIGHT'] as Side[]){const d=dist(this.anchors[s],tips[s]);if(d>=.0005){this.paths[s]+=d;this.anchors[s]=[...tips[s]];}}
 if(this.clock>=this.nextSample){this.append('samples',{time_seconds:this.clock,active_seconds:this.active,tips_metres:structuredClone(tips)});this.nextSample=this.clock+.1;}
 for(const n of Object.keys(task.owners).sort()){const owner=task.owners[n],old=this.owners[n]??null;if(old===owner)continue;this.event('ownership_change',{object:n,previous_owner:old,owner});if(old){this.counts.releases++;this.event('release',{object:n,side:old});}if(owner){this.counts.grasps++;this.event('grasp',{object:n,side:owner});}if(old&&owner){this.counts.handoffs++;this.event('handoff',{object:n,donor:old,receiver:owner});}else if(old){const kind=({DROPPED:'drops',INCORRECT:'incorrect_placements',CORRECT:'successful_placements'} as const)[task.placements[n] as 'DROPPED'|'INCORRECT'|'CORRECT'];if(kind){this.counts[kind]++;this.event(kind,{object:n});}}}
 this.owners={...task.owners};if(task.state==='COMPLETE'){this.event('task_complete');this.finish(task.completed,'COMPLETE');}
 }
 finish(completed:number,outcome='STOPPED'){if(this.started===null||this.result)return;if(this.pauseStart!==null){this.pausedSeconds+=this.clock-this.pauseStart;this.append('pauses',{start_seconds:this.pauseStart,end_seconds:this.clock});this.pauseStart=null;this.event('pause_end');}this.ended=this.clock;this.event('session_end',{outcome});this.result=structuredClone({schema_version:1,task:'peg_transfer',outcome,start_seconds:this.started,end_seconds:this.ended,active_seconds:this.active,paused_seconds:this.pausedSeconds,objects_completed:completed,objects_total:6,counts:this.counts,path_metres:{...this.paths,TOTAL:this.paths.LEFT+this.paths.RIGHT},path_threshold_metres:.0005,pause_intervals:this.pauses,events:this.events,tip_samples:this.samples,truncated:this.truncated});}
}
