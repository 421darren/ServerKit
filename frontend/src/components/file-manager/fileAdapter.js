// All file operations cross this boundary. Unsupported targets never fall back
// to the panel host, even if a caller forgets to disable a control.
const OPERATIONS = ['browse', 'read', 'write', 'delete', 'download', 'upload',
    'search', 'create folder', 'rename', 'change permissions', 'preview'];

function unwrapAgentData(result) {
    return result && typeof result === 'object' && 'success' in result && 'data' in result
        ? result.data : result;
}

export function createFileAdapter(api, target) {
    const local = {
        browse: (path, hidden) => api.browseFiles(path, hidden),
        read: (path) => api.readFile(path),
        write: (path, content) => api.writeFile(path, content),
        delete: (path) => api.deleteFile(path),
        download: (entry) => api.downloadFile(entry.path),
        upload: (path, file, progress) => api.uploadFile(path, file, progress),
        search: (path, query) => api.searchFiles(path, query),
        'create folder': (path) => api.createDirectory(path),
        rename: (path, name) => api.renameFile(path, name),
        'change permissions': (path, mode) => api.changeFilePermissions(path, mode),
        preview: async (path) => ({ blob: await api.getFileBlob(path) }),
    };
    const agent = {
        browse: async (path) => unwrapAgentData(await api.browseRemoteFiles(target.server_id, path)),
        read: async (path) => unwrapAgentData(await api.readRemoteFile(target.server_id, path)),
        write: async (path, content) => unwrapAgentData(await api.writeRemoteFile(target.server_id, path, content)),
    };
    const s3 = {
        browse: (path) => api.browseS3(path),
        read: (path) => api.readS3(path),
        write: (path, content) => api.writeS3(path, content),
        delete: (path) => api.deleteS3(path),
        download: (entry) => api.downloadS3File(entry.path),
        upload: (path, file, progress) => api.uploadS3(path, file, progress),
        preview: (path) => api.getS3DownloadUrl(path),
    };
    const methods = { local, agent, s3 }[target.kind];
    if (!methods) throw new Error(`Unknown file target: ${target.kind}`);
    const supports = (operation) => Object.hasOwn(methods, operation);
    const adapter = { supports };
    for (const operation of OPERATIONS) {
        adapter[operation] = (...args) => {
            if (!supports(operation)) throw new Error(`${operation} is unavailable on ${target.kind}`);
            return methods[operation](...args);
        };
    }
    adapter.del = adapter.delete;
    return Object.freeze(adapter);
}
