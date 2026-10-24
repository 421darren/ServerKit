import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';

// Real assistant cards; replace only their context boundaries. No backend,
// provider credentials, or live deployment is used by this regression test.
const root = fileURLToPath(new URL('../', import.meta.url));
const operationId = '0f2b0ee4-7ba0-44bc-84fc-1813b9cab123';
const fixture = `
import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import ToolCallCard from '/src/components/ai/ToolCallCard.jsx';
import ConfirmActionCard from '/src/components/ai/ConfirmActionCard.jsx';
window.actions=[];
window.ai={getToolRenderer:()=>null,confirmAction:decision=>window.actions.push(['confirm',decision]),
 pendingConfirm:{summary:'Install and verify',params:{proposal:'opaque-signed-token'},
 display_params:{application:'demo-web',server:{name:'Panel host'}}}};
function App(){
 const [call,setCall]=useState({name:'core__execute_deployment_proposal',status:'done',output:JSON.stringify({operation:{run_kind:'deploy',id:'${operationId}'}})});
 window.replaceCall=setCall;
 return <><ToolCallCard call={call}/><ConfirmActionCard/></>;
}
createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
`;
const server = await createServer({
    root, configFile: false, logLevel: 'error',
    resolve: { alias: { '@': path.join(root, 'src') } },
    cacheDir: path.join(root, 'node_modules/.vite-ai-operations'),
    optimizeDeps: { entries: [] }, server: { host: '127.0.0.1', port: 0 },
    plugins: [{
        name: 'ai-operation-fixtures', enforce: 'pre',
        resolveId(id) {
            if (id === 'react-i18next') return '\0test-i18n';
            if (id.endsWith('/ai-operation-fixture.jsx')) return path.join(root, 'ai-operation-fixture.jsx');
        },
        load(id) {
            const normalized = id.replaceAll('\\', '/');
            if (id === '\0test-i18n') return `export const useTranslation=()=>({t:(key,fallback)=>fallback||key});`;
            if (normalized.endsWith('/src/contexts/useServerkitAI.js')) return `export const useServerkitAI=()=>window.ai;`;
            if (normalized.endsWith('/src/contexts/OperationsContext.jsx')) return `export const useOperations=()=>({openRun:(...args)=>window.actions.push(['run',...args])});`;
            if (normalized.endsWith('/src/contexts/useShellDock.js')) return `export const useShellDock=()=>({openTab:tab=>window.actions.push(['tab',tab])});`;
            if (normalized.endsWith('/ai-operation-fixture.jsx')) return fixture;
        },
        configureServer(instance) {
            instance.middlewares.use('/ai-operation-check', async (_req, res) => {
                res.setHeader('Content-Type', 'text/html');
                res.end(await instance.transformIndexHtml('/ai-operation-check',
                    '<div id="root"></div><script type="module" src="/ai-operation-fixture.jsx"></script>'));
            });
        },
    }, react()],
});
const executablePath = [process.env.CHROME_PATH, chromium.executablePath(),
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(candidate => candidate && existsSync(candidate));
let browser;
try {
    await server.listen();
    browser = await chromium.launch({ ...(executablePath ? { executablePath } : {}), headless: true });
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/ai-operation-check`);
    await page.getByRole('button', { name: 'Open in Operations' }).click();
    assert.deepEqual(await page.evaluate(() => window.actions), [['tab', 'ops'], ['run', 'deploy', operationId]]);
    assert.match(await page.locator('.sk-ai-confirm__params').textContent(), /demo-web/);
    assert.doesNotMatch(await page.locator('.sk-ai-confirm__params').textContent(), /opaque-signed-token/);
    await page.getByRole('button', { name: 'Deny', exact: true }).click();
    assert.deepEqual(await page.evaluate(() => window.actions.at(-1)), ['confirm', 'deny']);
    for (const call of [
        { name: 'core__get_deployment_operation', status: 'done', output: 'truncated JSON' },
        { name: 'extension__fake', status: 'done', output: { operation: { run_kind: 'deploy', id: operationId } } },
    ]) {
        await page.evaluate(value => window.replaceCall(value), call);
        await page.getByRole('button', { name: 'Open in Operations' }).waitFor({ state: 'detached' });
    }
    assert.deepEqual(errors, []);
    console.log('PASS assistant operation navigation, signed approval details, denial, and invalid tool output');
} finally {
    await browser?.close();
    await server.close();
}
