"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
export type PlanT = { code: string; name: string; trial_days: number; price_month: string | null; price_year: string | null };
export const tk = (n: string | number) => "Tk." + Number(n).toLocaleString("en-US");
export function usePlans() {
  const [plans, setPlans] = useState<PlanT[]>([]);
  useEffect(() => { api<PlanT[]>("/public/plans", { auth: false }).then(setPlans).catch(() => {}); }, []);
  return plans;
}
export function IntervalToggle({ value, onChange }: { value: string; onChange: (v: "month" | "year") => void }) {
  return <div className="toggle"><button className={value === "month" ? "on" : ""} onClick={() => onChange("month")} type="button">Monthly</button><button className={value === "year" ? "on" : ""} onClick={() => onChange("year")} type="button">Yearly, 2 months free</button></div>;
}
export function Price({ p, interval }: { p: PlanT; interval: string }) {
  const v = interval === "year" ? p.price_year : p.price_month;
  return v ? <div className="price">{tk(v)} <small>/{interval}</small></div> : <div className="price">Custom</div>;
}
export default function Pricing() {
  const plans = usePlans();
  const [iv, setIv] = useState<"month" | "year">("month");
  return <><IntervalToggle value={iv} onChange={setIv} /><div className="grid3">{plans.map((p) => (
    <div key={p.code} className={`card plan ${p.code === "starter" ? "hi" : ""}`}>
      {p.trial_days ? <span className="badge">{p.trial_days}-day trial</span> : <span className="hint">{p.code === "enterprise" ? "Talk to us" : "No trial"}</span>}
      <h3>{p.name}</h3><Price p={p} interval={iv} />
      {p.code === "enterprise" ? <a href="mailto:hello@fitssort.com"><button className="btn-forest" type="button">Contact sales</button></a>
        : <Link href={`/signup?plan=${p.code}&interval=${iv}`}><button className={p.code === "starter" ? "btn-lime" : "btn-forest"} type="button">{p.trial_days ? "Start free trial" : `Choose ${p.name}`}</button></Link>}
    </div>))}</div></>;
}
