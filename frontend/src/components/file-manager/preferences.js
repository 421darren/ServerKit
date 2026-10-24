export const STORAGE = {
    sidebar: 'serverkit-fm-sidebar',
    treeCollapsed: 'serverkit-fm-tree-collapsed',
    expanded: 'serverkit-fm-tree-expanded',
    viewMode: 'serverkit-fm-view-mode',
    sortBy: 'serverkit-fm-sort-by',
    sortDir: 'serverkit-fm-sort-dir',
};

export const serializeExpanded = (set) => JSON.stringify([...set]);
export const parseExpanded = (stored) => {
    try {
        return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
        return new Set();
    }
};
export const isNarrowScreen = () =>
    typeof window !== 'undefined' && window.matchMedia('(max-width: 1024px)').matches;
