import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';

// The real Terminal page. Changing the line count, clearing a search or
// picking a journal unit used to re-fetch through a stale closure, i.e. with
// the PREVIOUS value. Only HTTP, toasts and translation are stubbed.
const root = fileURLToPath(new URL('../', import.meta.url));
const fixture = `
import React from 'react';
import {createRoot} from 'react-dom/client';
import {MemoryRouter,Routes,Route} from 'react-router-dom';
import Terminal from '/src/pages/Terminal.jsx';
window.calls=[];
const log=(...c)=>{window.calls.push(c);return Promise.resolve({content:'line',lines:['line']});};
window.testApi={
 getLogFiles:()=>Promise.resolve({logs:[{path:'/var/log/syslog',name:'syslog',size:10}]}),
 readLog:(p,n)=>log('read',p,n),
 searchLog:(p,q,n)=>log('search',p,q,n),
 getJournalLogs:(u,n,pr)=>log('journal',u,n,pr),
};
const tab=new URLSearchParams(location.search).get('tab');
createRoot(document.getElementById('root')).render(
 <MemoryRouter initialEntries={['/terminal/'+tab]}><Routes><Route path='/terminal/:tab' element={<Terminal/>}/></Routes></MemoryRouter>);
`;
const server = await createServer({
    root, configFile: false, logLevel: 'error', resolve: { alias: { '@': path.join(root, 'src') } },
    cacheDir: path.join(root, 'node_modules/.vite-terminal-regression'),
    server: { host: '127.0.0.1', port: 0 },
    plugins: [{
        name: 'terminal-regression-fixtures', enforce: 'pre',
        resolveId(id) {
            if (id === 'react-i18next') return '\0test-i18n';
            if (id.endsWith('/terminal-fixture.jsx')) return path.join(root, 'terminal-fixture.jsx');
        },
        load(id) {
            const normalized = id.replaceAll('\\', '/');
            if (id === '\0test-i18n') return `const t=(key,fallback)=>typeof fallback==='string'?fallback:key;export const useTranslation=()=>({t,i18n:{language:'en'}});export const Trans=({children})=>children;export const initReactI18next={type:'3rdParty',init(){}};`;
            if (normalized.endsWith('/src/contexts/useAuth.js')) return `import {createContext} from 'react';export const AuthContext=createContext(null);const auth={user:{id:1,username:'admin',role:'admin'},isAdmin:true,isAuthenticated:true,hasPermission:()=>true};export const useAuth=()=>auth;`;
            if (normalized.endsWith('/src/contexts/useWorkspace.js')) return `const ws={activeWorkspaceId:null,activeWorkspace:null,workspaces:[],setActiveWorkspace(){}};export const useWorkspace=()=>ws;`;
            if (normalized.endsWith('/src/contexts/useToast.js')) return `const toast={error(){},success(){},info(){},warning(){}};export const useToast=()=>toast;`;
            if (normalized.endsWith('/src/services/api.js') || normalized.endsWith('/src/services/api/index.js')) return `export default new Proxy({}, {get:(_,key)=>(...args)=>(window.testApi[key]?window.testApi[key](...args):Promise.resolve({}))});`;
            if (normalized.endsWith('/terminal-fixture.jsx')) return fixture;
        },
        configureServer(vite) {
            vite.middlewares.use('/terminal-check', async (_req, res) => {
                res.setHeader('Content-Type', 'text/html');
                res.end(await vite.transformIndexHtml('/terminal-check', '<div id="root"></div><script type="module" src="/terminal-fixture.jsx"></script>'));
            });
        },
    }, react()],
});
const executablePath = [process.env.CHROME_PATH, chromium.executablePath(), 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(candidate => candidate && existsSync(candidate));
const LINE_OPTIONS = [50, 100, 200, 500, 1000, 5000];
async function pickLines(page, n) {
    await page.getByLabel('Lines to fetch').first().click();
    await page.getByRole('option').nth(LINE_OPTIONS.indexOf(n)).click();
}
const last = (page, kind) => page.evaluate(k => window.calls.filter(c => c[0] === k).at(-1), kind);
let browser;
try {
    await server.listen();
    browser = await chromium.launch({ ...(executablePath ? { executablePath } : {}), headless: true });
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => localStorage.clear());
    const base = `http://127.0.0.1:${server.httpServer.address().port}/terminal-check`;

    await page.goto(`${base}?tab=logs`);
    await page.getByText('syslog', { exact: false }).first().click();
    await page.waitForFunction(() => window.calls.some(c => c[0] === 'read'));
    const before = (await last(page, 'read'))[2];
    await pickLines(page, 1000);
    await page.waitForFunction(() => window.calls.filter(c => c[0] === 'read').at(-1)[2] === 1000);
    assert.notEqual(before, 1000);
    console.log('PASS changing the line count re-reads the file with the NEW count');

    const search = page.getByPlaceholder('Search in log…').first();
    await search.fill('error');
    await search.press('Enter');
    await page.waitForFunction(() => window.calls.some(c => c[0] === 'search'));
    const reads = await page.evaluate(() => window.calls.filter(c => c[0] === 'read').length);
    const searches = await page.evaluate(() => window.calls.filter(c => c[0] === 'search').length);
    await page.getByTitle('Clear', { exact: true }).first().click();
    await page.waitForFunction(n => window.calls.filter(c => c[0] === 'read').length > n, reads);
    assert.equal(await page.evaluate(() => window.calls.filter(c => c[0] === 'search').length), searches);
    console.log('PASS clearing the search re-reads unfiltered instead of searching the old pattern');

    await page.goto(`${base}?tab=journal`);
    await page.waitForFunction(() => window.calls.some(c => c[0] === 'journal'));
    await page.getByText('Nginx', { exact: true }).first().click();
    await page.waitForFunction(() => window.calls.filter(c => c[0] === 'journal').at(-1)[1] === 'nginx');
    await pickLines(page, 1000);
    await page.waitForFunction(() => {
        const c = window.calls.filter(x => x[0] === 'journal').at(-1);
        return c[1] === 'nginx' && c[2] === 1000;
    });
    console.log('PASS picking a unit and a line count fetch the journal with the NEW values');

    // The priority filter was decorative: its value never reached the API.
    await page.getByText('Error', { exact: true }).first().click();
    await page.waitForFunction(() => window.calls.filter(x => x[0] === 'journal').at(-1)[3] === '3');
    const journalCall = await page.evaluate(() => window.calls.filter(x => x[0] === 'journal').at(-1));
    assert.deepEqual(journalCall.slice(1), ['nginx', 1000, '3']);
    console.log('PASS the priority filter is sent with the unit and line count');
    assert.deepEqual(errors, []);
} finally {
    await browser?.close();
    await server.close();
}
