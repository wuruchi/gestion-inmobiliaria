"""Each saved example listing (AT Barcelona and idealista) rebuilt through the models.

For every example the listing is created the way staff would enter it, and the public API must
return every fact the original page shows. Where the page shows something the model does not
hold, the test says so in a `NO MODELADO` comment instead of pretending it fits.

The reference pages are in ../gestion-inmobiliaria-examples/ (atb-01..03, idealista-01..03, locb-01..03).
"""
from datetime import date

from django.core.cache import cache
from django.test import TestCase

from base.models import (
    InclusionesAlquiler, Propietario, InmueblePropietario, Agencia, DeclaracionZonaTensionada, RegulacionAlquiler,
    AreaRecreo, CertificadoEnergetico, AcuerdoAdministracion, Comarca, Condiciones, DatosInternos, Distrito, Barrio, Distribucion, Dotacion,
    Entorno, Estancias, ImageInmueble, Inmueble, InmuebleModalidad, Instalaciones, MediaInmueble,
    Modalidad, Municipio, Caracteristicas, OtrosEspacios, TerminosAlquiler, PlazaAparcamiento, Provincia, RegistroLegal,
    Seguridad, SolicitudReserva, Suministro, DescripcionInmueble, TransporteInmueble,
)


def crear_inmueble(**campos):
    """Create an Inmueble; `descripcion_<idioma>` keywords become `DescripcionInmueble` rows and the
    energy keywords (`eficiencia`, `consumo_energetico`, `emisiones_co2`, `numero_certificado`) a certificate."""
    descripciones = {i: campos.pop(f'descripcion_{i}', '') for i, _ in DescripcionInmueble.IDIOMAS}
    energia = {k: campos.pop(k) for k in ('eficiencia', 'consumo_energetico', 'emisiones_co2') if k in campos}
    if 'numero_certificado' in campos:
        energia['numero'] = campos.pop('numero_certificado')
    inm = Inmueble.objects.create(**campos)
    if energia:
        CertificadoEnergetico.objects.create(inmueble=inm, **energia)
    for idioma, texto in descripciones.items():
        if texto:
            DescripcionInmueble.objects.create(inmueble=inm, idioma=idioma, texto=texto)
    return inm



class EjemploTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.temporal = Modalidad.objects.create(codigo='temporal', nombre='Vivienda temporal', orden=1)
        cls.habitual = Modalidad.objects.create(codigo='habitual', nombre='Vivienda habitual', orden=2)
        cls.venta = Modalidad.objects.create(
            codigo='venta', nombre='Venta', orden=3, unidad_precio=Modalidad.TOTAL)
        cls.barcelona_prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        cls.asturias = Provincia.objects.create(codigo_ine='33', nombre='Asturias')
        cls.barcelona = Municipio.objects.create(
            provincia=cls.barcelona_prov, codigo_ine='08019', nombre='Barcelona')

    def detalle(self, inmueble):
        response = self.client.get(f'/api/inmuebles/{inmueble.id}/')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def assertContiene(self, actual, esperado, mensaje=''):
        """Every key of `esperado` is in `actual` with that value."""
        self.assertEqual({k: actual.get(k, '<falta>') for k in esperado}, esperado, mensaje)

    def en_el_listado(self, inmueble, **esperado):
        item = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}[
            inmueble.referencia]
        self.assertContiene(item, esperado)

    def solicitar(self, inmueble, **extra):
        cache.clear()
        self.addCleanup(cache.clear)
        cuerpo = {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600000000',
                  'acepta_aviso_legal': True, **extra}
        return self.client.post(
            f'/api/inmuebles/{inmueble.id}/reservas/', cuerpo, content_type='application/json')


