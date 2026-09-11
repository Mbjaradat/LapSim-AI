import {add,sub,dist,type V,type Side,sides} from './core';
export type Hands=Partial<Record<Side,[V,number]>>;
export const sources:Record<string,V>=Object.fromEntries([.020,.042,.064].flatMap((y,j)=>[-.033,-.014].map((x,i)=>[`RING_${j*2+i+1}`,[x,y,-.110]])));
export const targets:Record<string,V>=Object.fromEntries(Object.entries(sources).map(([n,p])=>[n,[-p[0],p[1],p[2]]]));
const targetHomes=targets;
export class PegTransfer {
 positions:Record<string,V>={};owners:Record<string,Side|null>={};offsets:Record<string,V>={};previousJaw:Record<Side,number>={LEFT:1,RIGHT:1};pending:Record<string,Side>={};placements:Record<string,string>={};state='READY';elapsed=0;
 constructor(public homes=sources,public targets:Record<string,V>=targetHomes){this.reset();}
 reset(){this.positions=structuredClone(this.homes);this.owners=Object.fromEntries(Object.keys(this.homes).map(n=>[n,null]));this.offsets={};this.previousJaw={LEFT:1,RIGHT:1};this.pending={};this.placements=Object.fromEntries(Object.keys(this.homes).map(n=>[n,'SOURCE']));this.state='READY';this.elapsed=0;}
 get completed(){return Object.values(this.placements).filter(s=>s==='CORRECT').length;}
 place(name:string){let p=this.positions[name];const candidates:{d:number;kind:string;peg:string;seat:V}[]=[];
 for(const [kind,locations] of [['TARGET',this.targets],['SOURCE',this.homes]] as [string,Record<string,V>][]){for(const [peg,seat] of Object.entries(locations)){
 if(dist(p.slice(0,2),seat.slice(0,2))<=.006&&Math.abs(p[2]-seat[2])<=.012&&!Object.entries(this.positions).some(([other,pos])=>other!==name&&!this.owners[other]&&dist(pos,seat)<.006))candidates.push({d:dist(p,seat),kind,peg,seat});}}
 candidates.sort((a,b)=>a.d-b.d||a.kind.localeCompare(b.kind)||a.peg.localeCompare(b.peg));
 if(candidates.length){const c=candidates[0];this.positions[name]=[...c.seat];this.placements[name]=c.kind==='SOURCE'?'SOURCE':c.peg===name?'CORRECT':'INCORRECT';}
 else {const offsets:V[]=[[0,0]];for(const r of [.012,.024,.036])for(const [x,y] of [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]])offsets.push([x*r,y*r]);
 for(const [dx,dy] of offsets){const xy=[p[0]+dx,p[1]+dy];if([...Object.values(this.targets),...Object.values(this.homes)].every(v=>dist(xy,v.slice(0,2))>=.008)&&Object.entries(this.positions).every(([n,v])=>n===name||this.owners[n]||dist(xy,v.slice(0,2))>=.014)){p=[...xy,p[2]];break;}}
 this.positions[name]=[p[0],p[1],-.110];this.placements[name]='DROPPED';}
 }
 update(hands:Hands,dt:number){if(!Number.isFinite(dt)||dt<0)throw Error('Invalid time');if(this.state==='COMPLETE')return;
 const safe=Object.fromEntries(Object.entries(hands).filter(([s,[p,j]])=>sides.includes(s as Side)&&p.length===3&&[...p,j].every(Number.isFinite)&&j>=0&&j<=1)) as Hands;
 const before={...this.owners},previous={...this.previousJaw};
 for(const [n,s] of Object.entries(this.owners)){if(s&&safe[s]){const [p,j]=safe[s]!;this.positions[n]=add(p,this.offsets[n]);if(j>=.65){this.owners[n]=null;delete this.offsets[n];}}}
 const occupied=new Set(Object.values(this.owners).filter(Boolean));const candidates:[number,string,Side][]=[];
 for(const s of sides){const h=safe[s];if(h&&!occupied.has(s)&&h[1]<=.25&&this.previousJaw[s]>.25)for(const [n,p] of Object.entries(this.positions))if(!this.owners[n]&&dist(h[0],p)<=.009)candidates.push([dist(h[0],p),n,s]);}
 candidates.sort((a,b)=>a[0]-b[0]||a[1].localeCompare(b[1])||a[2].localeCompare(b[2]));
 for(const [,n,s] of candidates)if(!this.owners[n]&&!occupied.has(s)){this.owners[n]=s;this.offsets[n]=sub(this.positions[n],safe[s]![0]);occupied.add(s);}
 for(const s of sides)if(safe[s])this.previousJaw[s]=safe[s]![1];
 for(const s of sides){const h=safe[s];if(!h||Object.values(this.owners).includes(s))continue;
 if(h[1]<=.25&&previous[s]>.25){const possible=Object.entries(before).filter(([n,owner])=>owner&&owner!==s&&dist(h[0],this.positions[n])<=.009).map(([n])=>[dist(h[0],this.positions[n]),n] as [number,string]).sort((a,b)=>a[0]-b[0]||a[1].localeCompare(b[1]));if(possible.length)this.pending[possible[0][1]]=s;}}
 for(const [n,r] of Object.entries(this.pending)){const h=safe[r];if(!h||h[1]>.25||Object.values(this.owners).includes(r)||dist(h[0],this.positions[n])>.009){delete this.pending[n];continue;}
 if(before[n]&&!this.owners[n]){this.owners[n]=r;this.offsets[n]=sub(this.positions[n],h[0]);delete this.pending[n];}}
 for(const [n,owner] of Object.entries(this.owners)){if(owner){this.placements[n]='HELD';if(this.state==='READY')this.state='RUNNING';}else if(before[n])this.place(n);}
 if(this.state==='RUNNING'){this.elapsed+=dt;if(this.completed===Object.keys(this.targets).length)this.state='COMPLETE';}
 }
}
