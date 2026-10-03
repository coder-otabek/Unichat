from django.contrib import admin
from .models import Book, BookChunk

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display   = ['title','file_type','is_processed','chunk_count','created_at']
    list_filter    = ['file_type','is_processed']
    search_fields  = ['title','author']
    readonly_fields= ['file_size','page_count','chunk_count','is_processed','processing_error','created_at']
    actions        = ['reprocess']
    def reprocess(self, request, qs):
        from .processor import process_async
        for b in qs:
            b.is_processed=False; b.processing_error=''; b.save(update_fields=['is_processed','processing_error'])
            process_async(b.id)
        self.message_user(request, f'{qs.count()} ta kitob qayta ishlanmoqda')
    reprocess.short_description='Qayta ishlash'

@admin.register(BookChunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display=['book','chunk_index','page']; list_filter=['book']; readonly_fields=['embedding']
