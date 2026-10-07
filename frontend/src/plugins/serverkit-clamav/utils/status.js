// Local slice of the host's status → tone vocabulary (components/ds/status.js)
// — the SDK does not export statusKind, and a runtime-ESM extension cannot
// deep-import host modules. Only the severity words the scanner emits are
// mapped; anything unknown reads gray, exactly like the host table.
const STATUS_KIND = {
    critical: 'red',
    high: 'red',
    error: 'red',
    warning: 'amber',
    medium: 'amber',
    timeout: 'amber',
    cancelled: 'amber',
    completed: 'green',
    running: 'cyan',
    low: 'gray',
    unknown: 'gray',
};

/** Status → ds Pill kind. Unknown statuses read gray. */
export function statusKind(status) {
    return STATUS_KIND[String(status ?? '').toLowerCase().trim()] || 'gray';
}
