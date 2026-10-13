from django.contrib import admin
from .models import User
admin.site.register(User, list_display=("email", "full_name", "is_staff"))
