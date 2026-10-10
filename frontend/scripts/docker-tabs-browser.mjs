import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';

// The real Containers and Images tabs. Switching servers while the old
// server's list was still loading let that late answer overwrite the new
// server's list, and a failed load left the previous list (or "No
// containers") on screen instead of an error. Only HTTP is stubbed.
const root = fileURLToPath(new URL('../', import.meta.url));
const fixture = `
import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import {ServerContext} from '/src/components/docker/dockerHelpers.js';
import ContainersTab from '/src/components/docker/ContainersTab.jsx';
import ImagesTab from '/src/components/docker/ImagesTab.jsx';
window.pending=[];
const hold=(server,kind)=>new Promise((resolve,reject)=>window.pending.push({server,kind,resolve,reject}));
window.release=(server,kind,ok=true)=>{const i=window.pending.findIndex(p=>p.server===server&&p.kind===kind);const p=window.pending.splice(i,1)[0];
 const row=kind==='containers'?{data:[{id:server+'-c',name:server+'-web',image:'nginx',status:'Up',state:'running'}]}:{data:[{id:server+'-i',repository:server+'-repo',tag:'latest',size:'1MB'}]};
 ok?p.resolve({success:true,...row}):p.reject(new Error('Docker is not reachable: daemon down'));};
window.testApi={
 getRemoteContainers:(server)=>hold(server,'containers'),
 getRemoteImages:(server)=>hold(server,'images'),
 getRemoteContainerStats:()=>Promise.resolve({}),
 getContainersStats:()=>Promise.resolve({}),
};
function App(){const [server,setServer]=useState('alpha');window.setServer=setServer;const tab=new URLSearchParams(location.search).get('tab');
 return <ServerContext.Provider value={{serverId:server,serverName:server,isRemote:true}}>{tab==='images'?<ImagesTab/>:<ContainersTab/>}</ServerContext.Provider>}
createRoot(document.getElementById('root')).render(<MemoryRouter><App/></MemoryRouter>);
`;
const server = await createServer({
    root, configFile: false, logLevel: 'error', resolve: { alias: { '@': path.join(root, 'src') } },
    cacheDir: path.join(root, 'node_modules/.vite-docker-tabs-regression'),
    optimizeDeps: { entries: [] }, server: { host: '127.0.0.1', port: 0 },
    plugins: [{
        name: 'docker-tabs-fixtures', enforce: 'pre',
        resolveId(id) {
            if (id === 'react-i18next') return '\0test-i18n';
            if (id.endsWith('/docker-fixture.jsx')) return path.join(root, 'docker-fixture.jsx');
        },
        load(id) {
            const normalized = id.replaceAll('\\', '/');
            if (id === '\0test-i18n') return `const t=(key,f)=>typeof f==='string'?f:(f&&(f.defaultValue_other||f.defaultValue))||key;export const useTranslation=()=>({t,i18n:{language:'en'}});export const Trans=({children})=>children;export const initReactI18next={type:'3rdParty',init(){}};`;
            if (normalized.endsWith('/src/contexts/useAuth.js')) return `import {createContext} from 'react';export const AuthContext=createContext(null);const auth={user:{id:1,role:'admin'},isAdmin:true,isAuthenticated:true,hasPermission:()=>true};export const useAuth=()=>auth;`;
            if (normalized.endsWith('/src/contexts/useWorkspace.js')) return `const ws={activeWorkspaceId:null,workspaces:[],setActiveWorkspace(){}};export const useWorkspace=()=>ws;`;
            if (normalized.endsWith('/src/contexts/useToast.js')) return `const toast={error(){},success(){},info(){},warning(){}};export const useToast=()=>toast;`;
            if (normalized.endsWith('/src/services/api.js') || normalized.endsWith('/src/services/api/index.js')) return `export default new Proxy({}, {get:(_,key)=>(...args)=>(window.testApi[key]?window.testApi[key](...args):Promise.resolve({}))});`;
            if (normalized.endsWith('/docker-fixture.jsx')) return fixture;
        },
        configureServer(vite) {
            vite.middlewares.use('/docker-check', async (_req, res) => {
                res.setHeader('Content-Type', 'text/html');
                res.end(await vite.transformIndexHtml('/docker-check', '<div id="root"></div><script type="module" src="/docker-fixture.jsx"></script>'));
            });
        },
    }, react()],
});
const executablePath = [process.env.CHROME_PATH, chromium.executablePath(), 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(candidate => candidate && existsSync(candidate));
const waitPending = (page, srv, kind) => page.waitForFunction(([s, k]) => (window.pending || []).some(p => p.server === s && p.kind === k), [srv, kind]);
let browser;
try {
    await server.listen();
    browser = await chromium.launch({ ...(executablePath ? { executablePath } : {}), headless: true });
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const base = `http://127.0.0.1:${server.httpServer.address().port}/docker-check`;

    for (const [tab, kind, label] of [['containers', 'containers', 'web'], ['images', 'images', 'repo']]) {
        await page.goto(`${base}?tab=${tab}`);
        await waitPending(page, 'alpha', kind);
        await page.evaluate(() => window.setServer('beta'));
        await waitPending(page, 'beta', kind);
        await page.evaluate(k => window.release('beta', k), kind);
        await page.getByText(`beta-${label}`).first().waitFor();
        await page.evaluate(k => window.release('alpha', k), kind);  // the late answer
        await page.waitForTimeout(300);
        assert.equal(await page.getByText(`alpha-${label}`).count(), 0, `${tab}: old server's late answer replaced the list`);
        assert.equal(await page.getByText(`beta-${label}`).count() > 0, true);
        console.log(`PASS ${tab}: a late answer from the previous server is ignored`);

        await page.evaluate(() => window.setServer('gamma'));
        await waitPending(page, 'gamma', kind);
        await page.evaluate(k => window.release('gamma', k, false), kind);
        await page.getByText('Docker is not reachable', { exact: false }).first().waitFor();
        assert.equal(await page.getByText(`beta-${label}`).count(), 0, `${tab}: previous list still shown after a failed load`);
        assert.equal(await page.getByText(/^No (containers|images)$/).count(), 0, `${tab}: failure rendered as an empty host`);
        console.log(`PASS ${tab}: a failed load shows the error, not an empty or stale list`);
    }
    assert.deepEqual(errors, []);
} finally {
    await browser?.close();
    await server.close();
}
