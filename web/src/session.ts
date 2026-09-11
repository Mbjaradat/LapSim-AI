import {Collision,approach,copyPoses,neutral,proxies,limited,type Target,type Poses,type Side,sides} from './core';
import {PegTransfer} from './task';
import {BeginnerTransfer} from './beginner';
import {Telemetry} from './telemetry';
import {GuidedSetup,LiveGate} from './setup';
import {Stabilizer,mapHand,type Raw,type Stable} from './tracking';
export class Session {
 poses:Poses=copyPoses(neutral);task=new PegTransfer();telemetry=new Telemetry();collision=new Collision();setup=new GuidedSetup();stabilizer=new Stabilizer();gate=new LiveGate();
 targets:Target[]=[];stable:Stable[]=[];raw:Raw[]=[];stamp:number|null=null;last:number|null=null;paused=false;state='CAMERA_SETUP';message='Show both hands to begin';
 constructor(public mode:'structured'|'beginner'='structured'){if(mode==='beginner')this.task=new BeginnerTransfer();}
 get remaining(){return Math.max(0,120-this.telemetry.active);}
 observe(raw:Raw[],now:number){this.raw=raw;this.stamp=now;this.setup.update(raw,now,this.stabilizer);this.stable=this.stabilizer.update(raw,now);this.targets=this.stable.map(mapHand);}
 retry(){this.poses=copyPoses(neutral);this.task.reset();this.telemetry.reset();this.collision=new Collision();this.gate=new LiveGate();this.paused=false;this.last=null;this.state='WAITING_FOR_LIVE';}
 recalibrate(){if(!this.paused||Object.values(this.task.owners).some(Boolean))return false;this.setup=new GuidedSetup();this.stabilizer=new Stabilizer();this.gate=new LiveGate();this.targets=[];this.stamp=null;this.paused=false;return true;}
 fresh(now:number){return this.stamp!==null&&now-this.stamp>=0&&now-this.stamp<=.5;}
 resume(now:number){if(!this.fresh(now)||this.targets.length!==2||!this.targets.every(t=>t.valid))return false;this.paused=false;return true;}
 tick(now:number){if(this.last!==null&&now<=this.last)return;let dt=this.last===null?0:now-this.last;this.last=now;
 const fresh=this.fresh(now),targets=fresh?this.targets:[],eligible=fresh&&this.setup.ready&&this.setup.nearHome&&this.setup.state!=='CALIBRATION_COMPLETE'&&targets.length===2&&targets.every(t=>t.valid);
 const entered=this.gate.update(eligible,now);const blocked=!this.gate.started||entered||this.paused;
 if(this.mode==='beginner'&&!blocked&&this.telemetry.started!==null&&this.task.state!=='COMPLETE'&&dt>=this.remaining){
  dt=this.remaining;this.task.state='COMPLETE';
  this.telemetry.observe(dt,false,this.task,{LEFT:proxies('LEFT',this.poses.LEFT).tip,RIGHT:proxies('RIGHT',this.poses.RIGHT).tip});
  if(this.telemetry.result)Object.assign(this.telemetry.result,{task:'beginner_free_transfer',successful_transfers:this.task.completed,objects_total:null});
 }
 if(this.task.state==='COMPLETE'){this.state='COMPLETE';this.message=this.mode==='beginner'?'Practice session complete':'Peg Transfer complete';return;}
 if(!this.gate.started){this.state=this.gate.deadline!==null?'LIVE_COUNTDOWN':this.setup.state;this.message=this.gate.deadline!==null?`Get ready · ${this.gate.remaining}`:fresh?this.setup.message:'Show both hands · waiting for camera';}
 else if(this.paused){this.state='PAUSED';this.message='Paused · return both hands, then Resume';}
 else {const missing=sides.filter(s=>!targets.some(t=>t.side===s&&t.valid));this.state=missing.length?'TRACKING_LOST':'LIVE';this.message=missing.length?`${missing.join(' + ')} HAND LOST · RETURN TO CAMERA / HOME`:this.mode==='beginner'?'Move any ring onto any target peg.':'Live · transfer each ring to its matching target';}
 if(!blocked){const proposed=approach(this.poses,targets,dt),held=Object.fromEntries(Object.entries(this.task.owners).filter(([,s])=>s).map(([n,s])=>[s,this.task.offsets[n]]));const accepted=this.collision.resolve(this.poses,proposed,held);this.poses={LEFT:limited(accepted.LEFT),RIGHT:limited(accepted.RIGHT)};
 this.task.update(Object.fromEntries(sides.map(s=>[s,[proxies(s,this.poses[s]).contact,this.poses[s].jaw]])),Math.min(dt,.05));}
 this.telemetry.observe(dt,blocked,this.task,{LEFT:proxies('LEFT',this.poses.LEFT).tip,RIGHT:proxies('RIGHT',this.poses.RIGHT).tip});
 if(this.task.state==='COMPLETE'){this.state='COMPLETE';this.message='Peg Transfer complete';}
 }
}
