import {add,sub,mul,dot,cross,unit,dist,median,clamp,type V,type Side,type Target,sides} from './core';
export type Frame={longitudinal:V;transverse:V};
export type Landmark={x:number;y:number;z:number};
export type Raw={side:Side;values:number[];palm:V;scale:number;pinch:number;orientation:Frame|null;bounds:number[];landmarks:Landmark[]};
export type Calibration={neutral:number[]|null;orientation:Frame|null;open:number|null;closed:number|null};
export const emptyCalibration=():Calibration=>({neutral:null,orientation:null,open:null,closed:null});
export const ready=(c:Calibration)=>!!c.neutral&&!!c.orientation&&c.open!==null&&c.closed!==null&&c.open>c.closed;
export function frameAxes(long:V,trans:V):Frame|null {const a=unit(long);if(!a)return null;const b=unit(sub(trans,mul(a,dot(a,trans))));return b?{longitudinal:a,transverse:b}:null;}
export function palmFrame(points:V[]):Frame|null {const [w,...knuckles]=points;return frameAxes(sub([0,1,2].map(i=>knuckles.reduce((s,p)=>s+p[i],0)/4),w),[0,1,2].map(i=>knuckles.reduce((s,p,j)=>s+[-1.5,-.5,.5,1.5][j]*p[i],0)/5));}
export function twist(n:Frame|null,c:Frame|null):number|null {if(!n||!c)return null;const a=n.longitudinal,b=c.longitudinal,cos=clamp(dot(a,b));if(cos<-.95)return null;const v=cross(a,b),first=cross(v,n.transverse),second=cross(v,first),reference=add(add(n.transverse,first),mul(second,1/(1+cos)));return Math.atan2(dot(b,cross(reference,c.transverse)),dot(reference,c.transverse));}
export const wrap=(n:number)=>((n+Math.PI)%(2*Math.PI)+2*Math.PI)%(2*Math.PI)-Math.PI;
export function extract(points:Landmark[],label:string,aspect:number,mirrored=true):Raw|null {
 if(!['Left','Right'].includes(label)||points.length!==21||!points.every(p=>[p.x,p.y,p.z].every(Number.isFinite)))return null;
 const side=(mirrored?(label==='Left'?'RIGHT':'LEFT'):label.toUpperCase()) as Side;
 const xy=(i:number)=>[clamp(points[i].x,0,1),clamp(points[i].y,0,1)];const [w,index,thumb,middle]=[0,8,4,9].map(xy),pinch=dist(index,thumb);
 const ids=[0,5,9,13,17],ps=ids.map(i=>[points[i].x*aspect,points[i].y,points[i].z*aspect]);
 const scale=median([[0,1],[0,2],[0,3],[0,4],[1,4],[1,3],[2,4]].map(([a,b])=>dist(ps[a],ps[b])));
 const line=sub(xy(17),xy(5)),palm=[0,1].map(i=>ids.reduce((s,id,j)=>s+[.4,.15,.15,.15,.15][j]*xy(id)[i],0));
 return {side,values:[...w,...index,...thumb,pinch,...middle,scale,...line,...palm],palm,scale,pinch,orientation:palmFrame(ps),bounds:[Math.min(...points.map(p=>p.x)),Math.min(...points.map(p=>p.y)),Math.max(...points.map(p=>p.x)),Math.max(...points.map(p=>p.y))],landmarks:points};
}
export type Stable={side:Side;tracked:boolean;values:number[]|null;calibration:Calibration;roll:number|null;normalizedPinch:number|null;valid:boolean};
export class Stabilizer {
 hands:Record<Side,{cal:Calibration;filtered:number[]|null;output:number[]|null;angle:number|null}>= {LEFT:{cal:emptyCalibration(),filtered:null,output:null,angle:null},RIGHT:{cal:emptyCalibration(),filtered:null,output:null,angle:null}};
 last:number|null=null;
 capture(stage:'neutral'|'open'|'closed',frames:Raw[][]):boolean {
 if(frames.length<30)return false;const candidates={} as Record<Side,Calibration>;
 for(const side of sides){const samples=frames.slice(-30).map(f=>f.filter(h=>h.side===side));if(samples.some(f=>f.length!==1))return false;const raw=samples.map(f=>f[0]);
 const values=raw[0].values.map((_,i)=>median(raw.map(h=>h.values[i]))),cal={...this.hands[side].cal};
 if(stage==='neutral'){cal.neutral=values;const axes=raw.map(h=>h.orientation);if(axes.some(a=>!a))return false;cal.orientation=frameAxes([0,1,2].map(i=>median(axes.map(a=>a!.longitudinal[i]))),[0,1,2].map(i=>median(axes.map(a=>a!.transverse[i]))));}
 else cal[stage]=values[6];
 if(!cal.neutral||!cal.orientation||!values.every(Number.isFinite)||cal.neutral[9]<=0)return false;
 if(cal.open!==null&&cal.closed!==null&&cal.open-cal.closed<.005)return false;
 if(stage==='closed'&&(!ready(cal)||cal.open!-cal.closed!<Math.max(.005,.35*cal.neutral[9])))return false;candidates[side]=cal;
 }
 for(const s of sides){this.hands[s].cal=candidates[s];if(stage==='neutral')this.hands[s].angle=null;}return true;
 }
 update(raw:Raw[],now:number):Stable[]{if(!Number.isFinite(now)||(this.last!==null&&now<=this.last))throw Error('Time must increase');const dt=this.last===null?1/30:Math.min(now-this.last,1/15);this.last=now;
 return sides.map(side=>{const hand=this.hands[side],matches=raw.filter(h=>h.side===side),r=matches.length===1?matches[0]:null,cal=hand.cal;
 const tracked=!!r&&r.values.every(Number.isFinite)&&r.scale>0;
 if(tracked){const v=r!.values;if(!hand.filtered){hand.filtered=[...v];hand.output=[...v];}else{hand.filtered=hand.filtered.map((old,i)=>old+(1-Math.exp(-dt/(i===6?.04:i===9?.10:.06)))*(v[i]-old));hand.output=hand.output!.map((old,i)=>{const delta=hand.filtered![i]-old;let movement=Math.max(0,Math.abs(delta)-.002),limit=.03;
 if(i===9){const base=cal.neutral?.[9]??old;movement=Math.max(0,Math.abs(delta)-.005*base);limit=.03*base;}
 if(i===6&&ready(cal)){const span=cal.open!-cal.closed!;movement=Math.max(0,Math.abs(delta)-.005*span);limit=.35*span;}
 return old+Math.min(limit,movement)*(delta>=0?1:-1);});}}
 const angle=tracked?twist(cal.orientation,r!.orientation):null;if(angle!==null)hand.angle=hand.angle===null?angle:wrap(hand.angle+(1-Math.exp(-dt/.06))*wrap(angle-hand.angle));
 const normalizedPinch=ready(cal)&&hand.output?clamp((hand.output[6]-cal.closed!)/(cal.open!-cal.closed!),0,1):null;
 return {side,tracked,values:hand.output,calibration:cal,roll:angle===null?null:hand.angle,normalizedPinch,valid:tracked&&ready(cal)};
 });
 }
}
export function relative(delta:number,range:number,dead:number){return clamp(Math.max(0,Math.abs(delta)-dead)/(range-dead))*(delta>=0?1:-1);}
export function mapHand(s:Stable):Target{const c=s.calibration,o=s.values,n=c.neutral;if(!s.valid||!o||!n||s.roll===null||s.normalizedPinch===null||!o.every(Number.isFinite))return {side:s.side,valid:false};return {side:s.side,valid:true,yaw:relative(o[12]-n[12],.08,.003),pitch:relative(o[13]-n[13],.08,.003),insertion:relative(1-o[9]/n[9],.15,.02),rotation:relative(-s.roll,35*Math.PI/180,2*Math.PI/180),jaw:s.normalizedPinch};}
