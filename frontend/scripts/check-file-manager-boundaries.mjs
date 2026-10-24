import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'espree';

const src = resolve(dirname(fileURLToPath(import.meta.url)), '../src');
const feature = 'components/file-manager/';
const apiOwners = new Set(['pages/FileManager.jsx', `${feature}hooks/useFileTargets.js`,
    `${feature}hooks/useFileVolumes.js`]);

export function inspectFileManagerSource(path, source) {
    const errors = [];
    const ast = parse(source, { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } });
    const page = path === 'pages/FileManager.jsx';
    const hook = path.startsWith(`${feature}hooks/`);
    const view = path.startsWith(feature) && path.endsWith('.jsx');
    const imports = ast.body.filter(node => node.type === 'ImportDeclaration');
    for (const node of imports) {
        const target = node.source.value;
        if (/services\//.test(target) && !apiOwners.has(path)) {
            errors.push(`${path}: transport imports belong to the adapter composition or metadata hooks`);
        }
        if (path.startsWith(feature) && /(?:^|\/)pages\//.test(target)) {
            errors.push(`${path}: a feature cannot depend on route pages`);
        }
        if (view && /(?:^|\/)hooks\/use(?:File|Directory)/.test(target)) {
            errors.push(`${path}: views receive feature state through props`);
        }
    }
    function visit(node) {
        if (!node || typeof node !== 'object') return;
        if (page && node.type === 'AwaitExpression') errors.push(`${path}: asynchronous work belongs in hooks`);
        if ((page || view) && node.type === 'CallExpression' && node.callee?.object?.name === 'api') {
            errors.push(`${path}: views must not call API methods`);
        }
        if (view && node.type === 'CallExpression' && node.callee?.name === 'fetch') {
            errors.push(`${path}: views must not fetch`);
        }
        for (const value of Object.values(node)) {
            if (Array.isArray(value)) value.forEach(visit);
            else if (value && typeof value === 'object') visit(value);
        }
    }
    visit(ast);
    // Backstops for accidental recombination, in addition to dependency rules.
    const lines = source.split('\n').filter(line => line.trim()).length;
    if (page && lines > 650) errors.push(`${path}: keep the route focused on composition (650 nonblank lines)`);
    if (hook && lines > 300) errors.push(`${path}: split unrelated hook responsibilities (300 nonblank lines)`);
    return errors;
}

export function checkFileManagerBoundaries() {
    const walk = dir => readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
        if (entry.name === '__tests__') return [];
        const path = join(dir, entry.name);
        return entry.isDirectory() ? walk(path) : /\.[jt]sx?$/.test(path) ? [path] : [];
    });
    const files = [join(src, 'pages/FileManager.jsx'), ...walk(join(src, feature))];
    const errors = files.flatMap(path => inspectFileManagerSource(
        relative(src, path).replaceAll('\\', '/'), readFileSync(path, 'utf8')));
    if (errors.length) throw new Error(errors.join('\n'));
}
