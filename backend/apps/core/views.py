import re
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Count, F, Max, Q, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from apps.billing.features import ALL_FEATURES, NEVER_HIDE
from apps.billing.models import FeatureOverride, Plan, Subscription
from apps.billing.services import effective_features, get_subscription, hidden_features
from apps.gym import models as g
from apps.tenants.models import Membership, Tenant
from .permissions import HasFeature, IsTenantMember

User = get_user_model()
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,28})[a-z0-9]$")


def slug_problem(slug):
    if not SLUG_RE.match(slug or ""):
        return "Use 3-30 lowercase letters, numbers or dashes"
    if slug in settings.RESERVED_SLUGS:
        return "That name is reserved"
    if Tenant.objects.filter(slug=slug).exists():
        return "That workspace URL is taken"
    return None


def issue_tokens(user, tenant):
    refresh = RefreshToken.for_user(user)
    refresh["tenant"] = tenant.slug        # access token inherits this claim
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def me_payload(request):
    t, user, mem = request.tenant, request.user, request.membership
    sub = get_subscription(t)
    return {
        "user_id": user.id, "email": user.email, "full_name": user.full_name,
        "tenant": {"slug": t.slug, "name": t.name, "timezone": t.timezone, "currency": t.currency},
        "role": mem.role, "is_tenant_admin": mem.role == "owner", "permissions": {},
        "subscription": {"plan": sub.plan.code, "interval": sub.interval, "status": sub.status,
                         "trial_ends_at": sub.trial_ends_at, "current_period_end": sub.current_period_end} if sub else None,
        "enabled_features": sorted(effective_features(t)),
        "limits": sub.plan.limits if sub else {},
    }


class PublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


class SlugAvailable(PublicView):
    def get(self, request):
        slug = request.query_params.get("slug", "").lower()
        problem = slug_problem(slug)
        return Response({"available": problem is None, "reason": problem})


class PlansView(PublicView):
    def get(self, request):
        return Response([{"code": p.code, "name": p.name, "trial_days": p.trial_days, "price_month": p.price_month,
                          "price_year": p.price_year, "features": p.features} for p in Plan.objects.filter(is_public=True).order_by("id")])


class SignupView(PublicView):
    throttle_scope = "signup"

    @transaction.atomic
    def post(self, request):
        d = request.data
        slug = str(d.get("slug", "")).lower()
        errors = {}
        if (p := slug_problem(slug)):
            errors["slug"] = p
        email = str(d.get("email", "")).strip().lower()
        if "@" not in email:
            errors["email"] = "Enter a valid email"
        plan = Plan.objects.filter(code=d.get("plan", "starter"), is_public=True).first()
        if not plan or plan.code == "enterprise":
            errors["plan"] = "Choose Starter or Growth (Enterprise is by quote)"
        if not str(d.get("gym_name", "")).strip():
            errors["gym_name"] = "Gym name is required"
        user = User.objects.filter(email=email).first()
        if user:
            if not user.check_password(d.get("password", "")):
                errors["email"] = "This email already has an account; enter its password or sign in"
        else:
            try:
                validate_password(d.get("password", ""))
            except DjangoValidationError as e:
                errors["password"] = list(e.messages)
        if errors:
            raise ValidationError(errors)
        if not user:
            user = User.objects.create_user(email, d["password"], full_name=str(d.get("full_name", ""))[:120])
        interval = "year" if d.get("interval") == "year" else "month"
        tenant = Tenant.objects.create(slug=slug, name=d["gym_name"].strip()[:120], status="trialing" if plan.trial_days else "active")
        Membership.objects.create(tenant=tenant, user=user, role="owner")
        now = timezone.now()
        Subscription.objects.create(
            tenant=tenant, plan=plan, interval=interval, status="trialing" if plan.trial_days else "active",
            trial_ends_at=now + timedelta(days=plan.trial_days) if plan.trial_days else None,
            current_period_end=None if plan.trial_days else now + timedelta(days=365 if interval == "year" else 30))
        return Response({"tenant": tenant.slug, **issue_tokens(user, tenant)}, status=status.HTTP_201_CREATED)


