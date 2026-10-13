from django.contrib import admin
from .models import Plan, Subscription, FeatureOverride
admin.site.register(Plan); admin.site.register(Subscription, list_display=("tenant", "plan", "status", "trial_ends_at")); admin.site.register(FeatureOverride)
