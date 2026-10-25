from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler

PROBLEM_JSON = 'application/problem+json'


def problem_exception_handler(exc, context):
  """DRF errors as `application/problem+json` (RFC 9457).

  Body: `type` (always `about:blank`), `title` (the HTTP reason), `status`, `detail` and, for a validation error,
  `errors` ({field: [messages]}). The headers DRF sets (`Retry-After`, `Allow`) are kept.
  """
  if isinstance(exc, Http404):
    exc = exceptions.NotFound()  # not Django's message, which names the model
  response = exception_handler(exc, context)
  if response is None:
    return None
  titulo = response.status_text
  if isinstance(exc, exceptions.ValidationError):
    detalle = 'La solicitud no es válida.'
    errores = response.data
    if isinstance(errores, list):
      errores = {'non_field_errors': errores}
    body = {'type': 'about:blank', 'title': titulo, 'status': response.status_code, 'detail': detalle, 'errors': errores}
  else:
    body = {
      'type': 'about:blank', 'title': titulo, 'status': response.status_code,
      'detail': str(response.data.get('detail', titulo)) if isinstance(response.data, dict) else titulo,
    }
  response.data = body
  # The browsable API renders HTML; only a JSON response carries the problem media type.
  renderer = getattr(context.get('request'), 'accepted_renderer', None)
  if renderer is None or renderer.format == 'json':
    response.content_type = PROBLEM_JSON
  return response
