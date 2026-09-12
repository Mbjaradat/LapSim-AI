import {defineConfig, type Plugin, type ViteDevServer, type PreviewServer} from 'vite';
import deployment from './vercel.json' with {type: 'json'};

// Keep local worker responses consistent with the production Vercel policy.
// Asset response CSP governs workers, not the document importing a script.
function workerCsp(): Plugin {
 const install = (server: ViteDevServer | PreviewServer) => {
  server.middlewares.use((request, response, next) => {
   const path = new URL(request.url ?? '/', 'http://localhost').pathname;
   if (path.startsWith('/assets/') || path === '/src/hand-worker.ts') {
    for (const header of deployment.headers[0].headers) response.setHeader(header.key, header.value);
   }
   next();
  });
 };
 return {name: 'worker-response-csp', configureServer: install, configurePreviewServer: install};
}
export default defineConfig(({command})=>({
 plugins:[workerCsp(),{name:'production-csp',transformIndexHtml(html){return command==='build'?html.replace(' ws://127.0.0.1:*',''):html;}}],
 worker:{format:'es'},build:{target:'es2022',chunkSizeWarningLimit:900},server:{port:5173,strictPort:true},preview:{port:4173,strictPort:true}
}));
