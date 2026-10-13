"use client";
import { useEffect, useState } from "react";
import { api, errText } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { money } from "@/components/ResourcePage";

const delta = (cur: number, prev: number) => { if (!prev) return null; const p = Math.round(((cur - prev) / prev) * 100); return <span className={p >= 0 ? "up" : "dn"}>{p >= 0 ? "+" : ""}{p}% vs last period</span>; };
const hourLabel = (h: number | null) => (h === null ? "No data yet" : `Peak at ${h % 12 || 12}${h < 12 ? "am" : "pm"}`);

function Chart({ s }: { s: { date: string; revenue: number; expenses: number }[] }) {
  const w = 560, h = 170, max = Math.max(1, ...s.flatMap((d) => [d.revenue, d.expenses]));
  const pts = (k: "revenue" | "expenses") => s.map((d, i) => `${(i * w / (s.length - 1)).toFixed(0)},${(h - 6 - (d[k] / max) * (h - 12)).toFixed(0)}`).join(" ");
  return <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%" }} role="img" aria-label="Daily revenue versus expenses, last 30 days"><polyline fill="none" stroke="var(--forest)" strokeWidth="3" points={pts("revenue")} /><polyline fill="none" stroke="#a9b92c" strokeWidth="3" strokeDasharray="6 4" points={pts("expenses")} /></svg>;
}
function Meter({ label, n, total }: { label: string; n: number; total: number }) {
  return <><span className="hint">{label} {n}</span><div className="meter"><i style={{ width: `${total ? Math.round((100 * n) / total) : 0}%` }} /></div></>;
}

export default function Dashboard() {
  const { me } = useAuth();
  const [d, setD] = useState<any>(null), [err, setErr] = useState("");
  useEffect(() => { api("/dashboard/summary").then(setD).catch((e) => setErr(errText(e))); }, []);
  if (err) return <div className="err">{err}</div>;
  if (!d) return <div className="hint">Loading insights...</div>;
  const k = d.kpis, a = d.attention, hmax = Math.max(1, ...d.heatmap.flat());
  const hour = new Date().getHours(), greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  return <>
    <div className="bar"><div><h2>{greet}, {me!.full_name.split(" ")[0] || "there"}</h2><span className="hint">Here is how {me!.tenant.name} is doing</span></div></div>
    <div className="kpis">
      <div className="card kpi"><span className="hint">Active members</span><b>{k.active_members}</b>{delta(k.active_members, k.active_members_prev)}</div>
      {k.revenue_mtd !== undefined && <div className="card kpi"><span className="hint">Revenue (this month)</span><b>{money(k.revenue_mtd)}</b>{delta(k.revenue_mtd, k.revenue_prev_month)}</div>}
      <div className="card kpi"><span className="hint">New joins (30 days)</span><b>{k.new_joins_30d}</b>{delta(k.new_joins_30d, k.new_joins_prev_30d)}</div>
      <div className="card kpi"><span className="hint">Check-ins today</span><b>{k.checkins_today}</b><span className="hint">{hourLabel(k.peak_hour)}</span></div>
      {k.profit_mtd !== undefined && <div className="card kpi"><span className="hint">Cash profit (this month)</span><b>{money(k.profit_mtd)}</b><span className="hint">Payments minus expenses</span></div>}
    </div>
    <div className="cols">
      {d.series ? <div className="card"><h3>Revenue and expenses</h3><p className="hint">Solid: revenue. Dashed: expenses. Last 30 days.</p><Chart s={d.series} /></div> : <div className="card"><h3>Revenue</h3><p>Financial charts are visible to owners and managers.</p></div>}
      <div className="card"><h3>Needs your attention</h3><ul className="att">
        <li>Memberships expiring in 7 days<em>{a.expiring_7d}</em></li>
        {a.overdue_members !== undefined && <li>Unpaid balances ({money(a.overdue_amount)})<em>{a.overdue_members}</em></li>}
        <li>Active members absent 14+ days<em>{a.at_risk_14d}</em></li>
        {a.followups_due !== undefined && <li>Inquiries to follow up<em>{a.followups_due}</em></li>}</ul></div>
    </div>
    <div className="cols3">
      <div className="card"><h3>When people show up</h3><div className="heat" role="img" aria-label="Attendance by weekday and hour">{d.heatmap.flat().map((v: number, i: number) => <i key={i} title={`${v} check-ins`} style={{ background: `rgba(6,46,35,${(0.07 + (v / hmax) * 0.88).toFixed(2)})` }} />)}</div><p className="hint">Rows: Monday to Sunday. Columns: 12am to 11pm. Last 90 days.</p></div>
      <div className="card"><h3>Retention</h3><b style={{ fontSize: 30 }}>{d.retention.rate === null ? "n/a" : d.retention.rate + "%"}</b> <span className="hint">renewal rate</span><div className="meter"><i style={{ width: `${d.retention.rate || 0}%` }} /></div><p className="hint">{d.retention.ended_30d} memberships ended in the last 30 days, {d.retention.renewed} renewed.</p></div>
      {d.funnel && <div className="card"><h3>Inquiry funnel</h3>{(() => { const f = d.funnel, t = f.new + f.contacted + f.trial + f.won + f.lost; return <><Meter label="All inquiries" n={t} total={t} /><Meter label="Trial or later" n={f.trial + f.won} total={t} /><Meter label="Joined" n={f.won} total={t} /></>; })()}</div>}
    </div>
  </>;
}
