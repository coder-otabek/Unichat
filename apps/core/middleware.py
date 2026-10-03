class AllowGoogleAvatarMiddleware:
    """
    Google profil rasmlarini ko'rsatish uchun CSP headerini qo'shadi
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # HTML sahifalarda Google rasm domeniga ruxsat beramiz
        ct = response.get('Content-Type', '')
        if 'text/html' in ct:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://accounts.google.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https://lh3.googleusercontent.com https://www.gstatic.com; "
                "connect-src 'self' https://accounts.google.com https://api.groq.com; "
                "frame-src https://accounts.google.com; "
            )
        return response