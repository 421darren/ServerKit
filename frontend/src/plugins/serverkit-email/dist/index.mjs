import pe from "i18next";
import { jsx as a, jsxs as s, Fragment as U } from "react/jsx-runtime";
import { forwardRef as he, createElement as X, useState as S, useCallback as A, useEffect as P, useMemo as W } from "react";
import { api as m, useTranslation as R, useTabParam as ye, PageLayout as fe, Button as w, useToast as M, EmptyState as be, KpiBand as ge, MetricCard as B, DataTable as Q, DataTableFooter as j, useConfirm as ee, Input as q, Pill as L, useTableSort as ae, useColumnVisibility as ie, useTableChrome as te, GridViewPicker as le, GridFilterButton as se, GridToolsMenu as ne, ListToolbar as ve, GridChips as re, GridFilterDrawer as oe, SearchField as ke } from "serverkit-sdk";
const _e = '.sk-email{padding:24px}.sk-email__section{display:flex;flex-direction:column;gap:20px}.sk-email__section-title{display:flex;align-items:center;gap:8px;margin:0;font-family:var(--mono);font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--text-faint)}.sk-email__section-title svg{color:var(--text-dim)}.sk-email__empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:24px 20px;background:var(--surface);border:1px solid var(--border-soft);border-radius:var(--radius-lg);text-align:center;color:var(--text-dim);font-size:12px}.sk-email__empty svg{color:var(--text-faint)}.sk-email__empty p{margin:0}.sk-email__hero{max-width:560px;margin:24px auto 0}.sk-email__hero .empty-state{background:var(--surface);border:1px solid var(--border-soft);border-radius:var(--radius-lg);padding:32px 24px}.sk-email__hero-note{margin:16px 0 0;padding:12px 16px;background:var(--accent-bg);border:1px solid var(--border-soft);border-radius:var(--radius);font-family:var(--mono);font-size:11.5px;line-height:1.55;color:var(--text-dim);text-align:center}.sk-email__hero-error{margin:12px 0 0;padding:12px 16px;background:var(--red-bg);border:1px solid var(--red);border-radius:var(--radius);font-family:var(--mono);font-size:11.5px;line-height:1.55;color:var(--red);white-space:pre-line;overflow-wrap:anywhere;text-align:left}.sk-email__actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.sk-email__actions-col,.sk-email__actions-cell{text-align:right}.sk-email__actions-cell .sk-email__actions{justify-content:flex-end}.sk-email__filters>label{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--text-faint)}.sk-email__filters select{padding:6px 10px;background:var(--surface-2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-family:var(--mono, "IBM Plex Mono", ui-monospace, "SF Mono", "JetBrains Mono", Menlo, monospace);font-size:12px;cursor:pointer}.sk-email__filters select:focus{outline:none;border-color:var(--accent)}.sk-email__filters .search-box{flex:1;min-width:220px;max-width:360px}.sk-email__add,.sk-email__form{display:flex;flex-wrap:wrap;align-items:flex-end;gap:12px;padding:16px 20px;background:var(--surface);border:1px solid var(--border-soft);border-radius:var(--radius-lg)}.sk-email__add label,.sk-email__form label{display:flex;flex-direction:column;gap:4px;font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--text-faint)}.sk-email__form{flex-direction:column;align-items:stretch}.sk-email__check{flex-direction:row;align-items:center;gap:8px;font-family:inherit;font-size:12px;font-weight:400;letter-spacing:normal;text-transform:none;color:var(--text-dim);cursor:pointer}.sk-email__check input[type=checkbox]{width:15px;height:15px;accent-color:var(--accent)}.sk-email__domains{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}.sk-email__domain{display:flex;flex-direction:column;gap:12px;padding:15px 16px;background:var(--surface);border:1px solid var(--border-soft);border-radius:var(--radius-lg);transition:border-color .15s ease}.sk-email__domain:hover{border-color:var(--border-strong)}.sk-email__domain-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.sk-email__domain-name{font-family:var(--mono);font-size:13.5px;font-weight:600;color:var(--text);overflow-wrap:anywhere}.sk-email__dns{display:flex;flex-wrap:wrap;gap:6px}.sk-email__domain-meta{display:flex;flex-wrap:wrap;gap:12px;padding-top:12px;border-top:1px solid var(--border-soft);font-family:var(--mono);font-size:11.5px;color:var(--text-faint)}.sk-email__mono{font-family:var(--mono);font-size:12.5px;color:var(--text);overflow-wrap:anywhere}', Se = {
  email: {
    aDeliverabilityPreflightPtrPort25: "A deliverability preflight (PTR, port 25, RBL) gates outbound sending before mail can leave this host.",
    accountCreated: "Account created",
    accountDeleted: "Account deleted",
    accounts: "Accounts",
    addAMailDomainFirst: "Add a mail domain first.",
    addDomain: "Add domain",
    address: "Address",
    component: "Component",
    couldNotAddDomain: "Could not add domain",
    createFailed: "Create failed",
    delete3: "Delete {{email}}?",
    deleteAccount: "Delete account",
    deleteAndAllOfItsAccounts: "Delete {{name}} and all of its accounts and aliases?",
    deleteDomain: "Delete domain",
    deleteFailed: "Delete failed",
    deployDns: "Deploy DNS",
    deployFailedNoLinkedDnsProvider: "Deploy failed (no linked DNS provider?)",
    dkimSelector: "DKIM selector:",
    dnsCheckFailed: "DNS check failed",
    dnsChecked: "DNS checked",
    dnsRecordsDeployedToProvider: "DNS records deployed to provider",
    domainAdded: "Domain added",
    domainDeleted: "Domain deleted",
    emailServerInstallStarted: "Email server install started",
    enableRelay: "Enable relay",
    enableSpamFiltering: "Enable spam filtering",
    failedTo: "Failed to {{action}} {{component}}",
    failedToDisableRelay: "Failed to disable relay",
    failedToWebmail: "Failed to {{action}} webmail",
    flushFailed: "Flush failed",
    flushQueue: "Flush queue",
    host: "Host",
    installFailed: "Install failed",
    installMailServer: "Install mail server",
    installWebmail: "Install webmail",
    mailServerNotInstalled: "Mail server not installed",
    mailboxPassword: "Mailbox password",
    mailboxUsername: "Mailbox username",
    mostPanelsNeverRunAMail: "Most panels never run a mail server, install it when you need it.",
    newMailDomain: "New mail domain",
    noMailDomainsYet: "No mail domains yet.",
    outboundRelaySmarthost: "Outbound relay (smarthost)",
    queue: "Queue",
    queueFlushed: "Queue flushed",
    quota: "Quota",
    quotaInMb: "Quota in MB",
    quotaMb: "Quota (MB)",
    recipient: "Recipient",
    relayDisabled: "Relay disabled",
    relayReachable: "Relay reachable",
    relaySaved: "Relay saved",
    relayTestFailed: "Relay test failed",
    requiredScore: "Required score",
    roundcubeWebmail: "Roundcube webmail",
    ruleUpdateFailed: "Rule update failed",
    ruleUpdateStarted: "Rule update started",
    saveFailed: "Save failed",
    searchAccounts: "Search accounts",
    searchAccountsByAddress: "Search accounts by address…",
    searchQueueBySenderRecipientOr: "Search queue by sender, recipient, or ID…",
    sender: "Sender",
    spamConfigSaved: "Spam config saved",
    spamassassin: "SpamAssassin",
    updateRules: "Update rules",
    used: "Used",
    webmail: "Webmail: {{action}}",
    webmailInstallStarted: "Webmail install started",
    webmailIsNotInstalled: "Webmail is not installed."
  }
}, we = {
  app: Se
}, xe = {
  email: {
    aDeliverabilityPreflightPtrPort25: "Una verificación previa de entregabilidad (PTR, puerto 25, RBL) controla el envío saliente antes de que el correo pueda salir de este host.",
    accountCreated: "Cuenta creada",
    accountDeleted: "Cuenta eliminada",
    accounts: "Cuentas",
    addAMailDomainFirst: "Añade primero un dominio de correo.",
    addDomain: "Añadir dominio",
    address: "Dirección",
    component: "Componente",
    couldNotAddDomain: "No se pudo añadir el dominio",
    createFailed: "Error al crear",
    delete3: "¿Eliminar {{email}}?",
    deleteAccount: "Eliminar cuenta",
    deleteAndAllOfItsAccounts: "¿Eliminar {{name}} y todas sus cuentas y alias?",
    deleteDomain: "Eliminar dominio",
    deleteFailed: "Error al eliminar",
    deployDns: "Desplegar DNS",
    deployFailedNoLinkedDnsProvider: "Error al desplegar (¿no hay proveedor de DNS vinculado?)",
    dkimSelector: "Selector DKIM:",
    dnsCheckFailed: "Falló la comprobación de DNS",
    dnsChecked: "DNS comprobado",
    dnsRecordsDeployedToProvider: "Registros DNS desplegados en el proveedor",
    domainAdded: "Dominio añadido",
    domainDeleted: "Dominio eliminado",
    emailServerInstallStarted: "Instalación del servidor de correo iniciada",
    enableRelay: "Activar relay",
    enableSpamFiltering: "Activar filtrado de spam",
    failedTo: "No se pudo {{action}} {{component}}",
    failedToDisableRelay: "No se pudo desactivar el relay",
    failedToWebmail: "No se pudo {{action}} el webmail",
    flushFailed: "Error al vaciar la cola",
    flushQueue: "Vaciar la cola",
    host: "Host",
    installFailed: "Error en la instalación",
    installMailServer: "Instalar servidor de correo",
    installWebmail: "Instalar webmail",
    mailServerNotInstalled: "Servidor de correo no instalado",
    mailboxPassword: "Contraseña del buzón",
    mailboxUsername: "Nombre de usuario del buzón",
    mostPanelsNeverRunAMail: "La mayoría de los paneles nunca ejecutan un servidor de correo; instálalo cuando lo necesites.",
    newMailDomain: "Nuevo dominio de correo",
    noMailDomainsYet: "Aún no hay dominios de correo.",
    outboundRelaySmarthost: "Relay saliente (smarthost)",
    queue: "Cola",
    queueFlushed: "Cola vaciada",
    quota: "Cuota",
    quotaInMb: "Cuota en MB",
    quotaMb: "Cuota (MB)",
    recipient: "Destinatario",
    relayDisabled: "Relay desactivado",
    relayReachable: "Relay accesible",
    relaySaved: "Relay guardado",
    relayTestFailed: "Falló la prueba del relay",
    requiredScore: "Puntuación requerida",
    roundcubeWebmail: "Webmail Roundcube",
    ruleUpdateFailed: "Error al actualizar las reglas",
    ruleUpdateStarted: "Actualización de reglas iniciada",
    saveFailed: "Error al guardar",
    searchAccounts: "Buscar cuentas",
    searchAccountsByAddress: "Buscar cuentas por dirección...",
    searchQueueBySenderRecipientOr: "Buscar en la cola por remitente, destinatario o ID…",
    sender: "Remitente",
    spamConfigSaved: "Configuración de spam guardada",
    spamassassin: "SpamAssassin",
    updateRules: "Actualizar reglas",
    used: "Usado",
    webmail: "Webmail: {{action}}",
    webmailInstallStarted: "Se inició la instalación del webmail",
    webmailIsNotInstalled: "El webmail no está instalado."
  }
}, De = {
  app: xe
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
var Ne = {
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
const Ce = (e) => e.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const x = (e, t) => {
  const i = he(
    ({
      color: l = "currentColor",
      size: b = 24,
      strokeWidth: k = 2,
      absoluteStrokeWidth: h,
      className: _ = "",
      children: p,
      ...d
    }, f) => X(
      "svg",
      {
        ref: f,
        ...Ne,
        width: b,
        height: b,
        stroke: l,
        strokeWidth: h ? Number(k) * 24 / Number(b) : k,
        className: ["lucide", `lucide-${Ce(e)}`, _].join(" "),
        ...d
      },
      [
        ...t.map(([g, u]) => X(g, u)),
        ...Array.isArray(p) ? p : [p]
      ]
    )
  );
  return i.displayName = `${e}`, i;
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const qe = x("CircleCheck", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m9 12 2 2 4-4", key: "dzmm74" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ee = x("CircleHelp", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3", key: "1u773s" }],
  ["path", { d: "M12 17h.01", key: "p32p05" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Re = x("CircleX", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m15 9-6 6", key: "1uzhvr" }],
  ["path", { d: "m9 9 6 6", key: "z0biqf" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ae = x("ExternalLink", [
  ["path", { d: "M15 3h6v6", key: "1q9fwt" }],
  ["path", { d: "M10 14 21 3", key: "gplh6r" }],
  ["path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6", key: "a6xqqp" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Me = x("Filter", [
  ["polygon", { points: "22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3", key: "1yg77f" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ce = x("Globe", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20", key: "13o1zl" }],
  ["path", { d: "M2 12h20", key: "9i4pu4" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const de = x("Inbox", [
  ["polyline", { points: "22 12 16 12 14 15 10 15 8 12 2 12", key: "o97t9d" }],
  [
    "path",
    {
      d: "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
      key: "oot6mr"
    }
  ]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const $ = x("Plus", [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "M12 5v14", key: "s699le" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const ze = x("RefreshCw", [
  ["path", { d: "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8", key: "v9h5vc" }],
  ["path", { d: "M21 3v5h-5", key: "1q7to0" }],
  ["path", { d: "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16", key: "3uifl3" }],
  ["path", { d: "M8 16H3v5", key: "1cv678" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Pe = x("Search", [
  ["circle", { cx: "11", cy: "11", r: "8", key: "4ej97u" }],
  ["path", { d: "m21 21-4.3-4.3", key: "1qie3q" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Fe = x("Send", [
  ["path", { d: "m22 2-7 20-4-9-9-4Z", key: "1q3vgg" }],
  ["path", { d: "M22 2 11 13", key: "nzbqef" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Y = x("Server", [
  ["rect", { width: "20", height: "8", x: "2", y: "2", rx: "2", ry: "2", key: "ngkwjq" }],
  ["rect", { width: "20", height: "8", x: "2", y: "14", rx: "2", ry: "2", key: "iecqi9" }],
  ["line", { x1: "6", x2: "6.01", y1: "6", y2: "6", key: "16zg32" }],
  ["line", { x1: "6", x2: "6.01", y1: "18", y2: "18", key: "nzw8ys" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Te = x("ShieldCheck", [
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
const J = x("Trash2", [
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
const me = x("Users", [
  ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
  ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }],
  ["path", { d: "M22 21v-2a4 4 0 0 0-3-3.87", key: "kshegd" }],
  ["path", { d: "M16 3.13a4 4 0 0 1 0 7.75", key: "1da9ce" }]
]), v = {
  // Server
  getEmailStatus: () => m.request("/email/status"),
  installEmailServer: (e = {}) => m.request("/email/install", { method: "POST", body: JSON.stringify(e) }),
  controlEmailService: (e, t) => m.request(`/email/service/${e}/${t}`, { method: "POST" }),
  // Domains
  getEmailDomains: () => m.request("/email/domains"),
  addEmailDomain: (e) => m.request("/email/domains", { method: "POST", body: JSON.stringify(e) }),
  getEmailDomain: (e) => m.request(`/email/domains/${e}`),
  deleteEmailDomain: (e) => m.request(`/email/domains/${e}`, { method: "DELETE" }),
  verifyEmailDNS: (e) => m.request(`/email/domains/${e}/verify-dns`, { method: "POST" }),
  deployEmailDNS: (e) => m.request(`/email/domains/${e}/deploy-dns`, { method: "POST" }),
  // Accounts
  getEmailAccounts: (e) => m.request(`/email/domains/${e}/accounts`),
  createEmailAccount: (e, t) => m.request(`/email/domains/${e}/accounts`, { method: "POST", body: JSON.stringify(t) }),
  getEmailAccount: (e) => m.request(`/email/accounts/${e}`),
  updateEmailAccount: (e, t) => m.request(`/email/accounts/${e}`, { method: "PUT", body: JSON.stringify(t) }),
  getWebmailLogin: (e) => m.request(`/email/accounts/${e}/webmail-login`, { method: "POST" }), deleteEmailAccount: (e) => m.request(`/email/accounts/${e}`, { method: "DELETE" }),
  changeEmailPassword: (e, t) => m.request(`/email/accounts/${e}/password`, { method: "POST", body: JSON.stringify({ password: t }) }),
  // Aliases
  getEmailAliases: (e) => m.request(`/email/domains/${e}/aliases`),
  createEmailAlias: (e, t) => m.request(`/email/domains/${e}/aliases`, { method: "POST", body: JSON.stringify(t) }),
  deleteEmailAlias: (e) => m.request(`/email/aliases/${e}`, { method: "DELETE" }),
  // Forwarding
  getEmailForwarding: (e) => m.request(`/email/accounts/${e}/forwarding`),
  createEmailForwarding: (e, t) => m.request(`/email/accounts/${e}/forwarding`, { method: "POST", body: JSON.stringify(t) }),
  updateEmailForwarding: (e, t) => m.request(`/email/forwarding/${e}`, { method: "PUT", body: JSON.stringify(t) }),
  deleteEmailForwarding: (e) => m.request(`/email/forwarding/${e}`, { method: "DELETE" }),
  // Outbound SMTP relay (smarthost)
  getEmailRelay: () => m.request("/email/relay"),
  updateEmailRelay: (e) => m.request("/email/relay", { method: "PUT", body: JSON.stringify(e) }),
  testEmailRelay: (e) => m.request("/email/relay/test", { method: "POST", body: JSON.stringify(e) }),
  disableEmailRelay: () => m.request("/email/relay", { method: "DELETE" }),
  // SpamAssassin
  getSpamConfig: () => m.request("/email/spam/config"),
  updateSpamConfig: (e) => m.request("/email/spam/config", { method: "PUT", body: JSON.stringify(e) }),
  updateSpamRules: () => m.request("/email/spam/update-rules", { method: "POST" }),
  // Roundcube webmail
  getWebmailStatus: () => m.request("/email/webmail/status"),
  installWebmail: (e = {}) => m.request("/email/webmail/install", { method: "POST", body: JSON.stringify(e) }),
  controlWebmail: (e) => m.request(`/email/webmail/service/${e}`, { method: "POST" }),
  configureWebmailProxy: (e) => m.request("/email/webmail/configure-proxy", { method: "POST", body: JSON.stringify({ domain: e }) }),
  // Mail queue & logs
  getMailQueue: () => m.request("/email/queue"),
  flushMailQueue: () => m.request("/email/queue/flush", { method: "POST" }),
  deleteMailQueueItem: (e) => m.request(`/email/queue/${e}`, { method: "DELETE" }),
  getMailLogs: (e = 100) => m.request(`/email/logs?lines=${e}`)
}, Z = ["overview", "domains", "accounts", "relay", "spam", "webmail", "queue"], O = { match: "all", rules: [] }, ue = [
  { key: "spf", label: "SPF" },
  { key: "dkim", label: "DKIM" },
  { key: "dmarc", label: "DMARC" },
  { key: "ptr", label: "PTR" },
  { key: "mx", label: "MX" }
];
function Ie(e) {
  return e === "ok" ? "green" : e === "missing" ? "red" : "gray";
}
function Le(e, t) {
  const i = {};
  for (const { key: l } of ue)
    t && t[l] ? i[l] = t[l].valid || t[l].present || t[l].found ? "ok" : "missing" : l === "spf" ? i[l] = e != null && e.spf_record ? "ok" : "unknown" : l === "dkim" ? i[l] = e != null && e.dkim_public_key ? "ok" : "unknown" : l === "dmarc" ? i[l] = e != null && e.dmarc_record ? "ok" : "unknown" : i[l] = "unknown";
  return i;
}
function Oe({ state: e }) {
  return e === "ok" ? /* @__PURE__ */ a(qe, { size: 12, "aria-hidden": "true" }) : e === "missing" ? /* @__PURE__ */ a(Re, { size: 12, "aria-hidden": "true" }) : /* @__PURE__ */ a(Ee, { size: 12, "aria-hidden": "true" });
}
function $e() {
  const { t: e } = R(), [t] = ye("/email", Z), [i, l] = S(null), [b, k] = S([]), [h, _] = S(!0), p = A(async () => {
    try {
      const u = await v.getEmailStatus();
      l((u == null ? void 0 : u.status) || u || null);
    } catch {
      l(null);
    }
  }, []), d = A(async () => {
    try {
      const u = await v.getEmailDomains();
      k((u == null ? void 0 : u.domains) || u || []);
    } catch {
      k([]);
    }
  }, []);
  P(() => {
    let u = !0;
    return (async () => (await Promise.all([p(), d()]), u && _(!1)))(), () => {
      u = !1;
    };
  }, [p, d]);
  const f = (i == null ? void 0 : i.installed) ?? (i == null ? void 0 : i.is_installed) ?? (i != null && i.components != null), g = Z.map((u) => ({
    to: `/email/${u}`,
    label: u.charAt(0).toUpperCase() + u.slice(1),
    end: !1
  }));
  return /* @__PURE__ */ a(
    fe,
    {
      navLabel: "Email Server",
      tabs: g,
      actions: /* @__PURE__ */ s(w, { variant: "outline", size: "sm", onClick: () => {
        p(), d();
      }, children: [
        /* @__PURE__ */ a(ze, { size: 14 }),
        " ",
        e("common.actions.refresh", "Refresh")
      ] }),
      children: /* @__PURE__ */ a("div", { className: "sk-email", children: h ? /* @__PURE__ */ a("div", { className: "sk-email__empty", children: e("common.loading", "Loading…") }) : /* @__PURE__ */ s(U, { children: [
        t === "overview" && /* @__PURE__ */ a(Ke, { status: i, installed: f, onChange: p }),
        t === "domains" && /* @__PURE__ */ a(Be, { domains: b, onChange: d }),
        t === "accounts" && /* @__PURE__ */ a(We, { domains: b }),
        t === "relay" && /* @__PURE__ */ a(Ue, {}),
        t === "spam" && /* @__PURE__ */ a(Qe, {}),
        t === "webmail" && /* @__PURE__ */ a(je, {}),
        t === "queue" && /* @__PURE__ */ a(He, {})
      ] }) })
    }
  );
}
function Ke({ status: e, installed: t, onChange: i }) {
  const { t: l } = R(), b = M(), [k, h] = S(null), _ = (e == null ? void 0 : e.components) || {}, p = Object.keys(_), d = (c) => {
    var r;
    return Object.entries(((r = c == null ? void 0 : c.data) == null ? void 0 : r.results) || {}).filter(([, y]) => y && y.success === !1).map(([y, D]) => `${y}: ${D.error || "unknown error"}`);
  }, f = async () => {
    h(null);
    try {
      await v.installEmailServer(), b.success(l("app.email.emailServerInstallStarted", "Email server install started")), i();
    } catch (c) {
      const r = (c == null ? void 0 : c.message) || "Install failed", y = d(c);
      h([r, ...y].join(`
`)), b.error(y.length ? `${r} — ${y[0]}` : r);
    }
  }, g = async (c, r) => {
    try {
      await v.controlEmailService(c, r), b.success(`${c}: ${r}`), i();
    } catch {
      b.error(l("app.email.failedTo", "Failed to {{action}} {{component}}", { action: r, component: c }));
    }
  };
  if (!t)
    return /* @__PURE__ */ s("div", { className: "sk-email__hero", children: [
      /* @__PURE__ */ a(
        be,
        {
          icon: Y,
          title: l("app.email.mailServerNotInstalled", "Mail server not installed"),
          description: l("app.email.mostPanelsNeverRunAMail", "Most panels never run a mail server, install it when you need it."),
          action: /* @__PURE__ */ s(w, { size: "sm", onClick: f, children: [
            /* @__PURE__ */ a($, { size: 14 }),
            " ",
            l("app.email.installMailServer", "Install mail server")
          ] })
        }
      ),
      /* @__PURE__ */ a("p", { className: "sk-email__hero-note", children: l("app.email.aDeliverabilityPreflightPtrPort25", "A deliverability preflight (PTR, port 25, RBL) gates outbound sending before mail can leave this host.") }),
      k && /* @__PURE__ */ a("p", { className: "sk-email__hero-error", role: "alert", children: k })
    ] });
  const u = p.map((c) => {
    var y;
    const r = ((y = _[c]) == null ? void 0 : y.running) ?? _[c] === "running";
    return { id: c, name: c, running: r };
  }), C = [
    { key: "component", headerKey: "app.email.component", header: "Component", sortable: !0, hideable: !1, sortValue: (c) => c.name, render: (c) => c.name },
    {
      key: "state",
      headerKey: "common.labels.state",
      header: "State",
      sortable: !0,
      sortValue: (c) => c.running ? 1 : 0,
      render: (c) => /* @__PURE__ */ a(L, { kind: c.running ? "green" : "red", children: c.running ? "Running" : "Stopped" })
    },
    {
      key: "actions",
      header: "",
      hideable: !1,
      className: "sk-email__actions-col",
      cellClassName: "sk-email__actions-cell",
      render: (c) => /* @__PURE__ */ s("div", { className: "sk-email__actions", children: [
        /* @__PURE__ */ a(w, { variant: "ghost", size: "sm", onClick: () => g(c.name, c.running ? "restart" : "start"), children: c.running ? "Restart" : "Start" }),
        c.running && /* @__PURE__ */ a(w, { variant: "ghost", size: "sm", onClick: () => g(c.name, "stop"), children: l("common.actions.stop", "Stop") })
      ] })
    }
  ];
  return /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ s(ge, { children: [
      /* @__PURE__ */ a(B, { label: l("common.labels.domains", "Domains"), value: (e == null ? void 0 : e.domains_count) ?? 0, tone: "accent", icon: /* @__PURE__ */ a(ce, { size: 16 }) }),
      /* @__PURE__ */ a(B, { label: l("app.email.accounts", "Accounts"), value: (e == null ? void 0 : e.accounts_count) ?? 0, tone: "cyan", icon: /* @__PURE__ */ a(me, { size: 16 }) }),
      /* @__PURE__ */ a(B, { label: l("app.email.queue", "Queue"), value: (e == null ? void 0 : e.queue_count) ?? 0, tone: "amber", icon: /* @__PURE__ */ a(de, { size: 16 }) })
    ] }),
    /* @__PURE__ */ s("h2", { className: "sk-email__section-title", children: [
      /* @__PURE__ */ a(Y, { size: 16 }),
      " ",
      l("common.labels.services", "Services")
    ] }),
    /* @__PURE__ */ a(
      Q,
      {
        columns: C,
        data: u,
        keyField: "id",
        storageKey: "serverkit-table-email-components",
        footer: /* @__PURE__ */ a(j, { shown: u.length, total: u.length, noun: "service" }),
        emptyTitle: "No service components reported.",
        emptyMessage: ""
      }
    )
  ] });
}
function Be({ domains: e, onChange: t }) {
  const { t: i } = R(), l = M(), { confirm: b } = ee(), [k, h] = S(""), [_, p] = S({}), [d, f] = S({}), g = async (r) => {
    if (r.preventDefault(), !!k.trim())
      try {
        await v.addEmailDomain({ name: k.trim() }), l.success(i("app.email.domainAdded", "Domain added")), h(""), t();
      } catch {
        l.error(i("app.email.couldNotAddDomain", "Could not add domain"));
      }
  }, u = async (r) => {
    if (await b({
      title: i("app.email.deleteDomain", "Delete domain"),
      message: i("app.email.deleteAndAllOfItsAccounts", "Delete {{name}} and all of its accounts and aliases?", { name: r.name }),
      confirmLabel: i("common.actions.delete", "Delete"),
      danger: !0
    }))
      try {
        await v.deleteEmailDomain(r.id), l.success(i("app.email.domainDeleted", "Domain deleted")), t();
      } catch {
        l.error(i("app.email.deleteFailed", "Delete failed"));
      }
  }, C = async (r) => {
    p((y) => ({ ...y, [r.id]: !0 }));
    try {
      const y = await v.verifyEmailDNS(r.id);
      f((D) => ({ ...D, [r.id]: (y == null ? void 0 : y.records) || y || {} })), l.success(i("app.email.dnsChecked", "DNS checked"));
    } catch {
      l.error(i("app.email.dnsCheckFailed", "DNS check failed"));
    } finally {
      p((y) => ({ ...y, [r.id]: !1 }));
    }
  }, c = async (r) => {
    try {
      await v.deployEmailDNS(r.id), l.success(i("app.email.dnsRecordsDeployedToProvider", "DNS records deployed to provider"));
    } catch {
      l.error(i("app.email.deployFailedNoLinkedDnsProvider", "Deploy failed (no linked DNS provider?)"));
    }
  };
  return /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ s("form", { className: "sk-email__add", onSubmit: g, children: [
      /* @__PURE__ */ a(
        q,
        {
          value: k,
          onChange: (r) => h(r.target.value),
          placeholder: "example.com",
          "aria-label": i("app.email.newMailDomain", "New mail domain")
        }
      ),
      /* @__PURE__ */ s(w, { type: "submit", size: "sm", children: [
        /* @__PURE__ */ a($, { size: 14 }),
        " ",
        i("app.email.addDomain", "Add domain")
      ] })
    ] }),
    e.length === 0 ? /* @__PURE__ */ s("div", { className: "sk-email__empty", children: [
      /* @__PURE__ */ a(ce, { size: 24, "aria-hidden": "true" }),
      /* @__PURE__ */ a("p", { children: i("app.email.noMailDomainsYet", "No mail domains yet.") })
    ] }) : /* @__PURE__ */ a("ul", { className: "sk-email__domains", children: e.map((r) => {
      const y = Le(r, d[r.id]);
      return /* @__PURE__ */ s("li", { className: "sk-email__domain", children: [
        /* @__PURE__ */ s("div", { className: "sk-email__domain-head", children: [
          /* @__PURE__ */ a("span", { className: "sk-email__domain-name", children: r.name }),
          /* @__PURE__ */ a(L, { kind: r.is_active ? "green" : "gray", children: r.is_active ? "Active" : "Disabled" })
        ] }),
        /* @__PURE__ */ a("div", { className: "sk-email__dns", children: ue.map(({ key: D, label: F }) => /* @__PURE__ */ s(L, { kind: Ie(y[D]), title: `${F}: ${y[D]}`, children: [
          /* @__PURE__ */ a(Oe, { state: y[D] }),
          " ",
          F
        ] }, D)) }),
        /* @__PURE__ */ s("div", { className: "sk-email__domain-meta", children: [
          /* @__PURE__ */ s("span", { children: [
            r.accounts_count ?? 0,
            " accounts"
          ] }),
          /* @__PURE__ */ s("span", { children: [
            r.aliases_count ?? 0,
            " aliases"
          ] }),
          r.dkim_selector && /* @__PURE__ */ s("span", { children: [
            i("app.email.dkimSelector", "DKIM selector:"),
            " ",
            r.dkim_selector
          ] })
        ] }),
        /* @__PURE__ */ s("div", { className: "sk-email__actions", children: [
          /* @__PURE__ */ s(
            w,
            {
              variant: "outline",
              size: "sm",
              onClick: () => C(r),
              disabled: _[r.id],
              children: [
                /* @__PURE__ */ a(Te, { size: 14 }),
                " ",
                _[r.id] ? "Checking…" : "Verify DNS"
              ]
            }
          ),
          /* @__PURE__ */ s(w, { variant: "outline", size: "sm", onClick: () => c(r), children: [
            /* @__PURE__ */ a(Ae, { size: 14 }),
            " ",
            i("app.email.deployDns", "Deploy DNS")
          ] }),
          /* @__PURE__ */ s(w, { variant: "ghost", size: "sm", onClick: () => u(r), children: [
            /* @__PURE__ */ a(J, { size: 14 }),
            " ",
            i("common.actions.delete", "Delete")
          ] })
        ] })
      ] }, r.id);
    }) })
  ] });
}
function V(e) {
  const t = (e == null ? void 0 : e.quota_mb) ?? 0;
  return t ? Math.round((e.quota_used_mb ?? 0) / t * 100) : null;
}
const Ve = [
  { name: "Active first", state: { search: "", sorts: [{ key: "state", direction: "desc" }], hiddenKeys: [], columnFilters: O } },
  { name: "Largest quota", state: { search: "", sorts: [{ key: "quota", direction: "desc" }], hiddenKeys: [], columnFilters: O } },
  {
    // A disabled mailbox still exists and still holds its mail — it just
    // cannot authenticate. This is the list you audit after an offboarding.
    name: "Disabled",
    state: {
      search: "",
      hiddenKeys: [],
      sorts: [{ key: "email", direction: "asc" }],
      columnFilters: {
        match: "all",
        rules: [{ id: "ac1", field: "state", op: "any", value: ["Disabled"] }]
      }
    }
  },
  {
    // Mailboxes about to start rejecting deliveries. Same 85% threshold the
    // fleet uses for disk pressure, and `gt` on a null keeps the unlimited
    // mailboxes out instead of ranking them as 0%.
    name: "Nearly full",
    state: {
      search: "",
      hiddenKeys: [],
      sorts: [{ key: "used", direction: "desc" }],
      columnFilters: {
        match: "all",
        rules: [{ id: "ac2", field: "used", op: "gt", value: 85 }]
      }
    }
  }
];
function We({ domains: e }) {
  var G;
  const { t } = R(), i = M(), { confirm: l } = ee(), [b, k] = S((G = e[0]) != null && G.id ? String(e[0].id) : ""), [h, _] = S([]), [p, d] = S(!1), [f, g] = S(""), [u, C] = S({ username: "", password: "", quota_mb: 1024 }), { sorts: c, setSorts: r } = ae({ storageKey: "serverkit-table-email-accounts-sort" }), { hiddenKeys: y, setHiddenKeys: D } = ie({ storageKey: "serverkit-table-email-accounts-cols" }), F = W(() => ({ search: f }), [f]), N = A((n) => {
    n.search !== void 0 && g(n.search);
  }, []), o = A(async () => {
    if (!b) {
      _([]);
      return;
    }
    d(!0);
    try {
      const n = await v.getEmailAccounts(b);
      _((n == null ? void 0 : n.accounts) || n || []);
    } catch {
      _([]);
    } finally {
      d(!1);
    }
  }, [b]);
  P(() => {
    o();
  }, [o]);
  const z = async (n) => {
    if (n.preventDefault(), !(!u.username.trim() || !u.password))
      try {
        await v.createEmailAccount(b, u), i.success(t("app.email.accountCreated", "Account created")), C({ username: "", password: "", quota_mb: 1024 }), o();
      } catch {
        i.error(t("app.email.createFailed", "Create failed"));
      }
  }, K = async (n) => {
    if (await l({
      title: t("app.email.deleteAccount", "Delete account"),
      message: t("app.email.delete3", "Delete {{email}}?", { email: n.email }),
      confirmLabel: t("common.actions.delete", "Delete"),
      danger: !0
    }))
      try {
        await v.deleteEmailAccount(n.id), i.success(t("app.email.accountDeleted", "Account deleted")), o();
      } catch {
        i.error(t("app.email.deleteFailed", "Delete failed"));
      }
  }, [skId, skSetId] = S(null), skOpen = async (n) => {
    const q = window.open("about:blank", "_blank");
    skSetId(n.id);
    try {
      const r = await v.getWebmailLogin(n.id);
      if (!(r != null && r.url)) throw new Error((r == null ? void 0 : r.error) || "No link");
      q ? q.location.href = r.url : window.location.href = r.url;
    } catch (e) {
      q && q.close(), i.error((e == null ? void 0 : e.message) || "Could not open webmail");
    } finally {
      skSetId(null);
    }
  }, T = W(() => {
    const n = f.trim().toLowerCase();
    return n ? h.filter((I) => (I.email || "").toLowerCase().includes(n)) : h;
  }, [h, f]), E = te({
    columns: [
      {
        key: "email",
        headerKey: "app.email.address",
        header: "Address",
        sortable: !0,
        hideable: !1,
        sortValue: (n) => n.email || "",
        render: (n) => /* @__PURE__ */ a("span", { className: "sk-email__mono", children: n.email })
      },
      {
        key: "quota",
        headerKey: "app.email.quota",
        header: "Quota",
        sortable: !0,
        type: "num",
        unit: " MB",
        // The allocation, which is what "Largest quota" orders by. How full
        // it is lives in its own column below.
        value: (n) => n.quota_mb ?? 0,
        sortValue: (n) => n.quota_mb ?? 0,
        render: (n) => `${n.quota_used_mb ?? 0} / ${n.quota_mb ?? 0} MB`
      },
      {
        key: "used",
        headerKey: "app.email.used",
        header: "Used",
        sortable: !0,
        type: "num",
        unit: "%",
        value: V,
        sortValue: V,
        render: (n) => {
          const I = V(n);
          return I == null ? "—" : `${I}%`;
        }
      },
      {
        key: "state",
        headerKey: "common.labels.state",
        header: "State",
        sortable: !0,
        // Filter on the label the pill shows; keep the 1/0 sortValue so
        // "Active first" still puts active first when the column sorts desc.
        type: "enum",
        value: (n) => n.is_active ? "Active" : "Disabled",
        sortValue: (n) => n.is_active ? 1 : 0,
        render: (n) => /* @__PURE__ */ a(L, { kind: n.is_active ? "green" : "gray", children: n.is_active ? "Active" : "Disabled" })
      },
      {
        key: "actions",
        header: "",
        hideable: !1,
        className: "sk-email__actions-col",
        cellClassName: "sk-email__actions-cell",
        render: (n) => /* @__PURE__ */ s("div", { className: "sk-email__actions", children: [
          /* @__PURE__ */ s(w, { variant: "ghost", size: "sm", disabled: !n.is_active || skId === n.id, title: "Open this mailbox in webmail, no password needed", onClick: () => skOpen(n), children: [
            skId === n.id ? /* @__PURE__ */ a(ze, { size: 14, className: "animate-spin" }) : /* @__PURE__ */ a(Ae, { size: 14 }),
            " Webmail"
          ] }),
          /* @__PURE__ */ s(w, { variant: "ghost", size: "sm", onClick: () => K(n), children: [
            /* @__PURE__ */ a(J, { size: 14 }),
            " ",
            t("common.actions.delete", "Delete")
          ] })
        ] })
      }
    ],
    rows: T,
    viewPageKey: "email-accounts",
    builtinViews: Ve,
    noun: "accounts",
    sorts: c,
    setSorts: r,
    hiddenKeys: y,
    setHiddenKeys: D,
    pageState: F,
    applyPage: N
  });
  return e.length === 0 ? /* @__PURE__ */ s("div", { className: "sk-email__empty", children: [
    /* @__PURE__ */ a(me, { size: 24, "aria-hidden": "true" }),
    /* @__PURE__ */ a("p", { children: t("app.email.addAMailDomainFirst", "Add a mail domain first.") })
  ] }) : /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ a(
      le,
      {
        views: E.views,
        label: "accounts",
        onCreate: E.createView,
        actions: /* @__PURE__ */ s(U, { children: [
          /* @__PURE__ */ a(
            se,
            {
              count: E.filterCount,
              onClick: () => E.setDrawerOpen(!0)
            }
          ),
          /* @__PURE__ */ a(ne, { ...E.toolsProps, onRefresh: o })
        ] })
      }
    ),
    /* @__PURE__ */ s(ve, { className: "sk-email__filters", children: [
      /* @__PURE__ */ s("label", { children: [
        t("common.labels.domain", "Domain"),
        /* @__PURE__ */ a("select", { value: b, onChange: (n) => k(n.target.value), children: e.map((n) => /* @__PURE__ */ a("option", { value: String(n.id), children: n.name }, n.id)) })
      ] }),
      /* @__PURE__ */ s("label", { className: "search-box", children: [
        /* @__PURE__ */ a(Pe, { size: 16 }),
        /* @__PURE__ */ a(
          q,
          {
            type: "text",
            value: f,
            onChange: (n) => g(n.target.value),
            placeholder: t("app.email.searchAccountsByAddress", "Search accounts by address…"),
            "aria-label": t("app.email.searchAccounts", "Search accounts")
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ a(re, { ...E.chipProps }),
    /* @__PURE__ */ s("form", { className: "sk-email__add", onSubmit: z, children: [
      /* @__PURE__ */ a(
        q,
        {
          value: u.username,
          onChange: (n) => C({ ...u, username: n.target.value }),
          placeholder: "username",
          "aria-label": t("app.email.mailboxUsername", "Mailbox username")
        }
      ),
      /* @__PURE__ */ a(
        q,
        {
          type: "password",
          value: u.password,
          onChange: (n) => C({ ...u, password: n.target.value }),
          placeholder: "password",
          "aria-label": t("app.email.mailboxPassword", "Mailbox password")
        }
      ),
      /* @__PURE__ */ a(
        q,
        {
          type: "number",
          value: u.quota_mb,
          onChange: (n) => C({ ...u, quota_mb: Number(n.target.value) }),
          placeholder: t("app.email.quotaMb", "Quota (MB)"),
          "aria-label": t("app.email.quotaInMb", "Quota in MB")
        }
      ),
      /* @__PURE__ */ s(w, { type: "submit", size: "sm", children: [
        /* @__PURE__ */ a($, { size: 14 }),
        " ",
        t("common.actions.create", "Create")
      ] })
    ] }),
    /* @__PURE__ */ a(
      Q,
      {
        columns: E.columns,
        data: T,
        keyField: "id",
        sorts: c,
        onSortsChange: r,
        ...E.tableProps,
        loading: p,
        footer: /* @__PURE__ */ a(j, { shown: T.length, total: h.length, noun: "account" }),
        emptyTitle: h.length === 0 ? "No accounts in this domain." : "No accounts match this search.",
        emptyMessage: ""
      }
    ),
    /* @__PURE__ */ a(oe, { ...E.drawerProps })
  ] });
}
function Ue() {
  const { t: e } = R(), t = M(), [i, l] = S({ host: "", port: 587, username: "", password: "", enabled: !1 }), [b, k] = S(!0);
  P(() => {
    let d = !0;
    return v.getEmailRelay().then((f) => {
      d && l((g) => ({ ...g, ...(f == null ? void 0 : f.relay) || f || {} }));
    }).catch(() => {
    }).finally(() => {
      d && k(!1);
    }), () => {
      d = !1;
    };
  }, []);
  const h = async (d) => {
    d.preventDefault();
    try {
      await v.updateEmailRelay(i), t.success(e("app.email.relaySaved", "Relay saved"));
    } catch {
      t.error(e("app.email.saveFailed", "Save failed"));
    }
  }, _ = async () => {
    try {
      await v.testEmailRelay(i), t.success(e("app.email.relayReachable", "Relay reachable"));
    } catch {
      t.error(e("app.email.relayTestFailed", "Relay test failed"));
    }
  }, p = async () => {
    try {
      await v.disableEmailRelay(), l((d) => ({ ...d, enabled: !1 })), t.success(e("app.email.relayDisabled", "Relay disabled"));
    } catch {
      t.error(e("app.email.failedToDisableRelay", "Failed to disable relay"));
    }
  };
  return b ? /* @__PURE__ */ a("div", { className: "sk-email__empty", children: e("common.loading", "Loading…") }) : /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ s("h2", { className: "sk-email__section-title", children: [
      /* @__PURE__ */ a(Fe, { size: 16 }),
      " ",
      e("app.email.outboundRelaySmarthost", "Outbound relay (smarthost)")
    ] }),
    /* @__PURE__ */ s("form", { className: "sk-email__form", onSubmit: h, children: [
      /* @__PURE__ */ s("label", { children: [
        e("app.email.host", "Host"),
        /* @__PURE__ */ a(q, { value: i.host || "", onChange: (d) => l({ ...i, host: d.target.value }), placeholder: "smtp.provider.com" })
      ] }),
      /* @__PURE__ */ s("label", { children: [
        e("common.labels.port", "Port"),
        /* @__PURE__ */ a(q, { type: "number", value: i.port || 587, onChange: (d) => l({ ...i, port: Number(d.target.value) }) })
      ] }),
      /* @__PURE__ */ s("label", { children: [
        e("common.labels.username", "Username"),
        /* @__PURE__ */ a(q, { value: i.username || "", onChange: (d) => l({ ...i, username: d.target.value }) })
      ] }),
      /* @__PURE__ */ s("label", { children: [
        e("common.labels.password", "Password"),
        /* @__PURE__ */ a(q, { type: "password", value: i.password || "", onChange: (d) => l({ ...i, password: d.target.value }) })
      ] }),
      /* @__PURE__ */ s("label", { className: "sk-email__check", children: [
        /* @__PURE__ */ a("input", { type: "checkbox", checked: !!i.enabled, onChange: (d) => l({ ...i, enabled: d.target.checked }) }),
        e("app.email.enableRelay", "Enable relay")
      ] }),
      /* @__PURE__ */ s("div", { className: "sk-email__actions", children: [
        /* @__PURE__ */ a(w, { type: "submit", size: "sm", children: e("common.actions.save", "Save") }),
        /* @__PURE__ */ a(w, { type: "button", variant: "outline", size: "sm", onClick: _, children: e("common.actions.test", "Test") }),
        /* @__PURE__ */ a(w, { type: "button", variant: "ghost", size: "sm", onClick: p, children: e("common.actions.disable", "Disable") })
      ] })
    ] })
  ] });
}
function Qe() {
  const { t: e } = R(), t = M(), [i, l] = S({ enabled: !0, required_score: 5 }), [b, k] = S(!0);
  P(() => {
    let p = !0;
    return v.getSpamConfig().then((d) => {
      p && l((f) => ({ ...f, ...(d == null ? void 0 : d.config) || d || {} }));
    }).catch(() => {
    }).finally(() => {
      p && k(!1);
    }), () => {
      p = !1;
    };
  }, []);
  const h = async (p) => {
    p.preventDefault();
    try {
      await v.updateSpamConfig(i), t.success(e("app.email.spamConfigSaved", "Spam config saved"));
    } catch {
      t.error(e("app.email.saveFailed", "Save failed"));
    }
  }, _ = async () => {
    try {
      await v.updateSpamRules(), t.success(e("app.email.ruleUpdateStarted", "Rule update started"));
    } catch {
      t.error(e("app.email.ruleUpdateFailed", "Rule update failed"));
    }
  };
  return b ? /* @__PURE__ */ a("div", { className: "sk-email__empty", children: e("common.loading", "Loading…") }) : /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ s("h2", { className: "sk-email__section-title", children: [
      /* @__PURE__ */ a(Me, { size: 16 }),
      " ",
      e("app.email.spamassassin", "SpamAssassin")
    ] }),
    /* @__PURE__ */ s("form", { className: "sk-email__form", onSubmit: h, children: [
      /* @__PURE__ */ s("label", { className: "sk-email__check", children: [
        /* @__PURE__ */ a("input", { type: "checkbox", checked: !!i.enabled, onChange: (p) => l({ ...i, enabled: p.target.checked }) }),
        e("app.email.enableSpamFiltering", "Enable spam filtering")
      ] }),
      /* @__PURE__ */ s("label", { children: [
        e("app.email.requiredScore", "Required score"),
        /* @__PURE__ */ a(q, { type: "number", step: "0.1", value: i.required_score ?? 5, onChange: (p) => l({ ...i, required_score: Number(p.target.value) }) })
      ] }),
      /* @__PURE__ */ s("div", { className: "sk-email__actions", children: [
        /* @__PURE__ */ a(w, { type: "submit", size: "sm", children: e("common.actions.save", "Save") }),
        /* @__PURE__ */ a(w, { type: "button", variant: "outline", size: "sm", onClick: _, children: e("app.email.updateRules", "Update rules") })
      ] })
    ] })
  ] });
}
function je() {
  const { t: e } = R(), t = M(), [i, l] = S(null), [b, k] = S(!0), h = A(async () => {
    try {
      const g = await v.getWebmailStatus();
      l(g && typeof g.status === "object" ? g.status : g || null);
    } catch {
      l(null);
    } finally {
      k(!1);
    }
  }, []);
  P(() => {
    h();
  }, [h]);
  const _ = async () => {
    try {
      await v.installWebmail(), t.success(e("app.email.webmailInstallStarted", "Webmail install started")), h();
    } catch {
      t.error(e("app.email.installFailed", "Install failed"));
    }
  }, p = async (g) => {
    try {
      await v.controlWebmail(g), t.success(e("app.email.webmail", "Webmail: {{action}}", { action: g })), h();
    } catch {
      t.error(e("app.email.failedToWebmail", "Failed to {{action}} webmail", { action: g }));
    }
  };
  if (b) return /* @__PURE__ */ a("div", { className: "sk-email__empty", children: e("common.loading", "Loading…") });
  const d = (i == null ? void 0 : i.installed) ?? (i == null ? void 0 : i.is_installed), f = i == null ? void 0 : i.running;
  return /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ s("h2", { className: "sk-email__section-title", children: [
      /* @__PURE__ */ a(de, { size: 16 }),
      " ",
      e("app.email.roundcubeWebmail", "Roundcube webmail")
    ] }),
    d ? /* @__PURE__ */ s("div", { className: "sk-email__actions", children: [
      /* @__PURE__ */ a(L, { kind: f ? "green" : "red", children: f ? "Running" : "Stopped" }),
      /* @__PURE__ */ a(w, { variant: "outline", size: "sm", onClick: () => p(f ? "restart" : "start"), children: f ? "Restart" : "Start" }),
      f && /* @__PURE__ */ a(w, { variant: "ghost", size: "sm", onClick: () => p("stop"), children: e("common.actions.stop", "Stop") })
    ] }) : /* @__PURE__ */ s("div", { className: "sk-email__empty", children: [
      /* @__PURE__ */ a("p", { children: e("app.email.webmailIsNotInstalled", "Webmail is not installed.") }),
      /* @__PURE__ */ s(w, { size: "sm", onClick: _, children: [
        /* @__PURE__ */ a($, { size: 14 }),
        " ",
        e("app.email.installWebmail", "Install webmail")
      ] })
    ] })
  ] });
}
const Je = [
  { name: "Largest first", state: { search: "", sorts: [{ key: "size", direction: "desc" }], hiddenKeys: [], columnFilters: O } },
  { name: "By sender", state: { search: "", sorts: [{ key: "sender", direction: "asc" }], hiddenKeys: [], columnFilters: O } },
  {
    // What a backed-up queue is usually full of. 100 KB is the line between
    // a plain message (a few KB) and one carrying an attachment; Postfix's
    // own message_size_limit is 25 MB, so this is well inside real traffic.
    name: "Large messages",
    state: {
      search: "",
      hiddenKeys: [],
      sorts: [{ key: "size", direction: "desc" }],
      columnFilters: {
        match: "all",
        rules: [{ id: "q1", field: "size", op: "gt", value: 102400 }]
      }
    }
  }
];
function He() {
  const { t: e } = R(), t = M(), [i, l] = S([]), [b, k] = S(!0), [h, _] = S(""), { sorts: p, setSorts: d } = ae({ storageKey: "serverkit-table-email-queue-sort" }), { hiddenKeys: f, setHiddenKeys: g } = ie({ storageKey: "serverkit-table-email-queue-cols" }), u = W(() => ({ search: h }), [h]), C = A((o) => {
    o.search !== void 0 && _(o.search);
  }, []), c = A(async () => {
    k(!0);
    try {
      const o = await v.getMailQueue();
      l((o == null ? void 0 : o.queue) || o || []);
    } catch {
      l([]);
    } finally {
      k(!1);
    }
  }, []);
  P(() => {
    c();
  }, [c]);
  const r = async () => {
    try {
      await v.flushMailQueue(), t.success(e("app.email.queueFlushed", "Queue flushed")), c();
    } catch {
      t.error(e("app.email.flushFailed", "Flush failed"));
    }
  }, y = async (o) => {
    try {
      await v.deleteMailQueueItem(o), c();
    } catch {
      t.error(e("app.email.deleteFailed", "Delete failed"));
    }
  }, D = i.filter((o) => {
    const z = h.trim().toLowerCase();
    if (!z) return !0;
    const K = String(o.id || o.queue_id || "").toLowerCase(), T = String(o.sender || "").toLowerCase(), H = String(o.recipient || "").toLowerCase();
    return K.includes(z) || T.includes(z) || H.includes(z);
  }), N = te({
    columns: [
      {
        key: "id",
        header: "ID",
        sortable: !0,
        hideable: !1,
        sortValue: (o) => o.id || o.queue_id || "",
        render: (o) => /* @__PURE__ */ a("span", { className: "sk-email__mono", children: o.id || o.queue_id })
      },
      { key: "sender", headerKey: "app.email.sender", header: "Sender", sortable: !0, sortValue: (o) => o.sender || null, render: (o) => o.sender || "-" },
      { key: "recipient", headerKey: "app.email.recipient", header: "Recipient", sortable: !0, sortValue: (o) => o.recipient || null, render: (o) => o.recipient || "-" },
      {
        key: "size",
        headerKey: "common.labels.size",
        header: "Size",
        sortable: !0,
        // Bytes, straight off mailq. Typed explicitly because a preset
        // filters on it — inference would land on 'num' here anyway, but
        // only for as long as every loaded row happens to carry a size.
        type: "num",
        unit: " bytes",
        value: (o) => o.size ?? null,
        sortValue: (o) => o.size ?? null,
        render: (o) => o.size || "-"
      },
      {
        key: "actions",
        header: "",
        hideable: !1,
        className: "sk-email__actions-col",
        cellClassName: "sk-email__actions-cell",
        render: (o) => /* @__PURE__ */ a("div", { className: "sk-email__actions", children: /* @__PURE__ */ s(w, { variant: "ghost", size: "sm", onClick: () => y(o.id || o.queue_id), children: [
          /* @__PURE__ */ a(J, { size: 14 }),
          " ",
          e("common.actions.delete", "Delete")
        ] }) })
      }
    ],
    rows: D,
    viewPageKey: "email-queue",
    builtinViews: Je,
    noun: "messages",
    sorts: p,
    setSorts: d,
    hiddenKeys: f,
    setHiddenKeys: g,
    pageState: u,
    applyPage: C
  });
  return /* @__PURE__ */ s("section", { className: "sk-email__section", children: [
    /* @__PURE__ */ a(
      le,
      {
        views: N.views,
        label: "messages",
        onCreate: N.createView,
        actions: /* @__PURE__ */ s(U, { children: [
          /* @__PURE__ */ a(w, { variant: "outline", size: "sm", onClick: r, children: e("app.email.flushQueue", "Flush queue") }),
          /* @__PURE__ */ a(
            ke,
            {
              value: h,
              onSearch: _,
              placeholder: e("app.email.searchQueueBySenderRecipientOr", "Search queue by sender, recipient, or ID…")
            }
          ),
          /* @__PURE__ */ a(
            se,
            {
              count: N.filterCount,
              onClick: () => N.setDrawerOpen(!0)
            }
          ),
          /* @__PURE__ */ a(ne, { ...N.toolsProps, onRefresh: c })
        ] })
      }
    ),
    /* @__PURE__ */ a(re, { ...N.chipProps }),
    /* @__PURE__ */ a(
      Q,
      {
        columns: N.columns,
        data: D,
        keyField: (o) => o.id || o.queue_id,
        sorts: p,
        onSortsChange: d,
        ...N.tableProps,
        loading: b,
        footer: /* @__PURE__ */ a(j, { shown: D.length, total: i.length, noun: "message" }),
        emptyTitle: i.length === 0 ? "The mail queue is empty." : "No messages match this search.",
        emptyMessage: ""
      }
    ),
    /* @__PURE__ */ a(oe, { ...N.drawerProps })
  ] });
}
function ea() {
  return /* @__PURE__ */ a($e, {});
}
if (typeof document < "u" && !document.getElementById("serverkit-email-styles")) {
  const e = document.createElement("style");
  e.id = "serverkit-email-styles", e.textContent = _e, document.head.appendChild(e);
}
for (const [e, t] of Object.entries({ en: we, es: De }))
  pe.addResourceBundle(e, "translation", t, !0, !1);
export {
  ea as EmailPage
};
