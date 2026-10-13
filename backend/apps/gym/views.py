from django.db.models import Max, Q, Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from apps.core.permissions import IsTenantMember, HasFeature
from apps.billing.services import get_subscription
from . import models as m, serializers as s


class TenantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTenantMember, HasFeature]
    required_feature = None
    required_roles = None


class MemberViewSet(TenantViewSet):
    serializer_class = s.MemberSerializer
    required_feature = "members"
    search_fields = ["name", "phone", "email", "code"]
    ordering_fields = ["id", "name", "joined_at"]

    def get_queryset(self):
        qs = m.Member.objects.annotate(active_until=Max("packages__end_date", filter=Q(packages__status="active"))).order_by("-id")
        status = self.request.query_params.get("status")
        return qs.filter(status=status) if status else qs

    def perform_create(self, ser):
        limit = (get_subscription(self.request.tenant).plan.limits or {}).get("max_members")
        if limit and m.Member.objects.exclude(status="archived").count() >= limit:
            raise PermissionDenied({"code": "limit_reached", "detail": f"Your plan allows {limit} members. Upgrade to add more."})
        ser.save()

    def perform_destroy(self, inst):   # soft delete: invoices/payments reference members
        inst.status = "archived"
        inst.save(update_fields=["status"])


class PackageViewSet(TenantViewSet):
    serializer_class = s.PackageSerializer
    required_feature = "members.packages"
    search_fields = ["name"]

    def get_queryset(self):
        return m.Package.objects.all()

    def check_permissions(self, request):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            self.required_roles = ["owner", "manager"]
        super().check_permissions(request)


class MemberPackageViewSet(TenantViewSet):
    serializer_class = s.MemberPackageSerializer
    required_feature = "members.packages"
    http_method_names = ["get", "post", "head", "options"]
    search_fields = ["member__name", "member__phone"]

    def get_queryset(self):
        qs = m.MemberPackage.objects.select_related("member", "package").annotate(paid=Sum("payments__amount"))
        member = self.request.query_params.get("member")
        return qs.filter(member_id=member) if member else qs


class PaymentViewSet(TenantViewSet):
    serializer_class = s.PaymentSerializer
    required_feature = "payments"
    search_fields = ["member__name", "reference"]

    def get_queryset(self):
        return m.Payment.objects.select_related("member")

    def perform_create(self, ser):
        ser.save(received_by=self.request.user)


class ExpenseViewSet(TenantViewSet):
    serializer_class = s.ExpenseSerializer
    required_feature = "expenses"
    required_roles = ["owner", "manager"]
    search_fields = ["category", "note"]

    def get_queryset(self):
        return m.Expense.objects.all()


class AttendanceViewSet(TenantViewSet):
    serializer_class = s.AttendanceSerializer
    required_feature = "members.attendance"
    http_method_names = ["get", "post", "head", "options"]
    search_fields = ["member__name", "member__code"]

    def get_queryset(self):
        return m.Attendance.objects.select_related("member")

    def perform_create(self, ser):
        member = ser.validated_data["member"]
        today = timezone.localdate()
        if not m.MemberPackage.objects.filter(member=member, status="active", start_date__lte=today, end_date__gte=today).exists():
            raise PermissionDenied({"code": "no_active_package", "detail": f"{member.name} has no active membership"})
        ser.save(source="manual")


class InquiryViewSet(TenantViewSet):
    serializer_class = s.InquirySerializer
    required_feature = "crm.inquiries"
    search_fields = ["name", "phone", "interest"]

    def get_queryset(self):
        return m.Inquiry.objects.all()
