// Relative-time and duration helpers: thin wrappers over `utils/intl.js`
// with two deliberate output shapes.
//
//   - timeAgo(iso)           compact: "just now", "4m", "3h", "2d", else a date
//   - formatRelativeTime     verbose, now fully localized by Intl:
//                            "4 minutes ago", "hace 4 minutos"
//   - formatDuration(secs)   "45s", "3m 20s"

import { formatRelative, formatRelativeShort, formatDuration as formatDurationIntl } from './intl.js';

export function timeAgo(iso) {
    return formatRelativeShort(iso);
}

export function formatRelativeTime(iso) {
    return formatRelative(iso);
}

export function formatDuration(seconds) {
    return formatDurationIntl(seconds);
}

export default timeAgo;
