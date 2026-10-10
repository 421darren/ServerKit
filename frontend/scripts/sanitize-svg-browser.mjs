// sanitizeSvgInner output is rendered with dangerouslySetInnerHTML inside an
// <svg>, so the HTML parser — not the XML parser that scrubbed it — has the
// last word. Comments and processing instructions survive XML serialization
// but close early under HTML rules (`<!-->`, `<?x >`), letting the rest out.
// Run in a real browser so both parsers are the real ones. No backend needed.
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const PAYLOADS = [
    '<!--><img src=x onerror="window.__xss=1">-->',
    '<?x ><img src=x onerror="window.__xss=1">?>',
    '<![CDATA[<img src=x onerror="window.__xss=1">]]>',
    '<path d="M0 0" onload="window.__xss=1"/>',
    '<foreignObject><img xmlns="http://www.w3.org/1999/xhtml" src="x" onerror="window.__xss=1"/></foreignObject>',
    '<g><script>window.__xss=1</script></g>',
    '<a href="javascript:window.__xss=1"><path d="M0 0"/></a>',
    '<g><!--><img src=x onerror="window.__xss=1">--></g>',
];

const server = await createServer({ server: { host: '127.0.0.1', port: 0, strictPort: false, open: false } });
let browser;
try {
    await server.listen();
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(`${server.resolvedUrls.local[0]}src/utils/sanitizeSvg.js`);

    const results = await page.evaluate(async (payloads) => {
        const { sanitizeSvgInner } = await import('/src/utils/sanitizeSvg.js');
        const out = [];
        for (const payload of payloads) {
            const host = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            document.body.appendChild(host);
            host.innerHTML = sanitizeSvgInner(payload);
            await new Promise((resolve) => setTimeout(resolve, 50));
            out.push({
                payload,
                fired: Boolean(window.__xss),
                foreign: [...host.querySelectorAll('*')]
                    .filter((el) => el.namespaceURI !== 'http://www.w3.org/2000/svg'
                        || [...el.attributes].some((a) => a.name.startsWith('on') || a.name.includes('href')))
                    .map((el) => el.outerHTML),
            });
            window.__xss = 0;
            host.remove();
        }
        const kept = sanitizeSvgInner('<path d="M4 6h16" stroke="currentColor"/><circle cx="12" cy="12" r="3"/>');
        return { out, kept };
    }, PAYLOADS);

    for (const { payload, fired, foreign } of results.out) {
        assert.equal(fired, false, `script ran for ${payload}`);
        assert.deepEqual(foreign, [], `unsafe markup survived for ${payload}`);
    }
    assert.match(results.kept, /<path [^>]*d="M4 6h16" stroke="currentColor"/);
    assert.match(results.kept, /<circle [^>]*cx="12" cy="12" r="3"/);
    console.log(`SVG sanitizer: ${PAYLOADS.length} bypass payloads inert, safe icons intact.`);
} finally {
    await browser?.close();
    await server.close();
}
