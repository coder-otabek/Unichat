from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base
from .models import User

@admin.register(User)
class UserAdmin(Base):
    list_display    = ['email','full_name','is_active','is_staff','date_joined']
    list_filter     = ['is_active','is_staff','is_superuser']
    search_fields   = ['email','full_name']
    ordering        = ['-date_joined']
    readonly_fields = ['date_joined','last_login']
    fieldsets = (
        (None,           {'fields':('email','password')}),
        ("Ma'lumotlar",  {'fields':('full_name',)}),
        ('Huquqlar',     {'fields':('is_active','is_staff','is_superuser','groups','user_permissions')}),
        ('Vaqt',         {'fields':('date_joined','last_login')}),
    )
    add_fieldsets = ((None,{'classes':('wide',),'fields':('email','full_name','password1','password2','is_staff')}),)
