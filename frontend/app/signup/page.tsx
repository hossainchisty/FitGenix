"use client";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AuthSide from "@/components/AuthSide";
import { IntervalToggle, Price, tk, usePlans } from "@/components/Pricing";
import { api, errText, setTenant, tenantUrl, tokens } from "@/lib/api";

function Form() {
  const q = useSearchParams(), router = useRouter(), plans = usePlans();
  const [plan, setPlan] = useState(q.get("plan") || "starter"), [iv, setIv] = useState<"month" | "year">(q.get("interval") === "year" ? "year" : "month");
  const [f, setF] = useState({ full_name: "", email: "", password: "", gym_name: "", slug: "" });
  const [slugMsg, setSlugMsg] = useState<{ ok: boolean; text: string } | null>(null), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: k === "slug" ? e.target.value.toLowerCase() : e.target.value });
  useEffect(() => {   // debounced availability check
    if (f.slug.length < 3) { setSlugMsg(null); return; }
    const t = setTimeout(() => api("/public/slug-available?slug=" + encodeURIComponent(f.slug), { auth: false }).then((d) => setSlugMsg({ ok: d.available, text: d.available ? `${f.slug}.fitssort.com is available` : d.reason })).catch(() => {}), 350);
    return () => clearTimeout(t);
  }, [f.slug]);
  const p = plans.find((x) => x.code === plan);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const d = await api("/public/signup", { method: "POST", auth: false, body: { ...f, plan, interval: iv } });
      const target = tenantUrl(d.tenant, "/login");
      if (target !== "/login") { window.location.href = target; return; }   // prod: sign in on the new subdomain
      setTenant(d.tenant); tokens.set(d.access, d.refresh); router.replace("/dashboard");
    } catch (e) { setErr(errText(e)); } finally { setBusy(false); }
  }
  return <div className="authwrap"><AuthSide /><form className="authform" onSubmit={submit}>
    <h2>Create your gym workspace</h2>
    {err && <div className="err" role="alert">{err}</div>}
    <IntervalToggle value={iv} onChange={setIv} />
    <div className="row">{plans.filter((x) => x.code !== "enterprise").map((x) => <button type="button" key={x.code} className={plan === x.code ? "btn-forest" : "btn-ghost"} onClick={() => setPlan(x.code)}>{x.name}</button>)}</div>
    <div><label htmlFor="n">Your name</label><input id="n" value={f.full_name} onChange={set("full_name")} required /></div>
    <div><label htmlFor="e">Email</label><input id="e" type="email" value={f.email} onChange={set("email")} required /></div>
    <div><label htmlFor="p">Password</label><input id="p" type="password" minLength={8} value={f.password} onChange={set("password")} required /></div>
    <div><label htmlFor="g">Gym name</label><input id="g" value={f.gym_name} onChange={set("gym_name")} required /></div>
    <div><label htmlFor="s">Workspace URL</label><div className="slug"><input id="s" value={f.slug} onChange={set("slug")} required /><span>.fitssort.com</span></div>
      {slugMsg && <div className={`hint ${slugMsg.ok ? "ok" : "bad"}`}>{slugMsg.text}</div>}</div>
    {p && <div className="summary">Selected package: <b>{p.name}</b>{p.trial_days ? ` (${p.trial_days}-day trial included, no card needed)` : ""}<br />{(iv === "year" ? p.price_year : p.price_month) && tk((iv === "year" ? p.price_year : p.price_month)!)} / {iv}{p.trial_days ? " after the trial" : ""}</div>}
    <button className="btn-forest" disabled={busy || slugMsg?.ok === false}>{busy ? "Creating..." : "Create my gym"}</button>
    <p className="hint">Already have a workspace? <Link href="/login">Sign in</Link></p>
  </form></div>;
}
export default function Signup() { return <Suspense><Form /></Suspense>; }
