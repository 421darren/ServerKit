import M from "i18next";
import { jsx as a, jsxs as l, Fragment as U } from "react/jsx-runtime";
import { forwardRef as W, createElement as L, useState as o, useEffect as H } from "react";
import { api as g, useToast as Z, useConfirm as Q, useTableSort as X, useColumnVisibility as aa, useTableChrome as ea, EmptyState as na, Button as m, Pill as la, GridViewPicker as sa, GridFilterButton as ia, GridToolsMenu as ta, GridChips as ra, DataTable as oa, DataTableFooter as ca, GridFilterDrawer as da, Modal as ba, Label as K, Input as ua, Select as pa, SelectTrigger as fa, SelectValue as ma, SelectContent as ha, SelectItem as ga } from "serverkit-sdk";
import { useTranslation as ya } from "react-i18next";
const Ia = {
  fail2banTab: {
    activeJails: "Active jails",
    areYouSureYouWantTo: "Are you sure you want to unban {{ip}} from {{jail}}?",
    banIp: "Ban IP",
    banIpAddress: "Ban IP Address",
    banned: "Banned",
    fail2banInstalledSuccessfully: "Fail2ban installed successfully",
    fail2banNotInstalled: "Fail2ban Not Installed",
    fail2banStatus: "Fail2ban Status",
    failedToBanIp: "Failed to ban IP: {{message}}",
    failedToInstall: "Failed to install: {{message}}",
    failedToUnban: "Failed to unban: {{message}}",
    installFail2banToProtectAgainstBrute: "Install Fail2ban to protect against brute force attacks.",
    ipBannedIn: "IP {{banIP}} banned in {{banJail}}",
    ipUnbanned: "IP {{ip}} unbanned",
    jail: "Jail",
    loadingFail2banStatus: "Loading Fail2ban status…",
    noIpsAreCurrentlyBanned: "No IPs are currently banned.",
    none: "None",
    totalBanned: "Total banned",
    totalBannedIps: "Total banned IPs",
    unban: "Unban",
    unbanIp: "Unban IP"
  },
  securityTabs: {
    fail2ban: "Fail2ban"
  }
}, va = {
  app: Ia
}, Ta = {
  fail2banTab: {
    activeJails: "Jails activos",
    areYouSureYouWantTo: "¿Seguro que quieres desbloquear {{ip}} de {{jail}}?",
    banIp: "Bloquear IP",
    banIpAddress: "Bloquear dirección IP",
    banned: "Bloqueadas",
    fail2banInstalledSuccessfully: "Fail2ban se instaló correctamente",
    fail2banNotInstalled: "Fail2ban no está instalado",
    fail2banStatus: "Estado de Fail2ban",
    failedToBanIp: "No se pudo bloquear la IP: {{message}}",
    failedToInstall: "No se pudo instalar: {{message}}",
    failedToUnban: "No se pudo desbloquear: {{message}}",
    installFail2banToProtectAgainstBrute: "Instala Fail2ban para protegerte de ataques de fuerza bruta.",
    ipBannedIn: "IP {{banIP}} bloqueada en {{banJail}}",
    ipUnbanned: "IP {{ip}} desbloqueada",
    jail: "Jail",
    loadingFail2banStatus: "Cargando el estado de Fail2ban...",
    noIpsAreCurrentlyBanned: "No hay ninguna IP bloqueada en este momento.",
    none: "Ninguno",
    totalBanned: "Total bloqueadas",
    totalBannedIps: "Total de IPs bloqueadas",
    unban: "Desbloquear",
    unbanIp: "Desbloquear IP"
  },
  securityTabs: {
    fail2ban: "Fail2ban"
  }
}, Na = {
  app: Ta
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
var Fa = {
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
const Pa = (e) => e.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const x = (e, s) => {
  const v = W(
    ({
      color: r = "currentColor",
      size: y = 24,
      strokeWidth: T = 2,
      absoluteStrokeWidth: N,
      className: F = "",
      children: c,
      ...d
    }, b) => L(
      "svg",
      {
        ref: b,
        ...Fa,
        width: y,
        height: y,
        stroke: r,
        strokeWidth: N ? Number(T) * 24 / Number(y) : T,
        className: ["lucide", `lucide-${Pa(e)}`, F].join(" "),
        ...d
      },
      [
        ...s.map(([P, u]) => L(P, u)),
        ...Array.isArray(c) ? c : [c]
      ]
    )
  );
  return v.displayName = `${e}`, v;
};
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Ba = x("Ban", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m4.9 4.9 14.2 14.2", key: "1m5liu" }]
]);
/**
 * @license lucide-react v0.363.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const wa = x("Shield", [
  [
    "path",
    {
      d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
      key: "oel41y"
    }
  ]
]);
async function Sa() {
  return g.request("/security/fail2ban/status");
}
async function ja() {
  return g.request("/security/fail2ban/install", { method: "POST" });
}
async function ka(e) {
  return g.request(`/security/fail2ban/jails/${e}`);
}
async function Ca() {
  return g.request("/security/fail2ban/bans");
}
async function _a(e, s = null) {
  return g.request("/security/fail2ban/unban", {
    method: "POST",
    body: { ip: e, jail: s }
  });
}
async function Aa(e, s = "sshd") {
  return g.request("/security/fail2ban/ban", {
    method: "POST",
    body: { ip: e, jail: s }
  });
}
const h = {
  getFail2banStatus: Sa,
  installFail2ban: ja,
  getFail2banJailStatus: ka,
  getAllFail2banBans: Ca,
  fail2banUnban: _a,
  fail2banBan: Aa
}, V = "sshd", qa = [
  {
    // The drive-by traffic. Usually the longest list on the page and the
    // one you scan for a source you recognise rather than act on row by row.
    name: "SSH bans",
    state: {
      sorts: [{ key: "ip", direction: "asc" }],
      hiddenKeys: [],
      columnFilters: {
        match: "all",
        rules: [{ id: "f2b1", field: "jail", op: "any", value: [V] }]
      }
    }
  },
  {
    // Everything the SSH view buries: web-auth, WordPress and per-app jails.
    // A ban here means something reached an application, so it is the half
    // worth reading first. Jail before IP, so each jail stays together.
    name: "App & web jail bans",
    state: {
      sorts: [{ key: "jail", direction: "asc" }, { key: "ip", direction: "asc" }],
      hiddenKeys: [],
      columnFilters: {
        match: "all",
        rules: [{ id: "f2b2", field: "jail", op: "none", value: [V] }]
      }
    }
  }
], Ja = () => {
  var _, A, q;
  const { t: e } = ya(), [s, v] = o(null), [r, y] = o([]), [T, N] = o({}), [F, c] = o(!0), [d, b] = o(!1), [P, u] = o(!1), [I, j] = o(""), [B, $] = o("sshd"), p = Z(), { confirm: D } = Q(), { sorts: k, setSorts: C } = X({ storageKey: "serverkit-table-fail2ban-bans-sort" }), {
    hiddenKeys: E,
    setHiddenKeys: O
  } = aa({ storageKey: "serverkit-table-fail2ban-bans-cols" });
  H(() => {
    f();
  }, []);
  const f = async () => {
    var n;
    c(!0);
    try {
      const [i, J] = await Promise.all([
        h.getFail2banStatus(),
        h.getAllFail2banBans().catch(() => ({ banned_ips: [] }))
      ]);
      if (v(i), y(J.banned_ips || []), i != null && i.installed && ((n = i.jails) != null && n.length)) {
        const w = await Promise.all(
          i.jails.map(async (S) => {
            try {
              return [S, await h.getFail2banJailStatus(S)];
            } catch {
              return [S, null];
            }
          })
        );
        N(Object.fromEntries(w));
      } else
        N({});
    } catch (i) {
      console.error("Failed to load Fail2ban data:", i);
    } finally {
      c(!1);
    }
  }, R = async () => {
    b(!0);
    try {
      await h.installFail2ban(), p.success(e("app.fail2banTab.fail2banInstalledSuccessfully", "Fail2ban installed successfully")), await f();
    } catch (n) {
      p.error(e("app.fail2banTab.failedToInstall", "Failed to install: {{message}}", { message: n.message }));
    } finally {
      b(!1);
    }
  }, Y = async () => {
    if (I.trim()) {
      b(!0);
      try {
        await h.fail2banBan(I, B), p.success(e("app.fail2banTab.ipBannedIn", "IP {{banIP}} banned in {{banJail}}", { banIP: I, banJail: B })), u(!1), j(""), await f();
      } catch (n) {
        p.error(e("app.fail2banTab.failedToBanIp", "Failed to ban IP: {{message}}", { message: n.message }));
      } finally {
        b(!1);
      }
    }
  }, z = async (n, i) => {
    if (await D({
      title: e("app.fail2banTab.unbanIp", "Unban IP"),
      message: e("app.fail2banTab.areYouSureYouWantTo", "Are you sure you want to unban {{ip}} from {{jail}}?", { ip: n, jail: i }),
      confirmText: e("app.fail2banTab.unban", "Unban"),
      variant: "warning"
    }))
      try {
        await h.fail2banUnban(n, i), p.success(e("app.fail2banTab.ipUnbanned", "IP {{ip}} unbanned", { ip: n })), await f();
      } catch (w) {
        p.error(e("app.fail2banTab.failedToUnban", "Failed to unban: {{message}}", { message: w.message }));
      }
  }, t = ea({
    columns: [
      {
        key: "ip",
        headerKey: "common.labels.ipAddress",
        header: "IP Address",
        sortable: !0,
        hideable: !1,
        sortValue: (n) => n.ip || "",
        cellClassName: "sk-cell-mono sec-ip--red",
        render: (n) => n.ip
      },
      {
        key: "jail",
        headerKey: "app.fail2banTab.jail",
        header: "Jail",
        sortable: !0,
        // Declared, not inferred: a host with two jails and two bans fails
        // the enum cardinality test and would fall back to text, which
        // turns the jail pick-list into a typed fragment and both views
        // above into no-ops. `value` is what the rules read.
        type: "enum",
        value: (n) => n.jail || "",
        sortValue: (n) => n.jail || "",
        render: (n) => /* @__PURE__ */ a("span", { className: "sk-tag", children: n.jail })
      },
      {
        key: "actions",
        headerKey: "common.labels.actions",
        header: "Actions",
        sortable: !1,
        hideable: !1,
        render: (n) => /* @__PURE__ */ a(m, { variant: "secondary", size: "sm", onClick: () => z(n.ip, n.jail), children: e("app.fail2banTab.unban", "Unban") })
      }
    ],
    rows: r,
    viewPageKey: "security-fail2ban",
    builtinViews: qa,
    noun: "bans",
    sorts: k,
    setSorts: C,
    hiddenKeys: E,
    setHiddenKeys: O
  }), G = t.shownRows;
  return F ? /* @__PURE__ */ a("div", { className: "loading-sm", children: e("app.fail2banTab.loadingFail2banStatus", "Loading Fail2ban status…") }) : /* @__PURE__ */ l("div", { className: "fail2ban-tab", children: [
    s != null && s.installed ? /* @__PURE__ */ l(U, { children: [
      /* @__PURE__ */ l("div", { className: "card", children: [
        /* @__PURE__ */ l("div", { className: "card-header", children: [
          /* @__PURE__ */ a("h3", { children: e("app.fail2banTab.fail2banStatus", "Fail2ban Status") }),
          /* @__PURE__ */ l("div", { className: "card-actions", children: [
            /* @__PURE__ */ a(m, { variant: "default", size: "sm", onClick: () => u(!0), children: e("app.fail2banTab.banIp", "Ban IP") }),
            /* @__PURE__ */ a(m, { variant: "outline", size: "sm", onClick: f, children: e("common.actions.refresh", "Refresh") })
          ] })
        ] }),
        /* @__PURE__ */ a("div", { className: "card-body", children: /* @__PURE__ */ l("div", { className: "sec-rows", children: [
          /* @__PURE__ */ l("div", { className: "sk-info-row", children: [
            /* @__PURE__ */ a("span", { className: "k", children: e("common.labels.service", "Service") }),
            /* @__PURE__ */ a(la, { kind: s.service_running ? "green" : "red", children: s.service_running ? "Running" : "Stopped" })
          ] }),
          /* @__PURE__ */ l("div", { className: "sk-info-row", children: [
            /* @__PURE__ */ a("span", { className: "k", children: e("common.labels.version", "Version") }),
            /* @__PURE__ */ a("span", { className: "v", children: s.version || "Unknown" })
          ] }),
          /* @__PURE__ */ l("div", { className: "sk-info-row", children: [
            /* @__PURE__ */ a("span", { className: "k", children: e("app.fail2banTab.activeJails", "Active jails") }),
            ((_ = s.jails) == null ? void 0 : _.length) > 0 ? /* @__PURE__ */ a("span", { className: "sec-chiprow", children: s.jails.map((n) => /* @__PURE__ */ a("span", { className: "sk-tag", children: n }, n)) }) : /* @__PURE__ */ a("span", { className: "v", children: e("app.fail2banTab.none", "None") })
          ] }),
          /* @__PURE__ */ l("div", { className: "sk-info-row", children: [
            /* @__PURE__ */ a("span", { className: "k", children: e("app.fail2banTab.totalBannedIps", "Total banned IPs") }),
            /* @__PURE__ */ a("span", { className: `v ${r.length > 0 ? "sec-v-amber" : ""}`, children: r.length })
          ] })
        ] }) })
      ] }),
      ((A = s.jails) == null ? void 0 : A.length) > 0 && /* @__PURE__ */ a("div", { className: "f2b-jails", children: s.jails.map((n) => {
        const i = T[n] || {};
        return /* @__PURE__ */ l("div", { className: "f2b-jail", children: [
          /* @__PURE__ */ l("div", { className: "f2b-jail__name", children: [
            /* @__PURE__ */ a(Ba, { size: 15 }),
            n
          ] }),
          /* @__PURE__ */ l("div", { className: "f2b-jail__stats", children: [
            /* @__PURE__ */ l("div", { className: "f2b-jail__stat", children: [
              /* @__PURE__ */ a("div", { className: "f2b-jail__v f2b-jail__v--amber", children: i.currently_banned ?? "—" }),
              /* @__PURE__ */ a("div", { className: "f2b-jail__l", children: e("app.fail2banTab.banned", "Banned") })
            ] }),
            /* @__PURE__ */ l("div", { className: "f2b-jail__stat", children: [
              /* @__PURE__ */ a("div", { className: "f2b-jail__v", children: i.currently_failed ?? "—" }),
              /* @__PURE__ */ a("div", { className: "f2b-jail__l", children: e("common.state.failed", "Failed") })
            ] }),
            /* @__PURE__ */ l("div", { className: "f2b-jail__stat", children: [
              /* @__PURE__ */ a("div", { className: "f2b-jail__v", children: i.total_banned ?? "—" }),
              /* @__PURE__ */ a("div", { className: "f2b-jail__l", children: e("app.fail2banTab.totalBanned", "Total banned") })
            ] })
          ] })
        ] }, n);
      }) }),
      /* @__PURE__ */ a(
        sa,
        {
          views: t.views,
          label: "bans",
          onCreate: t.createView,
          actions: /* @__PURE__ */ l(U, { children: [
            /* @__PURE__ */ a(
              ia,
              {
                count: t.filterCount,
                onClick: () => t.setDrawerOpen(!0)
              }
            ),
            /* @__PURE__ */ a(ta, { ...t.toolsProps, onRefresh: f })
          ] })
        }
      ),
      /* @__PURE__ */ a(ra, { ...t.chipProps }),
      r.length === 0 ? /* @__PURE__ */ a("div", { className: "card", children: /* @__PURE__ */ a("p", { className: "text-muted", children: e("app.fail2banTab.noIpsAreCurrentlyBanned", "No IPs are currently banned.") }) }) : /* @__PURE__ */ a("div", { className: "card sec-flush", children: /* @__PURE__ */ a(
        oa,
        {
          columns: t.columns,
          data: r,
          keyField: (n) => `${n.ip}-${n.jail}`,
          sorts: k,
          onSortsChange: C,
          ...t.tableProps,
          footer: /* @__PURE__ */ a(
            ca,
            {
              shown: G.length,
              total: r.length,
              noun: "banned IP"
            }
          )
        }
      ) })
    ] }) : /* @__PURE__ */ a(
      na,
      {
        icon: wa,
        title: e("app.fail2banTab.fail2banNotInstalled", "Fail2ban Not Installed"),
        description: e("app.fail2banTab.installFail2banToProtectAgainstBrute", "Install Fail2ban to protect against brute force attacks."),
        action: /* @__PURE__ */ a(m, { variant: "default", onClick: R, disabled: d, children: d ? "Installing..." : "Install Fail2ban" })
      }
    ),
    /* @__PURE__ */ a(da, { ...t.drawerProps }),
    /* @__PURE__ */ l(ba, { open: P, onClose: () => u(!1), title: e("app.fail2banTab.banIpAddress", "Ban IP Address"), children: [
      /* @__PURE__ */ l("div", { className: "form-group", children: [
        /* @__PURE__ */ a(K, { children: e("common.labels.ipAddress", "IP Address") }),
        /* @__PURE__ */ a(
          ua,
          {
            type: "text",
            value: I,
            onChange: (n) => j(n.target.value),
            placeholder: "192.168.1.100"
          }
        )
      ] }),
      /* @__PURE__ */ l("div", { className: "form-group", children: [
        /* @__PURE__ */ a(K, { children: e("app.fail2banTab.jail", "Jail") }),
        /* @__PURE__ */ l(pa, { value: B, onValueChange: $, children: [
          /* @__PURE__ */ a(fa, { children: /* @__PURE__ */ a(ma, {}) }),
          /* @__PURE__ */ a(ha, { children: (q = s == null ? void 0 : s.jails) == null ? void 0 : q.map((n) => /* @__PURE__ */ a(ga, { value: n, children: n }, n)) })
        ] })
      ] }),
      /* @__PURE__ */ l("div", { className: "modal-footer", children: [
        /* @__PURE__ */ a(m, { variant: "outline", onClick: () => u(!1), children: e("common.actions.cancel", "Cancel") }),
        /* @__PURE__ */ a(m, { variant: "destructive", onClick: Y, disabled: d || !I.trim(), children: d ? "Banning..." : "Ban IP" })
      ] })
    ] })
  ] });
};
function Da() {
  return /* @__PURE__ */ a(Ja, {});
}
for (const [e, s] of Object.entries({ en: va, es: Na }))
  M.addResourceBundle(e, "translation", s, !0, !1);
export {
  Da as Fail2banTabPage
};
