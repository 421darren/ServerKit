import { useCallback, useEffect, useRef } from 'react';

// Local port of the host's usePolling hook (src/hooks/usePolling.js) — the
// SDK does not export it, and a runtime-ESM extension cannot deep-import
// host modules. Same contract the tabs relied on in-tree:
//
//   * an in-flight guard — a slow endpoint never piles up concurrent calls;
//   * pause while the tab is hidden (visibilitychange);
//   * `callback` held in a ref so an inline arrow doesn't restart the timer;
//   * returns a stable refresh() that goes through the same guard.
export function usePolling(callback, intervalMs, options = {}) {
    const { enabled = true, immediate = true, pauseWhenHidden = true } = options;

    const callbackRef = useRef(callback);
    callbackRef.current = callback;

    const inFlightRef = useRef(false);
    const timerRef = useRef(null);
    const hiddenRef = useRef(false);

    const runOnce = useCallback(async () => {
        if (inFlightRef.current) return;
        inFlightRef.current = true;
        try {
            await callbackRef.current?.();
        } catch {
            // polling is best-effort; the callback owns its own error surface
        } finally {
            inFlightRef.current = false;
        }
    }, []);

    useEffect(() => {
        if (!enabled || !intervalMs) return undefined;

        let stopped = false;
        const tick = async () => {
            if (stopped) return;
            if (!hiddenRef.current) await runOnce();
            if (stopped) return;
            timerRef.current = window.setTimeout(tick, intervalMs);
        };

        let onVisibility;
        if (pauseWhenHidden && typeof document !== 'undefined') {
            hiddenRef.current = document.visibilityState === 'hidden';
            onVisibility = () => {
                hiddenRef.current = document.visibilityState === 'hidden';
            };
            document.addEventListener('visibilitychange', onVisibility);
        }

        if (immediate) {
            tick();
        } else {
            timerRef.current = window.setTimeout(tick, intervalMs);
        }

        return () => {
            stopped = true;
            if (onVisibility) document.removeEventListener('visibilitychange', onVisibility);
            if (timerRef.current) window.clearTimeout(timerRef.current);
            timerRef.current = null;
        };
    }, [enabled, intervalMs, immediate, pauseWhenHidden, runOnce]);

    return runOnce;
}

export default usePolling;
