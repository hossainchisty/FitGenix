from django.contrib import admin
from .models import Tenant, Membership
admin.site.register(Tenant, list_display=("slug", "name", "status"))
admin.site.register(Membership, list_display=("tenant", "user", "role"))