class Atb01Test(EjemploTestCase):
    """Carrer de la Cera, ref G767: furnished flat in Ciutat Vella, seasonal rent, tensioned zone."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        eixample = Distrito.objects.create(municipio=cls.barcelona, codigo='02', nombre='Eixample')
        sant_antoni = Barrio.objects.create(distrito=eixample, codigo='07', nombre='Sant Antoni')
        cls.inm = inm = crear_inmueble(
            referencia='G767', municipio=cls.barcelona, distrito=eixample, barrio=sant_antoni,
            direccion='Carrer de la Cera', tipo='vivienda', subtipo='piso',
            sup_construida='70', publicar_web=True,
            descripcion_es='ARRENDAMIENTO DE USO DISTINTO DEL DE VIVIENDA (USO EXCLUSIVO VACACIONES/OCIO). '
                           'Fantástico piso de obra nueva y de diseño con una terraza privada, un solarium '
                           'y dos piscinas comunitarias. ALARMA Y WIFI INCLUIDO. Finca con ascensor.',
            eficiencia='D', consumo_energetico='71')
        DeclaracionZonaTensionada.objects.create(municipio=cls.barcelona, desde=date(2021, 9, 20))
        # "El propietario es gran tenedor: no" needs a recorded owner, otherwise it is unknown.
        InmueblePropietario.objects.create(inmueble=inm, propietario=Propietario.objects.create(nombre='Propietario G767'))
        precio_condiciones = Condiciones.objects.create(
            nombre='Temporada', modalidad=cls.temporal, por_defecto=True,
            fianza='Mínimo 2 mensualidades de alquiler.', honorarios='1 mensualidad + IVA',
            itp='0,5 % del importe del alquiler de todo el periodo (pago único)',
            suministros='Cuota fija mensual en concepto de provisión de fondos',
            actualizacion_renta='IRAV',
            limpieza_final='Obligatoria y a cargo del inquilino',
            incluido='Gastos de comunidad y seguro', no_incluido='Honorarios de la agencia, agua y luz',
            requisitos='Trabajador por cuenta ajena: DNI/NIE, contrato y 3 últimas nóminas, IBAN.')
        oferta = InmuebleModalidad.objects.create(
            inmueble=inm, modalidad=cls.temporal, precio='1750', fecha_disponibilidad=date(2026, 11, 23))
        # The index range and the last rent (1750 €, ended 30/06/2026) are declared on the rental offer.
        RegulacionAlquiler.objects.create(
            oferta=oferta, indice_referencia_min='839.99', indice_referencia_max='1153.53',
            indice_referencia_fecha=date(2026, 10, 1), renta_previa='con_renta',
            ultima_renta='1750', ultima_renta_fin=date(2026, 6, 30))
        RegistroLegal.objects.create(inmueble=inm, tipo='cedula_habitabilidad', numero='CHB0333*******')
        # AICAT 5205 is the agency's number: the same on every ATBarcelona listing.
        Inmueble.objects.filter(pk=inm.pk).update(agencia=Agencia.objects.get_or_create(
            nombre='ATBarcelona', aicat='5205')[0])
        Distribucion.objects.create(
            inmueble=inm, dobles=2, exteriores=2, suites=1, banios=2, capacidad_personas=4)
        Estancias.objects.create(
            inmueble=inm, cocina=True, tipo_cocina='americana', suelo_cocina='baldosa',
            cocina_amueblada=True, n_balcones=1, n_terrazas=2)
        Dotacion.objects.create(
            inmueble=inm, amueblado=True, lavadora=True, lavavajillas=True, microondas=True, nevera=True, horno=True,
            utensilios_cocina=True, camas=2, sofas=1, tendedero=True,
            vajilla=True, cuberteria=True, cristaleria=True, ropa_cama=True, toallas=True)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, aire_acondicionado=True, ascensor=1, internet=True)
        Suministro.objects.create(inmueble=inm, tipo='agua', contador=True)
        Suministro.objects.create(inmueble=inm, tipo='electricidad', contador=True)
        Entorno.objects.create(
            inmueble=inm, cerca_colegios=True, cerca_farmacia=True, cerca_guarderias=True,
            cerca_medico=True, cerca_supermercado=True, cerca_restaurantes=True)
        Seguridad.objects.create(
            inmueble=inm, puerta_blindada=True, sistema_alarma=True, portero_automatico=True)
        AreaRecreo.objects.create(inmueble=inm, piscina=True)
        TransporteInmueble.objects.create(inmueble=inm, tipo='bus', descripcion='Ronda Sant Pau - Parlament')
        TransporteInmueble.objects.create(inmueble=inm, tipo='metro', descripcion='L2 - Sant Antoni')
        Caracteristicas.objects.create(inmueble=inm, exterior=True)
        Inmueble.objects.filter(pk=inm.pk).update(anio_ultima_reforma=2019)
        TerminosAlquiler.objects.create(oferta=oferta, estancia_minima=2, estancia_maxima=11)

    def test_header_price_location_and_surface(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'referencia': 'G767', 'direccion': 'Carrer de la Cera', 'fecha_disponibilidad': '2026-11-23',
            'sup_construida': '70.00', 'tipo': 'vivienda', 'subtipo': 'piso', 'zona': 'Sant Antoni',
            'zona_ref': 'Eixample', 'importe_alquiler': '1750.00', 'importe_venta': None, 'es_venta': False,
            'n_habitaciones': 2, 'n_banios': 2})
        self.assertEqual(data['provincia']['nombre'], 'Barcelona')
        self.assertEqual([(m['codigo'], m['precio'], m['mas_iva']) for m in data['modalidades']],
                         [('temporal', '1750.00', False)])

    def test_regulatory_block(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'zona_tensionada': True, 'gran_tenedor': False})
        self.assertContiene(data['certificado_energetico'], {'eficiencia': 'D', 'consumo_energetico': '71.00'})
        oferta = data['modalidades'][0]
        self.assertContiene(oferta['regulacion'], {
            'indice_referencia_min': '839.99', 'indice_referencia_max': '1153.53',
            'renta_previa': 'con_renta', 'ultima_renta': '1750.00', 'ultima_renta_fin': '2026-06-30'})
        self.assertEqual(oferta['condiciones']['actualizacion_renta'], 'IRAV')
        self.assertEqual(
            [(r['tipo'], r['numero']) for r in data['registros_legales']],
            [('cedula_habitabilidad', 'CHB0333*******')])
        self.assertEqual(data['agencia'], {'nombre': 'ATBarcelona', 'aicat': '5205', 'numero_api': ''})

    def test_characteristics_tables(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['distribucion'], {'dobles': 2, 'exteriores': 2, 'suites': 1})
        self.assertContiene(data['cocina'], {
            'cocina': True, 'tipo_cocina': 'americana', 'suelo_cocina': 'baldosa', 'cocina_amueblada': True})
        self.assertContiene(data['terraza'], {'n_balcones': 1, 'n_terrazas': 2})
        self.assertContiene(data['dotacion'], {
            'amueblado': True, 'lavadora': True, 'lavavajillas': True, 'microondas': True, 'nevera': True, 'horno': True,
            'utensilios_cocina': True, 'camas': 2, 'sofas': 1, 'tendedero': True,
            'vajilla': True, 'cuberteria': True, 'cristaleria': True, 'ropa_cama': True, 'toallas': True})
        self.assertContiene(data['instalaciones'], {
            'contador_agua': True, 'contador_electricidad': True, 'calefaccion': True,
            'aire_acondicionado': True, 'ascensor': 1, 'internet': True})
        self.assertContiene(data['entorno'], {
            'cerca_colegios': True, 'cerca_farmacia': True, 'cerca_guarderias': True, 'cerca_medico': True,
            'cerca_supermercado': True, 'cerca_restaurantes': True})
        self.assertContiene(data['seguridad'], {
            'puerta_blindada': True, 'sistema_alarma': True, 'portero_automatico': True})
        self.assertTrue(data['arearecreo']['piscina'])
        self.assertContiene(data['transporte'], {
            'cerca_bus': True, 'descripcion_bus': 'Ronda Sant Pau - Parlament',
            'cerca_metro': True, 'descripcion_metro': 'L2 - Sant Antoni'})
        self.assertContiene(data['caracteristicas'], {'exterior': True})
        self.assertContiene(data['distribucion'], {'capacidad_personas': 4})
        self.assertContiene(data, {'anio_ultima_reforma': 2019})
        self.assertContiene(data['modalidades'][0]['terminos'], {
            'estancia_minima': 2, 'estancia_minima_unidad': 'meses',
            'estancia_maxima': 11, 'estancia_maxima_unidad': 'meses'})

    def test_conditions_and_requirements(self):
        condiciones = self.detalle(self.inm)['modalidades'][0]['condiciones']
        self.assertContiene(condiciones, {
            'fianza': 'Mínimo 2 mensualidades de alquiler.', 'honorarios': '1 mensualidad + IVA',
            'itp': '0,5 % del importe del alquiler de todo el periodo (pago único)',
            'incluido': 'Gastos de comunidad y seguro'})
        self.assertIn('3 últimas nóminas', condiciones['requisitos'])

    def test_reservation_form(self):
        respuesta = self.solicitar(self.inm, fecha_desde='2026-11-23')
        self.assertEqual(respuesta.status_code, 201)
        solicitud = SolicitudReserva.objects.get()
        self.assertEqual((solicitud.tipo, solicitud.referencia), ('reserva', 'G767'))

    def test_listing_card(self):
        self.en_el_listado(self.inm, importe_alquiler='1750.00', zona='Sant Antoni', n_habitaciones=2)

    # NO MODELADO: "Visita Virtual", "Street View" and the PDF sheet are links generated by the site;
    # the energy label image and the FAQs are site-wide content. The description says "32 días hasta
    # 5 meses" while the structured fields say 2 and 11 meses: the page contradicts itself (see ATB-03
    # for days). "Guardar como favorito" / "Enviar a un amigo" are site features.


class Atb02Test(EjemploTestCase):
    """Carrer Industria, ref G753-B-1: office in Sabadell, 450 € + IVA, optional parking."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        valles = Comarca.objects.create(codigo='28', nombre='Vallès Occidental')
        sabadell = Municipio.objects.create(
            provincia=cls.barcelona_prov, comarca=valles, codigo_ine='08187', nombre='Sabadell')
        cls.inm = inm = crear_inmueble(
            referencia='G753-B-1', municipio=sabadell, direccion='Carrer Industria', tipo='oficina',
            sup_construida='40', publicar_web=True,
            descripcion_es='Alquiler de Oficina (2 a 5 años). Oficina en Sabadell Centre a escasos metros '
                           'de la Gran Vía. Dos espacios diáfanos, uno (16 m2) con un baño con ducha y otro '
                           'independiente (18 m2) en el patio (60 m2). DETALLES: Persianas eléctricas.',
            eficiencia='E', consumo_energetico='126')
        # Honorarios are 700 € + IVA for this office, so it has conditions of its own.
        propias = Condiciones.objects.create(
            nombre='Oficina G753-B-1', modalidad=cls.habitual, honorarios='700 € + IVA',
            incluido='Gastos de comunidad, seguro e IBI', no_incluido='Honorarios de la agencia, ITP y suministros')
        # The page says "+IVA" without the rate; 21 % is the general rate for commercial leases.
        oferta = InmuebleModalidad.objects.create(
            inmueble=inm, modalidad=cls.habitual, precio='450', tipo_iva='21', fecha_disponibilidad=date(2026, 10, 25),
            condiciones=propias)
        # The page says the office was let before (390 €); when that contract ended is not shown.
        RegulacionAlquiler.objects.create(oferta=oferta, renta_previa='con_renta', ultima_renta='390')
        PlazaAparcamiento.objects.create(
            inmueble=inm, opcional=True, precio_opcional='60', precio_opcional_unidad='mensual',
            valor='25000', renta='45')
        # "En el precio están incluidos los gastos de comunidad, el seguro y el IBI."
        InclusionesAlquiler.objects.create(oferta=oferta, gastos_comunidad=True, ibi=True, seguro=True)
        TerminosAlquiler.objects.create(
            oferta=oferta, estancia_minima=1, estancia_minima_unidad='anios',
            estancia_maxima=3, estancia_maxima_unidad='anios')

    def test_office_price_with_vat_and_own_fees(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {'tipo': 'oficina', 'subtipo': '', 'sup_construida': '40.00'})
        precio = data['modalidades'][0]
        self.assertContiene(precio, {'codigo': 'habitual', 'precio': '450.00', 'mas_iva': True, 'tipo_iva': '21.00'})
        self.assertContiene(precio['condiciones'], {
            'honorarios': '700 € + IVA', 'incluido': 'Gastos de comunidad, seguro e IBI'})

    def test_included_costs_and_stay_in_years(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['modalidades'][0]['inclusiones'], {
            'gastos_comunidad': True, 'ibi': True, 'seguro': True, 'wifi': False})
        self.assertContiene(data['modalidades'][0]['terminos'], {
            'estancia_minima': 1, 'estancia_minima_unidad': 'anios',
            'estancia_maxima': 3, 'estancia_maxima_unidad': 'anios'})

    def test_optional_parking_has_a_public_price_and_hides_internal_amounts(self):
        respuesta = self.client.get(f'/api/inmuebles/{self.inm.id}/')
        plaza = respuesta.json()['plazas'][0]
        self.assertContiene(plaza, {
            'opcional': True, 'precio_opcional': '60.00', 'precio_opcional_unidad': 'mensual',
            'precio_opcional_mas_iva': False})
        self.assertNotIn('25000', respuesta.content.decode())

    def test_energy_and_last_rent(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['certificado_energetico'], {'eficiencia': 'E', 'consumo_energetico': '126.00'})
        self.assertContiene(data['modalidades'][0]['regulacion'], {
            'renta_previa': 'con_renta', 'ultima_renta': '390.00', 'ultima_renta_fin': None})

    # NO MODELADO: a long office lease has to use the `habitual` modalidad, whose name says "Vivienda
    # habitual". "Persianas eléctricas" has no field; it stays in the description. An office has no
    # bedroom or bathroom count on the card ("0 0"), which matches a missing Distribucion row.


