"""
Kitobni qayta ishlash: matn → bo'laklash → embedding → saqlash
"""
import logging
import threading
from django.conf import settings

# ── Model keshi — bir marta yuklanadi, xotirada saqlanadi ─────
_embed_model_cache = {}

def _get_embed_model(model_name: str):
    if model_name not in _embed_model_cache:
        from sentence_transformers import SentenceTransformer
        _embed_model_cache[model_name] = SentenceTransformer(model_name)
    return _embed_model_cache[model_name]

logger = logging.getLogger(__name__)


def process_async(book_id: int):
    t = threading.Thread(target=_run, args=(book_id,), daemon=True)
    t.start()


def _run(book_id):
    from apps.books.models import Book
    try:
        book = Book.objects.get(pk=book_id)
        _process(book)
        logger.info(f'Book {book_id} "{book.title}" muvaffaqiyatli qayta ishlandi')
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        logger.error(f'Book {book_id} xatosi:\n{err}')
        try:
            from apps.books.models import Book
            Book.objects.filter(pk=book_id).update(
                processing_error=str(e)[:800],
                is_processed=False,
            )
        except Exception:
            pass


def _process(book):
    from apps.books.models import BookChunk

    # 1. Matn ajratish
    pages = _extract(book)
    if not pages:
        raise ValueError('Fayldan matn ajratib bo\'lmadi (fayl bo\'sh yoki format noto\'g\'ri)')

    # 2. Bo'laklash
    chunks = _chunk(pages)
    if not chunks:
        raise ValueError('Bo\'laklash natija bermadi (matn juda qisqa)')

    # 3. Embedding
    texts = [c['text'] for c in chunks]
    try:
        embeddings = _embed(texts)
    except Exception as e:
        raise ValueError(f'Embedding xatosi: {e}')

    if len(embeddings) != len(chunks):
        raise ValueError(f'Embedding soni ({len(embeddings)}) bo\'laklar soniga ({len(chunks)}) mos kelmadi')

    # 4. Saqlash
    BookChunk.objects.filter(book=book).delete()
    objs = [
        BookChunk(
            book=book,
            text=c['text'],
            page=c.get('page'),
            chunk_index=i,
            embedding=e,
        )
        for i, (c, e) in enumerate(zip(chunks, embeddings))
    ]
    BookChunk.objects.bulk_create(objs, batch_size=200)

    book.chunk_count = len(objs)
    book.is_processed = True
    book.processing_error = ''
    book.save(update_fields=['chunk_count', 'is_processed', 'processing_error'])


# ── Matn ajratish ─────────────────────────────────────────────────────────────

def _extract(book):
    ext = book.file_type.lower()
    path = book.file.path

    extractors = {
        'pdf':  _pdf,
        'docx': _docx,
        'txt':  _txt,
        'md':   _txt,
        'epub': _epub,
    }
    fn = extractors.get(ext)
    if not fn:
        raise ValueError(f'"{ext}" fayl turi qo\'llab-quvvatlanmaydi')
    return fn(path, book)


def _pdf(path, book):
    try:
        import PyPDF2
        pages = []
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total = len(reader.pages)
            book.page_count = total
            book.save(update_fields=['page_count'])
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ''
                    if text.strip():
                        pages.append({'text': text, 'page': i + 1})
                except Exception:
                    continue
        return pages
    except ImportError:
        raise ValueError('PyPDF2 o\'rnatilmagan: pip install PyPDF2')
    except Exception as e:
        raise ValueError(f'PDF o\'qish xatosi: {e}')


def _docx(path, book):
    try:
        from docx import Document
        doc = Document(path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            # Jadvallarni ham tekshiramiz
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text.strip())
        text = '\n'.join(paragraphs)
        return [{'text': text, 'page': None}] if text else []
    except ImportError:
        raise ValueError('python-docx o\'rnatilmagan: pip install python-docx')
    except Exception as e:
        raise ValueError(f'DOCX o\'qish xatosi: {e}')


def _txt(path, book):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            text = f.read()
        return [{'text': text, 'page': None}] if text.strip() else []
    except Exception as e:
        raise ValueError(f'Fayl o\'qish xatosi: {e}')


def _epub(path, book):
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        bk = epub.read_epub(path)
        pages = []
        for item in bk.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            text = BeautifulSoup(item.get_content(), 'html.parser').get_text()
            if text.strip():
                pages.append({'text': text, 'page': None})
        return pages
    except ImportError:
        raise ValueError('ebooklib yoki beautifulsoup4 o\'rnatilmagan')
    except Exception as e:
        raise ValueError(f'EPUB o\'qish xatosi: {e}')


# ── Bo'laklash ────────────────────────────────────────────────────────────────

def _chunk(pages):
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        sz, ov = cfg.chunk_size, cfg.chunk_overlap
    except Exception:
        sz  = getattr(settings, 'CHUNK_SIZE',    800)
        ov  = getattr(settings, 'CHUNK_OVERLAP', 150)
    chunks = []
    for p in pages:
        words = p['text'].split()
        if not words:
            continue
        i = 0
        while i < len(words):
            txt = ' '.join(words[i:i + sz])
            if len(txt) > 60:
                chunks.append({'text': txt, 'page': p.get('page')})
            i += max(1, sz - ov)
    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────

def _embed(texts: list[str]) -> list:
    use_local = getattr(settings, 'USE_LOCAL_EMBEDDINGS', True)
    provider  = getattr(settings, 'LLM_PROVIDER', 'groq').lower()

    # Groq, Anthropic, DeepSeek, Together, OpenRouter, Ollama — embedding bermaydi
    no_embed_providers = {'groq', 'anthropic', 'deepseek', 'together', 'openrouter', 'ollama'}

    if use_local or provider in no_embed_providers:
        return _embed_local(texts)

    # OpenAI embedding
    try:
        from openai import OpenAI
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key or api_key.startswith('sk-...') or api_key == 'sk-':
            raise ValueError('OPENAI_API_KEY sozlanmagan')
        client = OpenAI(api_key=api_key)
        model  = getattr(settings, 'EMBED_MODEL', 'text-embedding-3-small')
        out = []
        for i in range(0, len(texts), 100):
            r = client.embeddings.create(model=model, input=texts[i:i+100])
            out.extend([x.embedding for x in r.data])
        return out
    except Exception as e:
        logger.warning(f'OpenAI embed xatosi, lokal fallbackga o\'tildi: {e}')
        return _embed_local(texts)


def _embed_local(texts: list[str]) -> list:
    """sentence-transformers bilan lokal embedding (keshdan)"""
    try:
        model_name = getattr(settings, 'LOCAL_EMBED_MODEL',
                             'paraphrase-multilingual-MiniLM-L12-v2')
        model = _get_embed_model(model_name)
        return model.encode(texts, show_progress_bar=False, batch_size=32).tolist()
    except ImportError:
        raise ValueError(
            'sentence-transformers o\'rnatilmagan!\n'
            'Hal qilish: pip install sentence-transformers'
        )
    except Exception as e:
        raise ValueError(f'Lokal embedding xatosi: {e}')