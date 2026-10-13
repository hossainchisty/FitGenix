"use client";
import { useEffect, useState } from "react";
import { api, errText } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { IntervalToggle, Price, usePlans } from "@/components/Pricing";

export default function Settings() {
  const { me, reload } = useAuth(); const plans = usePlans();
  const [avail, setAvail] = useState<string[]>([]), [hidden, setHidden] = useState<string[]>([]), [msg, setMsg] = useState(""), [err, setErr] = useState("");
  const [iv, setIv] = useState<"month" | "year">((me!.subscription?.interval as any) || "month");
  useEffect(() => { api("/settings/features").then((d) => { setAvail(d.available); setHidden(d.hidden); }).catch((e) => setErr(errText(e))); }, []);
  const toggle = (f: string) => setHidden(hidden.includes(f) ? hidden.filter((x) => x !== f) : [...hidden, f]);
  async function saveFeatures() { setErr(""); try { await api("/settings/features", { method: "PUT", body: { hidden } }); await reload(); setMsg("Saved. Hidden features are now off for everyone in this gym."); } catch (e) { setErr(errText(e)); } }
  async function change(plan: string) { setErr(""); try { await api("/billing/subscription", { method: "POST", body: { plan, interval: iv } }); await reload(); setMsg("Plan updated."); } catch (e) { setErr(errText(e)); } }
  return <>
    <div className="bar"><h2>Settings</h2></div>
    {err && <div className="err" role="alert" style={{ marginBottom: 12 }}>{err}</div>}{msg && <div className="summary" style={{ marginBottom: 12 }}>{msg}</div>}
    <div className="card" style={{ marginBottom: 12 }}><h3>Modules</h3><p className="hint" style={{ marginBottom: 10 }}>Hide what your gym does not use. The sidebar and the API both respect this. Dashboard and Settings cannot be hidden.</p>
      <div className="formgrid">{avail.map((f) => <label key={f} className="row" style={{ fontWeight: 500 }}><input type="checkbox" style={{ width: "auto" }} checked={!hidden.includes(f)} onChange={() => toggle(f)} />{f}</label>)}</div><button className="btn-forest" onClick={saveFeatures}>Save modules</button></div>
    <div className="card"><h3>Your plan: {me!.subscription?.plan} ({me!.subscription?.status})</h3><IntervalToggle value={iv} onChange={setIv} />
      <div className="grid3">{plans.filter((p) => p.code !== "enterprise").map((p) => <div className="card" key={p.code}><h3>{p.name}</h3><Price p={p} interval={iv} /><button className="btn-forest" style={{ marginTop: 10 }} disabled={me!.subscription?.plan === p.code && me!.subscription?.interval === iv} onClick={() => change(p.code)}>{me!.subscription?.plan === p.code ? "Current plan" : `Switch to ${p.name}`}</button></div>)}</div>
      <p className="hint" style={{ marginTop: 10 }}>Online payment is not connected yet, so plan changes are applied without charging. Wire your payment gateway before launch.</p></div>
  </>;
}
