import { useState, useEffect, useMemo } from 'react';
import { api } from '@/services/api';
export default function useFileVolumes(currentPath) {
    // ─── disk ────────────────────────────────────────────
    const [diskMounts, setDiskMounts] = useState([]);
    const [diskLastUpdated, setDiskLastUpdated] = useState(null);
    const [diskLoading, setDiskLoading] = useState(false);

    // ─── disk mounts ─────────────────────────────────────
    const loadDiskMounts = async () => {
        setDiskLoading(true);
        try {
            const data = await api.getAllDiskMounts();
            setDiskMounts(data.mounts || []);
            setDiskLastUpdated(new Date());
        } catch (e) {
            console.error('Failed to load disk mounts:', e);
        } finally {
            setDiskLoading(false);
        }
    };

    const activeMount = useMemo(
        () =>
            diskMounts
                .filter((mount) => {
                    const mountPath = mount.mountpoint || '/';
                    if (mountPath === '/') return currentPath.startsWith('/');
                    return (
                        currentPath === mountPath ||
                        currentPath.startsWith(`${mountPath.replace(/\/$/, '')}/`)
                    );
                })
                .sort((a, b) => (b.mountpoint || '/').length - (a.mountpoint || '/').length)[0] || null,
        [currentPath, diskMounts],
    );

    useEffect(() => {
        loadDiskMounts();
    }, []);

    return { diskMounts, diskLastUpdated, diskLoading, loadDiskMounts, activeMount };
}
