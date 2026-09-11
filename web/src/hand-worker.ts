import {FilesetResolver,HandLandmarker} from '@mediapipe/tasks-vision';
import {extract} from './tracking';
let detector:HandLandmarker|null=null;
self.onmessage=async(event:MessageEvent)=>{
 const data=event.data;
 try{
 if(data.type==='init'){
 const files=await FilesetResolver.forVisionTasks(data.base+'wasm',true);
 detector=await HandLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:data.base+'models/hand_landmarker.task',delegate:'CPU'},runningMode:'VIDEO',numHands:2,canvas:new OffscreenCanvas(640,480)});
 self.postMessage({type:'ready'});
 }else if(data.type==='frame'&&detector){const start=performance.now();try{const result=detector.detectForVideo(data.image,data.time);
 const raw=result.landmarks.flatMap((points,i)=>{const h=extract(points,result.handedness[i]?.[0]?.categoryName??'',data.aspect,true);return h?[h]:[];});
 self.postMessage({type:'hands',raw,time:data.time,inferenceMs:performance.now()-start});
 }finally{data.image.close();}}
 }catch(error){data.image?.close();self.postMessage({type:'error',message:error instanceof Error?error.message:String(error)});}
};
