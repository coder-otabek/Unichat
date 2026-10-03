from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Book
        fields = ['id','title','author','original_name','file_type','file_size',
                  'page_count','chunk_count','is_processed','processing_error','created_at']
