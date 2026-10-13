from django.utils import timezone
from .models import Subscription, FeatureOverride


def get_subscription(tenant):
    sub = Subscription.objects.select_related("plan").filter(tenant=tenant).first()
    if sub and sub.status == "trialing" and sub.trial_ends_at and sub.trial_ends_at < timezone.now():
        sub.status = "expired"   # lazy expiry; a Celery beat job should also do this
        sub.save(update_fields=["status"])
    return sub


def is_writable(tenant):
    sub = get_subscription(tenant)
    return bool(sub and sub.status in ("trialing", "active"))


def hidden_features(tenant):
    return [o.feature for o in FeatureOverride.objects.filter(tenant=tenant, mode="hide")]


def effective_features(tenant):
    """(plan features + granted) - hidden (prefix aware: hiding 'payments' hides 'payments.invoices')."""
    sub = get_subscription(tenant)
    if not sub:
        return set()
    ov = list(FeatureOverride.objects.filter(tenant=tenant))
    feats = set(sub.plan.features) | {o.feature for o in ov if o.mode == "grant"}
    hide = [o.feature for o in ov if o.mode == "hide"]
    return {f for f in feats if not any(f == h or f.startswith(h + ".") for h in hide)}
