from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.tenancy import TenantOwnedModel


class Member(TenantOwnedModel):
    STATUS = [("active", "Active"), ("frozen", "Frozen"), ("archived", "Archived")]
    code = models.CharField(max_length=12, blank=True)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    gender = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="active")
    joined_at = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("tenant", "code")]
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        # NOTE: count-based codes can race under heavy concurrency; use a locked Counter row at scale.
        if not self.code:
            from apps.core.tenancy import get_tenant
            t = self.tenant_id or (get_tenant().id if get_tenant() else None)
            if not t:
                raise RuntimeError("Refusing to save tenant-owned row without a tenant in context")
            self.code = f"M{Member.unscoped.filter(tenant_id=t).count() + 1:05d}"
        super().save(*args, **kwargs)


class Package(TenantOwnedModel):
    name = models.CharField(max_length=80)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    visit_limit = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class MemberPackage(TenantOwnedModel):
    STATUS = [("active", "Active"), ("expired", "Expired"), ("frozen", "Frozen"), ("canceled", "Canceled")]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="packages")
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)        # after discount
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="active")

    class Meta:
        ordering = ["-id"]


class Payment(TenantOwnedModel):
    METHODS = [("cash", "Cash"), ("bkash", "bKash"), ("nagad", "Nagad"), ("card", "Card"), ("bank", "Bank")]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="payments")
    member_package = models.ForeignKey(MemberPackage, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHODS, default="cash")
    reference = models.CharField(max_length=60, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-paid_at"]


class Expense(TenantOwnedModel):
    category = models.CharField(max_length=60)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-paid_on", "-id"]


class Attendance(TenantOwnedModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="attendance")
    checked_in_at = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=12, default="manual")

    class Meta:
        ordering = ["-checked_in_at"]


class Inquiry(TenantOwnedModel):
    STAGES = [("new", "New"), ("contacted", "Contacted"), ("trial", "Trial"), ("won", "Won"), ("lost", "Lost")]
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    interest = models.CharField(max_length=120, blank=True)
    stage = models.CharField(max_length=10, choices=STAGES, default="new")
    follow_up_at = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-id"]