class Atb03Test(EjemploTestCase):
    """Carrer Ribes, ref 576: four-bedroom flat, seasonal rent, most detail tables filled."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inm = inm = crear_inmueble(
            referencia='576', municipio=cls.barcelona, direccion='Carrer Ribes', tipo='vivienda',
            subtipo='piso', sup_construida='90', publicar_web=True,
            descripcion_es='ALQUILER DE TEMPORADA. Piso reformado de 4 habitaciones dobles con 2 baños, '
                           'balcón. Cocina office con lavadero. Salón-comedor de 22 m2. WIFI incluido.')
        RegistroLegal.objects.create(
            inmueble=inm, tipo='nrua', numero='ESFCNT00000807200037322600000000000000000000000000009')
        oferta = InmuebleModalidad.objects.create(
            inmueble=inm, modalidad=cls.temporal, precio='2200', fecha_disponibilidad=date(2026, 10, 25))
        Distribucion.objects.create(inmueble=inm, dobles=4, exteriores=2, banios=2, capacidad_personas=4)
        Estancias.objects.create(
            inmueble=inm, salon_m2='22', n_balcones=1, balcones_m2='4', cocina=True, tipo_cocina='office',
            cocina_amueblada=True, carpinteria_interior='madera', carpinteria_exterior='aluminio')
        OtrosEspacios.objects.create(inmueble=inm, vestidores=1, lavadero=True)
        Dotacion.objects.create(
            inmueble=inm, amueblado=True, armarios_empotrados=1, lavadora=True, lavavajillas=True, microondas=True,
            nevera=True, ropero=1, toldo=True, horno=True, utensilios_cocina=True, camas=3, sofas=2,
            vajilla=True, cuberteria=True)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, tipo_calefaccion='central', subtipo_calefaccion='gas_natural',
            tvs=1, ascensor=1, instalacion_telefono=True)
        Entorno.objects.create(
            inmueble=inm, cerca_colegios=True, cerca_farmacia=True, cerca_guarderias=True, cerca_medico=True,
            cerca_centro_comercial=True, distancia_playa_m=2000, cerca_supermercado=True,
            cerca_restaurantes=True)
        TransporteInmueble.objects.create(inmueble=inm, tipo='bus')
        TransporteInmueble.objects.create(inmueble=inm, tipo='metro')
        Caracteristicas.objects.create(inmueble=inm, suelo_piso='terrazo', altura_real_m='3')
        Inmueble.objects.filter(pk=inm.pk).update(anio_ultima_reforma=2014)
        InclusionesAlquiler.objects.create(oferta=oferta, gastos_comunidad=True, wifi=True)
        # The description says "32 días hasta 4-6 meses"; the structured field says 6 and 6 meses.
        TerminosAlquiler.objects.create(
            oferta=oferta, estancia_minima=32, estancia_minima_unidad='dias', estancia_maxima=6)
        # Agency-only data that the page leaked into its public "Otros" block (now `Caracteristicas`).
        DatosInternos.objects.create(inmueble=inm, tasacion_propietario='1200')
        AcuerdoAdministracion.objects.create(
            inmueble=inm, exclusiva=True, gestion_comercial=True, administracion=True)

    def test_nrua_is_a_registry_of_the_property(self):
        registro = self.detalle(self.inm)['registros_legales'][0]
        self.assertContiene(registro, {'tipo': 'nrua', 'estado': 'vigente'})
        self.assertTrue(registro['numero'].startswith('ESFCNT'))

    def test_card_and_rooms(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'importe_alquiler': '2200.00', 'sup_construida': '90.00', 'n_habitaciones': 4, 'n_banios': 2})
        self.assertContiene(data['distribucion'], {'dobles': 4, 'exteriores': 2})

    def test_living_areas_and_carpentry_material(self):
        data = self.detalle(self.inm)
        self.assertEqual(data['salon']['salon_m2'], '22.00')
        self.assertContiene(data['terraza'], {'n_balcones': 1, 'balcones_m2': '4.00'})
        self.assertContiene(data['cocina'], {'tipo_cocina': 'office', 'cocina_amueblada': True})
        self.assertContiene(data['carpinteria'], {
            'carpinteria_interior': 'madera', 'carpinteria_exterior': 'aluminio'})
        self.assertContiene(data['otros_espacios'], {'vestidores': 1, 'lavadero': True})

    def test_equipment_and_installations(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['dotacion'], {
            'amueblado': True, 'armarios_empotrados': 1, 'ropero': 1, 'toldo': True, 'camas': 3, 'sofas': 2})
        self.assertContiene(data['instalaciones'], {
            'calefaccion': True, 'tipo_calefaccion': 'central', 'subtipo_calefaccion': 'gas_natural',
            'tvs': 1, 'ascensor': 1, 'instalacion_telefono': True})
        self.assertContiene(data['entorno'], {'cerca_centro_comercial': True, 'distancia_playa_m': 2000})

    def test_other_data_and_stay_with_days(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['caracteristicas'], {'suelo_piso': 'terrazo', 'altura_real_m': '3.00'})
        self.assertContiene(data['distribucion'], {'capacidad_personas': 4})
        self.assertContiene(data, {'anio_ultima_reforma': 2014})
        self.assertContiene(data['modalidades'][0]['inclusiones'], {'gastos_comunidad': True, 'wifi': True})
        self.assertContiene(data['modalidades'][0]['terminos'], {
            'estancia_minima': 32, 'estancia_minima_unidad': 'dias',
            'estancia_maxima': 6, 'estancia_maxima_unidad': 'meses'})

    def test_internal_data_is_kept_but_never_published(self):
        datos = DatosInternos.objects.get(inmueble=self.inm)
        acuerdo = AcuerdoAdministracion.objects.get(inmueble=self.inm)
        self.assertEqual((acuerdo.exclusiva, str(datos.tasacion_propietario)), (True, '1200.00'))
        cuerpo = self.client.get(f'/api/inmuebles/{self.inm.id}/').content.decode()
        for secreto in ('1200.00', 'tasacion', 'exclusiva', 'gestion_comercial', 'administracion'):
            self.assertNotIn(secreto, cuerpo)

    # NO MODELADO (decided): "Empresas / Estudiantes / Particulares / Propietarios Serv. Alquiler" and
    # "Relación calidad precio" are not stored. The description says the balcony is 6 m2 while the
    # structured field says 4: the page contradicts itself; the structured value is used.


class LocabarcelonaMixin:
    """What the three Locabarcelona pages share: the agency, its numbers and the amenity list."""

    @classmethod
    def agencia(cls):
        return Agencia.objects.get_or_create(
            nombre='Loca Barcelona', defaults={'aicat': '11525', 'numero_api': 'A13529'})[0]

    @classmethod
    def propietario_no_gran_tenedor(cls, inm):
        InmueblePropietario.objects.create(
            inmueble=inm, propietario=Propietario.objects.create(nombre=f'Propietario {inm.referencia}'))

    @classmethod
    def equipamiento(cls, inm, internet=True):
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, aire_acondicionado=True, tvs=1, ascensor=1, internet=internet)
        Dotacion.objects.create(
            inmueble=inm, amueblado=True, lavadora=True, secadora=True, lavavajillas=True, horno=True, nevera=True,
            microondas=True, tendedero=True, ventilador=1, sofa_cama=True, cafetera=True, plancha=True,
            kit_limpieza=True, secador_pelo=True, papel_higienico=True, ropa_cama=True, toallas=True)
        OtrosEspacios.objects.create(inmueble=inm, vestidores=1, despachos=1, trastero=1, patio=True)
        AreaRecreo.objects.create(inmueble=inm, piscina=True)
        Seguridad.objects.create(inmueble=inm, portero_conserje=True, portero_automatico=True)


class Locb01Test(LocabarcelonaMixin, EjemploTestCase):
    """Passeig de la Zona Franca, LCPC82MOT322: long-term rental (6 months to 5 years) in Sants."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        sants = Distrito.objects.create(municipio=cls.barcelona, codigo='03', nombre='Sants-Montjuïc')
        cls.inm = inm = crear_inmueble(
            referencia='LCPC82MOT322', municipio=cls.barcelona, distrito=sants, tipo='vivienda', subtipo='piso',
            conservacion='buen_estado', sup_construida='70', planta=8, publicar_web=True,
            eficiencia='A', numero_certificado='1Z1R5Z8HN',
            titulo='New-build property on Passeig de la Zona Franca in Barcelona, with a swimming pool, '
                   'storage room and parking space')
        Inmueble.objects.filter(pk=inm.pk).update(agencia=cls.agencia())
        DeclaracionZonaTensionada.objects.create(municipio=cls.barcelona, desde=date(2021, 9, 20))
        cls.propietario_no_gran_tenedor(inm)
        oferta = InmuebleModalidad.objects.create(
            inmueble=inm, modalidad=cls.habitual, precio='1900', fianza_meses=3,
            fecha_disponibilidad=date(2026, 10, 1))
        # The page shows one index value (1900 €/month): the maximum, with no minimum.
        RegulacionAlquiler.objects.create(
            oferta=oferta, indice_referencia_max='1900', renta_previa='sin_renta',
            indice_referencia_fecha=date(2026, 10, 1))
        Condiciones.objects.create(nombre='Larga duración', modalidad=cls.habitual, por_defecto=True,
                                   actualizacion_renta='IPC')
        TerminosAlquiler.objects.create(
            oferta=oferta, acepta_animales=True, acepta_fumadores=True,
            estancia_minima=6, estancia_maxima=5, estancia_maxima_unidad='anios')
        Distribucion.objects.create(inmueble=inm, dobles=2, banios=2, aseos=1)
        Estancias.objects.create(inmueble=inm, n_balcones=1, n_terrazas=1)
        PlazaAparcamiento.objects.create(inmueble=inm)
        cls.equipamiento(inm)

    def test_price_deposit_and_single_index_value(self):
        data = self.detalle(self.inm)
        oferta = data['modalidades'][0]
        self.assertContiene(oferta, {
            'codigo': 'habitual', 'precio': '1900.00', 'fianza_meses': 3, 'fianza_total': '5700.00'})
        self.assertContiene(oferta['regulacion'], {
            'indice_referencia_min': None, 'indice_referencia_max': '1900.00', 'renta_previa': 'sin_renta'})
        self.assertEqual(oferta['condiciones']['actualizacion_renta'], 'IPC')
        self.assertContiene(oferta['terminos'], {
            'acepta_fumadores': True, 'estancia_minima': 6, 'estancia_minima_unidad': 'meses',
            'estancia_maxima': 5, 'estancia_maxima_unidad': 'anios'})
        self.assertContiene(data, {'zona_tensionada': True, 'gran_tenedor': False, 'n_plz_garaje': 1})

    def test_agency_numbers_and_energy_certificate(self):
        data = self.detalle(self.inm)
        self.assertEqual(data['agencia'], {'nombre': 'Loca Barcelona', 'aicat': '11525', 'numero_api': 'A13529'})
        self.assertContiene(data['certificado_energetico'], {'eficiencia': 'A', 'numero': '1Z1R5Z8HN'})

    def test_rooms_amenities_and_extra_spaces(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['distribucion'], {'dobles': 2, 'banios': 2, 'aseos': 1})
        self.assertContiene(data['dotacion'], {
            'cafetera': True, 'plancha': True, 'kit_limpieza': True, 'secador_pelo': True,
            'papel_higienico': True, 'sofa_cama': True, 'secadora': True, 'tendedero': True})
        self.assertContiene(data['otros_espacios'], {'patio': True, 'vestidores': 1, 'despachos': 1, 'trastero': 1})
        self.assertContiene(data['arearecreo'], {'piscina': True})

    def test_available_since_a_date_in_the_past(self):
        self.assertEqual(self.detalle(self.inm)['fecha_disponibilidad'], '2026-10-01')

    # NO MODELADO: "Available now" is shown from the date; the "cooktop" (placa de cocción), the "Room" feature,
    # "Similar properties" and the favourites are not stored. The flat is called new-build but "in perfect
    # condition": `conservacion` has no level above buen estado.


