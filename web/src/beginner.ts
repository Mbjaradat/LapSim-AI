import {PegTransfer,type Hands} from './task';
import {dist,add} from './core';

// Additive rules: ownership, grasp edges, placement geometry and drops stay native.
export class BeginnerTransfer extends PegTransfer {
 transfers=0;
 recycle:Record<string,number>={};
 override get completed(){return this.transfers;}
 override reset(){super.reset();this.transfers=0;this.recycle={};}
 override place(name:string){
  super.place(name);
  if(['CORRECT','INCORRECT'].includes(this.placements[name])){
   this.placements[name]='CORRECT';this.transfers++;this.recycle[name]=1.2;
  }
 }
 override update(hands:Hands,dt:number){
  if(this.state==='COMPLETE')return;
  // Confirmation lasts 1.2 active simulation seconds. Regrasp cancels recycling.
  for(const name of Object.keys(this.recycle).sort()){
   if(this.owners[name]){delete this.recycle[name];continue;}
   this.recycle[name]-=dt;
   if(this.recycle[name]>0)continue;
   if(Object.values(hands).some(([p])=>dist(p,this.positions[name])<.018))continue;
   const seat=Object.entries(this.homes).sort(([a],[b])=>a.localeCompare(b)).find(([,p])=>
    Object.entries(this.positions).every(([other,q])=>{
     const owner=this.owners[other],hand=owner?hands[owner]:null;
     const next=hand?add(hand[0],this.offsets[other]):q;
     return other===name||dist(p,next)>.016;
    })&&
    Object.values(hands).every(([palm])=>dist(p,palm)>.018));
   if(!seat)continue; // Wait until a source is clear of other rings and tool contacts.
   this.positions[name]=[...seat[1]];this.placements[name]='SOURCE';delete this.recycle[name];
  }
  super.update(hands,dt);
  // Structured completion is intentionally replaced by the session timer.
  if(this.state==='COMPLETE')this.state='RUNNING';
 }
}
