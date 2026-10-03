from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Session, Message
from .rag import retrieve, ask


@api_view(['POST'])
def chat_ask(request):
    from django.conf import settings
    q        = (request.data.get('question') or '').strip()
    book_ids = request.data.get('book_ids') or []
    sess_id  = request.data.get('session_id')
    if not q:
        return Response({'detail': 'Savol bo\'sh'}, status=400)

    chunks  = retrieve(q, book_ids=book_ids or None)
    history = []
    session = None

    if request.user.is_authenticated:
        if sess_id:
            try:
                session = Session.objects.get(pk=sess_id, user=request.user)
            except Session.DoesNotExist:
                pass
        if not session:
            title = q[:80] + ('...' if len(q) > 80 else '')
            session = Session.objects.create(user=request.user, title=title)
        history = list(session.messages.values('role', 'content').order_by('created_at'))
    elif not getattr(settings, 'ALLOW_GUEST_CHAT', True):
        return Response({'detail': 'Mehmon sifatida foydalanib bo\'lmaydi'}, status=403)

    try:
        # ask() har doim (answer, tokens, sources) qaytaradi
        # sources — nimadan javob berilgan bo'lsa o'sha (kitob yoki veb)
        answer, tokens, sources = ask(q, chunks, history)
    except Exception as e:
        return Response({'detail': f'AI xatosi: {e}'}, status=503)

    if session:
        Message.objects.create(session=session, role='user', content=q)
        Message.objects.create(
            session=session, role='assistant',
            content=answer, sources=sources, tokens_used=tokens
        )
        session.save(update_fields=['updated_at'])

    return Response({
        'answer':     answer,
        'sources':    sources,
        'tokens_used':tokens,
        'session_id': session.id if session else None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sessions(request):
    qs = Session.objects.filter(user=request.user).order_by('-updated_at')
    return Response([{
        'id': s.id, 'title': s.title,
        'created_at': s.created_at, 'updated_at': s.updated_at
    } for s in qs])


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def session_detail(request, pk):
    try:
        s = Session.objects.get(pk=pk, user=request.user)
    except Session.DoesNotExist:
        return Response({'detail': 'Topilmadi'}, status=404)
    if request.method == 'DELETE':
        s.delete()
        return Response(status=204)
    msgs = s.messages.all().values('id', 'role', 'content', 'sources', 'tokens_used', 'created_at')
    return Response({'id': s.id, 'title': s.title, 'messages': list(msgs)})