class Locb02Test(LocabarcelonaMixin, EjemploTestCase):
    """TAPARODF99: short-term rental (up to 11 months) in Dreta de l'Eixample, NRU in process."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        eixample = Distrito.objects.create(municipio=cls.barcelona, codigo='02', nombre='Eixample')
        cls.inm = inm = crear_inmueble(
            referencia='TAPARODF99', municipio=cls.barcelona, distrito=eixample, tipo='vivienda', subtipo='piso',
            conservacion='buen_estado', sup_construida='65', publicar_web=True,
            eficiencia='C', numero_certificado='2TPR806LB')
        Inmueble.objects.filter(pk=inm.pk).update(agencia=cls.agencia(), ibi='618.13')
        DeclaracionZonaTensionada.objects.create(municipio=cls.barcelona, desde=date(2021, 9, 20))
        cls.propietario_no_gran_tenedor(inm)
        # The page rounds 1.163,50 € to 1.164 € and shows a deposit of 2.327 € (two months).
        oferta = InmuebleModalidad.objects.create(
            inmueble=inm, modalidad=cls.temporal, precio='1163.50', fianza_meses=2,
            fecha_disponibilidad=date(2027, 6, 21))
        RegulacionAlquiler.objects.create(oferta=oferta, indice_referencia_max='1066.97', renta_previa='sin_renta')
        Condiciones.objects.create(
            nombre='Temporada', modalidad=cls.temporal, por_defecto=True, actualizacion_renta='IPC',
            itp='El inquilino paga el ITP: 0,5 % del total de las rentas, en el primer mes del contrato.')
        TerminosAlquiler.objects.create(
            oferta=oferta, acepta_animales=True, acepta_fumadores=True, estancia_maxima=11)
        RegistroLegal.objects.create(inmueble=inm, tipo='nrua', estado='en_tramite')
        Distribucion.objects.create(inmueble=inm, dobles=3, banios=1, aseos=1)
        cls.equipamiento(inm)

    def test_nru_in_process_has_no_number(self):
        registro = self.detalle(self.inm)['registros_legales'][0]
        self.assertContiene(registro, {'tipo': 'nrua', 'estado': 'en_tramite', 'numero': ''})

    def test_price_deposit_ibi_and_far_availability(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {'ibi': '618.13', 'fecha_disponibilidad': '2027-06-21'})
        self.assertContiene(data['modalidades'][0], {'fianza_total': '2327.00', 'precio': '1163.50'})
        self.assertContiene(data['modalidades'][0]['regulacion'], {'indice_referencia_max': '1066.97'})
        self.assertIn('0,5 %', data['modalidades'][0]['condiciones']['itp'])
        self.assertContiene(data['modalidades'][0]['terminos'], {'estancia_maxima': 11, 'estancia_maxima_unidad': 'meses'})

    def test_energy_certificate_and_bedrooms(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['certificado_energetico'], {'eficiencia': 'C', 'numero': '2TPR806LB'})
        self.assertContiene(data, {'n_habitaciones': 3, 'n_banios': 1})


class Locb03Test(LocabarcelonaMixin, EjemploTestCase):
    """VA12COU837: flat for sale in Antiga Esquerra de l'Eixample; the certificate has a rating but no number."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        eixample = Distrito.objects.create(municipio=cls.barcelona, codigo='02', nombre='Eixample')
        cls.inm = inm = crear_inmueble(
            referencia='VA12COU837', municipio=cls.barcelona, distrito=eixample, tipo='vivienda', subtipo='piso',
            conservacion='buen_estado', sup_construida='94', planta=1, publicar_web=True, eficiencia='E')
        Inmueble.objects.filter(pk=inm.pk).update(agencia=cls.agencia(), ibi='800')
        cls.propietario_no_gran_tenedor(inm)
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.venta, precio='610000')
        Distribucion.objects.create(inmueble=inm, dobles=4, banios=1)
        cls.equipamiento(inm)
        Instalaciones.objects.filter(inmueble=inm).update(internet_velocidad_mbps=300)

    def test_sale_with_internet_speed_and_certificate_without_number(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {'importe_venta': '610000.00', 'ibi': '800.00', 'gran_tenedor': False,
                                   'n_habitaciones': 4, 'planta': 1})
        self.assertContiene(data['certificado_energetico'], {'eficiencia': 'E', 'numero': ''})
        self.assertEqual(data['instalaciones']['internet_velocidad_mbps'], 300)
        self.assertEqual(data['agencia']['numero_api'], 'A13529')

    def test_a_sale_has_no_rental_data(self):
        oferta = self.detalle(self.inm)['modalidades'][0]
        self.assertContiene(oferta, {
            'codigo': 'venta', 'fianza_meses': None, 'fianza_total': None, 'regulacion': None,
            'terminos': None, 'inclusiones': None})

    # NO MODELADO: the page shows no stay limits, deposit or index for a sale; "Check in" in the contact form is
    # the optional `fecha_desde` of a request.


