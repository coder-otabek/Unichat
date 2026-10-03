from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('🌐 Sayt', {
            'fields': ('logo', 'site_title', 'site_description', 'allow_guest_chat', 'allow_register')
        }),
        ('🤖 AI Provayder', {
            'fields': ('llm_provider', 'llm_model', 'llm_temperature', 'llm_max_tokens'),
            'description': 'Groq modellar: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768'
        }),
        ('🔑 API Kalitlar', {
            'fields': (
                'groq_api_key', 'openai_api_key', 'anthropic_api_key',
                'deepseek_api_key', 'together_api_key', 'openrouter_api_key',
            ),
            'classes': ('collapse',),
        }),
        ('🔐 Google OAuth', {
            'fields': ('google_client_id',),
            'classes': ('collapse',),
        }),
        ('📐 Embedding', {
            'fields': ('use_local_embeddings', 'local_embed_model', 'openai_embed_model'),
            'classes': ('collapse',),
        }),
        ('📚 RAG Sozlamalari', {
            'fields': ('chunk_size', 'chunk_overlap', 'top_k', 'min_score', 'max_history'),
            'classes': ('collapse',),
        }),
        ('📁 Fayl', {
            'fields': ('max_file_mb',),
            'classes': ('collapse',),
        }),
        ('🌐 Tashqi veb qidiruv', {
            'fields': ('allow_web_search','web_search_provider','web_search_results','serpapi_key','google_cse_id','google_cse_key'),
            'description': 'Ichki bazada javob topilmasa internet qidiruvidan foydalanadi',
        }),
    )

    def has_add_permission(self, request):
        # Faqat bitta yozuv bo'lishi kerak
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False