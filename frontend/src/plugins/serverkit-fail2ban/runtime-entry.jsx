// Runtime-ESM entry for ServerKit's no-rebuild loader (same pattern as
// serverkit-cloudflare-ops). No styles ship in this bundle: the panel core's
// _security.scss stays in the panel and styles these tabs (fail2ban-tab,
// f2b-*, sec-* classes), so the single dist/index.mjs the panel blob-imports
// carries only code + locales. Shared libs (react, react-router-dom, i18next,
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
export { Fail2banTabPage } from './index.jsx';
