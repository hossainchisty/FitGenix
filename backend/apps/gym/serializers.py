from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import *


class MemberSerializer(serializers.ModelSerializer):
    active_until = serializers.DateField(read_only=True, required=False)

    class Meta:
        model = Member
        exclude = ("tenant",)
        read_only_fields = ("code",)


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        exclude = ("tenant",)


class MemberPackageSerializer(serializers.ModelSerializer):
    # pass the manager (not .all()) so the tenant filter is evaluated per request, never at import time
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects)
    package = serializers.PrimaryKeyRelatedField(queryset=Package.objects)
    member_name = serializers.CharField(source="member.name", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)
    paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, required=False)

    class Meta:
        model = MemberPackage
        exclude = ("tenant",)
        read_only_fields = ("end_date", "price", "status")

    def validate(self, data):
        pkg = data["package"]
        start = data.get("start_date") or timezone.localdate()
        discount = data.get("discount", 0)
        if discount > pkg.price:
            raise serializers.ValidationError({"discount": "Discount cannot exceed the package price"})
        data.update(start_date=start, end_date=start + timedelta(days=pkg.duration_days), price=pkg.price - discount, status="active")
        return data


class PaymentSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects)
    member_package = serializers.PrimaryKeyRelatedField(queryset=MemberPackage.objects, required=False, allow_null=True)
    member_name = serializers.CharField(source="member.name", read_only=True)

    class Meta:
        model = Payment
        exclude = ("tenant",)

    def validate(self, data):
        mp = data.get("member_package")
        if mp and mp.member_id != data["member"].id:
            raise serializers.ValidationError({"member_package": "This membership belongs to a different member"})
        if data["amount"] <= 0:
            raise serializers.ValidationError({"amount": "Amount must be positive"})
        return data


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        exclude = ("tenant",)


class AttendanceSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects)
    member_name = serializers.CharField(source="member.name", read_only=True)

    class Meta:
        model = Attendance
        exclude = ("tenant",)


class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        exclude = ("tenant",)
