"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import AuthSide from "@/components/AuthSide";
import { api, errText, setTenant, tenantSlug, tenantUrl, tokens } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [ws, setWs] = useState(""), [email, setEmail] = useState(""), [password, setPassword] = useState("");
  const [err, setErr] = useState(""), [busy, setBusy] = useState(false), [onSubdomain, setOnSub] = useState(false);
  useEffect(() => { const s = tenantSlug(); setWs(s); setOnSub(!!s && (location.hostname.startsWith(s + ".") )); }, []);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    const slug = ws.trim().toLowerCase();
    try {
      const target = tenantUrl(slug, "/login");
      if (target !== "/login") { window.location.href = target; return; }   // apex: hop to the gym's own subdomain first
      setTenant(slug);
      const d = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
      tokens.set(d.access, d.refresh);
      router.replace("/dashboard");
    } catch (e) { setErr(errText(e)); } finally { setBusy(false); }
  }
  return <div className="authwrap"><AuthSide /><form className="authform" onSubmit={submit}>
    <h2>Sign in to your gym</h2>
    {err && <div className="err" role="alert">{err}</div>}
    {!onSubdomain && <div><label htmlFor="ws">Workspace</label><div className="slug"><input id="ws" value={ws} onChange={(e) => setWs(e.target.value)} placeholder="hulkzone" required /><span>.fitssort.com</span></div></div>}
    <div><label htmlFor="em">Email</label><input id="em" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
    <div><label htmlFor="pw">Password</label><input id="pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
    <button className="btn-forest" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
    <p className="hint">New here? <Link href="/signup">Start your free trial</Link></p>
  </form></div>;
}
