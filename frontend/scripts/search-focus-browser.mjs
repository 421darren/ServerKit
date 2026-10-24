import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('../', import.meta.url));
const fixture = `
import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter, Routes, Route} from 'react-router-dom';
import TabGroupLayout from '/src/layouts/TabGroupLayout.jsx';
import Services from '/src/pages/Services.jsx';
import Templates from '/src/pages/Templates.jsx';
import Monitors from '/src/pages/Monitors.jsx';
import Jobs from '/src/pages/Jobs.jsx';
import Telemetry from '/src/pages/Telemetry.jsx';
import SearchField from '/src/components/ds/SearchField.jsx';
window.searchPending={monitors:[],jobs:[],telemetry:[]};
const defer=(kind,params)=>new Promise(resolve=>window.searchPending[kind].push({params,resolve}));
window.testApi={
 getApps:()=>Promise.resolve({apps:[{id:1,name:'serverkit-app',status:'running',app_type:'node',project_name:'alpha'},{id:2,name:'other-app',status:'stopped',app_type:'node',project_name:'beta'}]}),
 getBandwidthApps:()=>Promise.resolve({apps:{}}),
 getTemplateCategories:()=>Promise.resolve({categories:[]}),
 listTemplates:(_category,search)=>new Promise(resolve=>setTimeout(()=>resolve({templates:[{id:'wordpress',name:'WordPress',description:'CMS',categories:['cms']}].filter(item=>!search||item.name.toLowerCase().includes(search.toLowerCase()))}),400)),
 getMonitors:(params)=>defer('monitors',params),
 getJobs:(params)=>defer('jobs',params),
 getScheduledJobs:()=>Promise.resolve({scheduled:[]}),
 getJobKinds:()=>Promise.resolve([]),
 getTelemetrySources:()=>Promise.resolve({sources:[]}),
 getTelemetryEventTypes:()=>Promise.resolve({event_types:[]}),
 getTelemetryEvents:(params)=>defer('telemetry',params),
};
const page=new URLSearchParams(location.search).get('page')||'services';
function FieldReset(){const [query,setQuery]=useState('old');return <><SearchField value={query} onSearch={setQuery} placeholder="Reset search"/><button onClick={()=>setQuery('')}>Reset search</button><output id="query">{query}</output></>}
const initial=page==='templates'?'/templates':page==='monitors'?'/monitors':page==='jobs'?'/jobs':page==='telemetry'?'/telemetry':'/services';
const app=page==='field'?<FieldReset/>:<MemoryRouter initialEntries={[initial]}><Routes><Route element={<TabGroupLayout tabs={[{to:'/services',label:'Services'},{to:'/templates',label:'Templates'},{to:'/monitors',label:'Monitors'},{to:'/jobs',label:'Jobs'},{to:'/telemetry',label:'Telemetry'}]}/>}><Route path="/services" element={<Services/>}/><Route path="/templates" element={<Templates/>}/><Route path="/monitors" element={<Monitors/>}/><Route path="/jobs" element={<Jobs/>}/><Route path="/telemetry" element={<Telemetry/>}/></Route></Routes></MemoryRouter>;
createRoot(document.getElementById('root')).render(page==='monitors'||page==='jobs'||page==='telemetry'?app:<React.StrictMode>{app}</React.StrictMode>);
`;
const server = await createServer({
    root, configFile: false, logLevel: 'error', resolve: { alias: { '@': path.join(root, 'src') } },
    cacheDir: path.join(root, 'node_modules/.vite-search-focus'), optimizeDeps: { entries: [] },
    server: { host: '127.0.0.1', port: 0 },
    plugins: [{
        name: 'search-focus-fixtures', enforce: 'pre',
        resolveId(id) {
            if (id === 'react-i18next') return '\0test-i18n';
            if (id.endsWith('/search-fixture.jsx')) return path.join(root, 'search-fixture.jsx');
        },
        load(id) {
            const normalized = id.replaceAll('\\', '/');
            if (id === '\0test-i18n') return `const t=(key,f)=>typeof f==='string'?f:(f&&(f.defaultValue_other||f.defaultValue))||key;export const useTranslation=()=>({t,i18n:{language:'en'}});export const Trans=({children})=>children;export const initReactI18next={type:'3rdParty',init(){}};`;
            if (normalized.endsWith('/src/services/api.js') || normalized.endsWith('/src/services/api/index.js')) return `const api=new Proxy({}, {get:(_,key)=>(...args)=>(window.testApi[key]?window.testApi[key](...args):Promise.resolve({}))});export {api};export default api;`;
            if (normalized.endsWith('/src/contexts/useToast.js')) return `const toast={error(){},success(){},info(){},warning(){}};export const useToast=()=>toast;`;
            if (normalized.endsWith('/src/contexts/useResourceTier.js')) return `export const useResourceTier=()=>({canHostApps:true,loading:false});`;
            if (normalized.endsWith('/src/contexts/useManagedProfile.js')) return `export const useManagedProfile=()=>({isControlHeld:()=>false,profile:null});`;
            if (normalized.endsWith('/src/contexts/useAuth.js')) return `export const useAuth=()=>({user:{id:1,role:'admin'},isAdmin:true,isAuthenticated:true,hasPermission:()=>true});`;
            if (normalized.endsWith('/src/hooks/useConfirm.js')) return `export const useConfirm=()=>({confirm:async()=>true,confirmState:{isOpen:false},handleConfirm(){},handleCancel(){}});`;
            if (normalized.endsWith('/src/plugins/contributions.js')) return `export const useContributions=()=>({tabs:[]});`;
            if (normalized.endsWith('/search-fixture.jsx')) return fixture;
        },
        configureServer(vite) {
            vite.middlewares.use('/search-check', async (_req, res) => {
                res.setHeader('Content-Type', 'text/html');
                res.end(await vite.transformIndexHtml('/search-check', '<div id="root"></div><script type="module" src="/search-fixture.jsx"></script>'));
            });
        },
    }, react()],
});

