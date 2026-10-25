from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.urls import reverse

# Sections of the admin index: (title, models of the `base` app in the order they are listed).
# A registered model missing here falls into "Otros", so it never disappears from the index.
SECCIONES = (
    ('Inmuebles', ('Inmueble', 'ImageInmueble', 'Distribucion')),
    ('Ofertas y condiciones', ('InmuebleModalidad', 'Modalidad', 'Condiciones')),
    ('Agencia y propietarios', ('Agencia', 'Propietario')),
    ('Solicitudes', ('SolicitudReserva',)),
    ('Ubicación', ('Provincia', 'Comarca', 'Municipio', 'Distrito', 'Barrio', 'DeclaracionZonaTensionada')),
)
SECCION_SIN_CLASIFICAR = 'Otros'


class GestionAdminSite(admin.AdminSite):
    """Splits the `base` app, which holds every model, into the sections above on the admin index."""

    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label)
        if app_label not in (None, 'base'):
            return apps
        resultado = []
        for app in apps:
            if app['app_label'] != 'base':
                resultado.append(app)
                continue
            resultado.extend(self._secciones(app))
        return resultado

    @staticmethod
    def _secciones(app):
        por_nombre = {m['object_name']: m for m in app['models']}
        secciones = []
        for titulo, nombres in (*SECCIONES, (SECCION_SIN_CLASIFICAR, ())):
            if titulo == SECCION_SIN_CLASIFICAR:
                modelos = [m for n, m in por_nombre.items()]
            else:
                modelos = [por_nombre.pop(n) for n in nombres if n in por_nombre]
            if modelos:
                secciones.append({
                    **app, 'name': titulo, 'models': modelos,
                    'app_url': reverse('admin:app_list', kwargs={'app_label': 'base'}),
                })
        return secciones


class GestionAdminConfig(AdminConfig):
    default_site = 'base.admin_site.GestionAdminSite'
