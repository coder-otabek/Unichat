"""
Google avatar rasmini backend orqali proksilash.
Browser to'g'ridan-to'g'ri Google serveriga murojaat qilmaydi —
Django o'zi yuklab, foydalanuvchiga beradi.
"""
import urllib.request
from django.http import HttpResponse, Http404


def avatar_proxy(request):
    url = request.GET.get('url', '')

    # Faqat Google rasm domeniga ruxsat
    if not url.startswith('https://lh3.googleusercontent.com/'):
        raise Http404

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data        = resp.read()
            content_type= resp.headers.get('Content-Type', 'image/jpeg')
        response = HttpResponse(data, content_type=content_type)
        response['Cache-Control'] = 'public, max-age=86400'
        return response
    except Exception:
        raise Http404