// Runtime-ESM entry for ServerKit's no-rebuild loader (same pattern as
// serverkit-wordpress / serverkit-cloudflare-ops). No SCSS here on purpose:
// the panel's core _security.scss still styles the scanner/quarantine tabs
// (scan cards, sec-* helpers, quarantine table), so this bundle ships no
// styles of its own. Shared libs (react, react-router-dom, i18next,
// serverkit-sdk) are externalized by vite.config and resolved to the panel's
// singletons via its import map.

// Translations — registered against the PANEL's i18next singleton (shared via
// its vendor import map), additively; never init() or changeLanguage(), which
// the panel owns. Keys keep their historical app.* paths, so a panel that
// still carries them in core simply sees identical values.
import i18next from 'i18next';
import en from './locales/en.json';
import es from './locales/es.json';

for (const [language, bundle] of Object.entries({ en, es })) {
    i18next.addResourceBundle(language, 'translation', bundle, true, false);
}

// Named exports match the `component` values in plugin.json's route
// contributions; resolveComponent(slug, name) picks them up at runtime.
// Deliberately NO default export (PluginLoader auto-renders those globally).
export { ScannerTabPage, QuarantineTabPage } from './index.jsx';
