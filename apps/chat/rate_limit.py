"""
So'rov limiti tekshiruvi.
Har bir savol yuborishdan oldin chaqiriladi.
"""
from django.utils import timezone
from datetime import timedelta


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def check_limit(request) -> tuple[bool, str]:
    """
    Limitni tekshiradi.
    Returns: (is_allowed: bool, error_message: str)
    """
    try:
        from apps.core.models import SiteSettings
        cfg = SiteSettings.get()

        if not cfg.enable_rate_limit:
            return True, ''

        from apps.chat.models import UsageLog
        now  = timezone.now()
        user = request.user if request.user.is_authenticated else None

        # Admin va staff uchun limit yo'q
        if user and (user.is_staff or user.is_superuser):
            return True, ''

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if user:
            daily_count   = UsageLog.objects.filter(user=user,   created_at__gte=today_start).count()
            monthly_count = UsageLog.objects.filter(user=user,   created_at__gte=month_start).count()
            daily_limit   = cfg.user_daily_limit
            monthly_limit = cfg.user_monthly_limit

            if daily_count >= daily_limit:
                return False, f'⏳ Kunlik limitingiz tugadi ({daily_limit} savol/kun). Ertaga qayta urinib ko\'ring.'
            if monthly_count >= monthly_limit:
                return False, f'📅 Oylik limitingiz tugadi ({monthly_limit} savol/oy). Keyingi oyda qayta urinib ko\'ring.'
        else:
            # Mehmon — IP bo'yicha
            ip = get_client_ip(request)
            daily_count = UsageLog.objects.filter(
                ip_address=ip, user=None, created_at__gte=today_start
            ).count()
            if daily_count >= cfg.guest_daily_limit:
                return False, f'⏳ {cfg.limit_exceeded_message} Kirish orqali ko\'proq savol bering.'

        return True, ''
    except Exception:
        return True, ''  # Xato bo'lsa limitni o'tkazib yuboramiz


def log_usage(request):
    """Savol foydalanishini qayd etadi"""
    try:
        from apps.chat.models import UsageLog
        user = request.user if request.user.is_authenticated else None
        ip   = get_client_ip(request)
        UsageLog.objects.create(user=user, ip_address=ip)
    except Exception:
        pass