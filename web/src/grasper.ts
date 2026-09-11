import * as THREE from 'three';

// Original decorative meshes only. Unit-length Y meshes follow native segments.
export function grasperVisual(color:string){
 const steel=new THREE.MeshStandardMaterial({color,metalness:.72,roughness:.25});
 const dark=new THREE.MeshStandardMaterial({color:'#34434a',metalness:.5,roughness:.4});
 const shaft=new THREE.Mesh(new THREE.CylinderGeometry(.0027,.0027,1,24),steel);
 const jawGeometry=new THREE.CylinderGeometry(.0009,.002,1,4);jawGeometry.rotateY(Math.PI/4);
 const grooves=new THREE.BoxGeometry(.0018,.012,.00016);
 const jaws=[-1,1].map(()=>{const jaw=new THREE.Mesh(jawGeometry,steel);
  for(const y of [-.05,.04,.13,.22,.31])for(const z of [-.0011,.0011]){
   const groove=new THREE.Mesh(grooves,dark);groove.position.set(0,y,z);jaw.add(groove);
  }return jaw;
 });
 const hinge=new THREE.Group();
 const collar=new THREE.Mesh(new THREE.CylinderGeometry(.0029,.0029,.005,20),dark);
 collar.rotation.x=Math.PI/2;collar.position.z=.002;hinge.add(collar);
 const pin=new THREE.Mesh(new THREE.CylinderGeometry(.0021,.0021,.0045,16),steel);hinge.add(pin);
 const capGeometry=new THREE.CylinderGeometry(.0009,.0009,.00025,12);
 for(const sign of [-1,1]){const cap=new THREE.Mesh(capGeometry,dark);cap.position.y=sign*.00235;hinge.add(cap);}
 return {segments:[shaft,...jaws],hinge};
}
