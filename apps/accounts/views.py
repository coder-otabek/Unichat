from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, tokens_for


@api_view(['POST'])
def register(request):
    s = RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    return Response(tokens_for(user), status=201)


@api_view(['POST'])
def login(request):
    s = LoginSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.validated_data['user']
    resp = Response(tokens_for(user))
    resp.set_cookie('uc_token', tokens_for(user)['access_token'],
                    max_age=7*86400, httponly=False, samesite='Lax', path='/')
    return resp


@api_view(['POST'])
def google_login(request):
    """
    Google One Tap / OAuth2 orqali kirish.
    Frontend Google ID tokenini yuboradi, biz tekshiramiz va JWT qaytaramiz.
    """
    credential = request.data.get('credential') or request.data.get('token')
    if not credential:
        return Response({'detail': 'Google token topilmadi'}, status=400)

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    if not client_id:
        return Response({'detail': 'GOOGLE_CLIENT_ID sozlanmagan'}, status=503)

    # Google tokenini tekshirish
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as g_requests
        info = id_token.verify_oauth2_token(
            credential,
            g_requests.Request(),
            client_id,
            clock_skew_in_seconds=10,
        )
    except Exception as e:
        return Response({'detail': f'Google token xatosi: {e}'}, status=401)

    email     = info.get('email', '').lower()
    full_name = info.get('name') or email.split('@')[0]
    verified  = info.get('email_verified', False)

    if not email or not verified:
        return Response({'detail': 'Email tasdiqlanmagan'}, status=400)

    # Foydalanuvchini topish yoki yaratish
    from .models import User
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'full_name': full_name,
            'username':  email,
            'is_active': True,
        }
    )
    # Ism yangilash (agar avval yaratilgan bo'lsa va ismi bo'sh bo'lsa)
    if not created and not user.full_name:
        user.full_name = full_name
        user.save(update_fields=['full_name'])

    if not user.is_active:
        return Response({'detail': 'Hisobingiz bloklangan'}, status=403)

    resp = Response({**tokens_for(user), 'created': created})
    resp.set_cookie('uc_token', tokens_for(user)['access_token'],
                    max_age=7*86400, httponly=False, samesite='Lax', path='/')
    return resp


@api_view(['POST'])
def logout_view(request):
    resp = Response({'ok': True})
    resp.delete_cookie('uc_token')
    return resp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
