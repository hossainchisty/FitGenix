export type ApiError = { status: number; data: any };
const BASE = process.env.NEXT_PUBLIC_BASE_DOMAIN || "";

export function tenantSlug(): string {
  if (typeof window === "undefined") return "";
  const h = window.location.hostname;
  if (BASE && h.endsWith("." + BASE)) return h.slice(0, -(BASE.length + 1));
  const m = h.match(/^([a-z0-9-]+)\.localhost$/);
  if (m) return m[1];
  return localStorage.getItem("tenant") || "";   // plain localhost dev fallback
}
export const setTenant = (s: string) => localStorage.setItem("tenant", s.toLowerCase());
export const tokens = {
  get: () => ({ access: localStorage.getItem("access"), refresh: localStorage.getItem("refresh") }),
  set: (a: string, r?: string) => { localStorage.setItem("access", a); if (r) localStorage.setItem("refresh", r); },
  clear: () => { localStorage.removeItem("access"); localStorage.removeItem("refresh"); },
};
/** After auth on the apex domain, hop to the gym's own subdomain (production). */
export function tenantUrl(slug: string, path: string) {
  if (BASE && !window.location.hostname.startsWith(slug + ".")) return `${window.location.protocol}//${slug}.${BASE}${path}`;
  return path;
}

let refreshing: Promise<boolean> | null = null;
async function refresh(): Promise<boolean> {
  const { refresh } = tokens.get();
  if (!refresh) return false;
  refreshing ||= fetch("/api/v1/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh }) })
    .then(async (r) => { if (!r.ok) return false; const d = await r.json(); tokens.set(d.access, d.refresh); return true; })
    .finally(() => { refreshing = null; });
  return refreshing;
}

export async function api<T = any>(path: string, opts: { method?: string; body?: unknown; auth?: boolean } = {}, retry = true): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", "X-Tenant": tenantSlug() };
  const { access } = tokens.get();
  if (opts.auth !== false && access) headers.Authorization = `Bearer ${access}`;
  const res = await fetch(`/api/v1${path}`, { method: opts.method || "GET", headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
  if (res.status === 401 && retry && opts.auth !== false && (await refresh())) return api<T>(path, opts, false);
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw { status: res.status, data } as ApiError;
  return data as T;
}
export function errText(e: any): string {
  const d = e?.data;
  if (!d) return "Something went wrong. Check your connection and try again.";
  if (typeof d === "string") return d;
  if (d.detail && typeof d.detail === "string") return d.detail;
  if (d.detail?.detail) return d.detail.detail;
  return Object.entries(d).map(([k, v]: any) => `${k}: ${Array.isArray(v) ? v.join(" ") : typeof v === "object" ? v.detail ?? JSON.stringify(v) : v}`).join(" | ");
}
