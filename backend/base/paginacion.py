from rest_framework.pagination import PageNumberPagination


class PaginacionOfertas(PageNumberPagination):
  """`count`, `next`, `previous`, `results`, plus the same links in a `Link` header (RFC 8288).

  The client picks `page_size` (capped at 50); a page out of range is a 404.
  """
  page_size = 20
  page_size_query_param = 'page_size'
  max_page_size = 50

  def get_paginated_response(self, data):
    response = super().get_paginated_response(data)
    enlaces = []
    siguiente, anterior = self.get_next_link(), self.get_previous_link()
    if siguiente:
      enlaces.append(f'<{siguiente}>; rel="next"')
    if anterior:
      enlaces.append(f'<{anterior}>; rel="prev"')
    if enlaces:
      response['Link'] = ', '.join(enlaces)
    return response


class PaginacionReferencias(PaginacionOfertas):
  """Reference lists (municipios, distritos, barrios): bigger pages, same envelope."""
  page_size = 100
  max_page_size = 500
