"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, tokens } from "./api";

export type Me = {
  user_id: number; email: string; full_name: string; role: string; is_tenant_admin: boolean;
  tenant: { slug: string; name: string; timezone: string; currency: string };
  subscription: { plan: string; interval: string; status: string; trial_ends_at: string | null } | null;
  enabled_features: string[]; limits: Record<string, number>;
};
const Ctx = createContext<{ me: Me | null; has: (f: string) => boolean; reload: () => Promise<void>; logout: () => void }>({ me: null, has: () => false, reload: async () => {}, logout: () => {} });
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const router = useRouter();
  const reload = useCallback(async () => {
    try { setMe(await api<Me>("/auth/me")); } catch { tokens.clear(); router.replace("/login"); }
  }, [router]);
  useEffect(() => { reload().finally(() => setReady(true)); }, [reload]);
  const logout = () => { tokens.clear(); router.replace("/login"); };
  const has = (f: string) => !!me?.enabled_features.includes(f);
  if (!ready || !me) return <div className="center hint">Loading your gym...</div>;
  return <Ctx.Provider value={{ me, has, reload, logout }}>{children}</Ctx.Provider>;
}
