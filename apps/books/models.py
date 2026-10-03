from django.db import models
from django.conf import settings

class Book(models.Model):
    TYPES = [('pdf','PDF'),('docx','DOCX'),('txt','TXT'),('md','MD'),('epub','EPUB')]
    title            = models.CharField(max_length=500)
    author           = models.CharField(max_length=300, blank=True)
    original_name    = models.CharField(max_length=500)
    file             = models.FileField(upload_to='books/%Y/%m/')
    file_type        = models.CharField(max_length=10, choices=TYPES)
    file_size        = models.PositiveBigIntegerField(default=0)
    page_count       = models.PositiveIntegerField(default=0)
    chunk_count      = models.PositiveIntegerField(default=0)
    is_processed     = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    uploaded_by      = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at       = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name='Kitob'; verbose_name_plural='Kitoblar'; ordering=['-created_at']
    def __str__(self): return self.title

class BookChunk(models.Model):
    book        = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chunks')
    text        = models.TextField()
    page        = models.PositiveIntegerField(null=True, blank=True)
    chunk_index = models.PositiveIntegerField(default=0)
    embedding   = models.JSONField(null=True, blank=True)
    class Meta:
        ordering=['book','chunk_index']
    def __str__(self): return f'{self.book.title}[{self.chunk_index}]'
