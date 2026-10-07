// Fail2ban endpoints — the extension's own /api/v1/security/fail2ban client,
// built on the panel's ApiClient via the SDK singleton. Moved out of the
// host's services/api/security.js with the Fail2ban tab (plan 47 Ph3c /
// plan 55 Phase 3). Same paths and bodies as the host client had, so the
// backend blueprint (same url_prefix) is a drop-in.
import { api } from 'serverkit-sdk';

async function getFail2banStatus() {
    return api.request('/security/fail2ban/status');
}

async function installFail2ban() {
    return api.request('/security/fail2ban/install', { method: 'POST' });
}

async function getFail2banJailStatus(jail) {
    return api.request(`/security/fail2ban/jails/${jail}`);
}

async function getAllFail2banBans() {
    return api.request('/security/fail2ban/bans');
}

async function fail2banUnban(ip, jail = null) {
    return api.request('/security/fail2ban/unban', {
        method: 'POST',
        body: { ip, jail }
    });
}

async function fail2banBan(ip, jail = 'sshd') {
    return api.request('/security/fail2ban/ban', {
        method: 'POST',
        body: { ip, jail }
    });
}

export default {
    getFail2banStatus,
    installFail2ban,
    getFail2banJailStatus,
    getAllFail2banBans,
    fail2banUnban,
    fail2banBan,
};
