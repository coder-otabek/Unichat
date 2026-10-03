from django.contrib import admin
from .models import Session, Message

class MsgInline(admin.TabularInline):
    model=Message; extra=0; can_delete=False; max_num=0
    readonly_fields=['role','content','tokens_used','created_at']

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display=['user','title','created_at','updated_at']
    search_fields=['user__email','title']
    readonly_fields=['created_at','updated_at']
    inlines=[MsgInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display=['session','role','short_content','tokens_used','created_at']
    list_filter=['role']
    def short_content(self,o): return o.content[:60]
    short_content.short_description='Mazmun'
