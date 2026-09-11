import {dist,type Side,type V,sides} from './core';
import {Stabilizer,type Raw} from './tracking';
export function homeDirection(p:V|null,h:V|null){if(!p||!h)return 'RETURN TO CAMERA';if(dist(p,h)<=.065)return 'HOME';const dx=h[0]-p[0],dy=h[1]-p[1];return Math.abs(dx)>=Math.abs(dy)?dx>0?'RIGHT':'LEFT':dy>0?'DOWN':'UP';}
export class GuidedSetup {
 stage:'neutral'|'open'|'closed'|null='neutral';state='CAMERA_SETUP';message='CAMERA SETUP';home:Partial<Record<Side,V>>={};anchor:Record<Side,Raw>|null=null;since:number|null=null;last:number|null=null;completedAt:number|null=null;samples:Raw[][]=[];remaining:number|null=null;nearHome=false;
 get ready(){return this.stage===null;}
 restart(message:string){this.anchor=null;this.since=null;this.remaining=null;this.samples=[];this.message=message;}
 update(raw:Raw[],now:number,stabilizer:Stabilizer){if(!Number.isFinite(now)||(this.last!==null&&now<=this.last))throw Error('Time must increase');if(this.last!==null&&now-this.last>.5)this.restart('HOLD STILL');const first=this.last===null;this.last=now;this.nearHome=false;
 const matches=sides.map(s=>raw.filter(h=>h.side===s));let reason='';for(let i=0;i<2;i++){if(matches[i].length!==1){reason=`${sides[i]} HAND LOST - SHOW BOTH HANDS`;break;}const h=matches[i][0];if(!h.orientation||![...h.values,...h.bounds,...h.orientation.longitudinal,...h.orientation.transverse].every(Number.isFinite)){reason='RETRY - SHOW PALMS TO CAMERA';break;}
 if(h.scale<.045)reason='MOVE CLOSER';else if(h.scale>.30)reason='MOVE BACK SLIGHTLY';else if(Math.min(...h.bounds.slice(0,2))<.06||Math.max(...h.bounds.slice(2))>.94)reason='KEEP HANDS INSIDE FRAME';if(reason)break;}
 const pair=matches.every(m=>m.length===1)?Object.fromEntries(matches.map(m=>[m[0].side,m[0]])) as Record<Side,Raw>:null;
 if(pair&&this.home.LEFT)this.nearHome=sides.every(s=>homeDirection(pair[s].palm,this.home[s]??null)==='HOME');
 if(this.ready){this.state=now-this.completedAt!<1.5?'CALIBRATION_COMPLETE':'WAITING_FOR_LIVE';this.message=reason||(this.state==='CALIBRATION_COMPLETE'?'CALIBRATION COMPLETE':'GET READY - RETURN TO HOME');this.nearHome=this.nearHome&&!reason;return;}
 const prefix={neutral:'HOME',open:'OPEN',closed:'PINCH'}[this.stage!];this.state=prefix+'_SETUP';if(first){this.state='CAMERA_SETUP';return;}
 if(reason||!pair){if(!pair)this.state='WAITING_FOR_HANDS';this.restart(reason);return;}
 if(this.stage!=='neutral'&&!this.nearHome){this.restart('MOVE TO HOME');return;}
 for(const s of sides){const h=pair[s],ratio=h.pinch/h.scale;if(this.stage==='open'&&ratio<.65)reason='OPEN MORE - OPEN BOTH THUMB + INDEX';
 if(this.stage==='closed'){const opening=stabilizer.hands[s].cal.open;if(ratio>.22)reason='PINCH MORE - PINCH THUMB + INDEX';else if(opening===null||opening-h.pinch<Math.max(.005,.35*h.scale))reason='RETRY - OPEN AND PINCH TOO SIMILAR';}}
 if(reason){this.restart(reason);return;}
 if(this.anchor)for(const s of sides){const h=pair[s],a=this.anchor[s];if(dist(h.palm,a.palm)>.015||Math.abs(h.scale/a.scale-1)>.08||Math.abs(h.pinch-a.pinch)/a.scale>.12||dist(h.orientation!.longitudinal,a.orientation!.longitudinal)>.15||dist(h.orientation!.transverse,a.orientation!.transverse)>.15){this.restart('HOLD STILL');return;}}
 if(!this.anchor){this.anchor=pair;this.since=now;}this.samples.push(raw);if(this.samples.length>120)this.samples.shift();const elapsed=now-this.since!;
 this.message={neutral:'PLACE BOTH HANDS COMFORTABLY - HOLD STILL',open:'OPEN THUMB + INDEX - HOLD STILL',closed:'PINCH THUMB + INDEX - HOLD STILL'}[this.stage!];
 if(elapsed>=.75){this.state=prefix+'_COUNTDOWN';this.remaining=Math.max(1,Math.ceil(3.75-elapsed));}
 if(elapsed>=3.75&&this.samples.length>=30){if(!stabilizer.capture(this.stage!,this.samples)){this.restart('RETRY - SHOW PALMS AND USE A CLEAR OPEN/PINCH RANGE');return;}
 if(this.stage==='neutral')this.home=Object.fromEntries(sides.map(s=>[s,stabilizer.hands[s].cal.neutral!.slice(12,14)]));this.stage=this.stage==='neutral'?'open':this.stage==='open'?'closed':null;
 this.restart(this.ready?'CALIBRATION COMPLETE':this.stage==='open'?'OPEN HANDS':'PINCH THUMB + INDEX');this.state=this.ready?'CALIBRATION_COMPLETE':this.stage==='open'?'OPEN_SETUP':'PINCH_SETUP';if(this.ready)this.completedAt=now;}
 }
}
export class LiveGate {
 started=false;deadline:number|null=null;last:number|null=null;remaining=5;
 update(eligible:boolean,now:number){if(this.started)return false;if(this.last!==null&&now-this.last>.5)this.deadline=null;this.last=now;if(!eligible){this.deadline=null;this.remaining=5;return false;}if(this.deadline===null)this.deadline=now+5;this.remaining=Math.max(1,Math.ceil(this.deadline-now));if(now>=this.deadline){this.started=true;this.deadline=null;return true;}return false;}
}
