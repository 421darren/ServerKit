import assert from 'node:assert/strict';
import test from 'node:test';
import {
    checkFileManagerBoundaries,
    inspectFileManagerSource,
} from '../../../../scripts/check-file-manager-boundaries.mjs';

test('File Manager keeps transport, orchestration and views separate', () => {
    assert.doesNotThrow(checkFileManagerBoundaries);
});

test('boundary guard rejects dependencies that would recombine the feature', () => {
    for (const [path, source] of [
        ['pages/FileManager.jsx', 'async function load() { await api.browseFiles(); }'],
        ['pages/FileManager.jsx', "fetch('/api/v1/files').then(render);"],
        ['components/file-manager/FileManagerListing.jsx', "import { api } from '@/services/api';"],
        ['components/file-manager/hooks/useFileEditor.js', "import Page from '@/pages/FileManager';"],
        ['components/file-manager/FileManagerSidebar.jsx', "import useFileTree from './hooks/useFileTree';"],
    ])
        assert.ok(inspectFileManagerSource(path, source).length > 0, path);
});
