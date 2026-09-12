// Run against pnpm preview or the deployed site. Never inject response policies.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';

const base = new URL(process.env.TEST_BASE_URL || 'http://127.0.0.1:4173');
const policy = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'";
const output = new URL('../../outputs/phase6_2b/', import.meta.url);
const report = {base: base.origin, policy, headerInjection: false, externalRequests: [], resources: [], pageErrors: []};
const browser = await chromium.launch({headless: true, executablePath: process.env.TEST_CHROME_PATH || undefined,
 args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-background-timer-throttling', '--disable-renderer-backgrounding']});
try {
 report.browser = browser.version();
 const context = await browser.newContext({viewport: {width: 1440, height: 1100}, serviceWorkers: 'block'});
 // Fail closed if containment regresses; this guard is not counted as CSP success.
 await context.route('**/*', route => {
  const request = route.request(), url = new URL(request.url());
  if (url.origin !== base.origin && !['data:', 'blob:'].includes(url.protocol)) {
   report.externalRequests.push({destination: url.origin + url.pathname, method: request.method()});
   return route.abort('blockedbyclient');
  }
  return route.continue();
 });
 context.on('response', response => {
  const url = new URL(response.url());
  if (url.origin === base.origin && /hand-worker|\.wasm$|hand_landmarker\.task$/.test(url.pathname)) {
   report.resources.push({path: url.pathname, status: response.status(), csp: response.headers()['content-security-policy'] ?? null});
  }
 });
 const page = await context.newPage();
 page.on('pageerror', error => report.pageErrors.push(String(error)));
 await page.addInitScript(() => {
  window.__privacyAudit = {results: 0, lastResultMs: null};
  const OriginalWorker = window.Worker;
  window.Worker = class extends OriginalWorker {
   constructor(...args) {
    super(...args);
    this.addEventListener('message', event => {
     if (event.data.type === 'hands') {
      window.__privacyAudit.results++;
      window.__privacyAudit.lastResultMs = performance.now();
     }
    });
   }
  };
 });
 await page.goto(base.href, {waitUntil: 'networkidle'});
 await page.bringToFront();
 report.researchLink = await page.locator('#research-link').evaluate(link => ({href: link.href, target: link.target, rel: link.rel}));
 assert.equal(report.researchLink.href, 'https://forms.gle/Jz6Wva2JEVHcomc36');
 assert.equal(report.researchLink.target, '_blank');
 assert.equal(report.researchLink.rel, 'noreferrer');
 await page.locator('#start').click();
 await page.waitForFunction(() => window.__privacyAudit.results > 0, null, {timeout: 60000});
 const worker = page.workers().find(w => w.url().includes('hand-worker'));
 assert.ok(worker, 'MediaPipe worker not found');
 report.workerPath = new URL(worker.url()).pathname;
 // Verify actual server response independently, without route.fulfill or headers injection.
 const workerResponse = await context.request.get(worker.url());
 report.workerResponse = {status: workerResponse.status(), csp: workerResponse.headers()['content-security-policy']};
 assert.equal(report.workerResponse.status, 200);
 assert.equal(report.workerResponse.csp, policy);
 await worker.evaluate(() => {
  self.__privacyAudit = {fetches: [], violations: []};
  self.addEventListener('securitypolicyviolation', event => self.__privacyAudit.violations.push({
   blockedURI: event.blockedURI, directive: event.effectiveDirective, disposition: event.disposition
  }));
  const original = self.fetch;
  self.fetch = async function(input, options) {
   const url = typeof input === 'string' ? input : input.url || String(input);
   if (!url.includes('odml.pa.googleapis.com')) return original.apply(this, arguments);
   const record = {destination: new URL(url).origin + new URL(url).pathname, method: options?.method || 'GET', workerElapsedMs: performance.now()};
   self.__privacyAudit.fetches.push(record);
   try {const response = await original.apply(this, arguments); record.status = response.status; return response;}
   catch (error) {record.rejectedWith = error.name; throw error;}
  };
 });
 const start = Date.now();
 report.initialResults = await page.evaluate(() => window.__privacyAudit.results);
 for (let i = 0; i < 4; i++) {
  await page.waitForTimeout(20000);
  console.log(`Privacy check: ${Math.round((Date.now() - start) / 1000)} seconds`);
 }
 report.durationSeconds = (Date.now() - start) / 1000;
 report.worker = await worker.evaluate(() => self.__privacyAudit);
 report.final = await page.evaluate(() => ({...window.__privacyAudit,
  inferenceAgeMs: performance.now() - window.__privacyAudit.lastResultMs,
  camera: document.querySelector('#camera-state').textContent,
  guidance: document.querySelector('#guidance').textContent,
  practiceTime: document.querySelector('#practice-time').textContent
 }));
 const countAtBlockEnd = report.final.results;
 await page.waitForTimeout(2000);
 report.resultsAfterBlock = await page.evaluate(() => window.__privacyAudit.results);
 assert.ok(report.durationSeconds > 75);
 assert.ok(report.final.results > report.initialResults);
 assert.ok(report.resultsAfterBlock > countAtBlockEnd, 'Inference must continue after CSP rejection');
 assert.ok(report.final.inferenceAgeMs < 2000);
 assert.ok(report.final.camera.startsWith('ON'));
 assert.ok(report.resources.some(r => r.path.endsWith('.wasm') && r.status === 200));
 assert.ok(report.resources.some(r => r.path.endsWith('hand_landmarker.task') && r.status === 200));
 assert.ok(report.worker.fetches.some(r => r.method === 'POST' && r.rejectedWith === 'TypeError'));
 assert.ok(report.worker.violations.some(v => v.blockedURI === 'https://odml.pa.googleapis.com/v1/log' && v.directive === 'connect-src' && v.disposition === 'enforce'));
 assert.ok(report.worker.violations.every(v => v.blockedURI === 'https://odml.pa.googleapis.com/v1/log'), 'Unexpected resource blocked');
 assert.equal(report.externalRequests.length, 0, 'An external request escaped CSP and reached the harness guard');
 assert.equal(report.pageErrors.length, 0);
 report.status = 'PASS';
} catch (error) {report.status = 'FAIL'; report.error = String(error); throw error;}
finally {
 await mkdir(output, {recursive: true});
 await writeFile(new URL(base.port === '5173' ? 'development.json' : 'production.json', output), JSON.stringify(report, null, 2) + '\n');
 await browser.close();
 console.log(JSON.stringify(report, null, 2));
}
