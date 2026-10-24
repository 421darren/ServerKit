import { useEffect, useState } from 'react';

// Storage can be unavailable (blocked site data, some private modes) and then
// throws on access. A preference is a convenience: it must never crash a page.
export function readStorage(key) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

export function writeStorage(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch {
        // Unavailable storage: the preference just isn't remembered.
    }
}

/**
 * useState mirrored into localStorage.
 *
 * @param {string} key storage key
 * @param {(stored: string|null) => any} init builds the initial value from
 *   the stored string (null when nothing is stored or storage is unavailable)
 * @param {(value: any) => string} [serialize] must be stable (module-level),
 *   it is an effect dependency
 */
export default function usePersistentState(key, init, serialize = String) {
    const [value, setValue] = useState(() => init(readStorage(key)));
    useEffect(() => {
        writeStorage(key, serialize(value));
    }, [key, value, serialize]);
    return [value, setValue];
}
