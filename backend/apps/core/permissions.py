from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.billing.services import effective_features, is_writable
from apps.tenants.models import Membership


class IsTenantMember(BasePermission):
    """Token must be for THIS tenant and user must hold an active membership in it."""

    def has_permission(self, request, view):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound({"code": "tenant_not_found", "detail": "Unknown workspace"})
        if not request.user or not request.user.is_authenticated:
            return False
        if request.auth is not None and request.auth.get("tenant") != tenant.slug:
            raise PermissionDenied({"code": "wrong_tenant", "detail": "Token is not valid for this workspace"})
        m = Membership.objects.filter(tenant=tenant, user=request.user, is_active=True).first()
        if not m:
            raise PermissionDenied({"code": "not_a_member", "detail": "You do not belong to this workspace"})
        request.membership = m
        return True


class HasFeature(BasePermission):
    """View declares required_feature (and optionally required_roles). The API enforces it, not just the UI."""

    def has_permission(self, request, view):
        tenant = request.tenant
        if not hasattr(request, "_features"):
            request._features = effective_features(tenant)
        feature = getattr(view, "required_feature", None)
        if feature and feature not in request._features:
            raise PermissionDenied({"code": "feature_disabled", "feature": feature, "detail": f"'{feature}' is not enabled for this workspace"})
        roles = getattr(view, "required_roles", None)
        if roles and request.membership.role not in roles:
            raise PermissionDenied({"code": "role_forbidden", "detail": "Your role cannot do this"})
        if request.method not in SAFE_METHODS and not is_writable(tenant):
            raise PermissionDenied({"code": "subscription_inactive", "detail": "Subscription inactive: workspace is read-only"})
        return True
