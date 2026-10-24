import { useState, useEffect, useMemo } from 'react';
import { Globe, Boxes, SlidersHorizontal, FileText, Home } from 'lucide-react';
import { api } from '@/services/api';
// Demo rail shortcuts (Quick access) — one-click jumps to the paths people
// actually visit on a ServerKit host. "Stack" starts at the default install
// location and is re-pointed from /system/version's install_dir, so a custom
// SERVERKIT_DIR install jumps to the real tree.
const QUICK_ACCESS = [
    { labelKey: 'app.fileManager.sites', label: 'Sites', path: '/var/www', icon: Globe },
    { labelKey: 'app.fileManager.stack', label: 'Stack', path: '/opt/serverkit', icon: Boxes },
    {
        labelKey: 'app.fileManager.webConfig',
        label: 'Web config',
        path: '/etc/nginx',
        icon: SlidersHorizontal,
    },
    { labelKey: 'common.labels.logs', label: 'Logs', path: '/var/log', icon: FileText },
];

// Remote-agent rails: the panel stack doesn't exist on an agent box, so link
// the agent's own footprint instead. These paths are fixed by the agent
// installers the panel serves (scripts/install.sh: /etc/serverkit-agent;
// scripts/install.ps1: ProgramData\ServerKit\Agent) — agents run on the wire
// with forward-slash paths, Windows included.
const QUICK_ACCESS_AGENT = {
    linux: [
        { labelKey: 'app.fileManager.sites', label: 'Sites', path: '/var/www', icon: Globe },
        { labelKey: 'app.fileManager.agent', label: 'Agent', path: '/etc/serverkit-agent', icon: Boxes },
        {
            labelKey: 'app.fileManager.webConfig',
            label: 'Web config',
            path: '/etc/nginx',
            icon: SlidersHorizontal,
        },
        { labelKey: 'common.labels.logs', label: 'Logs', path: '/var/log', icon: FileText },
    ],
    windows: [
        {
            labelKey: 'app.fileManager.agent',
            label: 'Agent',
            path: 'C:/ProgramData/ServerKit/Agent',
            icon: Boxes,
        },
        {
            labelKey: 'app.fileManager.agentLogs',
            label: 'Agent logs',
            path: 'C:/ProgramData/ServerKit/Agent/logs',
            icon: FileText,
        },
        { labelKey: 'app.fileManager.users', label: 'Users', path: 'C:/Users', icon: Home },
    ],
    darwin: [
        { labelKey: 'app.fileManager.home', label: 'Home', path: '/Users', icon: Home },
        { labelKey: 'common.labels.logs', label: 'Logs', path: '/var/log', icon: FileText },
    ],
};

export default function useFileTargets({ target, isRemote, t }) {
    // The "S3 bucket" target is offered only when an S3-compatible backup
    // destination is configured (Connections → Storage, or the Backups page).
    const [s3Available, setS3Available] = useState(false);
    const s3Options = useMemo(
        () => (s3Available ? [{ value: 's3', label: t('app.fileManager.s3Bucket', 'S3 bucket') }] : []),
        [s3Available, t],
    );
    useEffect(() => {
        let cancelled = false;
        api.getStorageConfig()
            .then((c) => {
                if (cancelled) return;
                const p = c?.provider;
                setS3Available((p === 's3' || p === 'b2') && Boolean(c?.[p]?.bucket));
            })
            .catch(() => {});
        return () => {
            cancelled = true;
        };
    }, []);

    // The "Stack" quick link tracks the panel's real install dir (custom
    // SERVERKIT_DIR installs aren't at /opt/serverkit).
    const [panelInstallDir, setPanelInstallDir] = useState('/opt/serverkit');
    useEffect(() => {
        let cancelled = false;
        api.getVersion()
            .then((v) => {
                if (!cancelled && v?.install_dir) setPanelInstallDir(v.install_dir);
            })
            .catch(() => {});
        return () => {
            cancelled = true;
        };
    }, []);

    // Per-target rail: agents get their OS's set (unknown os_type — an agent
    // predating sysinfo reporting — is treated as linux, the historical
    // behavior), with the agent's SELF-REPORTED config dir preferred over the
    // installer convention when the agent sent one (system_info footprint);
    // the local host gets the panel set with the resolved Stack dir.
    const quickAccess = useMemo(() => {
        if (isRemote) {
            const os = (target.os_type || 'linux').toLowerCase();
            const rail = QUICK_ACCESS_AGENT[os] || QUICK_ACCESS_AGENT.linux;
            // Windows agents report filepath-style backslashes; the file
            // wire protocol speaks forward slashes.
            const configDir = target.agentConfigDir
                ? target.agentConfigDir.replace(/\\/g, '/').replace(/\/+$/, '')
                : null;
            if (!configDir) return rail;
            return rail.map((q) => {
                if (q.label === 'Agent') return { ...q, path: configDir };
                if (q.label === 'Agent logs') return { ...q, path: `${configDir}/logs` };
                return q;
            });
        }
        return QUICK_ACCESS.map((q) => (q.label === 'Stack' ? { ...q, path: panelInstallDir } : q));
    }, [isRemote, target.os_type, target.agentConfigDir, panelInstallDir]);

    return { s3Options, quickAccess };
}
