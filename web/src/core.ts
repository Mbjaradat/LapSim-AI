// Deterministic port of instrument/controller, collision and containment modules.
export type V = number[];
export type Side = 'LEFT'|'RIGHT';
export const sides: Side[] = ['LEFT','RIGHT'];
export type Pose = {yaw:number; pitch:number; insertion:number; rotation:number; jaw:number};
export type Poses = Record<Side,Pose>;
export const channels = ['yaw','pitch','insertion','rotation','jaw'] as const;
export const limits:Record<keyof Pose,[number,number]> = {yaw:[-35,35],pitch:[-25,25],insertion:[.12,.28],rotation:[-180,180],jaw:[0,1]};
export const pivots:Record<Side,V> = {LEFT:[-.085,0,.12],RIGHT:[.085,0,.12]};
export const neutral:Poses = {LEFT:{yaw:-18,pitch:12,insertion:.2,rotation:0,jaw:.5},RIGHT:{yaw:18,pitch:12,insertion:.2,rotation:0,jaw:.5}};
export const copyPoses=(p:Poses):Poses=>({LEFT:{...p.LEFT},RIGHT:{...p.RIGHT}});
export const add=(a:V,b:V)=>a.map((v,i)=>v+b[i]);
export const sub=(a:V,b:V)=>a.map((v,i)=>v-b[i]);
export const mul=(a:V,k:number)=>a.map(v=>v*k);
export const dot=(a:V,b:V)=>a.reduce((s,v,i)=>s+v*b[i],0);
export const length=(a:V)=>Math.hypot(...a);
export const dist=(a:V,b:V)=>length(sub(a,b));
export const cross=(a:V,b:V)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export const unit=(a:V)=>length(a)>1e-6?mul(a,1/length(a)):null;
export const clamp=(n:number,l=-1,h=1)=>Math.min(h,Math.max(l,n));
export const rad=(n:number)=>n*Math.PI/180;
export const median=(v:number[])=>{const a=[...v].sort((x,y)=>x-y),i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2;};
export function limited(p:Pose):Pose {const q={...p};for(const k of channels){if(!Number.isFinite(p[k]))throw Error('Nonfinite pose');q[k]=clamp(p[k],...limits[k]);}return q;}
export function transform(p:Pose,v:V):V {
 const [y,t,r]=[p.yaw,p.pitch,p.rotation].map(rad),[x0,y0,z0]=v;
 const x=x0*Math.cos(r)-y0*Math.sin(r),yy=x0*Math.sin(r)+y0*Math.cos(r);
 const y2=yy*Math.cos(t)-z0*Math.sin(t),z=yy*Math.sin(t)+z0*Math.cos(t);
 return [x*Math.cos(y)+z*Math.sin(y),y2,-x*Math.sin(y)+z*Math.cos(y)];
}
export function inverseContact(side:Side,point:V,jaw=0):Pose {const [x,y,z]=sub(point,pivots[side]),r=Math.hypot(x,y,z);return {yaw:Math.atan2(-x,-z)*180/Math.PI,pitch:Math.asin(y/r)*180/Math.PI,insertion:r-.0126*Math.cos(rad(30*jaw)),rotation:0,jaw};}
export type Segment=[V,V,number];
export function proxies(side:Side,p:Pose):{segments:Segment[];contact:V;tip:V} {
 const pivot=pivots[side],tip=add(pivot,transform(p,[0,0,-p.insertion])),theta=rad(30*p.jaw);
 const segments:Segment[]=[[pivot,tip,.003]];
 for(const sign of [-1,1]){const hinge=add(tip,transform(p,[sign*.0015,0,0]));segments.push([hinge,add(hinge,transform(p,[sign*Math.sin(theta)*.018,0,-Math.cos(theta)*.018])),.0025]);}
 return {segments,tip,contact:add(tip,transform(p,[0,0,-.0126*Math.cos(theta)]))};
}
export function segmentDistance(p:V,q:V,a:V,b:V):number {
 const u=sub(q,p),v=sub(b,a),w=sub(p,a),uu=dot(u,u),vv=dot(v,v),uv=dot(u,v),uw=dot(u,w),vw=dot(v,w);
 let s=0,t=0;const c=(x:number)=>clamp(x,0,1);
 if(uu<1e-15)t=vv>1e-15?c(vw/vv):0;
 else if(vv<1e-15)s=c(-uw/uu);
 else{const d=uu*vv-uv*uv;s=d>1e-15?c((uv*vw-uw*vv)/d):0;t=(uv*s+vw)/vv;if(t<0){t=0;s=c(-uw/uu);}else if(t>1){t=1;s=c((uv-uw)/uu);}}
 return dist(add(p,mul(u,s)),add(a,mul(v,t)));
}
export type Plane=[string,V,number];
export const cameraPosition=[0,-.105,.025],cameraTarget=[0,.042,-.099];
export const tanX=36/(2*48),tanY=tanX*3/4;
export function trainerPlanes():Plane[]{
 const ceiling=Math.max(...sides.map(s=>proxies(s,neutral[s]).tip[2]))+.036;
 const planes:Plane[]=[];
 for(const [axis,lo,hi,names] of [[0,-.053,.053,['left','right']],[1,-.001,.085,['front','back']],[2,-.112,ceiling,['floor','upper']]] as [number,number,number,string[]][]){const n=[0,0,0];n[axis]=1;planes.push([names[0],n,lo],[names[1],mul(n,-1),-hi]);}
 const forward=unit(sub(cameraTarget,cameraPosition))!,right=unit(cross(forward,[0,0,1]))!,up=cross(right,forward);
 for(const [label,axis,tan] of [['horizontal',right,tanX],['vertical',up,tanY]] as [string,V,number][])
  for(const sign of [-1,1]){const n=unit(add(mul(forward,tan*.92),mul(axis,sign)))!;planes.push([`camera_${label}_${sign}`,n,dot(n,cameraPosition)]);}
 return planes;
}
export type Held=Partial<Record<Side,V>>;
export class Collision {
 planes:Plane[];contacts=new Set<string>();cache=new Map<string,ReturnType<typeof proxies>>();
 constructor(planes=trainerPlanes()){this.planes=planes;}
 geometry(s:Side,p:Pose){const key=s+channels.map(k=>p[k]).join(',');let g=this.cache.get(key);if(!g){g=proxies(s,p);this.cache.set(key,g);}return g;}
 boardGap(s:Side,p:Pose,held:Held={}){const g=this.geometry(s,p);let low=Math.min(...g.segments.map(([a,b,r])=>Math.min(a[2],b[2])-r));if(held[s])low=Math.min(low,g.contact[2]+held[s]![2]-.0016);return low+.112-.0001;}
 pairGap(p:Poses){return Math.min(...this.geometry('LEFT',p.LEFT).segments.flatMap(([a,b,r])=>this.geometry('RIGHT',p.RIGHT).segments.map(([c,d,t])=>segmentDistance(a,b,c,d)-r-t-.0001)));}
 workspaceGaps(s:Side,p:Pose,held:Held={}){const g=this.geometry(s,p),base=g.tip,working:Segment[]=[[add(base,transform(p,[0,0,.018])),base,.003],...g.segments.slice(1)];const ring=held[s]?add(g.contact,held[s]!):null;
 return this.planes.map(([name,n,offset])=>{let low=Math.min(...working.map(([a,b,r])=>Math.min(dot(n,a),dot(n,b))-r));if(ring)low=Math.min(low,dot(n,ring)-.0071*Math.hypot(n[0],n[1])-.0016*Math.abs(n[2]));return [name,low-offset-.0001] as [string,number];});}
 workspaceGap(s:Side,p:Pose,h:Held={}){return Math.min(...this.workspaceGaps(s,p,h).map(x=>x[1]));}
 project(s:Side,p:Pose,h:Held){let q={...p},gap=this.boardGap(s,q,h);if(gap<0)q.insertion=Math.max(.12,q.insertion+gap/-transform(q,[0,0,-1])[2]);
 let [low,high]=limits.insertion;const direction=transform(q,[0,0,-1]),gaps=this.workspaceGaps(s,q,h);
 this.planes.forEach(([,n],i)=>{const slope=dot(n,direction);if(slope>1e-10)low=Math.max(low,q.insertion-gaps[i][1]/slope);else if(slope< -1e-10)high=Math.min(high,q.insertion-gaps[i][1]/slope);});
 if(low<=high)q.insertion=clamp(q.insertion,low,high);return q;
 }
 resolve(previous:Poses,proposed:Poses,held:Held={}):Poses{
 this.cache.clear();this.contacts.clear();const goal={LEFT:limited(proposed.LEFT),RIGHT:limited(proposed.RIGHT)};
 const travel=Math.max(...sides.map(s=>Math.abs(goal[s].insertion-previous[s].insertion)+.298*rad(Math.abs(goal[s].yaw-previous[s].yaw)+Math.abs(goal[s].pitch-previous[s].pitch))+.018*rad(Math.abs(goal[s].rotation-previous[s].rotation)+30*Math.abs(goal[s].jaw-previous[s].jaw))));
 const count=Math.max(1,Math.ceil(travel/.00075));let current=copyPoses(previous);
 for(let step=1;step<=Math.min(count,64);step++){const before=JSON.stringify(current);
 for(const s of sides){for(const k of ['jaw','rotation','yaw','pitch','insertion'] as (keyof Pose)[]){const start=current[s],desired=previous[s][k]+(goal[s][k]-previous[s][k])*step/count;
 if(Math.abs(desired-start[k])<1e-12)continue;
 const candidate=(f:number)=>this.project(s,{...start,[k]:start[k]+(desired-start[k])*f},held);
 const valid=(p:Pose)=>(!this.planes.length||Math.abs(p.insertion-start.insertion)<=.00075+1e-10)&&this.boardGap(s,p,held)>=-1e-10&&this.workspaceGap(s,p,held)>=-1e-10&&this.pairGap({...current,[s]:p})>=-1e-10;
 const q=candidate(1);if(valid(q))current={...current,[s]:q};else{this.contacts.add(s+':contact');let lo=0,hi=1;for(let i=0;i<9;i++){const m=(lo+hi)/2;if(valid(candidate(m)))lo=m;else hi=m;}current={...current,[s]:lo?candidate(lo):start};}
 }
 if(this.boardGap(s,current[s],held)<1e-7)this.contacts.add(s+':board');
 for(const [name,gap] of this.workspaceGaps(s,current[s],held))if(gap<1e-7)this.contacts.add(s+':'+name);
 }if(JSON.stringify(current)===before)break;
 }return current;
 }
}
export type Target={side:Side;valid:boolean; yaw?:number;pitch?:number;insertion?:number;rotation?:number;jaw?:number};
export function targetPose(t:Target):Pose|null{if(!t.valid)return null;const p={...neutral[t.side]};for(const k of channels){const v=t[k];if(v===undefined||!Number.isFinite(v))throw Error('Invalid target');if(k==='jaw')p[k]=clamp(v,0,1);else{const n=neutral[t.side][k];p[k]=n+clamp(v)*(v>=0?limits[k][1]-n:n-limits[k][0]);}}return limited(p);}
export function approach(old:Poses,targets:Target[],dt:number):Poses{if(!Number.isFinite(dt)||dt<0)throw Error('Invalid time');const poses=copyPoses(old),rates={yaw:22,pitch:22,insertion:.035,rotation:90,jaw:8};for(const t of targets){const p=targetPose(t);if(p)for(const k of channels){const step=rates[k]*Math.min(dt,.05);poses[t.side][k]+=clamp(p[k]-poses[t.side][k],-step,step);}}return {LEFT:limited(poses.LEFT),RIGHT:limited(poses.RIGHT)};}
