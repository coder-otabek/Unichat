"""
Tashqi veb qidiruv moduli.
Provayder: DuckDuckGo (bepul), SerpAPI, Google CSE
"""
import logging
import urllib.request
import urllib.parse
import json

logger = logging.getLogger(__name__)


def search(query: str, cfg) -> list[dict]:
    """
    Savolga mos veb natijalarni qaytaradi.
    cfg — SiteSettings obyekti.
    Returns: [{'title': ..., 'snippet': ..., 'url': ...}, ...]
    """
    provider = getattr(cfg, 'web_search_provider', 'duckduckgo')
    count    = min(int(getattr(cfg, 'web_search_results', 3)), 5)

    try:
        if provider == 'serpapi' and getattr(cfg, 'serpapi_key', ''):
            return _serpapi(query, cfg.serpapi_key, count)
        if provider == 'google' and getattr(cfg, 'google_cse_id', '') and getattr(cfg, 'google_cse_key', ''):
            return _google_cse(query, cfg.google_cse_id, cfg.google_cse_key, count)
        # Default: DuckDuckGo
        return _duckduckgo(query, count)
    except Exception as e:
        logger.warning(f'Web search xatosi ({provider}): {e}')
        return []


def _duckduckgo(query: str, count: int) -> list[dict]:
    """DuckDuckGo Instant Answer API — bepul, API key shart emas"""
    url = 'https://api.duckduckgo.com/?' + urllib.parse.urlencode({
        'q': query, 'format': 'json', 'no_redirect': 1,
        'no_html': 1, 'skip_disambig': 1,
    })
    req = urllib.request.Request(url, headers={'User-Agent': 'UniChat/1.0'})
    with urllib.request.urlopen(req, timeout=6) as r:
        data = json.loads(r.read())

    results = []
    # AbstractText — asosiy javob
    if data.get('AbstractText'):
        results.append({
            'title':   data.get('Heading', 'DuckDuckGo'),
            'snippet': data['AbstractText'][:400],
            'url':     data.get('AbstractURL', ''),
            'source':  'web',
        })
    # RelatedTopics
    for t in data.get('RelatedTopics', [])[:count]:
        if isinstance(t, dict) and t.get('Text'):
            results.append({
                'title':   t.get('Text', '')[:80],
                'snippet': t.get('Text', '')[:400],
                'url':     t.get('FirstURL', ''),
                'source':  'web',
            })
        if len(results) >= count:
            break

    # Agar hech narsa yo'q bo'lsa — DuckDuckGo HTML search fallback
    if not results:
        results = _ddg_html(query, count)

    return results[:count]


def _ddg_html(query: str, count: int) -> list[dict]:
    """DuckDuckGo lite HTML parser — fallback"""
    try:
        url = 'https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': query})
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; UniChatBot/1.0)',
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='replace')

        import re
        results = []
        # Extract result snippets
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles   = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        urls     = re.findall(r'class="result__url"[^>]*>(.*?)</span>', html, re.DOTALL)

        def clean(t): return re.sub(r'<[^>]+>', '', t).strip()

        for i in range(min(count, len(snippets))):
            results.append({
                'title':   clean(titles[i]) if i < len(titles) else query,
                'snippet': clean(snippets[i])[:400],
                'url':     clean(urls[i]) if i < len(urls) else '',
                'source':  'web',
            })
        return results
    except Exception as e:
        logger.warning(f'DDG HTML fallback xatosi: {e}')
        return []


def _serpapi(query: str, key: str, count: int) -> list[dict]:
    url = 'https://serpapi.com/search?' + urllib.parse.urlencode({
        'q': query, 'api_key': key, 'num': count, 'hl': 'uz',
    })
    req = urllib.request.Request(url, headers={'User-Agent': 'UniChat/1.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read())
    return [
        {'title': r.get('title',''), 'snippet': r.get('snippet','')[:400],
         'url': r.get('link',''), 'source': 'web'}
        for r in data.get('organic_results', [])[:count]
    ]


def _google_cse(query: str, cse_id: str, api_key: str, count: int) -> list[dict]:
    url = 'https://www.googleapis.com/customsearch/v1?' + urllib.parse.urlencode({
        'q': query, 'cx': cse_id, 'key': api_key, 'num': count,
    })
    req = urllib.request.Request(url, headers={'User-Agent': 'UniChat/1.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read())
    return [
        {'title': i.get('title',''), 'snippet': i.get('snippet','')[:400],
         'url': i.get('link',''), 'source': 'web'}
        for i in data.get('items', [])[:count]
    ]