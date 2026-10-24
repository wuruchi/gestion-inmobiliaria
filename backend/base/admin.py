from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.forms.models import BaseInlineFormSet
from django.http import Http404, JsonResponse
from django.urls import path, reverse
from base.models import (
    AreaRecreo,
    Banios,
    Dormitorios,
    Dotacion,
    Entorno,
    Estancias,
    ImageInmueble,
    MediaInmueble,
    HistorialPrecio,
    Inmueble,
    InmueblePropietario,
    InmuebleModalidad,
    Instalaciones,
    OtrosEspacios,
    PlazaAparcamiento,
    Otros,
    RegistroLegal,
    Seguridad,
    Transporte,
    Provincia,
    Barrio,
    Modalidad,
    Comarca,
    Municipio,
    Distrito,
    Condiciones,
    DatosInternos,
    DeclaracionZonaTensionada,
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
    fields = ('image', 'tipo', 'alt_text', 'posicion', 'default')

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


class InmueblePropietarioInline(admin.TabularInline):
    model = InmueblePropietario
    extra = 1
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


class MediaInmuebleInline(admin.TabularInline):
    model = MediaInmueble
    extra = 0


class RegistroLegalInline(admin.TabularInline):
    model = RegistroLegal
    extra = 0


class HistorialPrecioInline(admin.TabularInline):
    model = HistorialPrecio
    extra = 1


class InmuebleAdminForm(forms.ModelForm):
    """Distrito and barrio only offer what belongs to the chosen municipio / distrito."""

    class Meta:
        model = Inmueble
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        municipio = self._selected('municipio')
        distrito = self._selected('distrito')
        self.fields['distrito'].queryset = Distrito.objects.filter(municipio_id=municipio)
        barrios = Barrio.objects.filter(distrito__municipio_id=municipio)
        if distrito:
            barrios = barrios.filter(distrito_id=distrito)
        self.fields['barrio'].queryset = barrios
        widget = self.fields['municipio'].widget
        # The admin wraps related-field widgets; the attribute goes on the real select.
        getattr(widget, 'widget', widget).attrs['data-url'] = reverse(
            'admin:base_inmueble_ubicacion'
        )

    def _selected(self, name):
        """The submitted value when the form is bound, else the saved one."""
        raw = self.data.get(self.add_prefix(name)) if self.is_bound else getattr(
            self.instance, f'{name}_id'
        )
        try:
            return int(raw) if raw else None
        except (TypeError, ValueError):
            return None


class InmuebleAdmin(admin.ModelAdmin):
    form = InmuebleAdminForm
    inlines = [
        InmuebleModalidadInline,
        ImageInmuebleInline,
        MediaInmuebleInline,
        PlazaAparcamientoInline,
        RegistroLegalInline,
        HistorialPrecioInline,
        InmueblePropietarioInline,
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
        'estado',
        'publicar_web',
    )
    search_fields = ['referencia', 'direccion', 'propietarios__nombre']
    list_filter = ('modalidades', 'precios__estado', 'publicar_web')

    @admin.display(description='Propietario')
    def propietario(self, obj):
        return ', '.join(p.nombre for p in obj.propietarios.all())

    @admin.display(description='Precios')
    def precios_lista(self, obj):
        return ', '.join(
            f'{p.modalidad.nombre}: {p.precio} ({p.modalidad.get_unidad_precio_display().lower()})'
            for p in obj.precios.all()
        )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .prefetch_related(
                'propietarios',
                Prefetch('precios', queryset=InmuebleModalidad.objects.select_related('modalidad')))
        )

    class Media:
        js = ('base/admin/ubicacion.js',)

    def get_urls(self):
        return [
            path(
                'ubicacion/',
                self.admin_site.admin_view(self.ubicacion_options),
                name='base_inmueble_ubicacion',
            ),
            *super().get_urls(),
        ]

    def ubicacion_options(self, request):
        """Distritos of a municipio, or barrios of a distrito (else of a municipio)."""
        def pk(name):
            value = request.GET.get(name, '')
            return int(value) if value.isdigit() else None

        tipo = request.GET.get('tipo')
        if tipo == 'distritos':
            items = Distrito.objects.filter(municipio_id=pk('municipio'))
        elif tipo == 'barrios':
            items = Barrio.objects.filter(distrito__municipio_id=pk('municipio'))
            if pk('distrito'):
                items = items.filter(distrito_id=pk('distrito'))
        else:
            raise Http404
        return JsonResponse({'items': [{'id': i._id, 'nombre': i.nombre} for i in items]})

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
admin.site.register(Distrito)
admin.site.register(Barrio)

@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'unidad_precio', 'orden')


@admin.register(Propietario)
class PropietarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nif', 'email', 'telefono', 'gran_tenedor')
    list_filter = ('gran_tenedor',)
    search_fields = ('nombre', 'nif', 'email')


@admin.register(Condiciones)
class CondicionesAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'modalidad', 'por_defecto')
    list_filter = ('modalidad', 'por_defecto')


@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'tipo', 'nombre', 'email', 'telefono', 'fecha_desde', 'estado', 'created_at')
    list_filter = ('tipo', 'estado')
    search_fields = ('referencia', 'nombre', 'email')
    readonly_fields = ('inmueble', 'referencia', 'tipo', 'nombre', 'email', 'telefono',
                       'fecha_desde', 'mensaje', 'acepta_aviso_legal', 'datos_borrados', 'created_at')


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_ine', 'provincia', 'comarca')
    list_filter = ('provincia',)
    search_fields = ('nombre', 'codigo_ine')


@admin.register(DeclaracionZonaTensionada)
class DeclaracionZonaTensionadaAdmin(admin.ModelAdmin):
    list_display = ('municipio', 'desde', 'hasta', 'referencia')
    list_filter = ('desde', 'hasta')
    search_fields = ('municipio__nombre', 'referencia')
    autocomplete_fields = ('municipio',)
