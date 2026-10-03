"""
Universal LLM + RAG — sozlamalar SiteSettings DBdan olinadi
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

SYSTEM_BOOK = """Siz UniChat — o'zbek tilidagi bilimli AI yordamchisiz.
Berilgan kitob bo'laklari asosida to'liq va aniq javob bering.
Javobni o'zbek tilida yozing. Markdown formatlashdan foydalaning.
Kontekstda ma'lumot bo'lmasa faqat shuni ayting: ma'lumot bazada yo'q."""

SYSTEM_WEB = """Siz UniChat — o'zbek tilidagi bilimli AI yordamchisiz.
Kitob bazasida ma'lumot topilmadi. Quyidagi internet natijalariga asoslanib javob bering.
Javobni o'zbek tilida, aniq va foydali qilib yozing. Markdown formatlashdan foydalaning.
Manba sifatida faqat berilgan internet ma'lumotlaridan foydalaning."""

SYSTEM_NONE = """Siz UniChat — o'zbek tilidagi bilimli AI yordamchisiz.
Javobni o'zbek tilida yozing. Mavzu haqida umumiy bilimingizdan foydalaning."""

PROVIDERS = {
    'openai':    {'base_url': None,                                   'key': 'OPENAI_API_KEY'},
    'groq':      {'base_url': 'https://api.groq.com/openai/v1',       'key': 'GROQ_API_KEY'},
    'deepseek':  {'base_url': 'https://api.deepseek.com/v1',          'key': 'DEEPSEEK_API_KEY'},
    'together':  {'base_url': 'https://api.together.xyz/v1',          'key': 'TOGETHER_API_KEY'},
    'openrouter':{'base_url': 'https://openrouter.ai/api/v1',         'key': 'OPENROUTER_API_KEY'},
    'ollama':    {'base_url': 'http://localhost:11434/v1',             'key': None},
}


def _cfg():
    """Hozirgi sozlamalar (DB → .env fallback)"""
    from django.conf import settings
    try:
        from apps.core.models import SiteSettings
        return SiteSettings.get()
    except Exception:
        class _Fake:
            llm_provider=getattr(settings,'LLM_PROVIDER','groq')
            llm_model=getattr(settings,'LLM_MODEL','llama-3.3-70b-versatile')
            llm_temperature=getattr(settings,'LLM_TEMPERATURE',0.7)
            llm_max_tokens=getattr(settings,'LLM_MAX_TOKENS',2000)
            groq_api_key=getattr(settings,'GROQ_API_KEY','')
            openai_api_key=getattr(settings,'OPENAI_API_KEY','')
            anthropic_api_key=getattr(settings,'ANTHROPIC_API_KEY','')
            deepseek_api_key=getattr(settings,'DEEPSEEK_API_KEY','')
            together_api_key=getattr(settings,'TOGETHER_API_KEY','')
            openrouter_api_key=getattr(settings,'OPENROUTER_API_KEY','')
            use_local_embeddings=getattr(settings,'USE_LOCAL_EMBEDDINGS',True)
            local_embed_model=getattr(settings,'LOCAL_EMBED_MODEL','paraphrase-multilingual-MiniLM-L12-v2')
            openai_embed_model=getattr(settings,'EMBED_MODEL','text-embedding-3-small')
            top_k=getattr(settings,'TOP_K',5)
            min_score=getattr(settings,'MIN_SCORE',0.25)
            max_history=getattr(settings,'MAX_HISTORY_MESSAGES',10)
        return _Fake()


