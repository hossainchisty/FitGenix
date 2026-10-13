"""Tenant context + tenant-scoped ORM base. Fails CLOSED: no tenant in context => empty queryset."""
import contextvars
from django.db import models

_current = contextvars.ContextVar("current_tenant", default=None)


def set_tenant(tenant):
    return _current.set(tenant)


def reset_tenant(token):
    _current.reset(token)


def get_tenant():
    return _current.get()


class TenantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        t = get_tenant()
        return qs.filter(tenant_id=t.id) if t else qs.none()


class TenantOwnedModel(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, editable=False, related_name="+")
    objects = TenantManager()          # scoped (default)
    unscoped = models.Manager()        # platform/admin/seed use only

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            t = get_tenant()
            if not t:
                raise RuntimeError("Refusing to save tenant-owned row without a tenant in context")
            self.tenant_id = t.id
        super().save(*args, **kwargs)
