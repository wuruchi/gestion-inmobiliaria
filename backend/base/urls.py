from django.urls import path
from . import views

urlpatterns = [
  path('', views.getRoutes, name="routes"),
  path('inmuebles/', views.getInmuebles, name="inmuebles"),
  path('inmuebles/modalidad/temporales/', views.getInmueblesTemporales, name="inmuebles_temporales"),
  path('inmuebles/modalidad/habituales/', views.getInmueblesHabituales, name="inmuebles_habituales"),
  path('inmuebles/modalidad/ventas/', views.getInmueblesVenta, name="inmuebles_venta"),
  path('inmuebles/<str:pk>/', views.getInmueble, name="inmueble"),
  path('inmuebles/<str:pk>/reservas/', views.crearSolicitudReserva, name="inmueble_reserva"),
  path('inmuebles/modalidad/<str:modalidad>/distrito/<str:distrito_id>/count/', views.getInmueblesCount, name="inmuebles_count"),
  path('distritos/', views.getDistritos, name='distritos'),
  path('distritos/<str:distrito_id>/barrios', views.getBarriosByDistrito, name='distrito_barrios'),
  path('municipios/', views.getMunicipios, name='municipios'),
  path('municipios/<str:municipio_id>/distritos', views.getDistritosByMunicipio, name='municipio_distritos'),
  path('modalidades/', views.getModalidades, name='modalidades'),
  path('provincias/', views.getProvincias, name='provincias'),
  path('provincias/<str:provincia_id>/municipios', views.getMunicipiosByProvincia, name='provincia_municipios'),
]
