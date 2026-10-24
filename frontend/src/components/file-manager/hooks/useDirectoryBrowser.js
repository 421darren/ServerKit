import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useStableHandler } from '@/hooks/useStableHandler';
import { errorReason } from '@/utils/errorMessage';

function deriveParent(path) {
    if (!path || path === '/' || path === '') return null;
    // A Windows drive root ("C:/" or "C:") sits directly under the agent's
    // drive list, which the agent serves for the "/" path. Remote agents
    // emit forward-slash paths on the wire, so we only ever see "/" here.
    if (/^[A-Za-z]:\/?$/.test(path)) return '/';
    const trimmed = path.replace(/\/+$/, '');
    const idx = trimmed.lastIndexOf('/');
    if (idx <= 0) return '/';
    const parent = trimmed.slice(0, idx);
    // Keep a bare drive letter as a drive root ("C:" -> "C:/") so navigating
    // up doesn't hit Windows' "current directory on C:" semantics.
    if (/^[A-Za-z]:$/.test(parent)) return parent + '/';
    return parent;
}

export default function useDirectoryBrowser({
    fileApi,
    target,
    resetSelection,
    onNavigate,
    remoteGuard,
    toast,
    t,
}) {
    const [searchParams, setSearchParams] = useSearchParams();
    const previousTargetRef = useRef({ kind: target.kind, server_id: target.server_id });
    // ─── core ────────────────────────────────────────────
    const [currentPath, setCurrentPath] = useState(() => searchParams.get('path') || '/home');
    const [entries, setEntries] = useState([]);
    const [parentPath, setParentPath] = useState(null);
    const [loading, setLoading] = useState(true);
    // The open folder's own load failure, shown in the listing in place of
    // "This folder is empty". Navigation into a folder that fails still
    // toasts and steps back, since the previous folder is what stays shown.
    const [dirError, setDirError] = useState(null);
    const [showHidden, setShowHidden] = useState(false);

    // ─── search ──────────────────────────────────────────
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);

    // ─── history ─────────────────────────────────────────
    const [history, setHistory] = useState([currentPath]);
    const [historyIdx, setHistoryIdx] = useState(0);
    const navByHistory = useRef(false);
    const lastValidPathRef = useRef(null);
    // Only the newest browse may write: a slow answer for the folder the
    // user just left used to land last and navigate them back to it.
    const loadSeqRef = useRef(0);
    const activeRequest = useRef(null);
    activeRequest.current = { api: fileApi, path: currentPath };
    useEffect(
        () => () => {
            loadSeqRef.current++;
        },
        [],
    );

    useEffect(() => {
        const pathFromUrl = searchParams.get('path') || '/home';
        if (pathFromUrl !== currentPath) {
            setCurrentPath(pathFromUrl);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams]);

    useEffect(() => {
        const pathFromUrl = searchParams.get('path') || '/home';
        if (pathFromUrl === currentPath) return;

        const nextParams = new URLSearchParams(searchParams);
        nextParams.set('path', currentPath);
        setSearchParams(nextParams, { replace: true });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentPath]);

    // When the user switches to a remote target, jump to its first
    // advertised allowed_path so they don't see a "panel /home" view
    // that doesn't exist on the remote host.
    useEffect(() => {
        const previousTarget = previousTargetRef.current;
        const targetChanged =
            previousTarget.kind !== target.kind || previousTarget.server_id !== target.server_id;
        previousTargetRef.current = { kind: target.kind, server_id: target.server_id };

        if (!targetChanged) return;
        lastValidPathRef.current = null;
        onNavigate();
        resetSelection();

        const nextPath =
            target.kind === 'agent'
                ? target.allowedPaths?.[0] || currentPath
                : target.kind === 's3'
                  ? '/'
                  : '/home';
        navByHistory.current = nextPath !== currentPath;
        setHistory([nextPath]);
        setHistoryIdx(0);
        setCurrentPath(nextPath);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [target.kind, target.server_id]);

    // ─── load directory ──────────────────────────────────
    const loadDirectory = useStableHandler(async (path) => {
        if (path !== activeRequest.current.path || fileApi !== activeRequest.current.api) return;
        const seq = ++loadSeqRef.current;
        setLoading(true);
        setSearchResults(null);
        resetSelection();
        try {
            const data = await fileApi.browse(path, showHidden);
            if (
                seq !== loadSeqRef.current ||
                fileApi !== activeRequest.current.api ||
                path !== activeRequest.current.path
            )
                return;
            // Agent file:list returns {path, files: [...]} with a flat
            // entry shape; panel browseFiles returns {path, parent,
            // entries: [...]}. Normalize so the UI can keep using
            // entries/parent.
            const entriesList = data.entries || data.files || [];
            setEntries(entriesList);
            setParentPath(data.parent ?? deriveParent(data.path || path));
            setCurrentPath(data.path || path);
            lastValidPathRef.current = data.path || path;
            setDirError(null);
        } catch (error) {
            if (
                seq !== loadSeqRef.current ||
                fileApi !== activeRequest.current.api ||
                path !== activeRequest.current.path
            )
                return;
            if (lastValidPathRef.current !== null && path !== lastValidPathRef.current) {
                toast.error(
                    t('app.fileManager.failedToLoadDirectory', "Couldn't load the folder. {{message}}", {
                        message: errorReason(error),
                    }),
                );
                setCurrentPath(lastValidPathRef.current);
            } else {
                setEntries([]);
                setDirError(error);
            }
        } finally {
            if (
                seq === loadSeqRef.current &&
                fileApi === activeRequest.current.api &&
                path === activeRequest.current.path
            )
                setLoading(false);
        }
    });

    useEffect(() => {
        loadDirectory(currentPath);
    }, [currentPath, showHidden, fileApi, loadDirectory]);

    // history tracking
    useEffect(() => {
        if (navByHistory.current) {
            navByHistory.current = false;
            return;
        }
        setHistory((h) => {
            const trimmed = h.slice(0, historyIdx + 1);
            if (trimmed[trimmed.length - 1] === currentPath) return h;
            return [...trimmed, currentPath];
        });
        setHistoryIdx((i) => (history[i] === currentPath ? i : i + 1));
    }, [currentPath]); // eslint-disable-line react-hooks/exhaustive-deps

    // ─── search ──────────────────────────────────────────
    const clearSearch = () => {
        loadSeqRef.current++;
        setSearchResults(null);
        setSearchQuery('');
        setLoading(false);
    };
    const handleSearch = async () => {
        if (remoteGuard('search')) {
            setSearchResults([]);
            return;
        }
        if (!searchQuery.trim()) {
            clearSearch();
            return;
        }
        const seq = ++loadSeqRef.current;
        const path = currentPath;
        setLoading(true);
        try {
            const data = await fileApi.search(currentPath, searchQuery);
            if (
                seq !== loadSeqRef.current ||
                fileApi !== activeRequest.current.api ||
                path !== activeRequest.current.path
            )
                return;
            setSearchResults(data.results || []);
        } catch (error) {
            if (
                seq !== loadSeqRef.current ||
                fileApi !== activeRequest.current.api ||
                path !== activeRequest.current.path
            )
                return;
            toast.error(
                t('app.fileManager.searchFailed', "Couldn't search. {{message}}", {
                    message: errorReason(error),
                }),
            );
        } finally {
            if (
                seq === loadSeqRef.current &&
                fileApi === activeRequest.current.api &&
                path === activeRequest.current.path
            )
                setLoading(false);
        }
    };

    // ─── navigation ──────────────────────────────────────
    const navigateTo = (path) => {
        onNavigate();
        setCurrentPath(path);
    };

    const goBack = () => {
        if (historyIdx > 0) {
            onNavigate();
            navByHistory.current = true;
            setHistoryIdx(historyIdx - 1);
            setCurrentPath(history[historyIdx - 1]);
        }
    };
    const goForward = () => {
        if (historyIdx < history.length - 1) {
            onNavigate();
            navByHistory.current = true;
            setHistoryIdx(historyIdx + 1);
            setCurrentPath(history[historyIdx + 1]);
        }
    };
    const goUp = () => parentPath && navigateTo(parentPath);

    return {
        currentPath,
        entries,
        parentPath,
        loading,
        dirError,
        showHidden,
        setShowHidden,
        searchQuery,
        setSearchQuery,
        searchResults,
        clearSearch,
        history,
        historyIdx,
        loadDirectory,
        handleSearch,
        navigateTo,
        goBack,
        goForward,
        goUp,
    };
}
