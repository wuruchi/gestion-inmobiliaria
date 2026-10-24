from datetime import date

from django.db.models import F, Prefetch, Q
from django.db.models.functions import Substr
from django.utils import timezone

from base.models import Inmueble, InmuebleModalidad, Municipio, RegulacionAlquiler


def inconsistencias_ubicacion():
    """Locations that do not nest, as a list of `(tipo, descripcion)`; empty when everything is consistent.

    The models check this on every `save()`, but `bulk_create()`, `QuerySet.update()` and raw SQL skip
    those checks and the database cannot express them, so this scan is the safety net.
    """
    problemas = []

    def añadir(tipo, queryset, describir):
        problemas.extend((tipo, describir(o)) for o in queryset)

    añadir(
        'distrito_de_otro_municipio',
        Inmueble.objects.filter(distrito__isnull=False).exclude(distrito__municipio=F('municipio')),
        lambda i: f'{i.referencia}: el distrito {i.distrito} no es del municipio {i.municipio}',
    )
    añadir(
        'barrio_de_otro_distrito',
        Inmueble.objects.filter(barrio__isnull=False, distrito__isnull=False)
        .exclude(barrio__distrito=F('distrito')),
        lambda i: f'{i.referencia}: el barrio {i.barrio} no es del distrito {i.distrito}',
    )
    añadir(
        'barrio_de_otro_municipio',
        Inmueble.objects.filter(barrio__isnull=False, distrito__isnull=True)
        .exclude(barrio__distrito__municipio=F('municipio')),
        lambda i: f'{i.referencia}: el barrio {i.barrio} no es del municipio {i.municipio}',
    )
    añadir(
        'municipio_con_codigo_de_otra_provincia',
        Municipio.objects.annotate(prefijo=Substr('codigo_ine', 1, 2))
        .exclude(prefijo=F('provincia__codigo_ine')),
        lambda m: f'{m.codigo_ine} {m.nombre}: el código no empieza por el de su provincia {m.provincia}',
    )
    return problemas


def _hace_cinco_anios(hoy):
    try:
        return hoy.replace(year=hoy.year - 5)
    except ValueError:  # 29 February
        return date(hoy.year - 5, 2, 28)


def pendientes_regulacion_alquiler(hoy=None):
    """Rental data that a published habitual-residence offer in a stressed zone is missing.

    Those ads must show the maximum price of the state reference index and the rent of the last
    contract of the last five years (or that there was none). Returns `(tipo, descripcion)` pairs for
    offers that are not closed. Only the `habitual` modalidad is checked: a temporary lease whose
    purpose is not clearly justified is treated as habitual by the law, which this cannot tell.
    """
    hoy = hoy or timezone.localdate()
    limite = _hace_cinco_anios(hoy)
    ofertas = (
        InmuebleModalidad.objects
        .filter(inmueble__publicar_web=True, modalidad__codigo='habitual')
        .exclude(estado=InmuebleModalidad.CERRADO)
        .select_related('inmueble__municipio', 'modalidad', 'regulacion')
        .prefetch_related('inmueble__municipio__declaraciones_tensionada')
        .order_by('inmueble__referencia')
    )
    problemas = []
    for oferta in ofertas:
        if not oferta.inmueble.municipio.es_zona_tensionada(hoy):
            continue
        ref = oferta.inmueble.referencia
        try:
            reg = oferta.regulacion
        except RegulacionAlquiler.DoesNotExist:
            reg = None
        if reg is None or reg.renta_previa == RegulacionAlquiler.DESCONOCIDA:
            problemas.append(('renta_previa_sin_confirmar', f'{ref}: falta indicar si hubo un alquiler en los últimos 5 años'))
        elif reg.renta_previa == RegulacionAlquiler.CON_RENTA:
            if reg.ultima_renta_fin is None:
                problemas.append(('renta_previa_sin_fecha_fin', f'{ref}: falta la fecha de fin del último contrato'))
            elif reg.ultima_renta_fin < limite:
                problemas.append((
                    'renta_previa_fuera_de_5_anios',
                    f'{ref}: el último contrato terminó el {reg.ultima_renta_fin}, hace más de 5 años; marcar "sin alquiler"'))
        if reg is None or reg.indice_referencia_max is None:
            problemas.append(('indice_sin_rellenar', f'{ref}: falta el índice de referencia (máximo)'))
    return problemas
