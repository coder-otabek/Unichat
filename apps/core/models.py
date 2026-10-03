from django.db import models


class SiteSettings(models.Model):
    """
    Singleton model — barcha AI va sayt sozlamalari.
    Django admin orqali boshqariladi.
    """

    # ── Sayt ──────────────────────────────────────────────────
    site_title       = models.CharField(max_length=100, default='UniChat')
    site_description = models.TextField(default='AI yordamchi — bilim bazasidan javob beradi')
    logo = models.ImageField(
        upload_to='site/', blank=True, null=True,
        verbose_name='Sayt logosi',
        help_text='PNG yoki JPG, tavsiya: 128×128 px. Favicon va barcha joylarda ishlatiladi.'
    )
    allow_guest_chat = models.BooleanField(default=True, verbose_name='Mehmonlarga ruxsat')
    allow_register   = models.BooleanField(default=True, verbose_name="Ro'yxatdan o'tishga ruxsat")

    # ── LLM ───────────────────────────────────────────────────
    LLM_PROVIDERS = [
        ('groq',       'Groq'),
        ('openai',     'OpenAI'),
        ('anthropic',  'Anthropic'),
        ('deepseek',   'DeepSeek'),
        ('together',   'Together AI'),
        ('openrouter', 'OpenRouter'),
        ('ollama',     'Ollama (lokal)'),
    ]
    llm_provider    = models.CharField(max_length=20, choices=LLM_PROVIDERS, default='groq')
    llm_model       = models.CharField(max_length=100, default='llama-3.3-70b-versatile',
                        help_text='Groq: llama-3.3-70b-versatile | OpenAI: gpt-4o-mini | Anthropic: claude-3-haiku-20240307')
    llm_temperature = models.FloatField(default=0.7)
    llm_max_tokens  = models.IntegerField(default=2000)

    # ── API kalitlar ───────────────────────────────────────────
    groq_api_key       = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='Groq API Key')
    openai_api_key     = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='OpenAI API Key')
    anthropic_api_key  = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='Anthropic API Key')
    deepseek_api_key   = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='DeepSeek API Key')
    together_api_key   = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='Together AI API Key')
    openrouter_api_key = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='OpenRouter API Key')
    google_client_id   = models.CharField(max_length=200, blank=True, default='',
                           verbose_name='Google OAuth Client ID',
                           help_text='Google Cloud Console → OAuth 2.0 Client ID')

    # ── Embedding ──────────────────────────────────────────────
    use_local_embeddings = models.BooleanField(default=True,
                             verbose_name='Lokal embedding (sentence-transformers)',
                             help_text='False bo\'lsa OpenAI embedding ishlatiladi')
    local_embed_model    = models.CharField(max_length=200,
                             default='paraphrase-multilingual-MiniLM-L12-v2')
    openai_embed_model   = models.CharField(max_length=100,
                             default='text-embedding-3-small')

    # ── RAG ────────────────────────────────────────────────────
    chunk_size    = models.IntegerField(default=800,  help_text='Matn bo\'lak hajmi (so\'z)')
    chunk_overlap = models.IntegerField(default=150,  help_text='Bo\'laklar orasidagi o\'rtacha')
    top_k         = models.IntegerField(default=5,    help_text='Nechta manba qaytarilsin')
    min_score     = models.FloatField(default=0.25,   help_text='Minimal o\'xshashlik (0-1)')
    max_history   = models.IntegerField(default=10,   help_text='Suhbat tarixidan nechta xabar')

    # ── Fayl ───────────────────────────────────────────────────
    max_file_mb   = models.IntegerField(default=50)

    # ── Tashqi veb qidiruv ────────────────────────────────────
    allow_web_search = models.BooleanField(
        default=False,
        verbose_name='Tashqi veb qidiruv',
        help_text='Ichki manbadan javob topilmasa, internetdan izlaydi'
    )
    web_search_provider = models.CharField(
        max_length=20,
        choices=[('duckduckgo','DuckDuckGo (bepul)'),('serpapi','SerpAPI'),('google','Google CSE')],
        default='duckduckgo',
        verbose_name='Qidiruv provayderi'
    )
    serpapi_key     = models.CharField(max_length=200, blank=True, default='', verbose_name='SerpAPI Key')
    google_cse_id   = models.CharField(max_length=200, blank=True, default='', verbose_name='Google CSE ID')
    google_cse_key  = models.CharField(max_length=200, blank=True, default='', verbose_name='Google CSE API Key')
    web_search_results = models.IntegerField(default=3, verbose_name='Natijalar soni (1-5)')

    class Meta:
        verbose_name        = 'Sayt sozlamalari'
        verbose_name_plural = 'Sayt sozlamalari'

    def __str__(self):
        return f'Sozlamalar — {self.llm_provider} / {self.llm_model}'

    def save(self, *args, **kwargs):
        # Singleton: faqat bitta yozuv bo'ladi
        self.pk = 1
        super().save(*args, **kwargs)
        _invalidate_cache()

    @classmethod
    def get(cls):
        """Sozlamalarni olish — keshdan yoki DBdan"""
        obj = _get_cached()
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            _set_cache(obj)
        return obj


# ── Oddiy xotira keshi (thread-safe yetarli) ─────────────────
_cache = {}

def _get_cached():
    return _cache.get('settings')

def _set_cache(obj):
    _cache['settings'] = obj

def _invalidate_cache():
    _cache.clear()