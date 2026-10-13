from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.gym import views as gv
from . import views as v

router = DefaultRouter(trailing_slash=False)
router.register("members", gv.MemberViewSet, basename="member")
router.register("packages", gv.PackageViewSet, basename="package")
router.register("member-packages", gv.MemberPackageViewSet, basename="member-package")
router.register("payments", gv.PaymentViewSet, basename="payment")
router.register("expenses", gv.ExpenseViewSet, basename="expense")
router.register("attendance", gv.AttendanceViewSet, basename="attendance")
router.register("inquiries", gv.InquiryViewSet, basename="inquiry")

urlpatterns = [
    path("public/slug-available", v.SlugAvailable.as_view()),
    path("public/plans", v.PlansView.as_view()),
    path("public/signup", v.SignupView.as_view()),
    path("auth/login", v.LoginView.as_view()),
    path("auth/refresh", TokenRefreshView.as_view()),
    path("auth/me", v.MeView.as_view()),
    path("settings/features", v.FeatureSettingsView.as_view()),
    path("billing/subscription", v.SubscriptionView.as_view()),
    path("dashboard/summary", v.DashboardView.as_view()),
    path("", include(router.urls)),
]
