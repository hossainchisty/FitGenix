from django.core.management import call_command
from rest_framework.test import APITestCase


class Base(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()   # reset throttle counters between tests
        call_command("seed", "--no-demo", verbosity=0)

    def signup(self, slug, email, plan="starter"):
        r = self.client.post("/api/v1/public/signup", dict(slug=slug, email=email, password="Str0ngPass!9", gym_name=slug.title(), plan=plan), format="json")
        assert r.status_code == 201, r.content
        return r.json()

    def call(self, method, path, tenant, token, data=None):
        h = {"HTTP_X_TENANT": tenant}
        if token:
            h["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return getattr(self.client, method)("/api/v1" + path, data, format="json", **h)


class TenantFlowTests(Base):
    def test_signup_trial_and_me(self):
        a = self.signup("alpha", "a@x.com")
        me = self.call("get", "/auth/me", "alpha", a["access"]).json()
        self.assertEqual(me["subscription"]["status"], "trialing")
        self.assertIn("members", me["enabled_features"])
        self.assertNotIn("pos", me["enabled_features"])    # not in Starter
        self.assertTrue(me["is_tenant_admin"])

    def test_slug_rules(self):
        self.assertFalse(self.client.get("/api/v1/public/slug-available?slug=www").json()["available"])
        self.signup("alpha", "a@x.com")
        self.assertFalse(self.client.get("/api/v1/public/slug-available?slug=alpha").json()["available"])

    def test_tenant_isolation(self):
        a, b = self.signup("alpha", "a@x.com"), self.signup("beta", "b@x.com")
        r = self.call("post", "/members", "alpha", a["access"], {"name": "Alpha Guy"})
        self.assertEqual(r.status_code, 201)
        mid = r.json()["id"]
        # beta cannot see or touch alpha's member
        self.assertEqual(self.call("get", "/members", "beta", b["access"]).json()["count"], 0)
        self.assertEqual(self.call("get", f"/members/{mid}", "beta", b["access"]).status_code, 404)
        # alpha's token against beta's workspace is rejected
        self.assertEqual(self.call("get", "/members", "beta", a["access"]).status_code, 403)
        # cross-tenant FK injection: beta pays for alpha's member
        pkg = self.call("post", "/packages", "beta", b["access"], {"name": "M", "duration_days": 30, "price": "1000"}).json()
        r = self.call("post", "/member-packages", "beta", b["access"], {"member": mid, "package": pkg["id"]})
        self.assertEqual(r.status_code, 400)

    def test_feature_gate_enforced_by_api(self):
        a = self.signup("alpha", "a@x.com")                    # Starter has no CRM
        r = self.call("get", "/inquiries", "alpha", a["access"])
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["code"], "feature_disabled")
        g = self.signup("gamma", "g@x.com", plan="growth")
        self.assertEqual(self.call("get", "/inquiries", "gamma", g["access"]).status_code, 200)

    def test_hide_feature(self):
        g = self.signup("gamma", "g@x.com", plan="growth")
        r = self.call("put", "/settings/features", "gamma", g["access"], {"hidden": ["expenses"]})
        self.assertNotIn("expenses", r.json()["enabled_features"])
        self.assertEqual(self.call("get", "/expenses", "gamma", g["access"]).status_code, 403)
        self.assertEqual(self.call("put", "/settings/features", "gamma", g["access"], {"hidden": ["settings"]}).status_code, 400)

    def test_sell_package_pay_checkin_dashboard(self):
        a = self.signup("alpha", "a@x.com")
        tk = a["access"]
        mem = self.call("post", "/members", "alpha", tk, {"name": "Rahim"}).json()
        self.assertEqual(mem["code"], "M00001")
        self.assertEqual(self.call("post", "/attendance", "alpha", tk, {"member": mem["id"]}).status_code, 403)  # no package yet
        pkg = self.call("post", "/packages", "alpha", tk, {"name": "Monthly", "duration_days": 30, "price": "1500"}).json()
        mp = self.call("post", "/member-packages", "alpha", tk, {"member": mem["id"], "package": pkg["id"], "discount": "100"}).json()
        self.assertEqual(mp["price"], "1400.00")
        self.assertEqual(self.call("post", "/payments", "alpha", tk, {"member": mem["id"], "member_package": mp["id"], "amount": "400", "method": "bkash"}).status_code, 201)
        self.assertEqual(self.call("post", "/attendance", "alpha", tk, {"member": mem["id"]}).status_code, 201)
        d = self.call("get", "/dashboard/summary", "alpha", tk).json()
        self.assertEqual(d["kpis"]["active_members"], 1)
        self.assertEqual(d["kpis"]["revenue_mtd"], 400.0)
        self.assertEqual(d["attention"]["overdue_amount"], 1000.0)
        self.assertEqual(d["kpis"]["checkins_today"], 1)
        self.assertNotIn("funnel", d)                            # Starter: no CRM widget data

    def test_expired_trial_is_read_only(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.billing.models import Subscription
        a = self.signup("alpha", "a@x.com")
        Subscription.objects.filter(tenant__slug="alpha").update(trial_ends_at=timezone.now() - timedelta(days=1))
        self.assertEqual(self.call("get", "/members", "alpha", a["access"]).status_code, 200)
        r = self.call("post", "/members", "alpha", a["access"], {"name": "X"})
        self.assertEqual((r.status_code, r.json()["code"]), (403, "subscription_inactive"))

    def test_login_and_wrong_workspace(self):
        self.signup("alpha", "a@x.com"); self.signup("beta", "b@x.com")
        ok = self.client.post("/api/v1/auth/login", {"email": "a@x.com", "password": "Str0ngPass!9"}, format="json", HTTP_X_TENANT="alpha")
        self.assertEqual(ok.status_code, 200)
        bad = self.client.post("/api/v1/auth/login", {"email": "a@x.com", "password": "Str0ngPass!9"}, format="json", HTTP_X_TENANT="beta")
        self.assertEqual(bad.status_code, 400)

    def test_unscoped_orm_fails_closed(self):
        from apps.gym.models import Member
        self.assertEqual(Member.objects.count(), 0)              # no tenant in context -> nothing
        with self.assertRaises(RuntimeError):
            Member(name="x").save()
