// Malware scanner endpoints — the extension's own client for the ClamAV /
// scan / YARA / quarantine surface under /api/v1/security, built on the
// panel's ApiClient via the SDK singleton. Moved out of the host's
// services/api/security.js with the Scanner + Quarantine tabs. Same paths and bodies as the host client had, so the
// backend blueprint (same url_prefix) is a drop-in. Generic core calls the
// tabs also make (getApps, getJob) stay on the core client — import those
// from 'serverkit-sdk' directly.
import { api } from 'serverkit-sdk';

// ClamAV
async function getClamAVStatus() {
    return api.request('/security/clamav/status');
}

async function installClamAV() {
    return api.request('/security/clamav/install', { method: 'POST' });
}

async function updateVirusDefinitions() {
    return api.request('/security/clamav/update', { method: 'POST' });
}

async function startClamAV() {
    return api.request('/security/clamav/start', { method: 'POST' });
}

// Scans
async function scanFile(path) {
    return api.request('/security/scan/file', {
        method: 'POST',
        body: { path }
    });
}

async function scanDirectory(path, recursive = true) {
    return api.request('/security/scan/directory', {
        method: 'POST',
        body: { path, recursive }
    });
}

async function getScanStatus() {
    return api.request('/security/scan/status');
}

async function cancelScan() {
    return api.request('/security/scan/cancel', { method: 'POST' });
}

async function getScanHistory(limit = 50) {
    return api.request(`/security/scan/history?limit=${limit}`);
}

async function runQuickScan() {
    return api.request('/security/scan/quick', { method: 'POST' });
}

async function runFullScan() {
    return api.request('/security/scan/full', { method: 'POST' });
}

async function scanApp(appId) {
    // Job-backed malware scan (YARA + ClamAV) of an app's docroot → { job_id }
    return api.request(`/security/scan/app/${appId}`, { method: 'POST' });
}

async function scanPathJob(path) {
    return api.request('/security/scan/job', {
        method: 'POST',
        body: { path }
    });
}

// YARA web-shell rules
async function getYaraRules() {
    return api.request('/security/yara/rules');
}

async function uploadYaraRule(filename, content) {
    return api.request('/security/yara/rules', {
        method: 'POST',
        body: { filename, content }
    });
}

async function deleteYaraRule(filename) {
    return api.request(`/security/yara/rules/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    });
}

// Quarantine
async function getQuarantinedFiles() {
    return api.request('/security/quarantine');
}

async function quarantineFile(path) {
    return api.request('/security/quarantine', {
        method: 'POST',
        body: { path }
    });
}

async function deleteQuarantinedFile(filename) {
    return api.request(`/security/quarantine/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    });
}

async function restoreQuarantinedFile(filename) {
    return api.request(`/security/quarantine/${encodeURIComponent(filename)}/restore`, {
        method: 'POST'
    });
}

const clamavApi = {
    getClamAVStatus,
    installClamAV,
    updateVirusDefinitions,
    startClamAV,
    scanFile,
    scanDirectory,
    getScanStatus,
    cancelScan,
    getScanHistory,
    runQuickScan,
    runFullScan,
    scanApp,
    scanPathJob,
    getYaraRules,
    uploadYaraRule,
    deleteYaraRule,
    getQuarantinedFiles,
    quarantineFile,
    deleteQuarantinedFile,
    restoreQuarantinedFile,
};

export default clamavApi;
