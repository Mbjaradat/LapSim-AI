import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:5173';
const output=new URL('../../outputs/web/',import.meta.url);await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.TEST_CHROME_PATH||undefined,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const report={base,physicalWebcamValidation:'PENDING',checks:[],errors:[],requests:[],performance:{}};
try{
 const context=await browser.newContext({viewport:{width:1440,height:1100}}),page=await context.newPage();
 page.on('pageerror',e=>report.errors.push(String(e)));
 page.on('request',r=>report.requests.push({url:r.url(),method:r.method()}));
 await page.goto(base,{waitUntil:'networkidle'});await page.locator('#trainer canvas').waitFor();
 assert.equal(await page.title(),'LapSim-AI · Peg Transfer');assert.equal(await page.locator('#start').isVisible(),true);
 assert.equal(await page.locator('#research-link').getAttribute('href'),'https://forms.gle/Jz6Wva2JEVHcomc36');assert.equal(await page.locator('#research-link').getAttribute('rel'),'noreferrer');
 assert.equal(await page.locator('a[href="https://github.com/Mbjaradat/LapSim-AI"]').count(),1);
 await page.screenshot({path:fileURLToPath(new URL('landing.png',output)),fullPage:true});
 report.checks.push('Landing, Start CTA, scene canvas, GitHub and configured research CTA');
 await page.locator('#start').click();
 await page.waitForFunction(()=>document.querySelector('#camera-state')?.textContent?.startsWith('ON')||!document.querySelector('#error')?.hasAttribute('hidden'),null,{timeout:60000});
 if(!(await page.locator('#camera-state').textContent()).startsWith('ON'))throw Error('Camera/worker: '+await page.locator('#error').textContent());
 await page.waitForFunction(()=>document.querySelector('#guidance')?.textContent?.includes('HAND LOST'),null,{timeout:30000});
 report.checks.push('Real browser camera API with fake device; local worker/model/WASM; blank-frame inference');
 assert.ok((await page.evaluate(()=>{window.__testTracks=document.querySelector('video').srcObject.getTracks();return window.__testTracks.map(t=>t.readyState);})).every(t=>t==='live'));
 await page.locator('#stop').click();assert.ok((await page.evaluate(()=>window.__testTracks.map(t=>t.readyState))).every(s=>s==='ended'));
 report.checks.push('Stop ends all camera tracks');
 if(await page.evaluate(()=>!!window.__lapsim)){
 const result=await page.evaluate(()=>window.__lapsim.completeSynthetic());assert.equal(result.result.objects_completed,6);assert.equal(result.result.counts.handoffs,6);assert.equal(await page.locator('#results').isVisible(),true);assert.match(await page.locator('#metrics').textContent(),/6 \/ 6/);
 report.checks.push(`Synthetic guided calibration, LIVE, six constrained handoffs/placements (${result.ticks} ticks), results`);
 const pivotError=await page.evaluate(()=>{const v=window.__lapsim.renderer;v.draw(window.__lapsim.session);let maximum=0;for(const [side,x] of [['LEFT',-.085],['RIGHT',.085]]){const e=v.tools[side][0].matrixWorld.elements;maximum=Math.max(maximum,Math.hypot(e[12]-.5*e[4]-x,e[13]-.5*e[5],e[14]-.5*e[6]-.12));}return maximum;});
 assert.ok(pivotError<1e-6);report.checks.push(`Rendered shaft pivot error ${pivotError} m < 1e-6 m`);
 await page.screenshot({path:fileURLToPath(new URL('results.png',output)),fullPage:true});
 await page.locator('#result-retry').click();assert.equal(await page.locator('#results').isVisible(),false);assert.match(await page.locator('#completed').textContent(),/0/);report.checks.push('Visible Retry resets task/results');
 const frames=await page.evaluate(async()=>{const values=[];let last=performance.now();await new Promise(resolve=>{function tick(t){values.push(t-last);last=t;if(values.length>=61)resolve();else requestAnimationFrame(tick);}requestAnimationFrame(tick);});return values.slice(1);});
 report.performance={context:'headless software WebGL idle scene, not physical webcam gameplay',sampleFrames:frames.length,meanFrameMs:frames.reduce((a,b)=>a+b,0)/frames.length};
 await page.evaluate(async()=>{
  const s=window.__lapsim.beginSynthetic('beginner');const {sources,targets}=await import('/src/task.ts');
  s.tick(0);s.gate.started=true;s.task.update({RIGHT:[sources.RING_2,0]},0);s.tick(.05);
  s.task.update({RIGHT:[targets.RING_5,0]},.05);s.task.update({RIGHT:[targets.RING_5,1]},.05);s.tick(.1);
  s.tick(121);window.__lapsim.updateUI();
 });
 assert.match(await page.locator('#metrics').textContent(),/Successful Transfers1/);assert.match(await page.locator('#metrics').textContent(),/02:00/);
 await page.screenshot({path:fileURLToPath(new URL('beginner-results.png',output)),fullPage:true});
 await page.locator('#result-retry').click();assert.equal(await page.locator('#completed').textContent(),'0');assert.match(await page.locator('#practice-time').textContent(),/02:00/);
 report.checks.push('Beginner synthetic task transition: arbitrary target, timed results, Try again resets');
 }else report.checks.push('Production has no development synthetic seam');
 await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#start').isVisible(),true);report.checks.push('Root refresh');
 await page.setViewportSize({width:800,height:900});assert.equal(await page.locator('.small-layout').isVisible(),true);report.checks.push('Small-layout guidance');
 const denied=await context.newPage();await denied.addInitScript(()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Test denied','NotAllowedError');};});await denied.goto(base);await denied.locator('#start').click();await denied.waitForFunction(()=>document.querySelector('#error')?.textContent?.includes('denied'));assert.equal(await denied.locator('#start').isEnabled(),true);report.checks.push('Simulated permission denial is actionable/retryable');
 const absent=await context.newPage();await absent.addInitScript(()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Test absent','NotFoundError');};});await absent.goto(base);await absent.locator('#start').click();await absent.waitForFunction(()=>document.querySelector('#error')?.textContent?.includes('No camera'));assert.equal(await absent.locator('#start').isEnabled(),true);report.checks.push('Simulated missing camera is actionable/retryable');
 assert.equal(report.requests.filter(r=>!r.url.startsWith(base)&&!r.url.startsWith('data:')&&!r.url.startsWith('blob:')).length,0,'Unexpected external request');assert.ok(report.requests.every(r=>r.method==='GET'),'Unexpected upload');assert.equal(report.errors.length,0);
 report.checks.push('No page errors; same-origin GET assets only; no uploads');console.log(JSON.stringify(report,null,2));
}catch(error){report.errors.push(String(error));throw error;}
finally{await writeFile(new URL(base.includes('4173')?'browser-production.json':'browser-development.json',output),JSON.stringify(report,null,2));await browser.close();}
