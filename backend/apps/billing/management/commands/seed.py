"""python manage.py seed  -> plans + demo tenant `hulkzone` (owner@hulkzone.com / password123)."""
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.billing.features import PLAN_SEED
from apps.billing.models import Plan, Subscription
from apps.core.tenancy import reset_tenant, set_tenant
from apps.gym import models as g
from apps.tenants.models import Membership, Tenant


class Command(BaseCommand):
    def add_arguments(self, p):
        p.add_argument("--no-demo", action="store_true")

    def handle(self, *a, **o):
        for d in PLAN_SEED:
            Plan.objects.update_or_create(code=d["code"], defaults=d)
        self.stdout.write("plans ok")
        if o["no_demo"] or Tenant.objects.filter(slug="hulkzone").exists():
            return
        rnd = random.Random(7)
        now = timezone.now()
        user = User.objects.create_user("owner@hulkzone.com", "password123", full_name="Ratul")
        t = Tenant.objects.create(slug="hulkzone", name="HulkZone", status="active")
        Membership.objects.create(tenant=t, user=user, role="owner")
        Subscription.objects.create(tenant=t, plan=Plan.objects.get(code="growth"), status="active", current_period_end=now + timedelta(days=20))
        tok = set_tenant(t)
        try:
            pk = [g.Package.objects.create(name=n, duration_days=d, price=p) for n, d, p in [("Monthly", 30, 1500), ("Quarterly", 90, 4000), ("Yearly", 365, 14000)]]
            first = ["Rahim", "Karim", "Nabila", "Sadia", "Tanvir", "Mim", "Fahim", "Ayesha", "Imran", "Sumaiya"]
            for i in range(80):
                joined = (now - timedelta(days=rnd.randint(0, 120))).date()
                mem = g.Member.objects.create(name=f"{rnd.choice(first)} {chr(65 + i % 26)}.", phone=f"017{rnd.randint(10000000, 99999999)}", joined_at=joined)
                pkg = rnd.choice(pk)
                start = joined if rnd.random() < .7 else (now - timedelta(days=rnd.randint(0, 25))).date()
                mp = g.MemberPackage.objects.create(member=mem, package=pkg, start_date=start, end_date=start + timedelta(days=pkg.duration_days), price=pkg.price,
                                                    status="active" if start + timedelta(days=pkg.duration_days) >= now.date() else "expired")
                paid = pkg.price if rnd.random() < .85 else pkg.price / 2
                g.Payment.objects.create(member=mem, member_package=mp, amount=Decimal(paid), method=rnd.choice(["cash", "bkash", "nagad"]), paid_at=now - timedelta(days=rnd.randint(0, 29), hours=rnd.randint(0, 20)), received_by=user)
                if mp.status == "active":
                    for _ in range(rnd.randint(0, 25)):
                        hour = rnd.choice([6, 7, 8, 17, 18, 18, 19, 20])
                        day = (timezone.localtime(now) - timedelta(days=rnd.randint(0, 40))).replace(hour=hour, minute=rnd.randint(0, 59))
                        g.Attendance.objects.create(member=mem, checked_in_at=day)
            for d in range(30):
                for cat, amt in [("Equipment", 4000), ("Utilities", 2500), ("Cleaning", 800)]:
                    if rnd.random() < .25:
                        g.Expense.objects.create(category=cat, amount=amt, paid_on=(now - timedelta(days=d)).date())
            for i, st in enumerate(["new"] * 6 + ["contacted"] * 4 + ["trial"] * 3 + ["won"] * 3 + ["lost"] * 2):
                g.Inquiry.objects.create(name=f"Lead {i + 1}", phone="01800000000", interest="Weight loss", stage=st, follow_up_at=(now - timedelta(days=rnd.randint(-3, 3))).date())
        finally:
            reset_tenant(tok)
        self.stdout.write("demo tenant hulkzone ready: owner@hulkzone.com / password123")
