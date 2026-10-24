import { useState } from 'react';
import usePersistentState from '@/hooks/usePersistentState';
import { STORAGE, isNarrowScreen } from '../preferences';
export default function useFilePreferences() {
    // ─── view prefs ──────────────────────────────────────
    const [viewMode, setViewMode] = usePersistentState(STORAGE.viewMode, (v) => v || 'list');
    const gridSize = 'md';
    const [sortBy, setSortBy] = usePersistentState(STORAGE.sortBy, (v) => v || 'name');
    const [sortDir, setSortDir] = usePersistentState(STORAGE.sortDir, (v) => v || 'asc');
    const [activeFilter, setActiveFilter] = useState('all');

    // ─── left sidebar ────────────────────────────────────
    const [sidebarVisible, setSidebarVisible] = usePersistentState(STORAGE.sidebar, (v) =>
        isNarrowScreen() ? false : v !== null ? v === 'true' : true,
    );
    const [treeCollapsed, setTreeCollapsed] = usePersistentState(STORAGE.treeCollapsed, (v) => v === 'true');

    return {
        viewMode,
        setViewMode,
        gridSize,
        sortBy,
        setSortBy,
        sortDir,
        setSortDir,
        activeFilter,
        setActiveFilter,
        sidebarVisible,
        setSidebarVisible,
        treeCollapsed,
        setTreeCollapsed,
    };
}
