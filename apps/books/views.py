from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Book
from .serializers import BookSerializer
from .processor import process_async

def _staff(request):
    return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

@api_view(['GET'])
def book_list(request):
    qs = Book.objects.all() if _staff(request) else Book.objects.filter(is_processed=True)
    return Response({'items': BookSerializer(qs, many=True).data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def book_upload(request):
    if not _staff(request):
        return Response({'detail':'Ruxsat yo\'q'}, status=403)
    f = request.FILES.get('file')
    if not f:
        return Response({'detail':'Fayl topilmadi'}, status=400)
    ext = f.name.rsplit('.',1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        return Response({'detail':f'"{ext}" qo\'llab-quvvatlanmaydi'}, status=400)
    if f.size > settings.MAX_FILE_MB * 1024 * 1024:
        return Response({'detail':f'Fayl {settings.MAX_FILE_MB}MB dan katta'}, status=400)
    book = Book.objects.create(
        title=f.name.rsplit('.',1)[0], original_name=f.name,
        file=f, file_type=ext, file_size=f.size, uploaded_by=request.user
    )
    process_async(book.id)
    return Response(BookSerializer(book).data, status=201)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def book_delete(request, pk):
    if not _staff(request): return Response({'detail':'Ruxsat yo\'q'}, status=403)
    try:
        b = Book.objects.get(pk=pk)
        b.file.delete(save=False); b.delete()
        return Response(status=204)
    except Book.DoesNotExist:
        return Response({'detail':'Topilmadi'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_reprocess(request, pk):
    if not _staff(request): return Response({'detail':'Ruxsat yo\'q'}, status=403)
    try:
        b = Book.objects.get(pk=pk)
        b.is_processed=False; b.processing_error=''; b.save(update_fields=['is_processed','processing_error'])
        process_async(b.id)
        return Response({'ok':True})
    except Book.DoesNotExist:
        return Response({'detail':'Topilmadi'}, status=404)
