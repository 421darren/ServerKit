import assert from 'node:assert/strict';
import test from 'node:test';
import { createFileAdapter } from '../fileAdapter.js';

function fixture(target) {
    const calls = [];
    const api = new Proxy({}, { get: (_, name) => (...args) => {
        calls.push([name, ...args]);
        return Promise.resolve({ success: true, data: { files: [] } });
    } });
    return { adapter: createFileAdapter(api, target), calls };
}

test('agent operations use its server id and unwrap older envelopes', async () => {
    const { adapter, calls } = fixture({ kind: 'agent', server_id: 7 });
    assert.deepEqual(await adapter.browse('/home', true), { files: [] });
    await adapter.read('/home/a');
    await adapter.write('/home/a', 'edited');
    assert.deepEqual(calls, [['browseRemoteFiles', 7, '/home'],
        ['readRemoteFile', 7, '/home/a'], ['writeRemoteFile', 7, '/home/a', 'edited']]);
});

for (const kind of ['agent', 's3']) {
    test(`${kind} unsupported operations never reach the panel host`, () => {
        const { adapter, calls } = fixture({ kind, server_id: 7 });
        const unsupported = ['search', 'create folder', 'rename', 'change permissions'];
        if (kind === 'agent') unsupported.push('delete', 'download', 'upload', 'preview');
        for (const operation of unsupported) {
            assert.equal(adapter.supports(operation), false);
            assert.throws(() => adapter[operation]('/home/a'), /unavailable/);
        }
        assert.deepEqual(calls, []);
    });
}

test('S3 transfer and mutation operations stay in the bucket', async () => {
    const { adapter, calls } = fixture({ kind: 's3' });
    const progress = () => {};
    await adapter.upload('/folder', 'file', progress);
    await adapter.write('/a', 'edited');
    await adapter.del('/a');
    adapter.download({ path: '/b' });
    assert.deepEqual(calls, [['uploadS3', '/folder', 'file', progress],
        ['writeS3', '/a', 'edited'], ['deleteS3', '/a'], ['downloadS3File', '/b']]);
});

test('local calls retain hidden flag and mutation arguments', async () => {
    const { adapter, calls } = fixture({ kind: 'local' });
    await adapter.browse('/home', true);
    await adapter['create folder']('/home/assets');
    await adapter.rename('/home/assets', 'new');
    await adapter['change permissions']('/home/assets', '700');
    assert.deepEqual(calls, [['browseFiles', '/home', true],
        ['createDirectory', '/home/assets'], ['renameFile', '/home/assets', 'new'],
        ['changeFilePermissions', '/home/assets', '700']]);
});

test('unknown targets fail closed', () => {
    assert.throws(() => fixture({ kind: 'typo' }), /Unknown file target/);
});
