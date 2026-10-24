import { useMemo } from 'react';
import { getFileType } from '../fileTypes';

export const FILTER_OPTIONS = [
    { id: 'all', labelKey: 'common.labels.all', label: 'All' },
    { id: 'folder', labelKey: 'app.fileManager.folders', label: 'Folders' },
    { id: 'image', labelKey: 'app.fileManager.images', label: 'Images' },
    { id: 'code', labelKey: 'app.fileManager.code', label: 'Code' },
    { id: 'text', labelKey: 'app.fileManager.documents', label: 'Documents' },
    { id: 'data', labelKey: 'app.fileManager.data', label: 'Data' },
    { id: 'video', labelKey: 'app.fileManager.videos', label: 'Videos' },
    { id: 'audio', labelKey: 'app.fileManager.audio', label: 'Audio' },
    { id: 'archive', labelKey: 'app.fileManager.archives', label: 'Archives' },
];

export default function useFileListingModel({
    currentPath,
    entries,
    searchResults,
    activeFilter,
    sortBy,
    sortDir,
    selectedPaths,
    setSortBy,
    setSortDir,
    t,
}) {
    // ─── derived ─────────────────────────────────────────
    const breadcrumbs = useMemo(() => {
        const parts = currentPath.split('/').filter(Boolean);
        // Windows drive-rooted path ("C:/Users/Juan"): the first segment is
        // the drive and the root crumb is the agent's drive list. Building
        // crumbs with a leading "/" (the POSIX branch below) would produce
        // bogus "/C:" paths that the agent can't resolve.
        if (/^[A-Za-z]:$/.test(parts[0] || '')) {
            const crumbs = [{ name: 'Drives', path: '/' }];
            let acc = parts[0];
            crumbs.push({ name: parts[0], path: acc + '/' });
            for (let i = 1; i < parts.length; i++) {
                acc += '/' + parts[i];
                crumbs.push({ name: parts[i], path: acc });
            }
            return crumbs;
        }
        const crumbs = [{ name: '/', path: '/' }];
        let acc = '';
        parts.forEach((p) => {
            acc += '/' + p;
            crumbs.push({ name: p, path: acc });
        });
        return crumbs;
    }, [currentPath]);

    const sortedFiltered = useMemo(() => {
        let list = [...(searchResults || entries)];
        if (activeFilter !== 'all') list = list.filter((e) => getFileType(e) === activeFilter);
        const dir = sortDir === 'asc' ? 1 : -1;
        list.sort((a, b) => {
            if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
            switch (sortBy) {
                case 'size':
                    return ((a.size || 0) - (b.size || 0)) * dir;
                case 'modified':
                    return (new Date(a.modified) - new Date(b.modified)) * dir;
                case 'type':
                    return getFileType(a).localeCompare(getFileType(b)) * dir;
                case 'name':
                default:
                    return a.name.localeCompare(b.name) * dir;
            }
        });
        return list;
    }, [entries, searchResults, sortBy, sortDir, activeFilter]);

    const filterCounts = useMemo(() => {
        const counts = { all: entries.length };
        FILTER_OPTIONS.forEach((c) => {
            if (c.id !== 'all') counts[c.id] = 0;
        });
        entries.forEach((e) => {
            const t = getFileType(e);
            if (counts[t] !== undefined) counts[t]++;
        });
        return counts;
    }, [entries]);

    const stats = useMemo(() => {
        const list = sortedFiltered;
        const folders = list.filter((e) => e.is_dir).length;
        const files = list.length - folders;
        const totalBytes = list.reduce((s, e) => s + (e.size || 0), 0);
        const selectedList = list.filter((e) => selectedPaths.has(e.path));
        const selectedBytes = selectedList.reduce((s, e) => s + (e.size || 0), 0);
        return {
            folders,
            files,
            totalBytes,
            total: list.length,
            selectedCount: selectedList.length,
            selectedBytes,
        };
    }, [sortedFiltered, selectedPaths]);

    const sortValue = `${sortBy}-${sortDir}`;
    const filterLabels = {
        all: t('common.labels.all', 'All'),
        folder: t('app.fileManager.folders', 'Folders'),
        image: t('app.fileManager.images', 'Images'),
        code: t('app.fileManager.code', 'Code'),
        text: t('app.fileManager.documents', 'Documents'),
        data: t('app.fileManager.data', 'Data'),
        video: t('app.fileManager.videos', 'Videos'),
        audio: t('app.fileManager.audio', 'Audio'),
        archive: t('app.fileManager.archives', 'Archives'),
    };
    const handleSortChange = (value) => {
        const [nextSortBy, nextSortDir] = value.split('-');
        setSortBy(nextSortBy);
        setSortDir(nextSortDir);
    };

    const selectedEntries = useMemo(
        () => sortedFiltered.filter((e) => selectedPaths.has(e.path)),
        [sortedFiltered, selectedPaths],
    );

    return {
        breadcrumbs,
        sortedFiltered,
        filterCounts,
        stats,
        sortValue,
        filterLabels,
        handleSortChange,
        selectedEntries,
    };
}
