"use client";
import { useCallback, useEffect, useState } from "react";
import { api, errText } from "@/lib/api";

export type Field = { key: string; label: string; type?: "text" | "number" | "date" | "email" | "select"; required?: boolean; options?: [string, string][]; from?: { path: string; label: (r: any) => string }; initial?: string };
export type Col = { key: string; label: string; render?: (r: any) => React.ReactNode };
type Props = { title: string; path: string; cols: Col[]; fields: Field[]; hint?: string; deletable?: boolean; addLabel?: string; search?: boolean; noAdd?: boolean };

export default function ResourcePage({ title, path, cols, fields, hint, deletable, addLabel = "Add", search = true }: Props) {
  const [rows, setRows] = useState<any[]>([]), [count, setCount] = useState(0), [page, setPage] = useState(1), [q, setQ] = useState("");
  const [open, setOpen] = useState(false), [form, setForm] = useState<Record<string, string>>({}), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const [opts, setOpts] = useState<Record<string, [string, string][]>>({});
  const load = useCallback(() => api(`${path}?page=${page}&search=${encodeURIComponent(q)}`).then((d) => { setRows(d.results); setCount(d.count); }).catch((e) => setErr(errText(e))), [path, page, q]);
  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t); }, [load]);
  useEffect(() => { fields.filter((f) => f.from).forEach((f) => api(f.from!.path + "?page_size=200").then((d) => setOpts((o) => ({ ...o, [f.key]: d.results.map((r: any) => [String(r.id), f.from!.label(r)]) }))).catch(() => {})); }, []); // eslint-disable-line
  async function save(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const body: any = {}; fields.forEach((f) => { const v = form[f.key] ?? f.initial; if (v !== undefined && v !== "") body[f.key] = v; });
      await api(path, { method: "POST", body }); setOpen(false); setForm({}); setPage(1); await load();
    } catch (e) { setErr(errText(e)); } finally { setBusy(false); }
  }
  async function del(id: number) { if (!confirm("Remove this record?")) return; try { await api(`${path}/${id}`, { method: "DELETE" }); load(); } catch (e) { setErr(errText(e)); } }
  return <>
    <div className="bar"><div><h2>{title}</h2>{hint && <span className="hint">{hint}</span>}</div><button className="btn-lime" onClick={() => setOpen(!open)}>{open ? "Close" : addLabel}</button></div>
    {err && <div className="err" role="alert" style={{ marginBottom: 12 }}>{err}</div>}
    {open && <form className="card" onSubmit={save} style={{ marginBottom: 12 }}><div className="formgrid">{fields.map((f) => <div key={f.key}><label htmlFor={f.key}>{f.label}</label>
      {f.from || f.options ? <select id={f.key} required={f.required} value={form[f.key] ?? f.initial ?? ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}><option value="">Select...</option>{(opts[f.key] || f.options || []).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        : <input id={f.key} type={f.type || "text"} required={f.required} step={f.type === "number" ? "0.01" : undefined} value={form[f.key] ?? f.initial ?? ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />}</div>)}</div>
      <button className="btn-forest" disabled={busy}>{busy ? "Saving..." : "Save"}</button></form>}
    {search && <input placeholder="Search..." value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} style={{ maxWidth: 320, marginBottom: 12 }} aria-label="Search" />}
    <div className="card tablewrap"><table><thead><tr>{cols.map((c) => <th key={c.key}>{c.label}</th>)}{deletable && <th />}</tr></thead>
      <tbody>{rows.map((r) => <tr key={r.id}>{cols.map((c) => <td key={c.key}>{c.render ? c.render(r) : String(r[c.key] ?? "")}</td>)}{deletable && <td><button className="btn-ghost" onClick={() => del(r.id)}>Remove</button></td>}</tr>)}
        {!rows.length && <tr><td colSpan={cols.length + 1} className="hint">Nothing here yet. Use "{addLabel}" to create the first record.</td></tr>}</tbody></table></div>
    <div className="row" style={{ marginTop: 12 }}><button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span className="hint">{count} total, page {page}</span><button className="btn-ghost" disabled={page * 50 >= count} onClick={() => setPage(page + 1)}>Next</button></div>
  </>;
}
export const chip = (s: string) => <span className={`chip ${s}`}>{s}</span>;
export const money = (v: any) => "Tk." + Number(v).toLocaleString("en-US");
export const when = (v: string) => new Date(v).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