class LoginView(PublicView):
    throttle_scope = "auth"

    def post(self, request):
        tenant = request.tenant
        if not tenant:
            raise NotFound({"code": "tenant_not_found", "detail": "Unknown workspace"})
        user = authenticate(request, username=str(request.data.get("email", "")).lower(), password=request.data.get("password", ""))
        # same error for bad password and non-member: do not reveal who belongs to which gym
        if not user or not Membership.objects.filter(tenant=tenant, user=user, is_active=True).exists():
            raise ValidationError({"detail": "Wrong email or password"})
        return Response(issue_tokens(user, tenant))


class MeView(APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        return Response(me_payload(request))


class FeatureSettingsView(APIView):
    """Owner hides/shows modules for the workspace. Hidden features are enforced by the API too."""
    permission_classes = [IsTenantMember, HasFeature]
    required_feature = "settings"
    required_roles = ["owner"]

    def get(self, request):
        sub = get_subscription(request.tenant)
        return Response({"available": sorted(set(sub.plan.features) - NEVER_HIDE), "hidden": hidden_features(request.tenant)})

    def put(self, request):
        sub = get_subscription(request.tenant)
        hide = request.data.get("hidden", [])
        bad = [h for h in hide if h not in ALL_FEATURES or h in NEVER_HIDE]
        if not isinstance(hide, list) or bad:
            raise ValidationError({"hidden": f"Cannot hide: {bad}" if bad else "Expected a list"})
        FeatureOverride.objects.filter(tenant=request.tenant, mode="hide").delete()
        FeatureOverride.objects.bulk_create([FeatureOverride(tenant=request.tenant, feature=h, mode="hide") for h in set(hide)])
        return Response({"hidden": sorted(set(hide)), "enabled_features": sorted(effective_features(request.tenant))})


class SubscriptionView(APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        return Response(me_payload(request)["subscription"])

    def post(self, request):
        """Change plan. PAYMENT IS NOT WIRED YET: upgrades are free until a gateway (SSLCommerz/bKash) creates an invoice first."""
        if request.membership.role != "owner":
            raise PermissionDenied({"code": "role_forbidden", "detail": "Only the owner can change the plan"})
        plan = Plan.objects.filter(code=request.data.get("plan"), is_public=True).first()
        if not plan or plan.code == "enterprise":
            raise ValidationError({"plan": "Choose Starter or Growth. Enterprise is by quote."})
        sub = get_subscription(request.tenant)
        limit = (plan.limits or {}).get("max_members")
        if limit and g.Member.objects.exclude(status="archived").count() > limit:
            raise ValidationError({"plan": f"You have more than {limit} members; archive some before downgrading"})
        sub.plan, sub.interval = plan, ("year" if request.data.get("interval") == "year" else "month")
        if sub.status in ("trialing", "expired") and not plan.trial_days:
            sub.status, sub.trial_ends_at = "active", None
        sub.save()
        return Response(me_payload(request)["subscription"])


def f(x):
    return float(x or 0)


class DashboardView(APIView):
    permission_classes = [IsTenantMember, HasFeature]
    required_feature = "dashboard"

    def get(self, request):
        feats = effective_features(request.tenant)
        money = request.membership.role in ("owner", "manager")
        now = timezone.localtime()
        today = now.date()
        mstart = today.replace(day=1)
        pend = mstart - timedelta(days=1)
        pstart = pend.replace(day=1)
        P, E, A, M, MP = g.Payment.objects, g.Expense.objects, g.Attendance.objects, g.Member.objects, g.MemberPackage.objects

        active_q = Q(packages__status="active", packages__end_date__gte=today)
        active_members = M.filter(active_q).distinct().count()
        active_prev = M.filter(joined_at__lt=mstart).filter(active_q).distinct().count()
        new_30 = M.filter(joined_at__gte=today - timedelta(days=30)).count()
        new_prev_30 = M.filter(joined_at__gte=today - timedelta(days=60), joined_at__lt=today - timedelta(days=30)).count()
        checkins_today = A.filter(checked_in_at__date=today).count()

        # peak hour today-ish + heatmap (Mon-first rows, last 90 days)
        heat = [[0] * 24 for _ in range(7)]
        for r in A.filter(checked_in_at__gte=now - timedelta(days=90)).annotate(wd=ExtractWeekDay("checked_in_at"), hr=ExtractHour("checked_in_at")).values("wd", "hr").annotate(n=Count("id")):
            heat[(r["wd"] + 5) % 7][r["hr"]] += r["n"]
        peak = max(range(24), key=lambda h: sum(row[h] for row in heat)) if any(any(r) for r in heat) else None

        expiring = MP.filter(status="active", end_date__gte=today, end_date__lte=today + timedelta(days=7)).values("member").distinct().count()
        at_risk = M.filter(active_q).distinct().exclude(attendance__checked_in_at__gte=now - timedelta(days=14)).count()

        ended = list(MP.filter(end_date__gte=today - timedelta(days=30), end_date__lt=today).values("member_id", "end_date"))
        renewed = sum(1 for e in ended if MP.filter(member_id=e["member_id"], start_date__gte=e["end_date"] - timedelta(days=7)).exclude(end_date=e["end_date"]).exists())
        out = {
            "as_of": now, "role": request.membership.role,
            "kpis": {"active_members": active_members, "active_members_prev": active_prev, "new_joins_30d": new_30, "new_joins_prev_30d": new_prev_30,
                     "checkins_today": checkins_today, "peak_hour": peak},
            "attention": {"expiring_7d": expiring, "at_risk_14d": at_risk},
            "heatmap": heat,
            "retention": {"ended_30d": len(ended), "renewed": renewed, "rate": round(100 * renewed / len(ended)) if ended else None},
        }
        if money:
            rev = lambda a, b: f(P.filter(paid_at__date__gte=a, paid_at__date__lte=b).aggregate(s=Sum("amount"))["s"])
            exp = lambda a, b: f(E.filter(paid_on__gte=a, paid_on__lte=b).aggregate(s=Sum("amount"))["s"])
            days = [today - timedelta(days=i) for i in range(29, -1, -1)]
            pr = {r["d"]: f(r["s"]) for r in P.filter(paid_at__date__gte=days[0]).annotate(d=TruncDate("paid_at")).values("d").annotate(s=Sum("amount"))}
            ex = {r["paid_on"]: f(r["s"]) for r in E.filter(paid_on__gte=days[0]).values("paid_on").annotate(s=Sum("amount"))}
            dues = [(mp.price - (mp.paid or 0), mp.member_id) for mp in MP.exclude(status="canceled").annotate(paid=Sum("payments__amount"))]
            dues = [d for d in dues if d[0] > 0]
            out["kpis"].update(revenue_mtd=rev(mstart, today), revenue_prev_month=rev(pstart, pend), expenses_mtd=exp(mstart, today),
                               profit_mtd=rev(mstart, today) - exp(mstart, today))
            out["attention"].update(overdue_amount=f(sum(d[0] for d in dues)), overdue_members=len({d[1] for d in dues}))
            out["series"] = [{"date": d.isoformat(), "revenue": pr.get(d, 0), "expenses": ex.get(d, 0)} for d in days]
        if "crm.inquiries" in feats:
            c = dict(g.Inquiry.objects.values_list("stage").annotate(n=Count("id")))
            out["funnel"] = {k: c.get(k, 0) for k in ("new", "contacted", "trial", "won", "lost")}
            out["attention"]["followups_due"] = g.Inquiry.objects.filter(follow_up_at__lte=today).exclude(stage__in=["won", "lost"]).count()
        return Response(out)
