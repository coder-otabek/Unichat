from django.db import models
from django.conf import settings

class Session(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    title      = models.CharField(max_length=200, default='Yangi suhbat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name='Sessiya'; verbose_name_plural='Sessiyalar'; ordering=['-updated_at']
    def __str__(self): return f'{self.user.email}: {self.title}'

class Message(models.Model):
    ROLES=[('user','Foydalanuvchi'),('assistant','Yordamchi')]
    session     = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='messages')
    role        = models.CharField(max_length=10, choices=ROLES)
    content     = models.TextField()
    sources     = models.JSONField(null=True, blank=True)
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['created_at']
    def __str__(self): return f'[{self.role}] {self.content[:50]}'
