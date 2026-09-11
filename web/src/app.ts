import './style.css';
import {projectLinks,externalResearchUrl} from './config';
import {TrainerView} from './renderer';
import {Session} from './session';
import {sides,type V} from './core';
import {homeDirection} from './setup';
import {cameraError,stopStream} from './camera';
import type {Raw} from './tracking';
const el=<T extends HTMLElement>(id:string)=>document.getElementById(id) as T;
const video=el<HTMLVideoElement>('video'),overlay=el<HTMLCanvasElement>('overlay'),start=el<HTMLButtonElement>('start'),pause=el<HTMLButtonElement>('pause'),retry=el<HTMLButtonElement>('retry'),recalibrate=el<HTMLButtonElement>('recalibrate'),stop=el<HTMLButtonElement>('stop'),select=el<HTMLSelectElement>('camera-select');
const researchUrl=externalResearchUrl(projectLinks.researchInterest);
if(researchUrl){const link=el<HTMLAnchorElement>('research-link');link.href=researchUrl;link.target='_blank';link.rel='noreferrer';link.removeAttribute('aria-disabled');el('research-unavailable').hidden=true;}
let session=new Session('beginner'),view:TrainerView|null=null,stream:MediaStream|null=null,worker:Worker|null=null,busy=false,workerReady=false,active=false,loading=false,run=0,lastCapture=-1,lastVideo=-1,lastUI=-1,lastSim=-1,notice='',synthetic=false;
const capture=document.createElement('canvas');const captureContext=capture.getContext('2d')!;
try{view=new TrainerView(el('trainer'));}catch{notice='WebGL2 is unavailable. Enable hardware acceleration or use a current desktop browser.';}
function showError(message:string){notice=message;el('error').textContent=message;el('error').hidden=!message;}
function stopCamera(){run++;stopStream(stream);stream=null;worker?.terminate();worker=null;workerReady=false;busy=false;active=false;loading=false;video.srcObject=null;session.paused=true;session.targets=[];session.stamp=null;overlay.getContext('2d')?.clearRect(0,0,overlay.width,overlay.height);}
async function enumerate(){try{const devices=await navigator.mediaDevices.enumerateDevices();const chosen=select.value;select.replaceChildren(new Option('Default / front camera',''));devices.filter(d=>d.kind==='videoinput').forEach((d,i)=>select.add(new Option(d.label||`Camera ${i+1}`,d.deviceId)));select.value=chosen;}catch{/* Camera selection is optional; permission failure is handled at start. */}}
async function begin(){if(loading||active)return;if(!view){showError('WebGL2 is required to display the trainer. Enable hardware acceleration.');return;}if(innerWidth<900){showError('Widen this window to at least 900 pixels before starting.');return;}if(!isSecureContext||!navigator.mediaDevices?.getUserMedia){showError('Camera access requires HTTPS or localhost in a supported browser.');return;}
 stopCamera();session=new Session('beginner');showError('');loading=true;const id=run;
 try{const acquired=await navigator.mediaDevices.getUserMedia({audio:false,video:select.value?{deviceId:{exact:select.value},width:{ideal:640},height:{ideal:480}}:{facingMode:'user',width:{ideal:640},height:{ideal:480}}});
 if(id!==run){stopStream(acquired);return;}stream=acquired;stream.getVideoTracks().forEach(t=>t.addEventListener('ended',()=>{stopCamera();showError('Camera disconnected. Connect it again, then start a new session.');}));video.srcObject=stream;await video.play();if(id!==run)return;
 capture.width=video.videoWidth;capture.height=video.videoHeight;overlay.width=video.videoWidth;overlay.height=video.videoHeight;el('video').parentElement!.style.aspectRatio=`${video.videoWidth}/${video.videoHeight}`;
 worker=new Worker(new URL('./hand-worker.ts',import.meta.url),{type:'module'});worker.onmessage=(e:MessageEvent)=>{if(id!==run)return;const d=e.data;if(d.type==='ready'){workerReady=true;loading=false;active=true;session.paused=false;}else if(d.type==='hands'){busy=false;if(d.time/1000> (session.stamp??-1))session.observe(d.raw,d.time/1000);}else if(d.type==='error'){stopCamera();showError('Hand tracking could not start. Check browser support and reload. '+d.message);}};
 worker.onerror=()=>{stopCamera();showError('Hand tracking could not load. Reload the page or try a current desktop Chrome or Edge browser.');};worker.postMessage({type:'init',base:new URL(import.meta.env.BASE_URL,location.href).href});await enumerate();
 }catch(error){if(id===run){stopCamera();showError(cameraError(error));}}
}
start.addEventListener('click',()=>void begin());stop.addEventListener('click',()=>{session.telemetry.finish(session.task.completed);stopCamera();});
pause.addEventListener('click',()=>{if(session.paused){if(!session.resume(performance.now()/1000))showError('Show both hands before resuming.');else showError('');}else session.paused=true;});
function retrySession(){session.retry();showError('');updateUI(performance.now());}
retry.addEventListener('click',retrySession);el('result-retry').addEventListener('click',retrySession);
recalibrate.addEventListener('click',()=>{if(!session.recalibrate())showError('Pause and release held rings before recalibrating.');else showError('');});
window.addEventListener('pagehide',stopCamera);document.addEventListener('visibilitychange',()=>{if(document.hidden){session.paused=true;session.gate.deadline=null;}});
window.addEventListener('resize',()=>{if(innerWidth<900&&session.gate.started)session.paused=true;});
function preview(now:number){const ctx=overlay.getContext('2d')!,w=overlay.width,h=overlay.height;ctx.clearRect(0,0,w,h);const fresh=session.fresh(now);
 if(fresh)for(const raw of session.raw){ctx.strokeStyle='#79d2bf';ctx.lineWidth=2;for(const chain of [[0,1,2,3,4],[0,5,6,7,8],[5,9,10,11,12],[9,13,14,15,16],[13,17,18,19,20],[0,17]]){ctx.beginPath();chain.forEach((i,j)=>{const p=raw.landmarks[i];if(j===0)ctx.moveTo(p.x*w,p.y*h);else ctx.lineTo(p.x*w,p.y*h);});ctx.stroke();}ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(raw.palm[0]*w,raw.palm[1]*h,4,0,2*Math.PI);ctx.fill();}
 for(const s of sides){const home=session.setup.home[s];if(!home)continue;ctx.strokeStyle=session.state==='LIVE'?'#dfc68a99':'#efd18e';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(home[0]*w,home[1]*h,.065*w,.065*h,0,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#fff';ctx.font=`bold ${Math.max(18,w*.047)}px sans-serif`;ctx.strokeStyle='#20333b';ctx.lineWidth=3;ctx.strokeText(s[0]+' HOME',home[0]*w+9,home[1]*h-12);ctx.fillText(s[0]+' HOME',home[0]*w+9,home[1]*h-12);
 const raw=fresh?session.raw.find(r=>r.side===s):null;if(raw&&session.state!=='LIVE'&&homeDirection(raw.palm,home)!=='HOME'){const a=[raw.palm[0]*w,raw.palm[1]*h],b=[home[0]*w,home[1]*h],angle=Math.atan2(b[1]-a[1],b[0]-a[0]);ctx.beginPath();ctx.moveTo(...a as [number,number]);ctx.lineTo(...b as [number,number]);ctx.lineTo(b[0]-12*Math.cos(angle-.5),b[1]-12*Math.sin(angle-.5));ctx.moveTo(...b as [number,number]);ctx.lineTo(b[0]-12*Math.cos(angle+.5),b[1]-12*Math.sin(angle+.5));ctx.stroke();}}
}
let shownResult:Session['telemetry']['result']=null;
const formatTime=(seconds:number)=>`${Math.floor(seconds/60).toString().padStart(2,'0')}:${Math.floor(seconds%60).toString().padStart(2,'0')}`;
function updateUI(ms:number){const now=ms/1000,started=active||synthetic;
 el('entry').hidden=active||synthetic;el<HTMLButtonElement>('result-retry').disabled=!started;
 start.disabled=loading||active;start.textContent=loading?'Starting camera & tracking…':active?'Camera active':'Start training →';select.disabled=active||loading;stop.disabled=!active&&!loading;
 pause.disabled=!started||!session.gate.started||session.task.state==='COMPLETE';pause.textContent=session.paused?'Resume':'Pause';retry.disabled=!started;recalibrate.disabled=!started||!session.paused||Object.values(session.task.owners).some(Boolean);
 el('camera-state').textContent=loading?'STARTING':active?'ON · LOCAL':'OFF';el('camera-placeholder').style.display=stream?'none':'flex';
 el('state-badge').textContent=started?session.state.replaceAll('_',' '):'READY TO SET UP';el('completed').innerHTML=session.mode==='beginner'?String(session.task.completed):`${session.task.completed} <span>/ 6</span>`;el('practice-time').textContent=session.mode==='beginner'?`${formatTime(Math.ceil(session.remaining))} remaining${session.telemetry.started===null?' · starts on first grasp':''}`:'';
 el('guide-label').textContent=session.gate.started&&session.mode==='beginner'?'BEGINNER PRACTICE':started?'GUIDED TRAINING':'GET STARTED';el('guidance').textContent=started?session.message:'Make room for both hands.';
 const count=session.gate.deadline!==null?session.gate.remaining:!session.gate.started?session.setup.remaining:null;el('countdown').textContent=count===null?'':String(count);
 el('help').textContent=session.gate.started?(session.mode==='beginner'?'Pinch to grasp. Open to release. Complete as many successful transfers as you can in 2 minutes. Green confirms a transfer; the ring returns to a free source peg.':'Close thumb + index to grasp. Open to release. Match each ring to its numbered target.'):session.setup.home.LEFT?'Return toward the HOME markers. Keep both hands visible and follow the next hold.':'Face your webcam toward your hands. Start around 0.8–1.2 m away, then adjust for your camera. Leave room to move.';
 el('lighting').hidden=!!session.setup.home.LEFT;
 for(const s of sides){const h=session.stable.find(h=>h.side===s),tracked=!!h?.tracked&&session.fresh(now);const label=el(s.toLowerCase()+'-status');label.textContent=`${s} · ${tracked?'tracked':'waiting'}`;label.className=tracked?'tracked':'';}
 document.querySelectorAll<HTMLElement>('[data-step]').forEach(li=>li.classList.toggle('active',li.dataset.step===(session.setup.stage??'live')));
 const result=session.telemetry.result;el('results').hidden=!result||result.outcome!=='COMPLETE';if(result&&result.outcome==='COMPLETE'&&result!==shownResult){
 const c=result.counts,p=result.path_metres;const metrics:[string,string|number][]=[['Time',formatTime(result.active_seconds)],['Objects',`${result.objects_completed} / 6`],['Grasps',c.grasps],['Drops',c.drops],['Handoffs',c.handoffs],['Incorrect placements',c.incorrect_placements],['Successful placements',c.successful_placements],['Left path',p.LEFT.toFixed(3)+' m'],['Right path',p.RIGHT.toFixed(3)+' m'],['Total path',p.TOTAL.toFixed(3)+' m']];
 if(session.mode==='beginner'){metrics.splice(0,metrics.length,['Successful Transfers',result.successful_transfers],['Time',formatTime(result.active_seconds)],['Grasps',c.grasps],['Drops',c.drops],['Handoffs',c.handoffs],['Left Instrument Path',p.LEFT.toFixed(3)+' m'],['Right Instrument Path',p.RIGHT.toFixed(3)+' m'],['Total Instrument Path',p.TOTAL.toFixed(3)+' m']);}el('results-title').textContent=session.mode==='beginner'?'Practice session complete':'Peg Transfer complete';
 el('metrics').replaceChildren(...metrics.map(([name,value])=>{const d=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=String(name);dd.textContent=String(value);d.append(dt,dd);return d;}));}
 shownResult=result;
 if(notice){el('error').hidden=false;el('error').textContent=notice;}
 preview(now);
}
function animate(ms:number){requestAnimationFrame(animate);
 if(!synthetic&&(active||loading)&&ms-lastSim>=1000/30){session.tick(ms/1000);lastSim=ms;}
 if(active&&workerReady&&!busy&&!document.hidden&&ms-lastCapture>=1000/30&&video.readyState>=2&&video.currentTime!==lastVideo){busy=true;lastCapture=ms;lastVideo=video.currentTime;const id=run;captureContext.setTransform(-1,0,0,1,capture.width,0);captureContext.drawImage(video,0,0,capture.width,capture.height);
 void createImageBitmap(capture).then(image=>{if(id!==run||!worker){image.close();return;}worker.postMessage({type:'frame',image,time:ms,aspect:capture.width/capture.height},[image]);}).catch(()=>{busy=false;});}
 view?.draw(session);if(ms-lastUI>=100){updateUI(ms);lastUI=ms;}
}
if(import.meta.env.DEV){Object.assign(window,{__lapsim:{get session(){return session;},get renderer(){return view;},beginSynthetic(mode:'structured'|'beginner'='structured'){synthetic=true;session=new Session(mode);return session;},async completeSynthetic(){const {syntheticTrial}=await import('./synthetic');synthetic=true;session=new Session();const result=syntheticTrial(session);updateUI(performance.now());view?.draw(session);return result;},updateUI:()=>updateUI(performance.now())}});}
updateUI(0);requestAnimationFrame(animate);
