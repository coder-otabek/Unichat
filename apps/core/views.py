from django.shortcuts import render
from django.http import Http404
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def _ctx():
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        return {
            'site_title':       cfg.site_title,
            'google_client_id': cfg.google_client_id or getattr(settings, 'GOOGLE_CLIENT_ID', ''),
        }
    except Exception:
        return {
            'site_title':       getattr(settings, 'SITE_TITLE', 'UniChat'),
            'google_client_id': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
        }


def index(request):
    return render(request, 'index.html', _ctx())


def panel(request):
    token = (request.COOKIES.get('uc_token') or
             request.headers.get('Authorization', '').replace('Bearer ', ''))
    if not token:
        raise Http404
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        data = AccessToken(token)
        from apps.accounts.models import User
        user = User.objects.get(id=data['user_id'])
        if not (user.is_staff or user.is_superuser):
            raise Http404
    except Http404:
        raise
    except Exception:
        raise Http404
    return render(request, 'panel.html', _ctx())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def panel_stats(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    from apps.accounts.models import User
    from apps.books.models import Book
    from apps.chat.models import Session, Message
    return Response({
        'users':    {'total': User.objects.count(),
                     'active': User.objects.filter(is_active=True).count(),
                     'staff': User.objects.filter(is_staff=True).count()},
        'books':    {'total': Book.objects.count(),
                     'processed': Book.objects.filter(is_processed=True).count(),
                     'processing': Book.objects.filter(is_processed=False, processing_error='').count(),
                     'failed': Book.objects.exclude(processing_error='').count()},
        'sessions': Session.objects.count(),
        'messages': Message.objects.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def panel_users(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    from apps.accounts.models import User
    from apps.accounts.serializers import UserSerializer
    return Response(UserSerializer(User.objects.all().order_by('-date_joined'), many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    from apps.accounts.models import User
    try:
        u = User.objects.get(pk=pk)
        if u.is_superuser:
            return Response({'detail': 'Superuserni bloklab bo\'lmaydi'}, status=400)
        u.is_active = not u.is_active
        u.save(update_fields=['is_active'])
        return Response({'is_active': u.is_active})
    except User.DoesNotExist:
        return Response({'detail': 'Topilmadi'}, status=404)


@api_view(['GET'])
def public_config(request):
    """Frontend uchun ommaviy sozlamalar"""
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        return Response({
            'site_title':        cfg.site_title,
            'allow_guest_chat':  cfg.allow_guest_chat,
            'allow_register':    cfg.allow_register,
            'google_client_id':  cfg.google_client_id,
            'allow_web_search':   cfg.allow_web_search,
            'web_search_provider': cfg.web_search_provider,
            'enable_rate_limit':   cfg.enable_rate_limit,
            'user_daily_limit':    cfg.user_daily_limit,
            'user_monthly_limit':  cfg.user_monthly_limit,
            'guest_daily_limit':   cfg.guest_daily_limit,
            'limit_exceeded_message': cfg.limit_exceeded_message,
        })
    except Exception:
        return Response({'site_title': 'UniChat', 'allow_guest_chat': True,
                         'allow_register': True, 'google_client_id': ''})


def site_logo(request):
    """
    Admindan yuklangan logoni qaytaradi.
    Yuklanmagan bo'lsa — static/favicon.png ga redirect qiladi.
    """
    import os
    from django.http import FileResponse, HttpResponseRedirect
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        if cfg.logo and cfg.logo.name:
            path = cfg.logo.path
            if os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                ct = 'image/png' if ext == '.png' else 'image/jpeg' if ext in ('.jpg','.jpeg') else 'image/png'
                resp = FileResponse(open(path, 'rb'), content_type=ct)
                resp['Cache-Control'] = 'public, max-age=300'
                return resp
    except Exception:
        pass
    return HttpResponseRedirect('/static/favicon.png')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_web_search(request):
    """Panel dan veb qidiruvni yoqish/o'chirish"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        cfg.allow_web_search = not cfg.allow_web_search
        cfg.save(update_fields=['allow_web_search'])
        return Response({'allow_web_search': cfg.allow_web_search})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_web_search_settings(request):
    """Panel dan veb qidiruv sozlamalarini yangilash"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        if 'allow_web_search'    in request.data: cfg.allow_web_search    = request.data['allow_web_search']
        if 'web_search_provider' in request.data: cfg.web_search_provider = request.data['web_search_provider']
        if 'web_search_results'  in request.data: cfg.web_search_results  = int(request.data['web_search_results'])
        if 'serpapi_key'         in request.data: cfg.serpapi_key         = request.data['serpapi_key']
        cfg.save()
        return Response({'ok': True, 'allow_web_search': cfg.allow_web_search})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_rate_limit(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        cfg.enable_rate_limit = not cfg.enable_rate_limit
        cfg.save(update_fields=['enable_rate_limit'])
        return Response({'enable_rate_limit': cfg.enable_rate_limit})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_rate_limit_settings(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'detail': 'Ruxsat yo\'q'}, status=403)
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()
        d = request.data
        if 'user_daily_limit'       in d: cfg.user_daily_limit       = int(d['user_daily_limit'])
        if 'user_monthly_limit'     in d: cfg.user_monthly_limit     = int(d['user_monthly_limit'])
        if 'guest_daily_limit'      in d: cfg.guest_daily_limit      = int(d['guest_daily_limit'])
        if 'limit_exceeded_message' in d: cfg.limit_exceeded_message = d['limit_exceeded_message']
        cfg.save()
        return Response({'ok': True})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)