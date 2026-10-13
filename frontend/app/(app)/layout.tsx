"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";

// Nav registry: adding a module = one line. Filtered by enabled_features (and role) from /auth/me.
const NAV = [
  { href: "/dashboard", label: "Dashboard", feature: "dashboard" },
  { href: "/members", label: "Members", feature: "members" },
  { href: "/packages", label: "Packages", feature: "members.packages" },
  { href: "/memberships", label: "Sell membership", feature: "members.packages" },
  { href: "/payments", label: "Payments", feature: "payments" },
  { href: "/attendance", label: "Attendance", feature: "members.attendance" },
  { href: "/expenses", label: "Expenses", feature: "expenses", roles: ["owner", "manager"] },
  { href: "/crm", label: "CRM", feature: "crm.inquiries" },
  { href: "/settings", label: "Settings", feature: "settings", roles: ["owner"] },
];
function Shell({ children }: { children: React.ReactNode }) {
  const { me, has, logout } = useAuth(); const path = usePathname();
  const sub = me!.subscription;
  return <div className="app"><aside className="side"><div className="logo"><i />{me!.tenant.name}</div>
    {NAV.filter((n) => has(n.feature) && (!n.roles || n.roles.includes(me!.role))).map((n) => <Link key={n.href} href={n.href} className={path === n.href ? "act" : ""}>{n.label}</Link>)}
    <div className="sub">{sub?.plan} plan ({sub?.status})<br />{me!.email}<br /><a href="#" onClick={(e) => { e.preventDefault(); logout(); }}>Sign out</a></div></aside>
    <main className="main">
      {sub?.status === "trialing" && sub.trial_ends_at && <div className="banner"><span>Trial ends {new Date(sub.trial_ends_at).toLocaleDateString()}</span><Link href="/settings"><button className="btn-forest">Choose a plan</button></Link></div>}
      {sub && ["expired", "suspended", "past_due"].includes(sub.status) && <div className="banner"><span><b>Read-only:</b> your subscription is {sub.status}. Your data is safe.</span><Link href="/settings"><button className="btn-forest">Fix billing</button></Link></div>}
      {children}</main></div>;
}
export default function AppLayout({ children }: { children: React.ReactNode }) { return <AuthProvider><Shell>{children}</Shell></AuthProvider>; }
