import { useState, useCallback, useEffect, useRef } from 'react';
import usePersistentState from '@/hooks/usePersistentState';
import { STORAGE, parseExpanded, serializeExpanded } from '../preferences';
import { TREE_ROOTS } from '../fileTypes';
export default function useFileTree({ fileApi, currentPath }) {
    // ─── folder tree state ───────────────────────────────
    const [treeExpanded, setTreeExpanded] = usePersistentState(
        STORAGE.expanded,
        parseExpanded,
        serializeExpanded,
    );
    const [treeCache, setTreeCache] = useState(new Map());
    const [treeLoading, setTreeLoading] = useState(new Set());
    const activeApi = useRef(fileApi);
    activeApi.current = fileApi;
    const mounted = useRef(true);
    useEffect(() => {
        mounted.current = true;
        return () => {
            mounted.current = false;
        };
    }, []);
    useEffect(() => {
        setTreeCache(new Map());
        setTreeLoading(new Set());
    }, [fileApi]);

    const refreshTree = async (path) => {
        if (!treeCache.has(path)) return;
        try {
            const data = await fileApi.browse(path, false);
            if (!mounted.current || activeApi.current !== fileApi) return;
            const folders = (data.entries || data.files || [])
                .filter((e) => e.is_dir)
                .map(({ path, name }) => ({ path, name }));
            setTreeCache((c) => new Map(c).set(path, folders));
        } catch {
            /* A failed refresh leaves the last known tree visible. */
        }
    };

    // ─── tree expand/collapse ────────────────────────────
    const toggleTreeExpand = useCallback(
        async (path) => {
            if (treeExpanded.has(path)) {
                const next = new Set(treeExpanded);
                next.delete(path);
                setTreeExpanded(next);
                return;
            }
            if (!treeCache.has(path)) {
                setTreeLoading((s) => {
                    const n = new Set(s);
                    n.add(path);
                    return n;
                });
                try {
                    const data = await fileApi.browse(path, false);
                    if (!mounted.current || activeApi.current !== fileApi) return;
                    const entries = data.entries || data.files || [];
                    const folders = entries
                        .filter((e) => e.is_dir)
                        .map((e) => ({
                            path: e.path,
                            name: e.name,
                        }));
                    setTreeCache((c) => {
                        const n = new Map(c);
                        n.set(path, folders);
                        return n;
                    });
                } catch {
                    if (!mounted.current || activeApi.current !== fileApi) return;
                    setTreeCache((c) => {
                        const n = new Map(c);
                        n.set(path, []);
                        return n;
                    });
                } finally {
                    if (mounted.current && activeApi.current === fileApi) {
                        setTreeLoading((s) => {
                            const n = new Set(s);
                            n.delete(path);
                            return n;
                        });
                    }
                }
            }
            setTreeExpanded((s) => {
                const n = new Set(s);
                n.add(path);
                return n;
            });
        },
        [treeExpanded, treeCache, fileApi, setTreeExpanded],
    );

    // Auto-expand the tree along the current path so the active row is visible.
    useEffect(() => {
        const parts = currentPath.split('/').filter(Boolean);
        const ancestors = [];
        let acc = '';
        for (const p of parts) {
            acc += '/' + p;
            ancestors.push(acc);
        }
        ancestors.forEach((a) => {
            const isUnderRoot = TREE_ROOTS.some(
                (r) => a === r.path || a.startsWith(r.path + '/') || r.path.startsWith(a + '/'),
            );
            if (isUnderRoot && !treeExpanded.has(a) && a !== currentPath) {
                toggleTreeExpand(a);
            }
        });
    }, [currentPath]); // eslint-disable-line react-hooks/exhaustive-deps

    return { treeExpanded, treeCache, refreshTree, treeLoading, toggleTreeExpand };
}
