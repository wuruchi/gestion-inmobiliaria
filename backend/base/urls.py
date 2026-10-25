from django.urls import path
from . import views

urlpatterns = [
  path('ofertas/', views.listarOfertas, name="ofertas"),
  path('ofertas/mapa/', views.mapaOfertas, name="ofertas_mapa"),
  path('ofertas/<uuid:pk>/', views.getOferta, name="oferta"),
  path('ofertas/<uuid:pk>/solicitudes/', views.crearSolicitud, name="oferta_solicitudes"),
  path('provincias/', views.listarProvincias, name='provincias'),
  path('municipios/', views.listarMunicipios, name='municipios'),
  path('distritos/', views.listarDistritos, name='distritos'),
  path('barrios/', views.listarBarrios, name='barrios'),
  path('catalogos/', views.getCatalogos, name='catalogos'),
  path('agencia/', views.getAgencia, name='agencia'),
]