class Idealista01Test(EjemploTestCase):
    """Chalet adosado en C-vega 18, Vega, Gijón: terraced house for sale, in another province."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        gijon = Municipio.objects.create(provincia=cls.asturias, codigo_ine='33024', nombre='Gijón')
        periurbano = Distrito.objects.create(municipio=gijon, codigo='99', nombre='Periurbano')
        vega = Barrio.objects.create(distrito=periurbano, codigo='01', nombre='Vega')
        cls.inm = inm = crear_inmueble(
            referencia='IDEA-01', municipio=gijon, distrito=periurbano, barrio=vega,
            direccion='C-vega, 18', dir_descripcion='Urb. Urbanización el Vaticano',
            tipo='vivienda', subtipo='chalet_adosado', conservacion='buen_estado', anio_construccion=1955,
            n_plantas=2, sup_construida='154', sup_parcela='142', gtos_comunidad='50', ibi='210',
            consumo_energetico='470.1', emisiones_co2='83', publicar_web=True,
            descripcion_es='Chalet adosado de dos plantas con amplio jardín de 79 m2, dos trasteros y '
                           'porche trasero con vistas y acceso directo al jardín.')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.venta, precio='279000')
        # The page does not say which kind of bedroom the 3 are.
        Distribucion.objects.create(inmueble=inm, dobles=3, banios=1)
        Estancias.objects.create(inmueble=inm, n_terrazas=1)
        Dotacion.objects.create(inmueble=inm, armarios_empotrados=1)
        OtrosEspacios.objects.create(inmueble=inm, trastero=2)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, tipo_calefaccion='individual', subtipo_calefaccion='electrica')
        Entorno.objects.create(inmueble=inm, jardin=True, jardin_m2='79')
        Caracteristicas.objects.create(inmueble=inm, orientacion_norte=True, orientacion_sur=True)
        for posicion, tipo in enumerate(
                ['terraza', 'fachada', 'fachada', 'salon', 'cocina', 'dormitorio', 'banio', 'vistas', 'jardin']):
            ImageInmueble.objects.create(
                inmueble=inm, image=f'{inm.pk}/{posicion}.jpg', tipo=tipo, posicion=posicion,
                default=posicion == 0)
        MediaInmueble.objects.create(inmueble=inm, tipo='tour', url='https://example.com/tour/idea-01')
        MediaInmueble.objects.create(inmueble=inm, tipo='video', url='https://example.com/video/idea-01-1', posicion=1)
        MediaInmueble.objects.create(inmueble=inm, tipo='video', url='https://example.com/video/idea-01-2', posicion=2)

    def test_headline_and_derived_price_per_square_metre(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'tipo': 'vivienda', 'subtipo': 'chalet_adosado', 'importe_venta': '279000.00',
            'importe_alquiler': None, 'es_venta': True, 'sup_construida': '154.00', 'n_habitaciones': 3,
            'n_banios': 1})
        # idealista shows "1.812 €/m²": derived by the client from the two fields above.
        self.assertEqual(round(float(data['importe_venta']) / float(data['sup_construida'])), 1812)

    def test_location_outside_barcelona(self):
        data = self.detalle(self.inm)
        self.assertEqual(
            (data['provincia']['nombre'], data['municipio']['nombre'], data['zona'], data['zona_ref']),
            ('Asturias', 'Gijón', 'Vega', 'Periurbano'))
        self.assertContiene(data, {'direccion': 'C-vega, 18', 'dir_descripcion': 'Urb. Urbanización el Vaticano'})

    def test_building_plot_and_garden(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'conservacion': 'buen_estado', 'anio_construccion': 1955, 'n_plantas': 2, 'planta': None,
            'sup_parcela': '142.00', 'gtos_comunidad': '50.00', 'ibi': '210.00'})
        self.assertContiene(data['entorno'], {'jardin': True, 'jardin_m2': '79.00'})
        self.assertEqual(data['otros_espacios']['trastero'], 2)
        self.assertEqual(data['dotacion']['armarios_empotrados'], 1)
        self.assertEqual(data['terraza']['n_terrazas'], 1)
        self.assertContiene(data['instalaciones'], {
            'calefaccion': True, 'tipo_calefaccion': 'individual', 'subtipo_calefaccion': 'electrica'})
        self.assertEqual(
            [data['caracteristicas'][f'orientacion_{lado}'] for lado in ('norte', 'sur', 'este', 'oeste')],
            [True, True, False, False])

    def test_energy_certificate_with_emissions(self):
        self.assertContiene(self.detalle(self.inm)['certificado_energetico'], {
            'consumo_energetico': '470.10', 'emisiones_co2': '83.00', 'eficiencia': ''})

    def test_tagged_photos_video_and_tour(self):
        data = self.detalle(self.inm)
        self.assertEqual(
            [i['tipo'] for i in data['images']],
            ['terraza', 'fachada', 'fachada', 'salon', 'cocina', 'dormitorio', 'banio', 'vistas', 'jardin'])
        self.assertTrue(data['images'][0]['default'])
        self.assertEqual(data['planos'], [])
        self.assertEqual([m['tipo'] for m in data['medios']], ['tour', 'video', 'video'])

    def test_sale_listing_is_found_by_the_sale_filters(self):
        ventas = '/api/inmuebles/modalidad/ventas/'
        for consulta in ('subtipo=chalet_adosado', 'sup_min=150', 'max_precio=300000', 'habitaciones=3',
                         'provincia=%d' % self.asturias.pk):
            refs = [i['referencia'] for i in self.client.get(f'{ventas}?{consulta}').json()['inmuebles']]
            self.assertEqual(refs, ['IDEA-01'], consulta)
        self.assertEqual(self.client.get(f'{ventas}?subtipo=piso').json()['inmuebles'], [])

    def test_contact_form_is_an_information_request(self):
        respuesta = self.solicitar(
            self.inm, tipo='visita', mensaje='Hola, me interesa este inmueble y me gustaría hacer una visita.')
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(SolicitudReserva.objects.get().tipo, 'visita')

    # NO MODELADO: the advertiser (an agency profile, chat, "Ver teléfono"), the listing statistics
    # (visits, favourites, contacts), "Foto editada con IA", mortgage and "Comparar hipotecas", and the
    # translations idealista generates (the model has es/en/cat texts only).


class Idealista02Test(EjemploTestCase):
    """Casa independiente en Calle Carmen, Avilés: building with two duplexes, address hidden."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        aviles = Municipio.objects.create(provincia=cls.asturias, codigo_ine='33004', nombre='Avilés')
        distrito = Distrito.objects.create(
            municipio=aviles, codigo='01', nombre='El Pozón - Villalegre - La Luz')
        cls.inm = inm = crear_inmueble(
            referencia='IDEA-02', municipio=aviles, distrito=distrito, direccion='Calle Carmen',
            ocultar_direccion=True, geo_latitude=43.5547, geo_longitude=-5.9248,
            tipo='vivienda', subtipo='chalet_independiente',
            conservacion='buen_estado', anio_construccion=2008, n_plantas=2, sup_construida='265',
            sup_util='260', consumo_energetico='210', emisiones_co2='36',
            situacion_actual='alquiler_vacacional', publicar_web=True,
            descripcion_es='Edificio moderno (2008) con 2 dúplex reformados. Dúplex 1 (Planta baja + 1ª) '
                           '127M2. Dúplex 2 (3ª + 4ª planta) 138M2. Ambos con división horizontal.')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.venta, precio='389500')
        Distribucion.objects.create(inmueble=inm, dobles=6, suites=2, banios=6)
        Dotacion.objects.create(inmueble=inm, armarios_empotrados=1)
        OtrosEspacios.objects.create(inmueble=inm, trastero=1)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, tipo_calefaccion='individual', subtipo_calefaccion='gas_natural')
        Caracteristicas.objects.create(inmueble=inm, orientacion_sur=True, orientacion_este=True)
        ImageInmueble.objects.create(inmueble=inm, image='p/1.jpg', tipo='fachada', default=True)
        ImageInmueble.objects.create(inmueble=inm, image='p/plan.jpg', tipo='plano', alt_text='Planta baja')
        MediaInmueble.objects.create(inmueble=inm, tipo='tour', url='https://example.com/tour/idea-02')

    def test_numbers(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'importe_venta': '389500.00', 'sup_construida': '265.00', 'sup_util': '260.00',
            'n_habitaciones': 6, 'n_banios': 6, 'n_plantas': 2, 'anio_construccion': 2008,
            'subtipo': 'chalet_independiente', 'situacion_actual': 'alquiler_vacacional'})
        self.assertContiene(data['certificado_energetico'], {'consumo_energetico': '210.00', 'emisiones_co2': '36.00'})
        self.assertContiene(data['distribucion'], {'dobles': 6, 'suites': 2})
        self.assertEqual(round(float(data['importe_venta']) / float(data['sup_construida'])), 1470)

    def test_exact_address_is_withheld_but_the_zone_is_shown(self):
        respuesta = self.client.get(f'/api/inmuebles/{self.inm.id}/')
        data = respuesta.json()
        self.assertContiene(data, {'ocultar_direccion': True, 'direccion': '', 'direccion_short': ''})
        self.assertNotIn('Calle Carmen', respuesta.content.decode())
        # The map shows an area, not the exact point.
        self.assertEqual((data['geo_latitude'], data['geo_longitude']), (43.555, -5.925))
        self.assertEqual(data['zona_ref'], 'El Pozón - Villalegre - La Luz')
        self.assertEqual(data['municipio']['nombre'], 'Avilés')
        listado = self.client.get('/api/inmuebles/').content.decode()
        self.assertNotIn('Calle Carmen', listado)

    def test_floor_plan_is_apart_from_the_photos(self):
        data = self.detalle(self.inm)
        self.assertEqual([i['tipo'] for i in data['images']], ['fachada'])
        self.assertEqual([(i['tipo'], i['alt_text']) for i in data['planos']], [('plano', 'Planta baja')])

    def test_the_two_duplexes_survive_in_the_description(self):
        descripcion = self.detalle(self.inm)['descripciones']['es']
        self.assertIn('127M2', descripcion)
        self.assertIn('138M2', descripcion)

    # NO MODELADO: the two duplexes are one listing; their separate areas (127 and 138 m2), bedrooms
    # and bathrooms live in the description only (decided: sub-units are out of scope). "Multimedia
    # realizado por idealista" is a marketplace badge.


