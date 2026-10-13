"use client";
import Pricing from "@/components/Pricing";
import { tenantSlug } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const FEATURES = [["Members and packages", "Sell, renew and freeze memberships. Every member has one timeline."], ["Attendance", "Check people in at the desk. See your peak hours at a glance."], ["Payments", "Take cash, bKash or Nagad. See who still owes you."], ["Expenses and profit", "Log rent and salaries. Know your real cash profit."], ["CRM", "Follow every inquiry until it joins or says no."], ["Reports", "Revenue, retention and attendance in one place."]];
export default function Landing() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  useEffect(() => { if (tenantSlug()) router.replace("/dashboard"); else setChecked(true); }, [router]);   // gym subdomain => straight to the app
  if (!checked) return null;
  return <>
    <div className="dark"><div className="wrap"><nav className="top"><div className="logo"><i />fitgenix</div><div className="row"><Link href="/login"><button className="btn-ghost" style={{ color: "#eef3e8", borderColor: "#1b3a2d" }}>Sign in</button></Link><Link href="/signup"><button className="btn-lime">Start free trial</button></Link></div></nav>
      <div className="hero"><h1>Run your whole gym from one place.</h1><p>Members, attendance, payments, packages and reports for owners, managers and front-desk staff. Know who is coming, who is paying, and who is about to leave.</p><Link href="/signup"><button className="btn-lime">Start your 14-day trial</button></Link></div></div></div>
    <section className="sec"><div className="wrap"><h2>Everything the front desk touches, in one tab</h2><div className="grid3">{FEATURES.map(([t, d]) => <div className="card" key={t}><h3>{t}</h3><p>{d}</p></div>)}</div></div></section>
    <section className="sec" style={{ paddingTop: 0 }}><div className="wrap"><h2>Pick a plan. Change it anytime.</h2><Pricing /></div></section>
  </>;
}
