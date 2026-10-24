from django.contrib import admin
from base.models import (
    AreaRecreo,
    Banios,
    Carpinteria,
    Cocina,
    Dormitorios,
    Dotacion,
    Entorno,
    ImageInmueble,
    Inmueble,
    Instalaciones,
    OtrosEspacios,
    Otros,
    Salon,
    Seguridad,
    Terraza,
    Transporte,
    Provincia,
    Barrio,
    Modalidad,
    Comarca,
    Municipio,
    Distrito,
    CondicionesAlquiler,
    SolicitudReserva,
)

# Register your models here.
# admin.site.register(Modulo)py

class AreaRecreoInline(admin.StackedInline):
    model = AreaRecreo

class BaniosInline(admin.StackedInline):
    model = Banios


class CarpinteriaInline(admin.StackedInline):
    model = Carpinteria


class CocinaInline(admin.StackedInline):
    model = Cocina


class DotacionInline(admin.StackedInline):
    model = Dotacion

class EntornoInline(admin.StackedInline):
    model = Entorno

class ImageInmuebleInline(admin.StackedInline):
    model = ImageInmueble
    extra = 3

class InstalacionesInline(admin.StackedInline):
    model = Instalaciones

class OtrosEspaciosInline(admin.StackedInline):
    model = OtrosEspacios

class OtrosInline(admin.StackedInline):
    model = Otros

class DormitoriosInline(admin.StackedInline):
    model = Dormitorios

class SalonInline(admin.StackedInline):
    model = Salon

class SeguridadInline(admin.StackedInline):
    model = Seguridad

class TerrazaInline(admin.StackedInline):
    model = Terraza

class TransporteInline(admin.StackedInline):
    model = Transporte


class InmuebleAdmin(admin.ModelAdmin):
    inlines = [
        ImageInmuebleInline,
        DormitoriosInline,
        BaniosInline,
        CarpinteriaInline,
        CocinaInline,
        SalonInline,
        SeguridadInline,
        TerrazaInline,
        DotacionInline,
        InstalacionesInline,
        OtrosEspaciosInline,
        EntornoInline,
        # AreaRecreoInline,
        TransporteInline,
        OtrosInline,
    ]
    list_display = (
        'referencia',
        'codigo_postal',
        'direccion',
        'tipo',
        'modalidades_lista',
        'importe_alquiler',
        'fecha_disponibilidad',
        'propietario',
        'publicar_web',
    )
    search_fields = ['referencia', 'direccion', 'propietario']
    filter_horizontal = ('modalidades',)
    list_filter = ('modalidades', 'publicar_web')

    @admin.display(description='Modalidades')
    def modalidades_lista(self, obj):
        return ', '.join(m.nombre for m in obj.modalidades.all())

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('modalidades')


admin.site.register(ImageInmueble)
admin.site.register(Dormitorios)
admin.site.register(Banios)
admin.site.register(Inmueble, InmuebleAdmin)
admin.site.register(Provincia)
admin.site.register(Comarca)
admin.site.register(Municipio)
admin.site.register(Distrito)
admin.site.register(Barrio)
admin.site.register(Modalidad)


@admin.register(CondicionesAlquiler)
class CondicionesAlquilerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'por_defecto')


@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'nombre', 'email', 'telefono', 'fecha_desde', 'atendida', 'created_at')
    list_filter = ('atendida',)
    search_fields = ('referencia', 'nombre', 'email')
    readonly_fields = ('inmueble', 'referencia', 'nombre', 'email', 'telefono',
                       'fecha_desde', 'acepta_aviso_legal', 'created_at')
