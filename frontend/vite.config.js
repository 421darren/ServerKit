/* global process */
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { VENDOR_IMPORTMAP } from './src/plugins/runtime/vendorManifest.js'

// Runtime-extension import map (plan 25 Decision 2). A runtime-loaded extension
// bundle externalizes exactly these bare specifiers and resolves them at load
// time to the panel's own singleton instances via the `/serverkit-vendor/*.mjs`
// shims (fed by src/plugins/runtime/vendorShare.js). Injected into index.html at
// BUILD time only: Vite's dev server does its own bare-specifier resolution, and
// runtime loading is a production concern (dev uses the build-time glob path).
// The map is inert for the host's own code (bundled to hashed relative chunks,
// never bare specifiers) — it only affects the extension blobs.
// Sourced from the ONE vendor manifest, so the import map, the shims under
// public/serverkit-vendor/ and vendorShare's namespace capture cannot drift
// apart. They previously did: two mapped specifiers had no shim at all.

function serverkitImportmap() {
    return {
        name: 'serverkit-vendor-importmap',
        apply: 'build',
        transformIndexHtml() {
            return [{
                tag: 'script',
                attrs: { type: 'importmap' },
                children: JSON.stringify(VENDOR_IMPORTMAP),
                injectTo: 'head-prepend',
            }]
        },
    }
}

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '')
    const frontendPort = Number(env.SERVERKIT_FRONTEND_PORT) || 41921
    const apiTarget = (env.VITE_API_URL || 'http://localhost:47927/api/v1').replace(/\/api\/v1\/?$/, '')

    const rawAllowedHosts = (env.VITE_ALLOWED_HOSTS || '').trim()
    let allowedHosts
    if (rawAllowedHosts === 'all') {
        allowedHosts = true
    } else if (rawAllowedHosts) {
        allowedHosts = rawAllowedHosts.split(',').map(s => s.trim()).filter(Boolean)
    }

    return {
        plugins: [react(), serverkitImportmap()],
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url)),
                // Stable import path for plugin code:
                //   import { api, useAuth } from 'serverkit-sdk';
                // Internal restructures of src/plugins/sdk are invisible
                // to plugins as long as the named exports stay stable.
                'serverkit-sdk': fileURLToPath(new URL('./src/plugins/sdk/index.js', import.meta.url)),
            },
            // Force every `react` / `react-dom` / `react-router-dom`
            // import (host code AND plugin code loaded via
            // import.meta.glob) to resolve to one copy. Without this
            // Vite can hand plugins a different React instance if dep
            // optimization runs mid-session, producing the
            // "Invalid hook call / ReactCurrentDispatcher is null"
            // crash inside the contributions hook.
            //
            // Do NOT add resolve.alias entries for these — aliasing to
            // the package directory bypasses Vite's optimizeDeps and
            // serves raw ESM, which (combined with pre-bundled
            // react-dom) recreates the same two-copies problem from the
            // other direction.
            // i18next/react-i18next join the list for the same reason: two
            // instances means an extension's t() reads an uninitialised store
            // and silently renders English forever (plan 79).
            dedupe: ['react', 'react-dom', 'react-router-dom', 'i18next', 'react-i18next'],
        },
        optimizeDeps: {
            // Pre-bundle the renderer at server start instead of
            // discovering it lazily. Lazy discovery is what triggers the
            // mid-session re-bundle that strands the open browser tab
            // on a stale React URL.
            include: ['react', 'react-dom', 'react-router-dom', 'i18next', 'react-i18next'],
        },
        server: {
            port: frontendPort,
            ...(allowedHosts !== undefined ? { allowedHosts } : {}),
            proxy: {
                '/api': {
                    target: apiTarget,
                    changeOrigin: true,
                },
                '/socket.io': {
                    target: apiTarget,
                    changeOrigin: true,
                    ws: true,
                },
            },
            // Enable polling for WSL (Windows filesystem doesn't support inotify)
            watch: {
                usePolling: true,
                interval: 1000,
            },
        },
        css: {
            preprocessorOptions: {
                scss: {
                    // Silence Dart Sass deprecation warnings for @import and slash-div
                    // These are expected during migration from LESS and will be addressed
                    // when moving to @use/@forward module system
                    silenceDeprecations: ['import', 'slash-div', 'legacy-js-api', 'global-builtin', 'color-functions', 'strict-unary'],
                },
            },
        },
        build: {
            sourcemap: false,
            rollupOptions: {
                output: {
                    // A group also captures its matched modules' dependencies,
                    // so priority decides who claims a shared one. React must
                    // win: with manualChunks, recharts pulled React core into
                    // vendor-charts and every page (Login included) preloaded
                    // the chart and flow libraries. Unmatched modules fall
                    // through to the default chunking.
                    codeSplitting: {
                        groups: [
                            { name: 'vendor-react', priority: 50, test: /[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|@remix-run[\\/]router|scheduler)[\\/]/ },
                            { name: 'vendor-icons', priority: 40, test: /[\\/]node_modules[\\/]lucide-react[\\/]/ },
                            { name: 'vendor-xterm', priority: 30, test: /[\\/]node_modules[\\/]@xterm[\\/]/ },
                            // Only the package itself: their small shared deps
                            // are also used by i18n, which would otherwise
                            // import (and preload) the whole chunk for them.
                            { name: 'vendor-flow', priority: 20, includeDependenciesRecursively: false, test: /[\\/]node_modules[\\/]@xyflow[\\/]/ },
                            { name: 'vendor-charts', priority: 10, includeDependenciesRecursively: false, test: /[\\/]node_modules[\\/]recharts[\\/]/ },
                        ],
                    },
                },
            },
        },
    }
})