const executablePath = [process.env.CHROME_PATH, chromium.executablePath(), 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(candidate => candidate && existsSync(candidate));
let browser;
try {
    await server.listen();
    browser = await chromium.launch({ ...(executablePath ? { executablePath } : {}), headless: true });
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/search-check`);
    const search = page.getByRole('searchbox', { name: 'Search services…' });
    await search.waitFor();
    await search.click();
    await search.pressSequentially('serverkit', { delay: 100 });
    await page.waitForTimeout(350);
    assert.equal(await search.inputValue(), 'serverkit');
    assert.equal(await search.evaluate(el => document.activeElement === el), true);
    await search.fill('');
    await page.waitForTimeout(350);
    await search.pressSequentially('zzzzz', { delay: 300 });
    await page.waitForTimeout(350);
    assert.equal(await search.inputValue(), 'zzzzz');
    assert.equal(await search.evaluate(el => document.activeElement === el), true);
    console.log('PASS Services search keeps full text and focus, including no matches');
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/search-check?page=templates`);
    const templateSearch = page.getByRole('searchbox', { name: 'Search templates…' });
    await templateSearch.waitFor();
    await templateSearch.click();
    await templateSearch.pressSequentially('wordpress', { delay: 300 });
    await page.waitForTimeout(500);
    assert.equal(await templateSearch.inputValue(), 'wordpress');
    assert.equal(await templateSearch.evaluate(el => document.activeElement === el), true);
    console.log('PASS Templates search keeps focus while requests load');
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/search-check?page=field`);
    const resetSearch = page.getByRole('searchbox', { name: 'Reset search' });
    await resetSearch.fill('new');
    await page.getByRole('button', { name: 'Reset search' }).click();
    await page.waitForTimeout(350);
    assert.equal(await resetSearch.inputValue(), '');
    assert.equal(await page.locator('#query').textContent(), '');
    console.log('PASS clearing a search cancels a pending debounce');

    const cases = [
        { kind: 'monitors', label: 'Search monitors or targets…', response: (name) => ({ monitors: name ? [{ id: name, name, check_type: 'http', status: 'operational' }] : [] }) },
        { kind: 'jobs', label: 'Search by kind or owner…', response: (name) => ({ jobs: name ? [{ id: name, kind: name, status: 'queued' }] : [], total: name ? 1 : 0 }) },
        { kind: 'telemetry', label: 'Search messages…', response: (name) => ({ events: name ? [{ id: name, message: name, event_type: 'test', source: 'test', severity: 'info', timestamp: '2026-01-01T00:00:00Z' }] : [] }) },
    ];
    for (const { kind, label, response } of cases) {
        await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/search-check?page=${kind}`);
        await page.waitForFunction(kind => window.searchPending[kind].length === 1, kind);
        await page.evaluate(({ kind, value }) => window.searchPending[kind][0].resolve(value), { kind, value: response('') });
        const input = page.getByRole('searchbox', { name: label });
        await input.waitFor();
        await input.fill('alpha');
        await page.waitForFunction(kind => window.searchPending[kind].length === 2, kind);
        await input.fill('beta');
        await page.waitForFunction(kind => window.searchPending[kind].length === 3, kind);
        await page.evaluate(({ kind, value }) => window.searchPending[kind][2].resolve(value), { kind, value: response('beta-result') });
        await page.getByText('beta-result').first().waitFor();
        await page.evaluate(({ kind, value }) => window.searchPending[kind][1].resolve(value), { kind, value: response('alpha-result') });
        await page.waitForTimeout(100);
        assert.equal(await page.getByText('beta-result').count() > 0, true, `${kind}: newest result disappeared`);
        assert.equal(await page.getByText('alpha-result').count(), 0, `${kind}: stale result appeared`);
        console.log(`PASS ${kind} ignores a late response from an older search`);
    }
    assert.deepEqual(errors, []);
} finally {
    await browser?.close();
    await server.close();
}
