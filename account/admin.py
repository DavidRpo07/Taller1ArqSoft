from django.contrib import admin
from .models import PendingUser

# Register your models here.


@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'confirmation_code')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'confirmation_code')