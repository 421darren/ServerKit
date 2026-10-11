// Uptime percentages for the status pages. A missing value means "no data
// yet", never a perfect record, and a real 0 is a fully down component.

export function formatUptimePercent(value) {
    if (typeof value !== 'number' || Number.isNaN(value)) return '—';
    return `${value.toFixed(2)}%`;
}

// Mean over the components that have a figure; null when none do.
export function averageUptime(components, key = 'uptime_30d') {
    const values = (components || [])
        .map((component) => component?.[key])
        .filter((value) => typeof value === 'number' && !Number.isNaN(value));
    if (!values.length) return null;
    return values.reduce((total, value) => total + value, 0) / values.length;
}
