import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';


const root = fileURLToPath(new URL('../', import.meta.url));
const fixture = `
import React from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import EnvironmentPanel from '/src/components/environment/EnvironmentPanel.jsx';
import PreviewList from '/src/components/previews/PreviewList.jsx';
import {ConfirmProvider} from '/src/contexts/ConfirmContext.jsx';
window.pending=[]; window.calls=[]; window.toasts=[];
window.answer=(service,data)=>window.pending.splice(window.pending.findIndex(x=>x.service===service),1)[0].resolve(data);
window.testApi={
 getEnvVars:()=>Promise.resolve({env_vars:[]}),
 getComposeServices:()=>window.discoveryError?Promise.reject(Error('no discovery')):Promise.resolve({services:['web','worker']}),
 getEffectiveEnvVars:(id,service)=>{window.calls.push(service);return new Promise((resolve,reject)=>window.pending.push({service,resolve,reject}));},
 getPreviews:()=>Promise.resolve({previews:[{id:1,pr_number:1,status:'unavailable',domain:'unavailable.test',url:'https://unavailable.test'},{id:2,pr_number:2,status:'running',domain:'running.test',url:'https://running.test'}]}),
 getPreviewSettings:()=>Promise.resolve({enabled:true}),
 redeployPreview:()=>Promise.resolve({status:'unavailable'}),
 createPreview:(id,pr)=>{window.created=pr;return Promise.resolve({status:'queued',job_id:'job'});},
 destroyPreview:()=>Promise.resolve({status:'queued'}),
 updatePreviewSettings:(id,patch)=>{window.settingsPatch=patch;return Promise.resolve({enabled:true,...patch});},
};
createRoot(document.getElementById('root')).render(<MemoryRouter><ConfirmProvider>{location.search==='?preview'?<PreviewList appId={1}/>:<EnvironmentPanel appId={1}/>}</ConfirmProvider></MemoryRouter>);
`;
const server = await createServer({
    root, configFile: false, logLevel: 'error', resolve: { alias: { '@': path.join(root, 'src') } },
    cacheDir: path.join(root, 'node_modules/.vite-effective-environment-regression'),
    optimizeDeps: { entries: [] }, server: { host: '127.0.0.1', port: 0 },
    plugins: [{
        name: 'effective-environment-fixtures', enforce: 'pre',
        resolveId(id) {
            if (id === 'react-i18next') return '\0test-i18n';
            if (id.endsWith('/env-fixture.jsx')) return path.join(root, 'env-fixture.jsx');
        },
        load(id) {
            const normalized = id.replaceAll('\\', '/');
            if (id === '\0test-i18n') return `const t=(key,f)=>typeof f==='string'?f:(f&&(f.defaultValue_other||f.defaultValue))||key;export const useTranslation=()=>({t,i18n:{language:'en'}});export const Trans=({children})=>children;export const initReactI18next={type:'3rdParty',init(){}};`;
            if (normalized.endsWith('/src/contexts/useAuth.js')) return `import {createContext} from 'react';export const AuthContext=createContext(null);const auth={user:{id:1,role:'admin'},isAdmin:true,isAuthenticated:true,hasPermission:()=>true};export const useAuth=()=>auth;`;
            if (normalized.endsWith('/src/contexts/useWorkspace.js')) return `const ws={activeWorkspaceId:null,workspaces:[],setActiveWorkspace(){}};export const useWorkspace=()=>ws;`;
            if (normalized.endsWith('/src/contexts/useToast.js')) return `const toast={error(m){(window.toasts=window.toasts||[]).push(m)},success(m){(window.toasts=window.toasts||[]).push('SUCCESS:'+m)},info(){},warning(){}};export const useToast=()=>toast;`;
            if (normalized.endsWith('/src/services/api.js') || normalized.endsWith('/src/services/api/index.js')) return `const api=new Proxy({}, {get:(_,key)=>(...args)=>(window.testApi[key]?window.testApi[key](...args):Promise.resolve({}))});export {api};export default api;`;
            if (normalized.endsWith('/env-fixture.jsx')) return fixture;
        },
        configureServer(vite) {
            vite.middlewares.use('/env-check', async (_req, res) => {
                res.setHeader('Content-Type', 'text/html');
                res.end(await vite.transformIndexHtml('/env-check', '<div id="root"></div><script type="module" src="/env-fixture.jsx"></script>'));
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
    const url = `http://127.0.0.1:${server.httpServer.address().port}/env-check`;
    await page.goto(url);
    await page.getByRole('tab', {name:'Effective environment', exact:true}).click();
    await page.waitForFunction(()=>window.pending.some(x=>x.service==='web'));
    const choose = async name => {
        await page.getByRole('combobox', {name:'Compose service'}).click();
        await page.getByRole('option', {name, exact:true}).click();
    };
    await choose('worker');
    await page.waitForFunction(()=>window.pending.some(x=>x.service==='worker'));
    await page.evaluate(()=>window.answer('worker',{complete:true,env_vars:[{key:'WORKER_KEY',source_scope:'local',overrides:{source_scope:'workspace',group_name:'shared'},value:'DO-NOT-RENDER'}]}));
    await page.getByText('WORKER_KEY',{exact:true}).waitFor();
    await page.evaluate(()=>window.answer('web',{complete:true,env_vars:[{key:'STALE_WEB',source_scope:'project'}]}));
    await page.waitForTimeout(150);
    assert.equal(await page.getByText('STALE_WEB',{exact:true}).count(),0);
    assert.equal(await page.getByText('DO-NOT-RENDER',{exact:true}).count(),0);
    assert.equal(await page.getByText('Workspace / shared',{exact:true}).count(),1);
    await page.getByRole('button',{name:'Refresh',exact:true}).click();
    await page.waitForFunction(()=>window.pending.some(x=>x.service==='worker'));
    assert.equal(await page.getByText('WORKER_KEY',{exact:true}).count(),0);
    await page.evaluate(()=>window.answer('worker',{complete:false,env_vars:[{key:'LOCAL_ONLY',source_scope:'local'}]}));
    await page.getByRole('alert').filter({hasText:'Incomplete:'}).waitFor();
    await page.getByText('LOCAL_ONLY',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Refresh',exact:true}).click();
    await page.waitForFunction(()=>window.pending.length>0);
    await page.evaluate(()=>window.pending.shift().reject(Error('network')));
    await page.getByRole('alert').filter({hasText:'Could not load'}).waitFor();
    assert.equal(await page.getByText('LOCAL_ONLY',{exact:true}).count(),0);
    // Failed service discovery must not silently use an unfiltered result.
    const before = await page.evaluate(()=>window.calls.length);
    await page.evaluate(()=>{window.discoveryError=true;});
    await page.getByRole('button',{name:'Refresh',exact:true}).click();
    await page.getByRole('alert').filter({hasText:'Could not load'}).waitFor();
    assert.equal(await page.evaluate(()=>window.calls.length),before);
    await page.getByRole('tab',{name:'Local variables',exact:true}).click();
    await page.getByText('No environment variables',{exact:true}).waitFor();
    assert.deepEqual(errors,[]);
    console.log('PASS effective environment: service races, masking, overrides, incomplete/error/retry, local editor');

    await page.goto(url+'?preview');
    await page.getByText('unavailable',{exact:true}).waitFor();
    assert.equal(await page.locator('a[href="https://unavailable.test"]').count(),0);
    assert.equal(await page.locator('a[href="https://running.test"]').count()>0,true);
    await page.getByRole('button',{name:'Redeploy',exact:true}).first().click();
    await page.waitForFunction(()=>window.toasts.length>0);
    assert.equal(await page.evaluate(()=>window.toasts.some(x=>x.includes('not deployed'))),true);
    assert.equal(await page.evaluate(()=>window.toasts.some(x=>x.startsWith('SUCCESS:'))),false);
    assert.deepEqual(errors,[]);
    console.log('PASS previews: unavailable links suppressed and unsuccessful redeploy has no success toast');
    await page.getByLabel('PR number', {exact:true}).fill('23');
    await page.getByLabel('Repository branch', {exact:true}).fill('feature/test');
    await page.getByLabel('Full commit SHA', {exact:true}).fill('a'.repeat(40));
    await page.getByRole('button',{name:'Deploy preview',exact:true}).click();
    await page.waitForFunction(()=>window.created?.pr_number===23);
    assert.deepEqual(await page.evaluate(()=>window.created),{pr_number:23,branch:'feature/test',commit_sha:'a'.repeat(40)});
    await page.getByRole('switch',{name:/Inherit application environment/}).click();
    await page.waitForFunction(()=>window.settingsPatch?.inherit_environment===true);
    await page.getByRole('button',{name:'Delete',exact:true}).first().click();
    await page.getByRole('alertdialog').getByRole('button',{name:'Delete',exact:true}).click();
    await page.waitForFunction(()=>window.toasts.some(t=>t.includes('deletion queued')));
    assert.deepEqual(errors,[]);
    console.log('PASS previews: pinned create form, explicit inheritance and queued deletion');

} finally {
    await browser?.close();
    await server.close();
}
