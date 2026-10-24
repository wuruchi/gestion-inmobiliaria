from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.forms.models import BaseInlineFormSet
from base.models import (
    AreaRecreo,
    Banios,
    Dormitorios,
    Dotacion,
    Entorno,
    Estancias,
    ImageInmueble,
    HistorialRenta,
    Inmueble,
    InmuebleModalidad,
    Instalaciones,
    OtrosEspacios,
    PlazaAparcamiento,
    Otros,
    Seguridad,
    Transporte,
    Provincia,
    Barrio,
    Modalidad,
    Comarca,
    Municipio,
    Distrito,
    CondicionesAlquiler,
    DatosInternos,
    Propietario,
    SolicitudReserva,
)

# Register your models here.
# admin.site.register(Modulo)py

class AreaRecreoInline(admin.StackedInline):
    model = AreaRecreo

class BaniosInline(admin.StackedInline):
    model = Banios


class DotacionInline(admin.StackedInline):
    model = Dotacion

class EstanciasInline(admin.StackedInline):
    model = Estancias

class EntornoInline(admin.StackedInline):
    model = Entorno

class ImageInmuebleInline(admin.TabularInline):
    model = ImageInmueble
    extra = 3
    fields = ('image', 'alt_text', 'posicion', 'default')

class InstalacionesInline(admin.StackedInline):
    model = Instalaciones

class OtrosEspaciosInline(admin.StackedInline):
    model = OtrosEspacios

class OtrosInline(admin.StackedInline):
    model = Otros

class DormitoriosInline(admin.StackedInline):
    model = Dormitorios

class SeguridadInline(admin.StackedInline):
    model = Seguridad

class TransporteInline(admin.StackedInline):
    model = Transporte


class DatosInternosInline(admin.StackedInline):
    model = DatosInternos
    autocomplete_fields = ('propietario',)


class InmuebleModalidadFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        alive = [
            f for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE')
        ]
        if not alive:
            raise ValidationError('Añade al menos una modalidad con su precio.')


class InmuebleModalidadInline(admin.TabularInline):
    model = InmuebleModalidad
    formset = InmuebleModalidadFormSet
    extra = 1
    min_num = 1
    validate_min = True


class PlazaAparcamientoInline(admin.TabularInline):
    model = PlazaAparcamiento
    extra = 0


class HistorialRentaInline(admin.TabularInline):
    model = HistorialRenta
    extra = 1


class InmuebleAdmin(admin.ModelAdmin):
    inlines = [
        InmuebleModalidadInline,
        ImageInmuebleInline,
        PlazaAparcamientoInline,
        HistorialRentaInline,
        DatosInternosInline,
        DormitoriosInline,
        BaniosInline,
        EstanciasInline,
        SeguridadInline,
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
        'precios_lista',
        'fecha_disponibilidad',
        'propietario',
        'publicar_web',
    )
    search_fields = ['referencia', 'direccion', 'datos_internos__propietario__nombre']
    list_filter = ('modalidades', 'publicar_web')

    @admin.display(description='Propietario')
    def propietario(self, obj):
        datos = getattr(obj, 'datos_internos', None)
        return datos.propietario if datos else None

    @admin.display(description='Precios')
    def precios_lista(self, obj):
        return ', '.join(
            f'{p.modalidad.nombre}: {p.precio} ({p.modalidad.get_unidad_precio_display().lower()})'
            for p in obj.precios.all()
        )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('datos_internos__propietario')
            .prefetch_related(Prefetch('precios', queryset=InmuebleModalidad.objects.select_related('modalidad')))
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(ImageInmueble)
admin.site.register(Dormitorios)
admin.site.register(Banios)
admin.site.register(Inmueble, InmuebleAdmin)
admin.site.register(Provincia)
admin.site.register(Comarca)
admin.site.register(Municipio)
admin.site.register(Distrito)
admin.site.register(Barrio)

@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'unidad_precio', 'orden')


@admin.register(Propietario)
class PropietarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nif', 'email', 'telefono')
    search_fields = ('nombre', 'nif', 'email')


@admin.register(CondicionesAlquiler)
class CondicionesAlquilerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'por_defecto')


@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'nombre', 'email', 'telefono', 'fecha_desde', 'estado', 'created_at')
    list_filter = ('estado',)
    search_fields = ('referencia', 'nombre', 'email')
    readonly_fields = ('inmueble', 'referencia', 'nombre', 'email', 'telefono',
                       'fecha_desde', 'acepta_aviso_legal', 'datos_borrados', 'created_at')
