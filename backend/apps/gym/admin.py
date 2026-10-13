from django.contrib import admin
from . import models
# Tenant rows use the scoped manager by default, which is empty in admin: read via the unscoped manager.
class UnscopedAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return self.model.unscoped.all()
for m in (models.Member, models.Package, models.MemberPackage, models.Payment, models.Expense, models.Attendance, models.Inquiry):
    admin.site.register(m, UnscopedAdmin)
