"""Builds one fake offer: a listing with its prices, conditions, equipment, legal records, owner, media and text."""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from . import textos
from .plantillas import PLANTILLAS

REFERENCIA_PATRON = r'^%s-\d+$'
NOTAS_INTERNAS = (
    'El propietario es flexible con la fecha de entrada.',
    'Llaves en la oficina; visitas solo con cita previa.',
    'Pendiente de revisar el certificado de la comunidad.',
    'El propietario prefiere inquilinos con nómina.',
    'Tasación actualizada con el propietario.',
    'Revisar la caldera antes de la próxima entrada.',
    'El propietario no quiere mascotas.',
    'Contacto preferido: correo electrónico.',
)
EFICIENCIA_CONSUMO = {  # kWh/m2/year bands, only the order of magnitude of the real scale
    'A': (20, 48), 'B': (48, 70), 'C': (70, 98), 'D': (98, 140), 'E': (140, 190), 'F': (190, 260), 'G': (260, 480),
}
ABREVIATURAS = (
    ("Carrer de la ", 'C/ '), ("Carrer de l'", 'C/ '), ("Carrer del ", 'C/ '), ("Carrer dels ", 'C/ '),
    ("Carrer de ", 'C/ '), ("Carrer ", 'C/ '), ("Avinguda de la ", 'Av. '), ("Avinguda de ", 'Av. '),
    ("Avinguda ", 'Av. '), ("Passeig de ", 'Pg. '), ("Passeig ", 'Pg. '),
)
CIA_ELECTRICA = ('Endesa', 'Iberdrola', 'Naturgy', 'Repsol')


def dec(valor, cifras=2):
    return Decimal(str(round(valor, cifras)))


def abreviar(calle):
    for largo, corto in ABREVIATURAS:
        if calle.startswith(largo):
            return corto + calle[len(largo):]
    return calle


