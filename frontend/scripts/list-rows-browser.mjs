import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';

// List rows on real pages; only HTTP, toasts, confirm and translation are
// stubbed.
//  - Row actions inside memoized columns: the columns were memoized without
//    the state their delete handlers read, so a delete after opening a vault
//    or a variable group used first-render values (a null vault, group null).
//  - Keyboard: a clickable row opens with Enter like it does with a click.
//  - A label can name a server picker: the picker puts its id on its trigger.
const root = fileURLToPath(new URL('../', import.meta.url));
const fixture = `
import React from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import Vaults from '/src/pages/Vaults.jsx';
import SharedVariableGroups from '/src/components/shared/SharedVariableGroups.jsx';
import ServerPicker from '/src/components/ServerPicker.jsx';
const log=(...a)=>(window.calls=window.calls||[]).push(a);
const vault={id:11,name:'alpha-vault',description:'',secret_count:1,workspace_id:null};
window.testApi={
 listVaults:()=>Promise.resolve({vaults:[vault]}),
 getWorkspaces:()=>Promise.resolve({workspaces:[]}),
 getVault:(id)=>{log('getVault',id);return Promise.resolve({vault});},
 listSecrets:()=>Promise.resolve({secrets:[{id:5,name:'API_TOKEN',value:'••••',updated_at:null}]}),
 deleteSecret:(id)=>{log('deleteSecret',id);return Promise.resolve({});},
 listVariableGroups:()=>Promise.resolve({groups:[{id:21,name:'shared-env',variable_count:1,attachment_count:0}]}),
 getVariableGroup:(id)=>Promise.resolve({id,name:'shared-env',variables:[{id:31,key:'REGION',value:'x',is_secret:false}],attachments:[]}),
 deleteGroupVariable:(gid,vid)=>{log('deleteGroupVariable',gid,vid);return Promise.resolve({});},
};
const which=new URLSearchParams(location.search).get('page');
const picker=<div><label htmlFor="pick-target">Applies to</label><ServerPicker id="pick-target" label="Server" onChange={()=>{}}/></div>;
createRoot(document.getElementById('root')).render(<MemoryRouter>{which==='vaults'?<Vaults/>:which==='picker'?picker:<SharedVariableGroups scopeType="workspace" scopeId={1}/>}</MemoryRouter>);
`;
const server = await createServer({
    root, configFile: false, logLevel: 'error', resolve: { alias: { '@': path.join(root, 'src') } },
    cacheDir: path.join(root, 'node_modules/.vite-list-rows-regression'),
    optimizeDeps: { entries: [] }, server: { host: '127.0.0.1', port: 0 },
    plugins: [{
        name: 'list-rows-fixtures', enforce: 'pre',
        resolveId(id) {
            if (id === 'react-i18next') return '\0test-i18n';
            if (id.endsWith('/sc-fixture.jsx')) return path.join(root, 'sc-fixture.jsx');
        },
        load(id) {
            const normalized = id.replaceAll('\\', '/');
            if (id === '\0test-i18n') return `const t=(key,f)=>typeof f==='string'?f:(f&&(f.defaultValue_other||f.defaultValue))||key;export const useTranslation=()=>({t,i18n:{language:'en'}});export const Trans=({children})=>children;export const initReactI18next={type:'3rdParty',init(){}};`;
            if (normalized.endsWith('/src/contexts/useAuth.js')) return `import {createContext} from 'react';export const AuthContext=createContext(null);const auth={user:{id:1,role:'admin'},isAdmin:true,isAuthenticated:true,hasPermission:()=>true};export const useAuth=()=>auth;`;
            if (normalized.endsWith('/src/contexts/useWorkspace.js')) return `const ws={activeWorkspaceId:null,workspaces:[],setActiveWorkspace(){}};export const useWorkspace=()=>ws;`;
            if (normalized.endsWith('/src/contexts/useToast.js')) return `const toast={error(m){(window.toasts=window.toasts||[]).push(m)},success(){},info(){},warning(){}};export const useToast=()=>toast;`;
            if (normalized.endsWith('/src/hooks/useConfirm.js')) return `const confirm=async()=>true;export function useConfirm(){return {confirm,confirmState:{isOpen:false},handleConfirm(){},handleCancel(){}};}`;
            if (normalized.endsWith('/src/services/api.js') || normalized.endsWith('/src/services/api/index.js')) return `const api=new Proxy({}, {get:(_,key)=>(...args)=>(window.testApi[key]?window.testApi[key](...args):Promise.resolve({}))});export {api};export default api;`;
            if (normalized.endsWith('/sc-fixture.jsx')) return fixture;
        },
        configureServer(vite) {
            vite.middlewares.use('/sc-check', async (_req, res) => {
                res.setHeader('Content-Type', 'text/html');
                res.end(await vite.transformIndexHtml('/sc-check', '<div id="root"></div><script type="module" src="/sc-fixture.jsx"></script>'));
            });
        },
    }, react()],
});
const executablePath = [process.env.CHROME_PATH, chromium.executablePath(), 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(candidate => candidate && existsSync(candidate));
let browser;
try {
    await server.listen();
    browser = await chromium.launch({ ...(executablePath ? { executablePath } : {}), headless: true });
    const base = `http://127.0.0.1:${server.httpServer.address().port}/sc-check`;

    const vaults = await browser.newPage();
    const vaultErrors = [];
    vaults.on('pageerror', error => vaultErrors.push(error.message));
    await vaults.goto(`${base}?page=vaults`);
    await vaults.getByText('alpha-vault').first().click();
    await vaults.getByText('API_TOKEN').first().waitFor();
    await vaults.getByTitle('Delete', { exact: true }).first().click();
    await vaults.waitForFunction(() => window.calls.filter(c => c[0] === 'getVault').length === 2);
    assert.deepEqual(await vaults.evaluate(() => window.calls),
        [['getVault', 11], ['deleteSecret', 5], ['getVault', 11]]);
    assert.deepEqual(await vaults.evaluate(() => window.toasts || []), []);
    assert.deepEqual(vaultErrors, []);
    console.log('PASS deleting a secret refreshes the vault that is open');

    const groups = await browser.newPage();
    const groupErrors = [];
    groups.on('pageerror', error => groupErrors.push(error.message));
    await groups.goto(`${base}?page=groups`);
    await groups.getByText('shared-env').first().click();
    await groups.getByText('REGION').first().waitFor();
    await groups.getByTitle('Delete variable', { exact: true }).first().click();
    await groups.waitForFunction(() => (window.calls || []).some(c => c[0] === 'deleteGroupVariable'));
    assert.deepEqual(await groups.evaluate(() => window.calls), [['deleteGroupVariable', 21, 31]]);
    assert.deepEqual(groupErrors, []);
    console.log('PASS deleting a group variable names the open group');

    const keys = await browser.newPage();
    const keyErrors = [];
    keys.on('pageerror', error => keyErrors.push(error.message));
    await keys.goto(`${base}?page=vaults`);
    const row = keys.getByRole('row').filter({ hasText: 'alpha-vault' }).first();
    await row.focus();
    await keys.keyboard.press('Enter');
    await keys.getByText('API_TOKEN').first().waitFor({ timeout: 5000 });
    assert.deepEqual(await keys.evaluate(() => window.calls), [['getVault', 11]]);
    assert.deepEqual(keyErrors, []);
    console.log('PASS Enter on a focused row opens it');

    const pick = await browser.newPage();
    const pickErrors = [];
    pick.on('pageerror', error => pickErrors.push(error.message));
    await pick.goto(`${base}?page=picker`);
    // Clicking the label activates the picker it names, as with any field.
    await pick.locator('label[for="pick-target"]').click();
    await pick.waitForFunction(() => document.getElementById('pick-target')?.getAttribute('aria-expanded') === 'true', null, { timeout: 5000 });
    assert.deepEqual(pickErrors, []);
    console.log('PASS clicking a label opens the server picker it names');
} finally {
    await browser?.close();
    await server.close();
}