def ask(question, chunks, history=None):
    cfg = _cfg()

    # Veb qidiruv sharti:
    # 1. Ichki bazada hech natija yo'q, YOKI
    # 2. Topilgan natijalar relevantligi past (max score < 0.40)
    web_results = []
    allow_web = getattr(cfg, 'allow_web_search', False)
    best_score = max((c['score'] for c in chunks), default=0) if chunks else 0
    needs_web  = allow_web and (not chunks or best_score < 0.40)
    if needs_web:
        try:
            from apps.core.web_search import search as web_search
            web_results = web_search(question, cfg)
            logger.info(f"Web search: {len(web_results)} natija topildi")
        except Exception as e:
            logger.warning(f"Web search xatosi: {e}")

    # Kontekstga qarab to'g'ri system promptni tanlaymiz
    if chunks and best_score >= 0.40:
        sys_prompt = SYSTEM_BOOK
    elif web_results:
        sys_prompt = SYSTEM_WEB
    else:
        sys_prompt = SYSTEM_NONE
    msgs = [{'role':'system','content':sys_prompt}]
    if history:
        for h in list(history)[-cfg.max_history:]:
            msgs.append({'role':h['role'],'content':h['content']})

    if chunks:
        content = 'Kitob bazasidan kontekst:\n' + _ctx(chunks) + '\n\nSavol: ' + question
    elif web_results:
        web_ctx = '\n\n'.join(
            f'[{i+1}] {r["title"]}:\n{r["snippet"]}'
            for i, r in enumerate(web_results)
        )
        content = (
            'Quyidagi ma\'lumotlar internetdan olingan (kitob bazasida topilmadi):\n\n'
            + web_ctx + '\n\nSavol: ' + question
        )
    else:
        content = question

    msgs.append({'role':'user','content':content})
    provider = cfg.llm_provider.lower()

    answer, tokens = (_anthropic(msgs, cfg) if provider == 'anthropic'
                      else _openai_compat(msgs, cfg, provider))

    # Manba: nimadan foydalanilgan bo'lsa shuni qaytaramiz
    if web_results:
        # Veb natijalar ishlatildi — kitob bo'laklari emas
        sources = web_results
    elif chunks and best_score >= 0.40:
        # Faqat yaxshi kitob natijalari ishlatildi
        sources = chunks
    else:
        sources = []
    return answer, tokens, sources


def _openai_compat(msgs, cfg, provider):
    from openai import OpenAI
    p = PROVIDERS.get(provider, PROVIDERS['groq'])
    key_attr = p['key']
    api_key = getattr(cfg, {
        'GROQ_API_KEY':'groq_api_key','OPENAI_API_KEY':'openai_api_key',
        'DEEPSEEK_API_KEY':'deepseek_api_key','TOGETHER_API_KEY':'together_api_key',
        'OPENROUTER_API_KEY':'openrouter_api_key',
    }.get(key_attr,'groq_api_key'), '') if key_attr else 'ollama'
    client = OpenAI(api_key=api_key or 'no-key', base_url=p['base_url'])
    r = client.chat.completions.create(
        model=cfg.llm_model, messages=msgs,
        temperature=cfg.llm_temperature, max_tokens=cfg.llm_max_tokens)
    return r.choices[0].message.content, (r.usage.total_tokens if r.usage else 0)


def _anthropic(msgs, cfg):
    import anthropic
    sys = next((m['content'] for m in msgs if m['role']=='system'), '')
    chat = [m for m in msgs if m['role']!='system']
    r = anthropic.Anthropic(api_key=cfg.anthropic_api_key).messages.create(
        model=cfg.llm_model, max_tokens=cfg.llm_max_tokens, system=sys, messages=chat)
    return r.content[0].text, (r.usage.input_tokens or 0)+(r.usage.output_tokens or 0)


def embed_query(text):
    cfg = _cfg()
    no_embed = {'groq','anthropic','deepseek','together','openrouter','ollama'}
    if cfg.use_local_embeddings or cfg.llm_provider.lower() in no_embed:
        return _local_embed([text])[0]
    try:
        from openai import OpenAI
        r = OpenAI(api_key=cfg.openai_api_key).embeddings.create(
            model=cfg.openai_embed_model, input=[text])
        return r.data[0].embedding
    except Exception as e:
        logger.warning(f'embed fallback: {e}')
        return _local_embed([text])[0]


def retrieve(question, book_ids=None):
    from apps.books.models import BookChunk
    cfg = _cfg()
    qs = BookChunk.objects.select_related('book').filter(book__is_processed=True)
    if book_ids:
        qs = qs.filter(book_id__in=book_ids)
    chunks = list(qs.values('text','page','embedding','book__title','book__id'))
    if not chunks: return []
    qemb = embed_query(question)
    scored = []
    for c in chunks:
        if not c.get('embedding'): continue
        s = _cos(qemb, c['embedding'])
        scored.append({'chunk_text':c['text'][:400],'page':c.get('page'),
                       'score':s,'book_title':c['book__title'],'book_id':c['book__id']})
    scored.sort(key=lambda x:x['score'], reverse=True)
    return [s for s in scored[:cfg.top_k] if s['score']>=cfg.min_score]


def _cos(a,b):
    a,b=np.array(a),np.array(b)
    n=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/n) if n else 0.0

def _ctx(chunks):
    return '\n\n'.join(f'[{i+1}] {c["book_title"]}:{chr(10)}{c["chunk_text"]}'
                       for i,c in enumerate(chunks))

def _local_embed(texts):
    cfg = _cfg()
    from apps.books.processor import _get_embed_model
    m = _get_embed_model(cfg.local_embed_model)
    return m.encode(texts, show_progress_bar=False).tolist()