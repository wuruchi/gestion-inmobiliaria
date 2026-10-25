"""Fake offers for development: realistic listings built from the saved example pages (see `generar`)."""
import random
import re

from django.conf import settings
from django.db import transaction

from ..locations import DryRun
from .constructor import Constructor
from .lugares import Lugares, resolver_municipio
from .medios import Medios
from .personas import DOMINIO, Propietarios
from .plantillas import PLANTILLAS
from .precios import Precios

PREFIJO_POR_DEFECTO = 'DEV'
AGENCIA_AICAT = '5205'  # AtBarcelona, see `python seed.py agencia`


def _modelos_contados():
    from base import models as m

    return (m.Inmueble, m.InmuebleModalidad, m.RegulacionAlquiler, m.TerminosAlquiler, m.InclusionesAlquiler,
            m.HistorialPrecio, m.ImageInmueble, m.MediaInmueble, m.DescripcionInmueble, m.RegistroLegal,
            m.CertificadoEnergetico, m.PlazaAparcamiento, m.Propietario, m.AcuerdoAdministracion)


def _siguiente_numero(prefijo):
    from base.models import Inmueble

    patron = re.compile(rf'^{re.escape(prefijo)}-(\d+)$')
    numeros = [int(m.group(1)) for r in Inmueble.objects.filter(referencia__startswith=f'{prefijo}-')
               .values_list('referencia', flat=True) if (m := patron.match(r))]
    return max(numeros, default=0) + 1


def _requisitos():
    from base.models import Agencia, Condiciones, Modalidad

    modalidades = {m.codigo: m for m in Modalidad.objects.all()}
    faltan = sorted({'temporal', 'habitual', 'venta'} - set(modalidades))
    if faltan:
        raise SystemExit(f'Load the modalidades first (python seed.py modalidades); missing: {", ".join(faltan)}')
    agencia = Agencia.objects.filter(aicat=AGENCIA_AICAT).first() or Agencia.objects.order_by('id').first()
    if agencia is None:
        raise SystemExit('Load the agency first (python seed.py agencia).')
    sin_condiciones = [c for c, m in modalidades.items() if not Condiciones.objects.filter(modalidad=m, por_defecto=True)]
    return modalidades, agencia, sin_condiciones


def generar(cantidad, municipio='Barcelona', semilla=None, ejemplos=None, con_medios=True,
            prefijo=PREFIJO_POR_DEFECTO, dry_run=False):
    """Creates `cantidad` fake offers in `municipio` and returns `(semilla, primero, estadisticas, avisos)`.

    Offer number `n` is built from example `(n - 1) % 9` (atb-01, atb-02, atb-03, idealista-01..03, locb-01..03),
    so the photos and the structure of the listing agree. Numbers continue after the last `PREFIJO-NNNN` in the
    database. The run is one transaction: if anything fails nothing is written.
    """
    if cantidad < 1:
        raise SystemExit('--count must be at least 1.')
    semilla = random.SystemRandom().randrange(1, 10**9) if semilla is None else semilla
    rng = random.Random(semilla)
    modalidades, agencia, sin_condiciones = _requisitos()
    muni = resolver_municipio(municipio)
    lugares = Lugares(muni)
    medios = Medios(ejemplos, settings.MEDIA_ROOT, copiar=con_medios and not dry_run)
    if con_medios:
        medios.comprobar()
    avisos = []
    if sin_condiciones:
        avisos.append('no default Condiciones for: ' + ', '.join(sin_condiciones) + ' (python seed.py condiciones)')
    zona = muni.zona_tensionada()
    if zona is None:
        avisos.append(f'{muni.nombre} has no stressed-zone declarations loaded, so no rent-regulation data is '
                      'created (python seed.py zonas-tensionadas)')
    elif zona is False:
        avisos.append(f'{muni.nombre} is not a stressed zone: no rent-regulation data is created')
    antes = {m: m.objects.count() for m in _modelos_contados()}
    primero = _siguiente_numero(prefijo)
    try:
        with transaction.atomic():
            constructor = Constructor(
                rng, lugares, Precios(muni, lugares.es_barcelona), Propietarios(rng), medios, agencia,
                modalidades, prefijo, con_medios)
            for n in range(primero, primero + cantidad):
                constructor.crear(n)
            estadisticas = {m.__name__: m.objects.count() - antes[m] for m in antes}
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return semilla, primero, estadisticas, avisos


def limpiar(prefijo=PREFIJO_POR_DEFECTO, dry_run=False):
    """Deletes the fake offers (`PREFIJO-NNNN`) and the fake owners left without listings. Returns the counts."""
    from base.models import Inmueble, Propietario

    patron = rf'^{re.escape(prefijo)}-\d+$'
    try:
        with transaction.atomic():
            inmuebles = Inmueble.objects.filter(referencia__regex=patron)
            n_inmuebles = inmuebles.count()
            inmuebles.delete()
            huerfanos = Propietario.objects.filter(email__endswith='@' + DOMINIO, inmuebles=None)
            n_propietarios = huerfanos.count()
            huerfanos.delete()
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return {'Inmueble': n_inmuebles, 'Propietario': n_propietarios}


__all__ = ['generar', 'limpiar', 'PLANTILLAS', 'PREFIJO_POR_DEFECTO']
