"""Assistant endpoints do not read users, uploads, or the application database."""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .assistant_engine import MAX_BODY, dispatch


@csrf_exempt
def assistant_api(request):
    # Strict Origin + JSON + hosted access-code checks are shared with the standalone API.
    try:
        length = int(request.META.get('CONTENT_LENGTH') or 0)
    except ValueError:
        length = MAX_BODY + 1
    if length > MAX_BODY:
        return JsonResponse({'error': 'Your message is too large.'}, status=413)
    status, data, headers = dispatch(request.method, request.path,
                                     {key.lower(): value for key, value in request.headers.items()},
                                     request.body, request.META.get('REMOTE_ADDR', ''))
    response = JsonResponse(data, status=status)
    for key, value in headers.items():
        response[key] = value
    return response