class Constructor:
    """Holds what is shared by every offer of a run (lookups, random generator, caches)."""

    def __init__(self, rng, lugares, precios, propietarios, medios, agencia, modalidades, prefijo, con_medios):
        self.rng = rng
        self.lugares = lugares
        self.precios = precios
        self.propietarios = propietarios
        self.medios = medios
        self.agencia = agencia
        self.modalidades = modalidades
        self.prefijo = prefijo
        self.con_medios = con_medios
        self.hoy = timezone.localdate()
        self.zona_tensionada = lugares.municipio.zona_tensionada() is True

    # ------------------------------------------------------------------ helpers
    def valor(self, v, entero=False):
        """A fixed value, or a `(low, high)` pair drawn at random."""
        if isinstance(v, tuple):
            return self.rng.randint(*v) if entero or all(isinstance(x, int) for x in v) else dec(self.rng.uniform(*v))
        return v

    def resolver(self, datos, *, decimales=()):
        salida = {}
        for clave, v in datos.items():
            if isinstance(v, tuple):
                salida[clave] = dec(self.rng.uniform(*v)) if clave in decimales else self.rng.randint(*v)
            else:
                salida[clave] = v
        return salida

    # ------------------------------------------------------------------ the offer
    def crear(self, n):
        from base.models import Inmueble

        rng, p = self.rng, PLANTILLAS[(n - 1) % len(PLANTILLAS)]
        lugar = self.lugares.elegir(rng, p.get('solo_distritos'))
        sup = round(p['sup'] * rng.uniform(0.9, 1.1))
        modalidades = [p['modalidad']] + [m for m, prob in p['extra'].items() if rng.random() < prob]
        referencia = f'{self.prefijo}-{n:04d}'
        tipo_texto = {'zona': lugar['zona'], 'municipio': self.lugares.municipio.nombre, 'sup': sup,
                      'planta': None}
        planta = self.valor(p['planta'], entero=True) if p['planta'] else None
        if p['planta'] == (0, 0):
            planta = 0
        tipo_texto['planta'] = planta
        valor_venta = self.precios.venta(rng, sup, lugar['distrito_codigo'], p['factor_precio'])
        ocultar = rng.random() < p['ocultar']
        calle, numero = lugar['calle'], lugar['numero']
        direccion = f'{calle}, {numero}' if rng.random() < 0.7 else calle
        publicada = rng.random() < 0.9
        inmueble = Inmueble.objects.create(
            referencia=referencia, municipio=self.lugares.municipio, distrito=lugar['distrito'],
            barrio=lugar['barrio'], agencia=self.agencia, tipo=p['tipo'], subtipo=p['subtipo'],
            titulo=textos.titulo(p['clave'], **tipo_texto), conservacion=p['conservacion'],
            anio_construccion=rng.randint(*p['anio']),
            anio_ultima_reforma=rng.randint(*p['reforma']) if p['reforma'] else None,
            planta=planta, n_plantas=p['n_plantas'], codigo_postal=lugar['codigo_postal'], direccion=direccion,
            direccion_short=abreviar(f'{calle} {numero}') if rng.random() < 0.6 else '',
            dir_descripcion=self._puerta(p, planta), ocultar_direccion=ocultar,
            geo_latitude=lugar['lat'], geo_longitude=lugar['lon'],
            fecha_alta=self.hoy - timedelta(days=rng.randint(7, 540)),
            sup_construida=dec(sup), sup_util=dec(sup * rng.uniform(*p['ratio_util'])),
            sup_cont_comun=dec(sup * rng.uniform(0.08, 0.16)) if p['subtipo'] == 'piso' and rng.random() < 0.4 else None,
            sup_parcela=dec(rng.uniform(*p['parcela'])) if p.get('parcela') else None,
            publicar_web=publicada, usos=p.get('usos', ''),
            referencia_catastral=f'{rng.randint(1_000_000, 9_999_999)}DF{rng.randint(1000, 9999)}E'
                                 f'{rng.randint(1, 9999):04d}XX',
            gtos_comunidad=self._comunidad(p),
            situacion_actual='',
        )
        ofertas = [self._oferta(inmueble, p, m, sup, lugar, valor_venta, m != p['modalidad']) for m in modalidades]
        self._situacion_y_gastos(inmueble, p, ofertas, valor_venta, sup)
        self._fichas(inmueble, p, lugar, sup)
        self._legal(inmueble, p, modalidades)
        self._propiedad(inmueble, valor_venta)
        self._texto(inmueble, p, tipo_texto)
        if self.con_medios:
            self._media(inmueble, p, lugar, tipo_texto)
        return inmueble, p

    def _puerta(self, p, planta):
        if p['subtipo'].startswith('chalet') or planta is None:
            return ''
        if planta == 0:
            return 'Bajos'
        return f'Planta {planta}, puerta {self.rng.choice(["1ª", "2ª", "3ª", "A", "B"])}'

    def _comunidad(self, p):
        desde, hasta = p['gastos']['comunidad']
        return dec(self.rng.uniform(desde, hasta)) if hasta else None

    # ------------------------------------------------------------------ prices and rental rules
    def _oferta(self, inmueble, p, codigo, sup, lugar, valor_venta, es_extra):
        from base.models import HistorialPrecio, InmuebleModalidad

        rng = self.rng
        modalidad = self.modalidades[codigo]
        alquiler = modalidad.unidad_precio == 'mensual'
        if alquiler:
            precio = self.precios.alquiler(rng, sup, lugar['distrito_codigo'], p['factor_precio'], codigo)
            if p['tipo'] == 'oficina':
                precio = max(150, precio)
        else:
            precio = valor_venta
        azar = rng.random()
        if azar < 0.78:
            estado, dias = 'disponible', rng.randint(-20, 120)
        elif azar < 0.9:
            estado, dias = 'reservado', rng.randint(10, 60)
        else:
            estado, dias = 'cerrado', -rng.randint(10, 200)
        oferta = InmuebleModalidad.objects.create(
            inmueble=inmueble, modalidad=modalidad, precio=dec(precio), estado=estado,
            fecha_disponibilidad=self.hoy + timedelta(days=dias),
            tipo_iva=dec(p['tipo_iva']) if alquiler and p.get('tipo_iva') else None,
            fianza_meses=rng.choice(p['fianza']) if alquiler and p.get('fianza')
            else (rng.choices((1, 2, 3), (30, 55, 15))[0] if alquiler else None),
        )
        for k in range(rng.choice((0, 0, 1, 2))):
            fecha = self.hoy - timedelta(days=60 * (k + 1) + rng.randint(5, 40))
            HistorialPrecio.objects.create(
                inmueble=inmueble, modalidad=modalidad, fecha=fecha, importe=dec(precio * rng.uniform(0.88, 1.08)))
        if alquiler:
            self._reglas_alquiler(oferta, p, codigo, sup, lugar, precio, es_extra)
        return oferta

    def _reglas_alquiler(self, oferta, p, codigo, sup, lugar, precio, es_extra):
        from base.models import InclusionesAlquiler, RegulacionAlquiler, TerminosAlquiler

        rng = self.rng
        if self.zona_tensionada:
            minimo, maximo = self.precios.indice(rng, sup, lugar['distrito_codigo'])
            if p.get('sin_indice'):  # an office has no residential rent index, only its previous rent
                minimo = maximo = None
            azar = rng.random()
            datos = {'renta_previa': 'desconocida'}
            if azar < 0.55:
                datos = {'renta_previa': 'con_renta', 'ultima_renta': dec(round(precio * rng.uniform(0.8, 1.0) / 5) * 5),
                         'ultima_renta_fin': self.hoy - timedelta(days=rng.randint(20, 1700))}
            elif azar < 0.95:
                datos = {'renta_previa': 'sin_renta'}
            RegulacionAlquiler.objects.create(
                oferta=oferta, indice_referencia_min=None if p.get('indice_unico') else minimo,
                indice_referencia_max=maximo,
                indice_referencia_fecha=None if maximo is None else self.hoy - timedelta(days=rng.randint(1, 60)),
                **datos)
        terminos = p.get('terminos')
        if es_extra or not terminos:  # an extra habitual offer of a temporary example: a regular long lease
            minimo, maximo, usos = (1, 'anios'), (5, 'anios'), ()
        else:
            minimo, maximo, usos = terminos['min'], terminos['max'], terminos['usos']
        TerminosAlquiler.objects.create(
            oferta=oferta, acepta_animales=rng.random() < 0.45, acepta_fumadores=rng.random() < 0.2,
            estancia_minima=minimo[0], estancia_minima_unidad=minimo[1],
            estancia_maxima=maximo[0], estancia_maxima_unidad=maximo[1],
            uso_temporada=rng.choice(usos) if usos and codigo == 'temporal' else '')
        inclusiones = p.get('inclusiones', {})
        if es_extra:
            inclusiones = {k: v for k, v in inclusiones.items() if k != 'wifi'}
        InclusionesAlquiler.objects.create(oferta=oferta, **inclusiones)

    def _situacion_y_gastos(self, inmueble, p, ofertas, valor_venta, sup):
        rng = self.rng
        cerradas = [o for o in ofertas if o.estado == 'cerrado']
        if len(cerradas) == len(ofertas):
            situacion = 'alquilado' if any(o.modalidad.unidad_precio == 'mensual' for o in ofertas) else 'ocupado'
        else:
            situacion = p.get('situacion', 'libre' if rng.random() < 0.85 else 'ocupado')
        if p['modalidad'] == 'venta':
            ibi = valor_venta * rng.uniform(0.0008, 0.0014)
        else:
            ibi = sup * rng.uniform(4.5, 10)
        inmueble.situacion_actual = situacion
        inmueble.ibi = dec(ibi)
        inmueble.save(update_fields=['situacion_actual', 'ibi'])

    # ------------------------------------------------------------------ detail tables
    def _fichas(self, inmueble, p, lugar, sup):
        from base.models import (
            AreaRecreo, Caracteristicas, Distribucion, Dotacion, Entorno, Estancias, Instalaciones, OtrosEspacios,
            PlazaAparcamiento, Seguridad, Suministro, TransporteInmueble,
        )

        rng = self.rng
        distribucion = dict(p['distribucion'])
        if 'dobles' in distribucion:
            distribucion.setdefault('individuales', 0)
        Distribucion.objects.create(inmueble=inmueble, **distribucion)
        estancias = self.resolver(p['estancias'], decimales=('salon_m2', 'terraza_m2', 'balcones_m2'))
        if estancias and p['tipo'] == 'vivienda' and 'salon_m2' not in estancias:
            estancias['salon_m2'] = dec(sup * rng.uniform(0.2, 0.3))
        if estancias:
            Estancias.objects.create(inmueble=inmueble, **estancias)
        if p['otros']:
            OtrosEspacios.objects.create(inmueble=inmueble, **p['otros'])
        if p['dotacion']:
            Dotacion.objects.create(inmueble=inmueble, **p['dotacion'])
        instalaciones = self.resolver(p['instalaciones'])
        instalaciones['ascensor'] = p['ascensor']
        Instalaciones.objects.create(inmueble=inmueble, **instalaciones)
        if p['seguridad']:
            Seguridad.objects.create(inmueble=inmueble, **p['seguridad'])
        if p['area']:
            AreaRecreo.objects.create(inmueble=inmueble, **p['area'])
        entorno = self.resolver(p['entorno'], decimales=('jardin_m2',))
        playa = self.lugares.metros_a_playa(rng, lugar['distrito_codigo'])
        if playa is not None:
            entorno['distancia_playa_m'] = playa
        if entorno:
            Entorno.objects.create(inmueble=inmueble, **entorno)
        caracteristicas = self.resolver(p['caracteristicas'], decimales=('altura_real_m',))
        caracteristicas.setdefault('orientacion_norte', False)
        if not any(caracteristicas.get(f'orientacion_{d}') for d in ('norte', 'sur', 'este', 'oeste')):
            caracteristicas[f'orientacion_{rng.choice(("norte", "sur", "este", "oeste"))}'] = True
        Caracteristicas.objects.create(inmueble=inmueble, **caracteristicas)
        for tipo in p['suministros']:
            Suministro.objects.create(
                inmueble=inmueble, tipo=tipo, contador=True,
                compania={'agua': 'Aigües de Barcelona' if self.lugares.es_barcelona else 'Companyia d\'aigües local',
                          'electricidad': rng.choice(CIA_ELECTRICA), 'gas': 'Nedgia'}[tipo],
                tipo_suministro=p.get('gas', '') if tipo == 'gas' else '')
        for tipo, descripcion in self.lugares.transporte(rng, lugar['distrito_codigo']):
            TransporteInmueble.objects.create(inmueble=inmueble, tipo=tipo, descripcion=descripcion)
        self._plaza(inmueble, p)

    def _plaza(self, inmueble, p):
        from base.models import PlazaAparcamiento

        rng, plaza = self.rng, p.get('plaza')
        if plaza is None:
            if p['tipo'] != 'vivienda' or rng.random() >= 0.12:
                return
            plaza = {'opcional': False}
        datos = {'numero': str(rng.randint(1, 80)), 'tipo': 'coche', 'superficie': dec(rng.uniform(9, 13), 1)}
        if plaza['opcional']:
            datos.update(opcional=True, precio_opcional=dec(round(rng.uniform(*plaza['precio_opcional']) / 5) * 5),
                         precio_opcional_unidad='mensual', precio_opcional_tipo_iva=dec(plaza['tipo_iva']))
        else:
            datos.update(valor=dec(rng.randrange(18_000, 36_000, 500)), renta=dec(rng.randrange(70, 150, 5)))
        PlazaAparcamiento.objects.create(inmueble=inmueble, **datos)

    # ------------------------------------------------------------------ legal records
    def _legal(self, inmueble, p, modalidades):
        from base.models import CertificadoEnergetico, RegistroLegal

        rng, reg = self.rng, p['registros']
        alquiler = any(m != 'venta' for m in modalidades)
        if rng.random() < reg.get('cedula', 0):
            digitos = ''.join(str(rng.randint(0, 9)) for _ in range(11))
            numero = f'CHB{digitos}'
            if alquiler and rng.random() < 0.5:
                numero = f'CHB{digitos[:4]}{"*" * 7}'
            RegistroLegal.objects.create(
                inmueble=inmueble, tipo='cedula_habitabilidad', numero=numero, organismo='Generalitat de Catalunya')
        if 'temporal' in modalidades and rng.random() < reg.get('nrua', 0.8):
            if rng.random() < reg.get('nrua_en_tramite', 0.1):
                RegistroLegal.objects.create(inmueble=inmueble, tipo='nrua', estado='en_tramite',
                                             organismo='Ministerio de Vivienda y Agenda Urbana')
            else:
                numero = 'ESFCNT' + '0' * 5 + ''.join(str(rng.randint(0, 9)) for _ in range(10)) + '0' * 31 + '9'
                RegistroLegal.objects.create(inmueble=inmueble, tipo='nrua', numero=numero[:53],
                                             organismo='Ministerio de Vivienda y Agenda Urbana')
        if rng.random() < reg.get('licencia_turistica', 0):
            numero = f'HUTB-{rng.randint(1000, 999999):06d}' if rng.random() < 0.5 else ''
            RegistroLegal.objects.create(inmueble=inmueble, tipo='licencia_turistica', numero=numero,
                                         organismo='Generalitat de Catalunya')
        certificado = p['certificado']
        letra = rng.choice(certificado['letras'])
        consumo = rng.uniform(*EFICIENCIA_CONSUMO[letra])
        emision = self.hoy - timedelta(days=rng.randint(60, 3300))
        alfabeto = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
        CertificadoEnergetico.objects.create(
            inmueble=inmueble, eficiencia=letra, consumo_energetico=dec(consumo, 1),
            emisiones_co2=dec(consumo * rng.uniform(0.17, 0.25), 1),
            numero=''.join(rng.choice(alfabeto) for _ in range(9)) if rng.random() < certificado['numero'] else '',
            fecha_emision=emision, fecha_vencimiento=emision + timedelta(days=3650))

    # ------------------------------------------------------------------ owners and agency data
    def _propiedad(self, inmueble, valor_venta):
        from base.models import AcuerdoAdministracion, DatosInternos, InmueblePropietario

        rng = self.rng
        propietarios = [self.propietarios.elegir()]
        if rng.random() < 0.1:
            otro = self.propietarios.nuevo()
            reparto = rng.choice(((50, 50), (60, 40), (70, 30)))
            for propietario, porcentaje in zip((propietarios[0], otro), reparto):
                InmueblePropietario.objects.create(inmueble=inmueble, propietario=propietario,
                                                   porcentaje=dec(porcentaje))
        else:
            InmueblePropietario.objects.create(inmueble=inmueble, propietario=propietarios[0])
        tasacion = valor_venta * rng.uniform(0.95, 1.15)
        DatosInternos.objects.create(
            inmueble=inmueble, notas_internas=rng.choice(NOTAS_INTERNAS),
            tasacion_propietario=dec(round(tasacion / 1000) * 1000),
            fecha_tasacion=self.hoy - timedelta(days=rng.randint(10, 700)))
        if rng.random() < 0.7:
            firma = inmueble.fecha_alta - timedelta(days=rng.randint(0, 20))
            fin = None if rng.random() < 0.6 else firma + timedelta(days=365)
            AcuerdoAdministracion.objects.create(
                inmueble=inmueble, fecha_firma=firma, fecha_fin=fin, exclusiva=rng.random() < 0.6,
                gestion_comercial=True, administracion=rng.random() < 0.5)

    # ------------------------------------------------------------------ text and media
    def _texto(self, inmueble, p, contexto):
        from base.models import DescripcionInmueble

        for idioma, texto in textos.descripciones(p['clave'], self.rng, **contexto).items():
            DescripcionInmueble.objects.create(inmueble=inmueble, idioma=idioma, texto=texto)

    def _media(self, inmueble, p, lugar, contexto):
        from base.models import ImageInmueble, MediaInmueble
        from .medios import ALT

        where = f'{lugar["zona"]}, {self.lugares.municipio.nombre}'
        articulo = 'de la oficina' if p['tipo'] == 'oficina' else 'del inmueble'
        for posicion, (ruta, tipo, principal) in enumerate(self.medios.fotos(p['clave'])):
            ImageInmueble.objects.create(
                inmueble=inmueble, image=ruta, tipo=tipo, posicion=posicion, default=principal,
                alt_text=f'{ALT[tipo]} {articulo} en {where}'[:150])
        for posicion, enlace in enumerate(self.medios.enlaces(p['clave'])):
            MediaInmueble.objects.create(inmueble=inmueble, tipo=enlace['tipo'], url=enlace['url'],
                                         titulo=enlace['titulo'], posicion=posicion)
