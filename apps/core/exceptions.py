from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    resp = exception_handler(exc, context)
    if resp is None:
        return Response({'detail': str(exc)}, status=500)
    return resp