class Idealista03Test(EjemploTestCase):
    """Piso en Calle de Sant Sebastià, Sitges: flat for sale with tourist licence and sale-cost clause."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        garraf = Comarca.objects.create(codigo='11', nombre='Garraf')
        sitges = Municipio.objects.create(
            provincia=cls.barcelona_prov, comarca=garraf, codigo_ine='08270', nombre='Sitges')
        centre = Distrito.objects.create(municipio=sitges, codigo='01', nombre='Centre')
        cls.inm = inm = crear_inmueble(
            referencia='IDEA-03', municipio=sitges, distrito=centre, direccion='Calle de Sant Sebastià',
            ocultar_direccion=True, tipo='vivienda', subtipo='piso', conservacion='buen_estado',
            anio_construccion=2009, sup_construida='55', sup_util='46',
            consumo_energetico='143', emisiones_co2='25', numero_certificado='QWVL2082D', publicar_web=True,
            descripcion_es='Piso en el corazón de Sitges. La propiedad cuenta con licencia turística. '
                           'PRECIO DE VENTA: 295.000€ + 29.500€ (ITP).')
        compraventa = Condiciones.objects.create(
            nombre='Compraventa', modalidad=cls.venta, por_defecto=True,
            honorarios='Honorarios de la agencia del vendedor: incluidos en el PVP.',
            itp='10 % hasta 600.000 € (29.500 € en este inmueble)',
            notaria='Arancel notarial oficial (Real Decreto 1426/1989)',
            registro='Arancel oficial (Real Decreto 1427/1989)',
            gestoria='350 € aproximadamente más IVA',
            honorarios_comprador='Solo si se contrata un personal shopper inmobiliario (PSI).',
            incluido='Honorarios de la agencia del vendedor', no_incluido='ITP, notaría, registro y gestoría')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.venta, precio='295000')
        RegistroLegal.objects.create(inmueble=inm, tipo='cedula_habitabilidad', numero='CHB00523426001')
        InmueblePropietario.objects.create(inmueble=inm, propietario=Propietario.objects.create(nombre='Propietario VSIT2576'))
        # AICAT 3366 and API A10580 are the agency's (GrupLiving), not the flat's.
        Inmueble.objects.filter(pk=inm.pk).update(agencia=Agencia.objects.create(
            nombre='GrupLiving Agents Immobiliaris', aicat='3366', numero_api='A10580'))
        # The page says the flat has a tourist licence but does not publish the number.
        RegistroLegal.objects.create(inmueble=inm, tipo='licencia_turistica')
        Distribucion.objects.create(inmueble=inm, dobles=1, banios=1)
        Dotacion.objects.create(inmueble=inm, amueblado=True)
        OtrosEspacios.objects.create(inmueble=inm, lavadero=True)
        Instalaciones.objects.create(inmueble=inm, calefaccion=False, aire_acondicionado=True, ascensor=1)
        Entorno.objects.create(inmueble=inm, zona_comunitaria=True)
        Caracteristicas.objects.create(inmueble=inm, orientacion_norte=True, exterior=True)

    def test_price_surfaces_and_energy(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'importe_venta': '295000.00', 'sup_construida': '55.00', 'sup_util': '46.00',
            'anio_construccion': 2009, 'conservacion': 'buen_estado', 'gran_tenedor': False,
            'n_habitaciones': 1, 'n_banios': 1})
        self.assertContiene(data['certificado_energetico'], {
            'numero': 'QWVL2082D', 'consumo_energetico': '143.00', 'emisiones_co2': '25.00'})
        self.assertEqual(round(float(data['importe_venta']) / float(data['sup_construida'])), 5364)

    def test_registry_numbers_and_the_licence_without_a_number(self):
        registros = {r['tipo']: r['numero'] for r in self.detalle(self.inm)['registros_legales']}
        self.assertEqual(registros, {
            'cedula_habitabilidad': 'CHB00523426001', 'licencia_turistica': ''})
        self.assertContiene(self.detalle(self.inm)['agencia'], {'aicat': '3366', 'numero_api': 'A10580'})

    def test_sale_costs_clause(self):
        condiciones = self.detalle(self.inm)['modalidades'][0]['condiciones']
        self.assertContiene(condiciones, {
            'honorarios': 'Honorarios de la agencia del vendedor: incluidos en el PVP.',
            'gestoria': '350 € aproximadamente más IVA',
            'honorarios_comprador': 'Solo si se contrata un personal shopper inmobiliario (PSI).'})
        for campo in ('itp', 'notaria', 'registro'):
            self.assertTrue(condiciones[campo], campo)
        self.assertIn('29.500', condiciones['itp'])

    def test_equipment_building_and_hidden_address(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['instalaciones'], {'calefaccion': False, 'aire_acondicionado': True, 'ascensor': 1})
        self.assertEqual(data['caracteristicas']['exterior'], True)
        self.assertEqual(data['entorno']['zona_comunitaria'], True)
        self.assertEqual(data['direccion'], '')
        self.assertEqual(data['municipio']['nombre'], 'Sitges')

    # NO MODELADO: "Enlace adicional"
    # (a link to the agency's own page) has no field. The page says both that it is sold furnished
    # and "sin muebles"; the model stores one answer (amueblado). The clause text about Ley 10/2025
    # stays in the description; only the amounts and bodies of the costs are structured.
