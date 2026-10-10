// DEPRECATED re-export. The saved-view stack lives in `components/ds/grid/`
// now, behind `useGridViews` — a page that reaches past it re-invents the
// envelope, which is exactly the divergence the list-page convergence removed.
//
// Still here only for the pages not yet on the shared chrome (Email, Jobs,
// Monitors, Telemetry). Delete this file once they are migrated; the broken
// imports are the point — they are the compile-time proof that nothing outside
// `ds/grid/` talks to the storage layer any more.
export { useTableViews, default } from '@/components/ds/grid/useTableViews';
