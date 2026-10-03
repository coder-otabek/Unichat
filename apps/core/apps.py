from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'

    def ready(self):
        # Server ishga tushganda DBdan sozlamalarni yuklaymiz
        try:
            from apps.core.settings_loader import load
            load()
        except Exception:
            pass

        # Embedding modelini oldindan yuklaymiz (birinchi so'rov tez bo'lsin)
        import threading
        def warmup():
            try:
                from django.conf import settings
                if getattr(settings, 'USE_LOCAL_EMBEDDINGS', True):
                    from apps.books.processor import _get_embed_model
                    model_name = getattr(settings, 'LOCAL_EMBED_MODEL',
                                         'paraphrase-multilingual-MiniLM-L12-v2')
                    _get_embed_model(model_name)
            except Exception:
                pass
        threading.Thread(target=warmup, daemon=True).start()