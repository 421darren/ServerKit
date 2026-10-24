import { useCallback, useLayoutEffect, useRef } from 'react';

// A callback whose identity never changes but that always runs the latest
// `fn`. Pass it to memoized children (list rows) so a parent re-render does
// not re-render every row just because its handlers were re-created.
// Not for use during render: the latest `fn` is installed after commit.
export function useStableHandler(fn) {
    const ref = useRef(fn);
    useLayoutEffect(() => {
        ref.current = fn;
    });
    return useCallback((...args) => ref.current(...args), []);
}
