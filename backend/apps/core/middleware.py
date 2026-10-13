from django.conf import settings
from apps.tenants.models import Tenant
from .tenancy import set_tenant, reset_tenant


def slug_from_request(request):
    slug = request.headers.get("X-Tenant", "").strip().lower()
    if slug:
        return slug
    host = request.get_host().split(":")[0].lower()
    base = settings.BASE_DOMAIN
    if host.endswith("." + base):
        return host[: -(len(base) + 1)]
    if host.endswith(".localhost"):
        return host[: -len(".localhost")]
    return ""


class TenantMiddleware:
    """Resolves request.tenant (None if absent/unknown) and puts it in a contextvar for the ORM."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        slug = slug_from_request(request)
        tenant = Tenant.objects.filter(slug=slug).exclude(status="canceled").first() if slug else None
        request.tenant = tenant
        token = set_tenant(tenant)
        try:
            return self.get_response(request)
        finally:
            reset_tenant(token)
