// Fail2ban management UI, contributed through the extension system. Both
// halves live in this extension: the /api/v1/security/fail2ban blueprint
// under backend/ (management surface only — the status/probe + unban seam
// stays on the panel's core Fail2banJailService, so managed per-site jails
// keep working with this extension absent), and the tab here plus its own
// API client. Imports go through 'serverkit-sdk' so the panel resolves them
// to its own singletons via the import map.
//
// It's a single security tab-group route (security/fail2ban), so no
// tab-group shell or self-rendered sub-router is needed.
import Fail2banTab from './components/Fail2banTab';

export function Fail2banTabPage() {
    return <Fail2banTab />;
}

// No default export on purpose: PluginLoader legacy-auto-renders any plugin
// default export globally. The route contribution resolves the NAMED export
// via resolveComponent.
