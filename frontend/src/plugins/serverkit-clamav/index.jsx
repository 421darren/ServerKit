// Malware Scanner UI, contributed through the extension system. Both halves
// live in this extension: the scanner/quarantine backend (the clamav_bp
// blueprint under the shared /api/v1/security prefix + ClamAVService /
// MalwareScanService / YaraScanService) under backend/, and the two security
// tabs here (components/ScannerTab.jsx + components/QuarantineTab.jsx + the
// extension's own API client). Imports go through 'serverkit-sdk' so the
// same source works baked in-tree (the panel's build-time glob) and as a
// runtime-ESM bundle once the extension leaves the tree (plan 52 Phase 2).
//
// The scan-history log, the security config store and the notification
// fan-out stay core (SecurityService) — this extension only adds the
// scanner + quarantine surfaces, slotted into the /security tab group.
import ScannerTab from './components/ScannerTab';
import QuarantineTab from './components/QuarantineTab';

export function ScannerTabPage() {
    return <ScannerTab />;
}

export function QuarantineTabPage() {
    return <QuarantineTab />;
}

// No default export on purpose: PluginLoader legacy-auto-renders any plugin
// default export globally. The route contributions resolve the NAMED exports
// via resolveComponent.
