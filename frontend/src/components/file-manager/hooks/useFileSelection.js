import { useState } from 'react';
export default function useFileSelection() {
    // ─── selection ───────────────────────────────────────
    const [selectedPaths, setSelectedPaths] = useState(new Set());
    const [lastClickedPath, setLastClickedPath] = useState(null);
    const [selectMode, setSelectMode] = useState(false);

    // ─── selection ───────────────────────────────────────
    const toggleSelect = (entry, e, sortedFiltered) => {
        const path = entry.path;
        if (e?.shiftKey && lastClickedPath) {
            const list = sortedFiltered;
            const a = list.findIndex((x) => x.path === lastClickedPath);
            const b = list.findIndex((x) => x.path === path);
            if (a >= 0 && b >= 0) {
                const [from, to] = [Math.min(a, b), Math.max(a, b)];
                const rangePaths = list.slice(from, to + 1).map((x) => x.path);
                const next = new Set([...selectedPaths, ...rangePaths]);
                setSelectedPaths(next);
                setSelectMode(next.size > 0);
            }
        } else {
            const next = new Set(selectedPaths);
            if (next.has(path)) next.delete(path);
            else next.add(path);
            setSelectedPaths(next);
            setSelectMode(next.size > 0);
            setLastClickedPath(path);
        }
    };

    const clearSelection = () => {
        setSelectedPaths(new Set());
        setSelectMode(false);
        setLastClickedPath(null);
    };

    return {
        selectedPaths,
        setSelectedPaths,
        selectMode,
        setSelectMode,
        setLastClickedPath,
        toggleSelect,
        clearSelection,
    };
}
