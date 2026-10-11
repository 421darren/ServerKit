#!/usr/bin/env node
// Ratchet: form labels must be tied to their field.
//
// A <label>/<Label> with no htmlFor that wraps no control names nothing:
// clicking it does not focus the field and a screen reader announces the
// field without a name. Associate it with `useId()` + `htmlFor`/`id`. What
// remains below the ceiling is mostly labels that head a group of options or
// sit over read-only text, plus pickers that do not forward an `id` yet.
//
// Usage (from frontend/):
//   node scripts/check-label-association.mjs            # check against the ceiling
//   node scripts/check-label-association.mjs --report   # list the offenders
//   node scripts/check-label-association.mjs --update   # write the current count

import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as espree from 'espree';

const here = dirname(fileURLToPath(import.meta.url));
const srcDir = resolve(here, '../src');
const ceilingFile = resolve(here, 'LABEL_ASSOCIATION_CEILING');

// Elements that count as "the field" when a label wraps them.
const CONTROLS = new Set(['input', 'select', 'textarea', 'Input', 'Textarea', 'Select', 'SelectTrigger',
    'Checkbox', 'Switch', 'RadioGroup', 'SearchField', 'PortField', 'DomainField', 'ServerPicker']);
// Bundled extension copies are checked in their own repos; tests are not UI.
const SKIP_DIRS = new Set(['plugins', '__tests__']);

const walk = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return SKIP_DIRS.has(entry.name) ? [] : walk(path);
    return entry.name.endsWith('.jsx') ? [path] : [];
});

const tagName = (opening) => opening.name.name
    || (opening.name.object && `${opening.name.object.name}.${opening.name.property.name}`);

function visit(node, fn) {
    if (!node || typeof node.type !== 'string') return;
    fn(node);
    for (const key of Object.keys(node)) {
        if (key === 'loc' || key === 'range') continue;
        const value = node[key];
        if (Array.isArray(value)) value.forEach((child) => visit(child, fn));
        else if (value && typeof value.type === 'string') visit(value, fn);
    }
}

function census() {
    const byFile = new Map();
    for (const path of walk(srcDir)) {
        const ast = espree.parse(readFileSync(path, 'utf8'), {
            ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true }, loc: true,
        });
        const lines = [];
        visit(ast, (node) => {
            if (node.type !== 'JSXElement') return;
            const tag = tagName(node.openingElement);
            if (tag !== 'label' && tag !== 'Label') return;
            if (node.openingElement.attributes.some((a) => a.type === 'JSXAttribute' && a.name.name === 'htmlFor')) return;
            let wraps = false;
            visit(node, (child) => {
                if (child !== node && child.type === 'JSXElement' && CONTROLS.has(tagName(child.openingElement))) wraps = true;
            });
            if (!wraps) lines.push(node.loc.start.line);
        });
        if (lines.length) byFile.set(relative(srcDir, path).replaceAll('\\', '/'), lines);
    }
    return byFile;
}

const byFile = census();
const count = [...byFile.values()].reduce((total, lines) => total + lines.length, 0);

if (process.argv.includes('--update')) {
    writeFileSync(ceilingFile, `${count}\n`);
    console.log(`label association ceiling updated to ${count}`);
    process.exit(0);
}

if (process.argv.includes('--report')) {
    for (const [file, lines] of [...byFile].sort((a, b) => b[1].length - a[1].length)) {
        console.log(`  ${String(lines.length).padStart(3)}  ${file}:${lines.join(',')}`);
    }
    console.log(`\ntotal: ${count} unassociated labels in ${byFile.size} files`);
    process.exit(0);
}

const ceiling = Number(readFileSync(ceilingFile, 'utf8').trim());
if (count > ceiling) {
    console.error(`\nlabel association check failed: ${count} labels name no field; the ceiling is ${ceiling}.`);
    console.error('  Give the field an id from useId() and the label a matching htmlFor:\n');
    console.error('      const fieldId = useId();');
    console.error('      <Label htmlFor={`${fieldId}-name`}>Name</Label>');
    console.error('      <Input id={`${fieldId}-name`} ... />\n');
    console.error('  Offenders: node scripts/check-label-association.mjs --report\n');
    process.exit(1);
}
if (count < ceiling) {
    console.error(`\nlabel association ceiling is ${ceiling} but only ${count} remain; run`);
    console.error('  node scripts/check-label-association.mjs --update\n');
    process.exit(1);
}
console.log(`✓ label association: ${count} unassociated labels remain ratcheted (ceiling ${ceiling}).`);
