import {defineConfig} from 'vite';
export default defineConfig(({command})=>({
 plugins:[{name:'production-csp',transformIndexHtml(html){return command==='build'?html.replace(' ws://127.0.0.1:*',''):html;}}],
 worker:{format:'es'},build:{target:'es2022',chunkSizeWarningLimit:900},server:{port:5173,strictPort:true},preview:{port:4173,strictPort:true}
}));
