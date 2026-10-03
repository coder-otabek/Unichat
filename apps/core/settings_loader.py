"""
SiteSettings DBdan o'qib, Django settings ustiga yozadi.
RAG, LLM, embedding sozlamalari admin paneldan boshqariladi.
"""
from django.conf import settings as django_settings


def load():
    """
    Server ishga tushganda va har bir so'rovda (kesh orqali) chaqiriladi.
    DBdagi qiymatlar .env qiymatlarini ustib yozadi.
    """
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()

        django_settings.SITE_TITLE          = cfg.site_title
        django_settings.SITE_DESCRIPTION    = cfg.site_description
        django_settings.ALLOW_GUEST_CHAT    = cfg.allow_guest_chat

        django_settings.LLM_PROVIDER        = cfg.llm_provider
        django_settings.LLM_MODEL           = cfg.llm_model
        django_settings.LLM_TEMPERATURE     = cfg.llm_temperature
        django_settings.LLM_MAX_TOKENS      = cfg.llm_max_tokens

        if cfg.groq_api_key:
            django_settings.GROQ_API_KEY        = cfg.groq_api_key
        if cfg.openai_api_key:
            django_settings.OPENAI_API_KEY      = cfg.openai_api_key
        if cfg.anthropic_api_key:
            django_settings.ANTHROPIC_API_KEY   = cfg.anthropic_api_key
        if cfg.deepseek_api_key:
            django_settings.DEEPSEEK_API_KEY    = cfg.deepseek_api_key
        if cfg.together_api_key:
            django_settings.TOGETHER_API_KEY    = cfg.together_api_key
        if cfg.openrouter_api_key:
            django_settings.OPENROUTER_API_KEY  = cfg.openrouter_api_key
        if cfg.google_client_id:
            django_settings.GOOGLE_CLIENT_ID    = cfg.google_client_id

        django_settings.USE_LOCAL_EMBEDDINGS = cfg.use_local_embeddings
        django_settings.LOCAL_EMBED_MODEL    = cfg.local_embed_model
        django_settings.EMBED_MODEL          = cfg.openai_embed_model

        django_settings.CHUNK_SIZE           = cfg.chunk_size
        django_settings.CHUNK_OVERLAP        = cfg.chunk_overlap
        django_settings.TOP_K                = cfg.top_k
        django_settings.MIN_SCORE            = cfg.min_score
        django_settings.MAX_HISTORY_MESSAGES = cfg.max_history
        django_settings.MAX_FILE_MB          = cfg.max_file_mb

    except Exception:
        pass  # DB tayyor bo'lmasa .env qiymatlari ishlatiladi
