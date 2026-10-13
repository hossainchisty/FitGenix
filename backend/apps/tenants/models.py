from django.conf import settings
from django.db import models


class Tenant(models.Model):
    STATUS = [("trialing", "Trialing"), ("active", "Active"), ("past_due", "Past due"), ("suspended", "Suspended"), ("canceled", "Canceled")]
    slug = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    status = models.CharField(max_length=12, choices=STATUS, default="trialing")
    timezone = models.CharField(max_length=40, default="Asia/Dhaka")
    currency = models.CharField(max_length=3, default="BDT")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.slug


class Membership(models.Model):
    ROLES = [("owner", "Owner"), ("manager", "Manager"), ("frontdesk", "Front desk"), ("instructor", "Instructor")]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=12, choices=ROLES, default="frontdesk")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "user")]
