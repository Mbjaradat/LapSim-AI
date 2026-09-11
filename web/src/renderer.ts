import * as THREE from 'three';
import {grasperVisual} from './grasper';
import {cameraPosition,cameraTarget,tanY,proxies,transform,sides,type Side,type V,type Pose} from './core';
import {sources,targets} from './task';
import type {Session} from './session';
// Original procedural geometry; all world coordinates remain native Z-up metres.
export class TrainerView {
 renderer:THREE.WebGLRenderer;scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(2*Math.atan(tanY)*180/Math.PI,4/3,.003,2);
 hinges:Partial<Record<Side,THREE.Group>>={};axisX=new THREE.Vector3();axisY=new THREE.Vector3();axisZ=new THREE.Vector3();basis=new THREE.Matrix4();
 rings:Record<string,THREE.Group>={};tools:Record<Side,THREE.Mesh[]>={LEFT:[],RIGHT:[]};markers:Record<string,THREE.Mesh>={};
 constructor(public host:HTMLElement){
 this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));this.renderer.setClearColor('#111c24');this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.2;this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFShadowMap;host.append(this.renderer.domElement);
 this.renderer.domElement.setAttribute('aria-label','3D Peg Transfer trainer');this.camera.up.set(0,0,1);this.camera.position.fromArray(cameraPosition);this.camera.lookAt(new THREE.Vector3(...cameraTarget));
 const ambient=new THREE.HemisphereLight('#e8f0f3','#253039',2);ambient.position.set(0,0,1);this.scene.add(ambient);
 for(const [p,intensity] of [[[-.06,-.03,.08],1.5],[[.07,.07,.03],1]] as [V,number][]){const l=new THREE.DirectionalLight('#ffffff',intensity);l.position.fromArray(p);l.target.position.fromArray(cameraTarget);this.scene.add(l.target);if(p[0]<0){l.castShadow=true;l.shadow.mapSize.set(1024,1024);Object.assign(l.shadow.camera,{left:-.15,right:.15,top:.15,bottom:-.15,near:.01,far:.6});l.shadow.bias=-.0002;l.shadow.normalBias=.0001;}this.scene.add(l);}
 const mat=(color:string,metalness=0,roughness=.55)=>new THREE.MeshStandardMaterial({color,metalness,roughness});
 const box=(p:V,size:V,m:THREE.Material)=>{const o=new THREE.Mesh(new THREE.BoxGeometry(...size as [number,number,number]),m);o.position.fromArray(p);o.receiveShadow=true;this.scene.add(o);return o;};
 box([0,.042,-.1175],[.106,.086,.008],mat('#263c46'));box([0,.042,-.1126],[.102,.082,.0012],mat('#405b61',.15,.7));
 box([0,.045,-.126],[.26,.22,.012],mat('#111b22'));
 const pegMat=mat('#879a9e',.65,.3),sourceMat=mat('#3c8993'),targetMat=mat('#c39045'),ringMat=mat('#e7c58c',.12,.28);
 for(const [kind,locations] of [['SOURCE',sources],['TARGET',targets]] as const){for(const [n,p] of Object.entries(locations)){
 const peg=new THREE.Mesh(new THREE.CylinderGeometry(.0018,.0018,.008,20),pegMat);peg.rotation.x=Math.PI/2;peg.position.set(p[0],p[1],-.108);peg.castShadow=true;peg.receiveShadow=true;this.scene.add(peg);
 const marker=new THREE.Mesh(new THREE.TorusGeometry(.008,.00045,8,40),kind==='SOURCE'?sourceMat:targetMat.clone());marker.position.set(p[0],p[1],-.1117);this.scene.add(marker);if(kind==='TARGET')this.markers[n]=marker;
 this.label(n.slice(-1),[p[0],p[1]-.011,-.1113],.003,'#e0e9e8');}}
 for(const [n,p] of Object.entries(sources)){const group=new THREE.Group(),ring=new THREE.Mesh(new THREE.TorusGeometry(.0055,.0016,12,40),ringMat);ring.castShadow=true;ring.receiveShadow=true;group.add(ring);
 const tab=new THREE.Mesh(new THREE.BoxGeometry(.004,.003,.0012),ringMat);tab.position.set(0,-.004,.0004);group.add(tab);
 group.add(this.label(n.slice(-1),[0,-.005,.0011],.0025,'#23343a',false));group.position.fromArray(p);this.scene.add(group);this.rings[n]=group;}
 this.label('SOURCE',[-.025,.078,-.1112],.013,'#89b9be');this.label('TARGET',[.025,.078,-.1112],.013,'#d7b67f');
 const handoff=new THREE.Mesh(new THREE.TorusGeometry(.004,.0003,6,32),sourceMat);handoff.position.set(0,.042,-.1117);this.scene.add(handoff);
 for(const side of sides){const visual=grasperVisual(side==='LEFT'?'#c0d2da':'#d5cec1');this.tools[side]=visual.segments;this.hinges[side]=visual.hinge;for(const mesh of [...visual.segments,visual.hinge]){mesh.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true;}});this.scene.add(mesh);}}
 new ResizeObserver(()=>this.resize()).observe(host);this.resize();
 }
 label(text:string,p:V,width:number,color:string,attach=true){const c=document.createElement('canvas');const ctx=c.getContext('2d')!;ctx.font='600 44px Arial';c.width=Math.ceil(ctx.measureText(text).width)+12;c.height=64;ctx.fillStyle=color;ctx.font='600 44px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,c.width/2,32);const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;const mesh=new THREE.Mesh(new THREE.PlaneGeometry(width,width*c.height/c.width),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false}));mesh.position.fromArray(p);if(attach)this.scene.add(mesh);return mesh;}
 resize(){const w=this.host.clientWidth,h=this.host.clientHeight;this.renderer.setSize(w,h,false);}
 draw(session:Session){for(const [n,o] of Object.entries(this.rings))o.position.fromArray(session.task.positions[n]);for(const [n,m] of Object.entries(this.markers))(m.material as THREE.MeshStandardMaterial).color.set(Object.entries(session.task.positions).some(([name,p])=>session.task.placements[name]==='CORRECT'&&Math.hypot(p[0]-targets[n][0],p[1]-targets[n][1])<.006)?'#3eaa75':'#c39045');
 for(const s of sides){const geometry=proxies(s,session.poses[s]),segments=geometry.segments;const pose=session.poses[s];this.axisX.fromArray(transform(pose,[1,0,0]));this.axisY.fromArray(transform(pose,[0,1,0]));this.axisZ.fromArray(transform(pose,[0,0,1]));this.basis.makeBasis(this.axisX,this.axisY,this.axisZ);this.hinges[s]!.position.fromArray(geometry.tip);this.hinges[s]!.quaternion.setFromRotationMatrix(this.basis);segments.forEach(([a,b],i)=>{const mesh=this.tools[s][i],va=new THREE.Vector3(...a),vb=new THREE.Vector3(...b),axis=vb.clone().sub(va);mesh.position.copy(va.add(vb).multiplyScalar(.5));mesh.scale.set(1,axis.length(),1);mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),axis.normalize());if(i>0){this.axisY.copy(axis);this.axisZ.fromArray(transform(pose,[0,1,0]));this.axisX.crossVectors(this.axisY,this.axisZ).normalize();this.basis.makeBasis(this.axisX,this.axisY,this.axisZ);mesh.quaternion.setFromRotationMatrix(this.basis);}});}
 const width=this.host.clientWidth,height=this.host.clientHeight,w=Math.min(width,height*4/3),h=w*3/4;this.renderer.setScissorTest(false);this.renderer.clear();this.renderer.setViewport((width-w)/2,(height-h)/2,w,h);this.renderer.setScissor((width-w)/2,(height-h)/2,w,h);this.renderer.setScissorTest(true);this.renderer.render(this.scene,this.camera);}
}
