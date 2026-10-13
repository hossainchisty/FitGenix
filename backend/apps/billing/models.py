from django.db import models


class Plan(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=40)
    trial_days = models.PositiveIntegerField(default=0)
    price_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)   # null = custom
    price_year = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    features = models.JSONField(default=list)
    limits = models.JSONField(default=dict)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Subscription(models.Model):
    STATUS = [("trialing", "Trialing"), ("active", "Active"), ("past_due", "Past due"), ("suspended", "Suspended"), ("canceled", "Canceled"), ("expired", "Expired")]
    tenant = models.OneToOneField("tenants.Tenant", on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    interval = models.CharField(max_length=5, choices=[("month", "Monthly"), ("year", "Yearly")], default="month")
    status = models.CharField(max_length=10, choices=STATUS, default="trialing")
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)


class FeatureOverride(models.Model):
    """grant = add a feature the plan lacks (add-on / sales deal). hide = owner hides a feature."""
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="feature_overrides")
    feature = models.CharField(max_length=60)
    mode = models.CharField(max_length=5, choices=[("grant", "Grant"), ("hide", "Hide")])

    class Meta:
        unique_together = [("tenant", "feature")]
