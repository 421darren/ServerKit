import De from "i18next";
import { jsxs as s, jsx as a, Fragment as Q } from "react/jsx-runtime";
import { forwardRef as Pe, createElement as ue, useRef as _, useCallback as ze, useEffect as ae, useState as d } from "react";
import { api as c, useConfirm as me, useTableSort as W, useColumnVisibility as M, useTableChrome as H, Button as g, Input as Ke, GridViewPicker as $, GridFilterButton as Y, GridToolsMenu as J, GridChips as G, DataTable as Z, DataTableFooter as X, GridFilterDrawer as ee, EmptyState as ye, Pill as Oe, formatBytes as _e } from "serverkit-sdk";
import { useTranslation as fe } from "react-i18next";
const Ve = {
  scannerTab: {
    curatedWebShellIndicatorsRunOn: "curated web-shell indicators run on every scan (engine:",
    customPath: "Custom Path",
    date: "Date",
    deleteCustomRuleFile: "Delete custom rule file {{name}}?",
    deleteRule: "Delete rule",
    deleteScannerRule: "Delete scanner rule",
    directory: "Directory",
    file: "File",
    filesScanned: "Files scanned:",
    fullScan: "Full Scan",
    inactiveYaraNotInstalled: "inactive — yara not installed",
    job: "Job:",
    match: "Match",
    noCustomRuleFilesUploadA: "No custom rule files. Upload a .yar file (max 64 KB) to extend the rule set.",
    noScansHaveBeenRunYet: "No scans have been run yet.",
    quickScan: "Quick Scan",
    rule: "Rule",
    scan: "Scan",
    scanASpecificDirectory: "Scan a specific directory",
    scanAnApp: "Scan an App",
    scanCommonWebDirectories: "Scan common web directories",
    scanEntireSystemSlow: "Scan entire system (slow)",
    scanInProgress: "Scan in Progress",
    scanning: "Scanning:",
    selectAnApp: "Select an app…",
    startAScanAboveToCheck: "Start a scan above to check for threats.",
    startScan: "Start Scan",
    started: "Started:",
    threats: "Threats",
    uploadYar: "Upload .yar",
    webShellDetectionRules: "Web-shell Detection Rules",
    webShellMalwareScanOfA: "Web-shell + malware scan of a docroot",
    webShellRules: "Web-shell Rules"
  },
  quarantineTab: {
    deleteFile: "Delete file",
    deleteQuarantinedFile: "Delete quarantined file",
    filename: "Filename",
    infectedFilesWillAppearHereWhen: "Infected files will appear here when detected",
    noFilesInQuarantine: "No files in quarantine",
    originalLocation: "Original Location",
    originalLocationUnknown: "Original location unknown",
    permanentlyDeleteThisCannotBeUndone: "Permanently delete {{filename}}? This cannot be undone.",
    quarantined: "Quarantined",
    restoreFile: "Restore file",
    restoreQuarantinedFile: "Restore quarantined file",
    restoreToOnlyDoThisFor: "Restore {{name}} to {{target}}? Only do this for false positives.",
    restoreToOriginalLocation: "Restore to original location"
  }
}, Ie = {
  app: Ve
}, Le = {
  scannerTab: {
    curatedWebShellIndicatorsRunOn: "indicadores seleccionados de web shells se ejecutan en cada análisis (motor:",
    customPath: "Ruta personalizada",
    date: "Fecha",
    deleteCustomRuleFile: "¿Eliminar el archivo de reglas personalizado {{name}}?",
    deleteRule: "Eliminar regla",
    deleteScannerRule: "Eliminar regla del analizador",
    directory: "Directorio",
    file: "Archivo",
    filesScanned: "Archivos analizados:",
    fullScan: "Análisis completo",
    inactiveYaraNotInstalled: "inactivo: yara no está instalado",
    job: "Trabajo:",
    match: "Coincidencia",
    noCustomRuleFilesUploadA: "No hay archivos de reglas personalizados. Sube un archivo .yar (máx. 64 KB) para ampliar el conjunto de reglas.",
    noScansHaveBeenRunYet: "Todavía no se ha ejecutado ningún análisis.",
    quickScan: "Análisis rápido",
    rule: "Regla",
    scan: "Analizar",
    scanASpecificDirectory: "Analizar un directorio específico",
    scanAnApp: "Analizar una app",
    scanCommonWebDirectories: "Analizar los directorios web habituales",
    scanEntireSystemSlow: "Analizar todo el sistema (lento)",
    scanInProgress: "Análisis en curso",
    scanning: "Analizando:",
    selectAnApp: "Selecciona una app…",
    startAScanAboveToCheck: "Inicia un análisis arriba para comprobar si hay amenazas.",
    startScan: "Iniciar análisis",
    started: "Iniciado:",
    threats: "Amenazas",
    uploadYar: "Subir .yar",
    webShellDetectionRules: "Reglas de detección de web shells",
    webShellMalwareScanOfA: "Análisis de web shells y malware de un docroot",
    webShellRules: "Reglas de web shells"
  },
  quarantineTab: {
    deleteFile: "Eliminar archivo",
    deleteQuarantinedFile: "Eliminar el archivo en cuarentena",
    filename: "Nombre del archivo",
    infectedFilesWillAppearHereWhen: "Los archivos infectados aparecerán aquí cuando se detecten",
    noFilesInQuarantine: "No hay archivos en cuarentena",
    originalLocation: "Ubicación original",
    originalLocationUnknown: "Ubicación original desconocida",
    permanentlyDeleteThisCannotBeUndone: "¿Eliminar permanentemente {{filename}}? Esta acción no se puede deshacer.",
    quarantined: "En cuarentena",
    restoreFile: "Restaurar archivo",
    restoreQuarantinedFile: "Restaurar el archivo en cuarentena",
    restoreToOnlyDoThisFor: "¿Restaurar {{name}} a {{target}}? Haz esto solo con falsos positivos.",
    restoreToOriginalLocation: "Restaurar a la ubicación original"
  }
}, Ee = {
  app: Le
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
var Qe = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round"
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Be = (n) => n.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const F = (n, l) => {
  const u = Pe(
    ({
      color: A = "currentColor",
      size: S = 24,
      strokeWidth: q = 2,
      absoluteStrokeWidth: o,
      className: h = "",
      children: p,
      ...k
    }, v) => ue(
      "svg",
      {
        ref: v,
        ...Qe,
        width: S,
        height: S,
        stroke: A,
        strokeWidth: o ? Number(q) * 24 / Number(S) : q,
        className: ["lucide", `lucide-${Be(n)}`, h].join(" "),
        ...k
      },
      [
        ...l.map(([w, f]) => ue(w, f)),
        ...Array.isArray(p) ? p : [p]
      ]
    )
  );
  return u.displayName = `${n}`, u;
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ue = F("Box", [
  [
    "path",
    {
      d: "M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z",
      key: "hh9hay"
    }
  ],
  ["path", { d: "m3.3 7 8.7 5 8.7-5", key: "g66t2b" }],
  ["path", { d: "M12 22V12", key: "d0xqtd" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const je = F("Download", [
  ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
  ["polyline", { points: "7 10 12 15 17 10", key: "2ggqvy" }],
  ["line", { x1: "12", x2: "12", y1: "15", y2: "3", key: "1vk2je" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const We = F("FileCode2", [
  ["path", { d: "M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4", key: "1pf5j1" }],
  ["path", { d: "M14 2v4a2 2 0 0 0 2 2h4", key: "tnqrlb" }],
  ["path", { d: "m5 12-3 3 3 3", key: "oke12k" }],
  ["path", { d: "m9 18 3-3-3-3", key: "112psh" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Me = F("FolderSearch", [
  ["circle", { cx: "17", cy: "17", r: "3", key: "18b49y" }],
  [
    "path",
    {
      d: "M10.7 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v4.1",
      key: "1bw5m7"
    }
  ],
  ["path", { d: "m21 21-1.5-1.5", key: "3sg1j" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const He = F("Radar", [
  ["path", { d: "M19.07 4.93A10 10 0 0 0 6.99 3.34", key: "z3du51" }],
  ["path", { d: "M4 6h.01", key: "oypzma" }],
  ["path", { d: "M2.29 9.62A10 10 0 1 0 21.31 8.35", key: "qzzz0" }],
  ["path", { d: "M16.24 7.76A6 6 0 1 0 8.23 16.67", key: "1yjesh" }],
  ["path", { d: "M12 18h.01", key: "mhygvu" }],
  ["path", { d: "M17.99 11.66A6 6 0 0 1 15.77 16.67", key: "1u2y91" }],
  ["circle", { cx: "12", cy: "12", r: "2", key: "1c9p78" }],
  ["path", { d: "m13.41 10.59 5.66-5.66", key: "mhq4k0" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const $e = F("Search", [
  ["circle", { cx: "11", cy: "11", r: "8", key: "4ej97u" }],
  ["path", { d: "m21 21-4.3-4.3", key: "1qie3q" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ye = F("ShieldCheck", [
  [
    "path",
    {
      d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
      key: "oel41y"
    }
  ],
  ["path", { d: "m9 12 2 2 4-4", key: "dzmm74" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Je = F("Trash2", [
  ["path", { d: "M3 6h18", key: "d0wm0j" }],
  ["path", { d: "M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6", key: "4alrt4" }],
  ["path", { d: "M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2", key: "v07s0e" }],
  ["line", { x1: "10", x2: "10", y1: "11", y2: "17", key: "1uufr5" }],
  ["line", { x1: "14", x2: "14", y1: "11", y2: "17", key: "xtxkd" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ge = F("Zap", [
  [
    "path",
    {
      d: "M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z",
      key: "1xq2db"
    }
  ]
]);
async function Ze() {
  return c.request("/security/clamav/status");
}
async function Xe() {
  return c.request("/security/clamav/install", { method: "POST" });
}
async function ea() {
  return c.request("/security/clamav/update", { method: "POST" });
}
async function aa() {
  return c.request("/security/clamav/start", { method: "POST" });
}
async function na(n) {
  return c.request("/security/scan/file", {
    method: "POST",
    body: { path: n }
  });
}
async function ta(n, l = !0) {
  return c.request("/security/scan/directory", {
    method: "POST",
    body: { path: n, recursive: l }
  });
}
async function sa() {
  return c.request("/security/scan/status");
}
async function ra() {
  return c.request("/security/scan/cancel", { method: "POST" });
}
async function ia(n = 50) {
  return c.request(`/security/scan/history?limit=${n}`);
}
async function ca() {
  return c.request("/security/scan/quick", { method: "POST" });
}
async function la() {
  return c.request("/security/scan/full", { method: "POST" });
}
async function oa(n) {
  return c.request(`/security/scan/app/${n}`, { method: "POST" });
}
async function da(n) {
  return c.request("/security/scan/job", {
    method: "POST",
    body: { path: n }
  });
}
async function ua() {
  return c.request("/security/yara/rules");
}
async function ha(n, l) {
  return c.request("/security/yara/rules", {
    method: "POST",
    body: { filename: n, content: l }
  });
}
async function pa(n) {
  return c.request(`/security/yara/rules/${encodeURIComponent(n)}`, {
    method: "DELETE"
  });
}
async function ma() {
  return c.request("/security/quarantine");
}
async function ya(n) {
  return c.request("/security/quarantine", {
    method: "POST",
    body: { path: n }
  });
}
async function fa(n) {
  return c.request(`/security/quarantine/${encodeURIComponent(n)}`, {
    method: "DELETE"
  });
}
async function ba(n) {
  return c.request(`/security/quarantine/${encodeURIComponent(n)}/restore`, {
    method: "POST"
  });
}
const y = {
  getClamAVStatus: Ze,
  installClamAV: Xe,
  updateVirusDefinitions: ea,
  startClamAV: aa,
  scanFile: na,
  scanDirectory: ta,
  getScanStatus: sa,
  cancelScan: ra,
  getScanHistory: ia,
  runQuickScan: ca,
  runFullScan: la,
  scanApp: oa,
  scanPathJob: da,
  getYaraRules: ua,
  uploadYaraRule: ha,
  deleteYaraRule: pa,
  getQuarantinedFiles: ma,
  quarantineFile: ya,
  deleteQuarantinedFile: fa,
  restoreQuarantinedFile: ba
}, ga = {
  critical: "red",
  high: "red",
  error: "red",
  warning: "amber",
  medium: "amber",
  timeout: "amber",
  cancelled: "amber",
  completed: "green",
  running: "cyan",
  low: "gray",
  unknown: "gray"
};
function Sa(n) {
  return ga[String(n ?? "").toLowerCase().trim()] || "gray";
}
function he(n, l, u = {}) {
  const { enabled: A = !0, immediate: S = !0, pauseWhenHidden: q = !0 } = u, o = _(n);
  o.current = n;
  const h = _(!1), p = _(null), k = _(!1), v = ze(async () => {
    var w;
    if (!h.current) {
      h.current = !0;
      try {
        await ((w = o.current) == null ? void 0 : w.call(o));
      } catch {
      } finally {
        h.current = !1;
      }
    }
  }, []);
  return ae(() => {
    if (!A || !l) return;
    let w = !1;
    const f = async () => {
      w || (k.current || await v(), !w && (p.current = window.setTimeout(f, l)));
    };
    let i;
    return q && typeof document < "u" && (k.current = document.visibilityState === "hidden", i = () => {
      k.current = document.visibilityState === "hidden";
    }, document.addEventListener("visibilitychange", i)), S ? f() : p.current = window.setTimeout(f, l), () => {
      w = !0, i && document.removeEventListener("visibilitychange", i), p.current && window.clearTimeout(p.current), p.current = null;
    };
  }, [A, l, S, q, v]), v;
}
const va = 5e3, wa = 3e3, ka = { critical: 0, high: 1, medium: 2, low: 3 }, be = { match: "all", rules: [] }, Ta = [
  {
    // The triage default: worst first. Sort only, and the empty rule set is
    // spelled out so switching here clears the previous view's filters.
    name: "Worst first",
    state: {
      sorts: [{ key: "severity", direction: "asc" }],
      hiddenKeys: [],
      groupBy: null,
      columnFilters: be
    }
  },
  {
    // What you act on before closing the tab. 'medium' is deliberately out:
    // the curated rules emit it as their default, so it is the bucket an
    // unclassified match lands in rather than a judgement about the file.
    name: "Critical & high",
    state: {
      sorts: [{ key: "severity", direction: "asc" }],
      hiddenKeys: [],
      groupBy: null,
      columnFilters: {
        match: "all",
        rules: [{ id: "fs1", field: "severity", op: "any", value: ["critical", "high"] }]
      }
    }
  },
  {
    // The curated web-shell pass on its own — a backdoor in a docroot, not
    // a known-malware signature. Grouped by file through the sort, because
    // one shell usually trips several rules and you quarantine the FILE.
    name: "Web-shell hits",
    state: {
      sorts: [{ key: "file", direction: "asc" }],
      hiddenKeys: [],
      groupBy: null,
      columnFilters: {
        match: "all",
        rules: [{ id: "fw1", field: "source", op: "any", value: ["yara"] }]
      }
    }
  }
], Na = [
  {
    name: "Newest first",
    state: {
      sorts: [{ key: "date", direction: "desc" }],
      hiddenKeys: [],
      groupBy: null,
      columnFilters: be
    }
  },
  {
    // Scans that actually found something — the audit trail you re-read
    // after an incident. A scan with no infected list reads 0 threats, so
    // `over 0` can only ever be a real hit.
    name: "Threats found",
    state: {
      sorts: [{ key: "date", direction: "desc" }],
      hiddenKeys: [],
      groupBy: null,
      columnFilters: {
        match: "all",
        rules: [{ id: "hs1", field: "threats", op: "gt", value: 0 }]
      }
    }
  },
  {
    // A scan that never finished proves nothing about the directory it was
    // pointed at — 'completed with 0 threats' and 'timed out' look equally
    // green from a distance, and only one of them is an answer.
    name: "Did not finish",
    state: {
      sorts: [{ key: "date", direction: "desc" }],
      hiddenKeys: [],
      groupBy: null,
      columnFilters: {
        match: "all",
        rules: [{
          id: "hf1",
          field: "status",
          op: "any",
          value: ["error", "timeout", "cancelled"]
        }]
      }
    }
  }
], Ca = () => {
  const { t: n } = fe(), { confirm: l } = me(), [u, A] = d({ status: "idle" }), [S, q] = d("/var/www"), [o, h] = d(!1), [p, k] = d(!1), [v, w] = d([]), [f, i] = d(null), [B, ne] = d([]), [m, t] = d(""), [T, P] = d(null), [te, se] = d(null), [V, I] = d([]), [re, ie] = d(null), L = W({ storageKey: "serverkit-table-scanner-findings-sort" }), ce = M({ storageKey: "serverkit-table-scanner-findings-cols" }), E = W({ storageKey: "serverkit-table-scanner-history-sort" }), le = M({ storageKey: "serverkit-table-scanner-history-cols" }), [N, ge] = d(null), [oe, Se] = d(!1), de = _(null);
  ae(() => {
    z(), U(), ve();
  }, []), he(z, va, { immediate: !1 });
  async function z() {
    try {
      const e = await y.getScanStatus();
      A(e), e.status === "completed" && Array.isArray(e.findings) && I(e.findings);
    } catch (e) {
      console.error("Failed to load scan status:", e);
    }
  }
  async function U() {
    try {
      const e = await y.getScanHistory(20);
      w(e.scans || []);
    } catch (e) {
      console.error("Failed to load scan history:", e);
    }
  }
  async function ve() {
    try {
      const e = await c.getApps();
      ne(e.apps || []);
    } catch (e) {
      console.error("Failed to load apps:", e);
    }
  }
  async function j() {
    try {
      const e = await y.getYaraRules();
      ge(e);
    } catch (e) {
      i({ type: "error", text: e.message });
    }
  }
  function we(e) {
    se(e);
  }
  he(async () => {
    var e;
    try {
      const r = await c.getJob(te), b = r.job || r;
      if (P(b), !["succeeded", "failed", "cancelled"].includes(b.status)) return;
      if (se(null), b.status === "succeeded" && ((e = b.result) != null && e.findings)) {
        I(b.result.findings);
        const D = b.result.findings.length;
        i({
          type: D > 0 ? "error" : "success",
          text: D > 0 ? `Scan finished: ${D} finding(s) — review below` : "Scan finished: no threats found"
        });
      } else b.status === "failed" && i({ type: "error", text: b.error_message || "Scan job failed" });
      z(), U();
    } catch (r) {
      console.error("Failed to poll scan job:", r);
    }
  }, wa, { enabled: !!te, immediate: !1 });
  async function ke() {
    if (m) {
      h(!0), i(null);
      try {
        const e = await y.scanApp(m);
        P({ id: e.job_id, status: "pending" }), i({ type: "success", text: `Scan queued for ${e.path || "app docroot"}` }), we(e.job_id);
      } catch (e) {
        i({ type: "error", text: e.message });
      } finally {
        h(!1);
      }
    }
  }
  async function K(e) {
    h(!0), i(null);
    try {
      let r;
      e === "quick" ? r = await y.runQuickScan() : e === "full" ? r = await y.runFullScan() : r = await y.scanDirectory(S), i({ type: "success", text: r.message }), z();
    } catch (r) {
      i({ type: "error", text: r.message });
    } finally {
      h(!1);
    }
  }
  async function Te() {
    k(!0), i(null);
    try {
      const e = await y.updateVirusDefinitions();
      i({ type: e.success ? "success" : "error", text: e.message || e.error });
    } catch (e) {
      i({ type: "error", text: e.message });
    } finally {
      k(!1);
    }
  }
  async function Ne() {
    try {
      await y.cancelScan(), z();
    } catch (e) {
      i({ type: "error", text: e.message });
    }
  }
  async function Ce(e) {
    ie(e.file);
    try {
      await y.quarantineFile(e.file), I((r) => r.filter((b) => b.file !== e.file)), i({ type: "success", text: `Quarantined ${e.file}` });
    } catch (r) {
      i({ type: "error", text: r.message });
    } finally {
      ie(null);
    }
  }
  async function Re() {
    const e = !oe;
    Se(e), e && !N && j();
  }
  async function qe(e) {
    var b;
    const r = (b = e.target.files) == null ? void 0 : b[0];
    if (e.target.value = "", !!r) {
      if (!r.name.endsWith(".yar")) {
        i({ type: "error", text: "Only .yar rule files are accepted" });
        return;
      }
      if (r.size > 64 * 1024) {
        i({ type: "error", text: "Rule file exceeds the 64 KB limit" });
        return;
      }
      try {
        const D = await r.text();
        await y.uploadYaraRule(r.name, D), i({ type: "success", text: `Rule file ${r.name} uploaded` }), j();
      } catch (D) {
        i({ type: "error", text: D.message });
      }
    }
  }
  async function Fe(e) {
    if (await l({
      title: n("app.scannerTab.deleteScannerRule", "Delete scanner rule"),
      message: n("app.scannerTab.deleteCustomRuleFile", "Delete custom rule file {{name}}?", { name: e }),
      confirmText: n("app.scannerTab.deleteRule", "Delete rule")
    }))
      try {
        await y.deleteYaraRule(e), j();
      } catch (r) {
        i({ type: "error", text: r.message });
      }
  }
  const x = u.status === "running", O = T && ["pending", "running"].includes(T.status), Ae = [
    {
      key: "rule",
      headerKey: "app.scannerTab.rule",
      header: "Rule",
      sortable: !0,
      hideable: !1,
      type: "text",
      value: (e) => e.rule || "",
      sortValue: (e) => e.rule || "",
      cellClassName: "sk-cell-mono",
      render: (e) => /* @__PURE__ */ a("span", { title: e.description, children: e.rule })
    },
    {
      key: "severity",
      headerKey: "common.labels.severity",
      header: "Severity",
      sortable: !0,
      type: "enum",
      // Both accessors spelled out: `value` is the word a rule matches,
      // `sortValue` is the urgency rank the table orders by. A numeric
      // sortValue on its own would type the column `num`, and every
      // severity preset would then match exactly zero rows.
      value: (e) => e.severity || "unknown",
      sortValue: (e) => ka[e.severity] ?? 9,
      enumOrder: ["critical", "high", "medium", "low"],
      render: (e) => /* @__PURE__ */ a("span", { className: `sec-state sec-state--${Sa(e.severity)}`, children: e.severity })
    },
    {
      key: "file",
      headerKey: "app.scannerTab.file",
      header: "File",
      sortable: !0,
      type: "text",
      value: (e) => e.file || "",
      sortValue: (e) => e.file || "",
      cellClassName: "sk-cell-mono sec-path sec-path--red",
      render: (e) => /* @__PURE__ */ a("span", { title: e.file, children: e.file })
    },
    {
      key: "match",
      headerKey: "app.scannerTab.match",
      header: "Match",
      // The row field is `matched`, not `match`, so without an accessor
      // the column has nothing behind it: no filter, and an export column
      // of empty strings.
      type: "text",
      value: (e) => e.matched || "",
      cellClassName: "sk-cell-mono scan-snippet",
      render: (e) => e.matched || "—"
    },
    {
      key: "source",
      headerKey: "common.labels.source",
      header: "Source",
      sortable: !0,
      type: "enum",
      value: (e) => e.source || "unknown",
      sortValue: (e) => e.source || "",
      enumOrder: ["yara", "clamav"],
      render: (e) => /* @__PURE__ */ a("span", { className: "sec-state sec-state--gray", children: e.source })
    },
    {
      key: "actions",
      header: "",
      sortable: !1,
      hideable: !1,
      cellClassName: "sec-rowend",
      render: (e) => /* @__PURE__ */ a(
        g,
        {
          variant: "destructive",
          size: "sm",
          onClick: () => Ce(e),
          disabled: re === e.file,
          children: re === e.file ? "Moving…" : "Quarantine"
        }
      )
    }
  ], xe = [
    {
      key: "date",
      headerKey: "app.scannerTab.date",
      header: "Date",
      sortable: !0,
      hideable: !1,
      // Declared, not inferred: the sorter wants epoch ms, and letting
      // that number type the column would offer "is under 1754…" instead
      // of a date picker — and make any date rule match nothing.
      type: "date",
      value: (e) => e.started_at || null,
      sortValue: (e) => {
        const r = new Date(e.started_at).getTime();
        return Number.isNaN(r) ? null : r;
      },
      cellClassName: "sk-cell-mono sec-faint",
      render: (e) => new Date(e.started_at).toLocaleString()
    },
    {
      key: "directory",
      headerKey: "app.scannerTab.directory",
      header: "Directory",
      sortable: !0,
      sortValue: (e) => e.directory || "",
      cellClassName: "sk-cell-mono sec-path",
      render: (e) => e.directory
    },
    {
      key: "status",
      headerKey: "common.labels.status",
      header: "Status",
      sortable: !0,
      type: "enum",
      value: (e) => e.status || "unknown",
      sortValue: (e) => e.status || "",
      enumOrder: ["completed", "running", "error", "timeout", "cancelled"],
      render: (e) => /* @__PURE__ */ a(Oe, { kind: e.status === "completed" ? "green" : e.status === "error" ? "red" : "amber", children: e.status })
    },
    {
      key: "threats",
      headerKey: "app.scannerTab.threats",
      header: "Threats",
      sortable: !0,
      type: "num",
      // A scan with no infected list reads 0 rather than blank, so the
      // "over 0" preset can only ever be a real hit — a scan that failed
      // before it wrote a list can never look like a clean one.
      value: (e) => {
        var r;
        return ((r = e.infected_files) == null ? void 0 : r.length) ?? 0;
      },
      sortValue: (e) => {
        var r;
        return ((r = e.infected_files) == null ? void 0 : r.length) ?? 0;
      },
      render: (e) => {
        var r;
        return ((r = e.infected_files) == null ? void 0 : r.length) > 0 ? /* @__PURE__ */ s("span", { className: "sec-state sec-state--red", children: [
          e.infected_files.length,
          " found"
        ] }) : /* @__PURE__ */ a("span", { className: "sec-state sec-state--green", children: "clean" });
      }
    }
  ], C = H({
    columns: Ae,
    rows: V,
    viewPageKey: "security-scanner-findings",
    urlScope: "findings",
    builtinViews: Ta,
    noun: "findings",
    sorts: L.sorts,
    setSorts: L.setSorts,
    hiddenKeys: ce.hiddenKeys,
    setHiddenKeys: ce.setHiddenKeys
  }), R = H({
    columns: xe,
    rows: v,
    viewPageKey: "security-scan-history",
    urlScope: "history",
    builtinViews: Na,
    noun: "scans",
    sorts: E.sorts,
    setSorts: E.setSorts,
    hiddenKeys: le.hiddenKeys,
    setHiddenKeys: le.setHiddenKeys
  });
  return /* @__PURE__ */ s("div", { className: "scanner-tab", children: [
    f && /* @__PURE__ */ a("div", { className: `alert alert-${f.type === "success" ? "success" : "danger"}`, children: f.text }),
    /* @__PURE__ */ s("div", { className: "scan-options", children: [
      /* @__PURE__ */ s("div", { className: "scan-card scan-card--quick", onClick: () => !x && !o && K("quick"), children: [
        /* @__PURE__ */ a("div", { className: "scan-card-icon", children: /* @__PURE__ */ a(Ge, { size: 20 }) }),
        /* @__PURE__ */ a("h4", { children: n("app.scannerTab.quickScan", "Quick Scan") }),
        /* @__PURE__ */ a("span", { className: "scan-desc", children: n("app.scannerTab.scanCommonWebDirectories", "Scan common web directories") }),
        /* @__PURE__ */ a(
          g,
          {
            variant: "default",
            size: "sm",
            onClick: (e) => {
              e.stopPropagation(), K("quick");
            },
            disabled: x || o,
            children: n("app.scannerTab.startScan", "Start Scan")
          }
        )
      ] }),
      /* @__PURE__ */ s("div", { className: "scan-card scan-card--full", onClick: () => !x && !o && K("full"), children: [
        /* @__PURE__ */ a("div", { className: "scan-card-icon", children: /* @__PURE__ */ a(He, { size: 20 }) }),
        /* @__PURE__ */ a("h4", { children: n("app.scannerTab.fullScan", "Full Scan") }),
        /* @__PURE__ */ a("span", { className: "scan-desc", children: n("app.scannerTab.scanEntireSystemSlow", "Scan entire system (slow)") }),
        /* @__PURE__ */ a(
          g,
          {
            variant: "default",
            size: "sm",
            onClick: (e) => {
              e.stopPropagation(), K("full");
            },
            disabled: x || o,
            children: n("app.scannerTab.startScan", "Start Scan")
          }
        )
      ] }),
      /* @__PURE__ */ s("div", { className: "scan-card scan-card--custom", children: [
        /* @__PURE__ */ a("div", { className: "scan-card-icon", children: /* @__PURE__ */ a(Me, { size: 20 }) }),
        /* @__PURE__ */ a("h4", { children: n("app.scannerTab.customPath", "Custom Path") }),
        /* @__PURE__ */ a("span", { className: "scan-desc", children: n("app.scannerTab.scanASpecificDirectory", "Scan a specific directory") }),
        /* @__PURE__ */ s("div", { className: "scan-custom-input", children: [
          /* @__PURE__ */ a(
            Ke,
            {
              type: "text",
              value: S,
              onChange: (e) => q(e.target.value),
              placeholder: "/path/to/scan",
              disabled: x,
              onClick: (e) => e.stopPropagation()
            }
          ),
          /* @__PURE__ */ a(
            g,
            {
              variant: "default",
              size: "sm",
              onClick: () => K("custom"),
              disabled: x || o || !S,
              children: n("app.scannerTab.scan", "Scan")
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ s("div", { className: "scan-card scan-card--app", children: [
        /* @__PURE__ */ a("div", { className: "scan-card-icon", children: /* @__PURE__ */ a(Ue, { size: 20 }) }),
        /* @__PURE__ */ a("h4", { children: n("app.scannerTab.scanAnApp", "Scan an App") }),
        /* @__PURE__ */ a("span", { className: "scan-desc", children: n("app.scannerTab.webShellMalwareScanOfA", "Web-shell + malware scan of a docroot") }),
        /* @__PURE__ */ s("div", { className: "scan-custom-input", children: [
          /* @__PURE__ */ s(
            "select",
            {
              className: "scan-app-select",
              value: m,
              onChange: (e) => t(e.target.value),
              disabled: O,
              children: [
                /* @__PURE__ */ a("option", { value: "", children: n("app.scannerTab.selectAnApp", "Select an app…") }),
                B.map((e) => /* @__PURE__ */ a("option", { value: e.id, children: e.name }, e.id))
              ]
            }
          ),
          /* @__PURE__ */ a(
            g,
            {
              variant: "default",
              size: "sm",
              onClick: ke,
              disabled: !m || o || O,
              children: O ? "Running…" : "Scan"
            }
          )
        ] })
      ] })
    ] }),
    /* @__PURE__ */ s("div", { className: "scan-toolbar", children: [
      /* @__PURE__ */ s(g, { variant: "outline", size: "sm", onClick: Re, children: [
        /* @__PURE__ */ a(We, { size: 14 }),
        n("app.scannerTab.webShellRules", "Web-shell Rules")
      ] }),
      /* @__PURE__ */ s(g, { variant: "outline", size: "sm", onClick: Te, disabled: p, children: [
        /* @__PURE__ */ a(je, { size: 14 }),
        p ? "Updating..." : "Update Definitions"
      ] })
    ] }),
    oe && /* @__PURE__ */ s("div", { className: "card sec-flush yara-rules-card", children: [
      /* @__PURE__ */ s("div", { className: "card-header", children: [
        /* @__PURE__ */ s("h3", { children: [
          n("app.scannerTab.webShellDetectionRules", "Web-shell Detection Rules"),
          N && /* @__PURE__ */ s("span", { className: "sec-count", children: [
            " · ",
            N.builtin_count,
            " builtin"
          ] })
        ] }),
        /* @__PURE__ */ s("div", { className: "card-actions", children: [
          /* @__PURE__ */ a(
            "input",
            {
              ref: de,
              type: "file",
              accept: ".yar",
              className: "yara-file-input",
              onChange: qe
            }
          ),
          /* @__PURE__ */ a(g, { variant: "outline", size: "sm", onClick: () => {
            var e;
            return (e = de.current) == null ? void 0 : e.click();
          }, children: n("app.scannerTab.uploadYar", "Upload .yar") })
        ] })
      ] }),
      /* @__PURE__ */ a("div", { className: "card-body", children: N ? /* @__PURE__ */ s(Q, { children: [
        /* @__PURE__ */ s("p", { className: "sec-hint sec-hint--lead", children: [
          N.builtin_count,
          " ",
          n("app.scannerTab.curatedWebShellIndicatorsRunOn", "curated web-shell indicators run on every scan (engine:"),
          " ",
          /* @__PURE__ */ a("span", { className: "sec-mono", children: N.engine }),
          ").",
          N.engine === "fallback" && " Install yara to enable custom .yar rule files."
        ] }),
        N.custom.length === 0 ? /* @__PURE__ */ a("p", { className: "sec-hint", children: n("app.scannerTab.noCustomRuleFilesUploadA", "No custom rule files. Upload a .yar file (max 64 KB) to extend the rule set.") }) : /* @__PURE__ */ a("div", { className: "yara-custom-list", children: N.custom.map((e) => /* @__PURE__ */ s("div", { className: "yara-custom-item", children: [
          /* @__PURE__ */ a("span", { className: "sec-mono", children: e.name }),
          /* @__PURE__ */ s("span", { className: "sec-faint sec-mono", children: [
            e.size,
            " B"
          ] }),
          !N.custom_rules_active && /* @__PURE__ */ a("span", { className: "sec-state sec-state--gray", children: n("app.scannerTab.inactiveYaraNotInstalled", "inactive — yara not installed") }),
          /* @__PURE__ */ a(g, { variant: "ghost", size: "sm", onClick: () => Fe(e.name), children: /* @__PURE__ */ a(Je, { size: 14 }) })
        ] }, e.name)) })
      ] }) : /* @__PURE__ */ a("div", { className: "loading-sm", children: n("common.loading", "Loading…") }) })
    ] }),
    (x || O) && /* @__PURE__ */ s("div", { className: "card scan-progress", children: [
      /* @__PURE__ */ s("div", { className: "card-header", children: [
        /* @__PURE__ */ a("h3", { children: n("app.scannerTab.scanInProgress", "Scan in Progress") }),
        x && /* @__PURE__ */ a(g, { variant: "destructive", size: "sm", onClick: Ne, children: n("common.actions.cancel", "Cancel") })
      ] }),
      /* @__PURE__ */ a("div", { className: "card-body", children: /* @__PURE__ */ s("div", { className: "progress-info", children: [
        /* @__PURE__ */ a("div", { className: "spinner" }),
        /* @__PURE__ */ s("div", { children: [
          u.directory && /* @__PURE__ */ s("p", { children: [
            /* @__PURE__ */ a("strong", { children: n("app.scannerTab.scanning", "Scanning:") }),
            " ",
            /* @__PURE__ */ a("span", { className: "sec-mono", children: u.directory })
          ] }),
          u.started_at && /* @__PURE__ */ s("p", { children: [
            /* @__PURE__ */ a("strong", { children: n("app.scannerTab.started", "Started:") }),
            " ",
            /* @__PURE__ */ a("span", { className: "sec-mono", children: new Date(u.started_at).toLocaleString() })
          ] }),
          O && /* @__PURE__ */ s("p", { children: [
            /* @__PURE__ */ a("strong", { children: n("app.scannerTab.job", "Job:") }),
            " ",
            /* @__PURE__ */ s("span", { className: "sec-mono", children: [
              T.id,
              " · ",
              T.status
            ] })
          ] }),
          u.files_scanned > 0 && /* @__PURE__ */ s("p", { children: [
            /* @__PURE__ */ a("strong", { children: n("app.scannerTab.filesScanned", "Files scanned:") }),
            " ",
            /* @__PURE__ */ a("span", { className: "sec-mono", children: u.files_scanned })
          ] })
        ] })
      ] }) })
    ] }),
    V.length > 0 && /* @__PURE__ */ s("div", { className: "card sec-flush scan-findings", children: [
      /* @__PURE__ */ s("div", { className: "card-header", children: [
        /* @__PURE__ */ a(
          $,
          {
            views: C.views,
            label: "findings",
            onCreate: C.createView,
            actions: /* @__PURE__ */ s(Q, { children: [
              /* @__PURE__ */ a(
                Y,
                {
                  count: C.filterCount,
                  onClick: () => C.setDrawerOpen(!0)
                }
              ),
              /* @__PURE__ */ a(J, { ...C.toolsProps, onRefresh: z })
            ] })
          }
        ),
        /* @__PURE__ */ a("div", { className: "sec-tableactions", children: /* @__PURE__ */ a(g, { variant: "outline", size: "sm", onClick: () => I([]), children: n("common.actions.dismiss", "Dismiss") }) })
      ] }),
      /* @__PURE__ */ a(G, { ...C.chipProps }),
      /* @__PURE__ */ a(
        Z,
        {
          columns: C.columns,
          data: V,
          keyField: (e) => `${e.file}-${e.rule}-${e.source}`,
          sorts: L.sorts,
          onSortsChange: L.setSorts,
          ...C.tableProps,
          footer: /* @__PURE__ */ a(
            X,
            {
              shown: C.shownCount,
              total: V.length,
              noun: "finding"
            }
          )
        }
      ),
      /* @__PURE__ */ a(ee, { ...C.drawerProps })
    ] }),
    /* @__PURE__ */ s("div", { className: "card sec-flush", children: [
      /* @__PURE__ */ a("div", { className: "card-header", children: /* @__PURE__ */ a(
        $,
        {
          views: R.views,
          label: "scans",
          onCreate: R.createView,
          actions: /* @__PURE__ */ s(Q, { children: [
            /* @__PURE__ */ a(
              Y,
              {
                count: R.filterCount,
                onClick: () => R.setDrawerOpen(!0)
              }
            ),
            /* @__PURE__ */ a(J, { ...R.toolsProps, onRefresh: U })
          ] })
        }
      ) }),
      /* @__PURE__ */ a(G, { ...R.chipProps }),
      v.length === 0 ? /* @__PURE__ */ a("div", { className: "card-body", children: /* @__PURE__ */ a(
        ye,
        {
          icon: $e,
          title: n("app.scannerTab.noScansHaveBeenRunYet", "No scans have been run yet."),
          description: n("app.scannerTab.startAScanAboveToCheck", "Start a scan above to check for threats.")
        }
      ) }) : /* @__PURE__ */ a(
        Z,
        {
          columns: R.columns,
          data: v,
          keyField: (e) => `${e.started_at}-${e.directory}`,
          sorts: E.sorts,
          onSortsChange: E.setSorts,
          ...R.tableProps,
          footer: /* @__PURE__ */ a(
            X,
            {
              shown: R.shownCount,
              total: v.length,
              noun: "scan"
            }
          )
        }
      ),
      /* @__PURE__ */ a(ee, { ...R.drawerProps })
    ] })
  ] });
}, pe = { match: "all", rules: [] }, Ra = [
  {
    // The landing view: quarantine is an event log, so the newest catch is
    // the one nobody has looked at yet.
    name: "Newest first",
    state: {
      sorts: [{ key: "quarantined", direction: "desc" }],
      hiddenKeys: [],
      columnFilters: pe
    }
  },
  {
    // Nothing ages out of quarantine on its own, so this is the view you
    // open when the partition holding it starts to fill.
    name: "Largest first",
    state: {
      sorts: [{ key: "size", direction: "desc" }],
      hiddenKeys: [],
      columnFilters: pe
    }
  },
  {
    // Restore needs the sidecar that recorded where the file came from —
    // without it the Restore button is dead and delete is the only move.
    // The rule is "an absolute path was recorded": the quarantine service
    // writes os.path.abspath(), and a row with no sidecar reads '', which
    // starts with nothing.
    name: "Restorable",
    state: {
      sorts: [{ key: "quarantined", direction: "desc" }],
      hiddenKeys: [],
      columnFilters: {
        match: "all",
        rules: [{ id: "qr1", field: "original", op: "starts", value: "/" }]
      }
    }
  }
], qa = () => {
  const { t: n } = fe(), { confirm: l } = me(), [u, A] = d([]), [S, q] = d(!0), [o, h] = d(null), { sorts: p, setSorts: k } = W({ storageKey: "serverkit-table-quarantine-sort" }), {
    hiddenKeys: v,
    setHiddenKeys: w
  } = M({ storageKey: "serverkit-table-quarantine-cols" });
  ae(() => {
    f();
  }, []);
  async function f() {
    try {
      const t = await y.getQuarantinedFiles();
      A(t.files || []);
    } catch (t) {
      console.error("Failed to load quarantined files:", t);
    } finally {
      q(!1);
    }
  }
  async function i(t) {
    if (await l({
      title: n("app.quarantineTab.deleteQuarantinedFile", "Delete quarantined file"),
      message: n("app.quarantineTab.permanentlyDeleteThisCannotBeUndone", "Permanently delete {{filename}}? This cannot be undone.", { filename: t }),
      confirmText: n("app.quarantineTab.deleteFile", "Delete file")
    }))
      try {
        await y.deleteQuarantinedFile(t), h({ type: "success", text: "File deleted" }), f();
      } catch (T) {
        h({ type: "error", text: T.message });
      }
  }
  async function B(t) {
    const T = t.original_path || "its original location";
    if (await l({
      title: n("app.quarantineTab.restoreQuarantinedFile", "Restore quarantined file"),
      message: n("app.quarantineTab.restoreToOnlyDoThisFor", "Restore {{name}} to {{target}}? Only do this for false positives.", { name: t.name, target: T }),
      confirmText: n("app.quarantineTab.restoreFile", "Restore file"),
      variant: "warning"
    }))
      try {
        const P = await y.restoreQuarantinedFile(t.name);
        h({ type: "success", text: P.message || "File restored" }), f();
      } catch (P) {
        h({ type: "error", text: P.message });
      }
  }
  const m = H({
    columns: [
      {
        key: "filename",
        headerKey: "app.quarantineTab.filename",
        header: "Filename",
        sortable: !0,
        hideable: !1,
        type: "text",
        value: (t) => t.name || "",
        sortValue: (t) => t.name || "",
        cellClassName: "sk-cell-mono sec-path sec-path--red",
        render: (t) => t.name
      },
      {
        key: "original",
        headerKey: "app.quarantineTab.originalLocation",
        header: "Original Location",
        sortable: !0,
        type: "text",
        // '' rather than null when the sidecar is missing: the Restorable
        // view asks whether the recorded path is absolute, and a null would
        // make that rule compare against the string "null".
        value: (t) => t.original_path || "",
        sortValue: (t) => t.original_path || "",
        cellClassName: "sk-cell-mono sec-path sec-faint",
        render: (t) => /* @__PURE__ */ a("span", { title: t.original_path || "", children: t.original_path || "—" })
      },
      {
        key: "size",
        headerKey: "common.labels.size",
        header: "Size",
        sortable: !0,
        type: "num",
        value: (t) => t.size == null ? null : Number(t.size),
        sortValue: (t) => t.size == null ? null : Number(t.size),
        cellClassName: "sk-cell-mono",
        render: (t) => _e(t.size, { defaultValue: "0 B" })
      },
      {
        key: "quarantined",
        headerKey: "app.quarantineTab.quarantined",
        header: "Quarantined",
        sortable: !0,
        // Declared, not inferred: the sorter wants epoch ms, and letting
        // that number type the column would offer "is under 1754…" instead
        // of a date picker — and make any date rule match nothing.
        type: "date",
        value: (t) => t.quarantined_at || null,
        sortValue: (t) => {
          const T = new Date(t.quarantined_at).getTime();
          return Number.isNaN(T) ? null : T;
        },
        cellClassName: "sk-cell-mono sec-faint",
        render: (t) => new Date(t.quarantined_at).toLocaleString()
      },
      {
        key: "actions",
        headerKey: "common.labels.actions",
        header: "Actions",
        sortable: !1,
        hideable: !1,
        render: (t) => /* @__PURE__ */ s("div", { className: "quarantine-actions", children: [
          /* @__PURE__ */ a(
            g,
            {
              variant: "outline",
              size: "sm",
              onClick: () => B(t),
              disabled: !t.original_path,
              title: t.original_path ? n("app.quarantineTab.restoreToOriginalLocation", "Restore to original location") : n("app.quarantineTab.originalLocationUnknown", "Original location unknown"),
              children: n("common.actions.restore", "Restore")
            }
          ),
          /* @__PURE__ */ a(
            g,
            {
              variant: "destructive",
              size: "sm",
              onClick: () => i(t.name),
              children: n("common.actions.delete", "Delete")
            }
          )
        ] })
      }
    ],
    rows: u,
    viewPageKey: "security-quarantine",
    builtinViews: Ra,
    noun: "files",
    sorts: p,
    setSorts: k,
    hiddenKeys: v,
    setHiddenKeys: w
  });
  return /* @__PURE__ */ s("div", { className: "quarantine-tab", children: [
    o && /* @__PURE__ */ a("div", { className: `alert alert-${o.type === "success" ? "success" : "danger"}`, children: o.text }),
    /* @__PURE__ */ a(
      $,
      {
        views: m.views,
        label: "files",
        onCreate: m.createView,
        actions: /* @__PURE__ */ s(Q, { children: [
          /* @__PURE__ */ a(
            Y,
            {
              count: m.filterCount,
              onClick: () => m.setDrawerOpen(!0)
            }
          ),
          /* @__PURE__ */ a(J, { ...m.toolsProps, onRefresh: f })
        ] })
      }
    ),
    /* @__PURE__ */ a(G, { ...m.chipProps }),
    /* @__PURE__ */ a(
      Z,
      {
        loading: S,
        columns: m.columns,
        data: u,
        keyField: "name",
        sorts: p,
        onSortsChange: k,
        ...m.tableProps,
        emptyState: /* @__PURE__ */ a(
          ye,
          {
            icon: Ye,
            title: n("app.quarantineTab.noFilesInQuarantine", "No files in quarantine"),
            description: n("app.quarantineTab.infectedFilesWillAppearHereWhen", "Infected files will appear here when detected")
          }
        ),
        footer: /* @__PURE__ */ a(
          X,
          {
            shown: m.shownCount,
            total: u.length,
            noun: "file"
          }
        )
      }
    ),
    /* @__PURE__ */ a(ee, { ...m.drawerProps })
  ] });
};
function za() {
  return /* @__PURE__ */ a(Ca, {});
}
function Ka() {
  return /* @__PURE__ */ a(qa, {});
}
for (const [n, l] of Object.entries({ en: Ie, es: Ee }))
  De.addResourceBundle(n, "translation", l, !0, !1);
export {
  Ka as QuarantineTabPage,
  za as ScannerTabPage
};
