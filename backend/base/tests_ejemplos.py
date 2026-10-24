"""Each saved example listing (AT Barcelona and idealista) rebuilt through the models.

For every example the listing is created the way staff would enter it, and the public API must
return every fact the original page shows. Where the page shows something the model does not
hold, the test says so in a `NO MODELADO` comment instead of pretending it fits.

The reference pages are in ../gestion-inmobiliaria-examples/ (atb-01..03, idealista-01..03).
"""
from datetime import date

from django.core.cache import cache
from django.test import TestCase

from base.models import (
    AreaRecreo, Banios, Comarca, Condiciones, DatosInternos, Distrito, Barrio, Dormitorios, Dotacion,
    Entorno, Estancias, ImageInmueble, Inmueble, InmuebleModalidad, Instalaciones, MediaInmueble,
    Modalidad, Municipio, Otros, OtrosEspacios, PlazaAparcamiento, Provincia, RegistroLegal,
    Seguridad, SolicitudReserva, Transporte,
)


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
        response = self.client.get(f'/api/inmuebles/{inmueble._id}/')
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
            f'/api/inmuebles/{inmueble._id}/reservas/', cuerpo, content_type='application/json')


class Atb01Test(EjemploTestCase):
    """Carrer de la Cera, ref G767: furnished flat in Ciutat Vella, seasonal rent, tensioned zone."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        eixample = Distrito.objects.create(municipio=cls.barcelona, codigo='02', nombre='Eixample')
        sant_antoni = Barrio.objects.create(distrito=eixample, codigo='07', nombre='Sant Antoni')
        cls.inm = inm = Inmueble.objects.create(
            referencia='G767', municipio=cls.barcelona, distrito=eixample, barrio=sant_antoni,
            direccion='Carrer de la Cera', tipo='Vivienda', subtipo='piso',
            fecha_disponibilidad=date(2026, 11, 23), sup_construida='70', publicar_web=True,
            descripcion_es='ARRENDAMIENTO DE USO DISTINTO DEL DE VIVIENDA (USO EXCLUSIVO VACACIONES/OCIO). '
                           'Fantástico piso de obra nueva y de diseño con una terraza privada, un solarium '
                           'y dos piscinas comunitarias. ALARMA Y WIFI INCLUIDO. Finca con ascensor.',
            zona_tensionada=True, indice_referencia_min='839.99', indice_referencia_max='1153.53',
            situacion_5_anios='Vivienda alquilada', ultima_renta='1750', gran_tenedor=False,
            actualizacion_renta='IRAV', eficiencia='D', consumo_energetico='71')
        precio_condiciones = Condiciones.objects.create(
            nombre='Temporada', modalidad=cls.temporal, por_defecto=True,
            fianza='Mínimo 2 mensualidades de alquiler.', honorarios='1 mensualidad + IVA',
            itp='0,5 % del importe del alquiler de todo el periodo (pago único)',
            suministros='Cuota fija mensual en concepto de provisión de fondos',
            limpieza_final='Obligatoria y a cargo del inquilino',
            incluido='Gastos de comunidad y seguro', no_incluido='Honorarios de la agencia, agua y luz',
            requisitos='Trabajador por cuenta ajena: DNI/NIE, contrato y 3 últimas nóminas, IBAN.')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.temporal, precio='1750')
        RegistroLegal.objects.create(inmueble=inm, tipo='cedula_habitabilidad', numero='CHB0333*******')
        RegistroLegal.objects.create(inmueble=inm, tipo='aicat', numero='5205')
        Dormitorios.objects.create(inmueble=inm, dobles=2, exteriores=2, suites=1)
        Banios.objects.create(inmueble=inm, banios=2)
        Estancias.objects.create(
            inmueble=inm, cocina=True, tipo_cocina='Americana', suelo_cocina='Baldosa',
            cocina_amueblada=True, balcones=1, terraza=2)
        Dotacion.objects.create(
            inmueble=inm, amueblado=True, lavadora=1, lavavajillas=1, microondas=1, nevera=1, horno=1,
            utensilios_cocina=True, camas=2, sofas=1, tendedero=1,
            vajilla=True, cuberteria=True, cristaleria=True, ropa_cama=True, toallas=True)
        Instalaciones.objects.create(
            inmueble=inm, contador_agua=True, contador_electricidad=True, calefaccion=True,
            aire_acondicionado=True, ascensor=1, internet=True)
        Entorno.objects.create(
            inmueble=inm, cerca_colegios=True, cerca_farmacia=True, cerca_guarderias=True,
            cerca_medico=True, cerca_supermercado=True, cerca_restaurantes=True)
        Seguridad.objects.create(
            inmueble=inm, puerta_blindada=True, sistema_alarma=True, portero_automatico=True)
        AreaRecreo.objects.create(inmueble=inm, piscina=True)
        Transporte.objects.create(
            inmueble=inm, cerca_bus=True, descripcion_bus='Ronda Sant Pau - Parlament',
            cerca_metro=True, descripcion_metro='L2 - Sant Antoni')
        Otros.objects.create(
            inmueble=inm, capacidad_personas=4, exterior=True, anio_ultima_reforma=2019,
            estancia_minima=2, estancia_maxima=11)

    def test_header_price_location_and_surface(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'referencia': 'G767', 'direccion': 'Carrer de la Cera', 'fecha_disponibilidad': '2026-11-23',
            'sup_construida': '70.00', 'tipo': 'Vivienda', 'subtipo': 'piso', 'zona': 'Sant Antoni',
            'zona_ref': 'Eixample', 'importe_alquiler': '1750.00', 'importe_venta': None, 'es_venta': False,
            'n_habitaciones': 2, 'n_banios': 2})
        self.assertEqual(data['provincia']['nombre'], 'Barcelona')
        self.assertEqual([(m['codigo'], m['precio'], m['mas_iva']) for m in data['modalidades']],
                         [('temporal', '1750.00', False)])

    def test_regulatory_block(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'zona_tensionada': True, 'indice_referencia_min': '839.99', 'indice_referencia_max': '1153.53',
            'situacion_5_anios': 'Vivienda alquilada', 'ultima_renta': '1750.00', 'gran_tenedor': False,
            'actualizacion_renta': 'IRAV', 'eficiencia': 'D', 'consumo_energetico': '71.00'})
        self.assertEqual(
            sorted((r['tipo'], r['numero']) for r in data['registros_legales']),
            [('aicat', '5205'), ('cedula_habitabilidad', 'CHB0333*******')])

    def test_characteristics_tables(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['dormitorios'], {'dobles': 2, 'exteriores': 2, 'suites': 1})
        self.assertContiene(data['cocina'], {
            'cocina': True, 'tipo_cocina': 'Americana', 'suelo_cocina': 'Baldosa', 'cocina_amueblada': True})
        self.assertContiene(data['terraza'], {'balcones': 1, 'terraza': 2})
        self.assertContiene(data['dotacion'], {
            'amueblado': True, 'lavadora': 1, 'lavavajillas': 1, 'microondas': 1, 'nevera': 1, 'horno': 1,
            'utensilios_cocina': True, 'camas': 2, 'sofas': 1, 'tendedero': 1,
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
        self.assertContiene(data['otros'], {
            'capacidad_personas': 4, 'exterior': True, 'anio_ultima_reforma': 2019,
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
        valles = Comarca.objects.create(provincia=cls.barcelona_prov, codigo='28', nombre='Vallès Occidental')
        sabadell = Municipio.objects.create(
            provincia=cls.barcelona_prov, comarca=valles, codigo_ine='08187', nombre='Sabadell')
        cls.inm = inm = Inmueble.objects.create(
            referencia='G753-B-1', municipio=sabadell, direccion='Carrer Industria', tipo='Oficina',
            fecha_disponibilidad=date(2026, 10, 25), sup_construida='40', publicar_web=True,
            descripcion_es='Alquiler de Oficina (2 a 5 años). Oficina en Sabadell Centre a escasos metros '
                           'de la Gran Vía. Dos espacios diáfanos, uno (16 m2) con un baño con ducha y otro '
                           'independiente (18 m2) en el patio (60 m2). DETALLES: Persianas eléctricas.',
            situacion_5_anios='Alquilado', ultima_renta='390', eficiencia='E', consumo_energetico='126')
        # Honorarios are 700 € + IVA for this office, so it has conditions of its own.
        propias = Condiciones.objects.create(
            nombre='Oficina G753-B-1', modalidad=cls.habitual, honorarios='700 € + IVA',
            incluido='Gastos de comunidad, seguro e IBI', no_incluido='Honorarios de la agencia, ITP y suministros')
        # The page says "+IVA" without the rate; 21 % is the general rate for commercial leases.
        InmuebleModalidad.objects.create(
            inmueble=inm, modalidad=cls.habitual, precio='450', mas_iva=True, tipo_iva='21',
            condiciones=propias)
        PlazaAparcamiento.objects.create(
            inmueble=inm, opcional=True, precio_opcional='60', precio_opcional_unidad='mensual',
            valor='25000', renta='45')
        Otros.objects.create(
            inmueble=inm, ibi_incluido=True, gastos_comunidad_incluidos=True,
            estancia_minima=1, estancia_minima_unidad='anios', estancia_maxima=3, estancia_maxima_unidad='anios')

    def test_office_price_with_vat_and_own_fees(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {'tipo': 'Oficina', 'subtipo': '', 'sup_construida': '40.00'})
        precio = data['modalidades'][0]
        self.assertContiene(precio, {'codigo': 'habitual', 'precio': '450.00', 'mas_iva': True, 'tipo_iva': '21.00'})
        self.assertContiene(precio['condiciones'], {
            'honorarios': '700 € + IVA', 'incluido': 'Gastos de comunidad, seguro e IBI'})

    def test_included_costs_and_stay_in_years(self):
        otros = self.detalle(self.inm)['otros']
        self.assertContiene(otros, {
            'ibi_incluido': True, 'gastos_comunidad_incluidos': True,
            'estancia_minima': 1, 'estancia_minima_unidad': 'anios',
            'estancia_maxima': 3, 'estancia_maxima_unidad': 'anios'})

    def test_optional_parking_has_a_public_price_and_hides_internal_amounts(self):
        respuesta = self.client.get(f'/api/inmuebles/{self.inm._id}/')
        plaza = respuesta.json()['plazas'][0]
        self.assertContiene(plaza, {
            'opcional': True, 'precio_opcional': '60.00', 'precio_opcional_unidad': 'mensual',
            'precio_opcional_mas_iva': False})
        self.assertNotIn('25000', respuesta.content.decode())

    def test_energy_and_last_rent(self):
        self.assertContiene(self.detalle(self.inm), {
            'situacion_5_anios': 'Alquilado', 'ultima_renta': '390.00', 'eficiencia': 'E',
            'consumo_energetico': '126.00'})

    # NO MODELADO: a long office lease has to use the `habitual` modalidad, whose name says "Vivienda
    # habitual". "Persianas eléctricas" has no field; it stays in the description. An office has no
    # bedroom or bathroom count on the card ("0 0"), which matches a missing Dormitorios/Banios row.


class Atb03Test(EjemploTestCase):
    """Carrer Ribes, ref 576: four-bedroom flat, seasonal rent, most detail tables filled."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inm = inm = Inmueble.objects.create(
            referencia='576', municipio=cls.barcelona, direccion='Carrer Ribes', tipo='Vivienda',
            subtipo='piso', fecha_disponibilidad=date(2026, 10, 25), sup_construida='90', publicar_web=True,
            descripcion_es='ALQUILER DE TEMPORADA. Piso reformado de 4 habitaciones dobles con 2 baños, '
                           'balcón. Cocina office con lavadero. Salón-comedor de 22 m2. WIFI incluido.')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.temporal, precio='2200')
        Dormitorios.objects.create(inmueble=inm, dobles=4, exteriores=2)
        Banios.objects.create(inmueble=inm, banios=2)
        Estancias.objects.create(
            inmueble=inm, salon_m2='22', balcones=1, balcones_m2='4', cocina=True, tipo_cocina='Office',
            cocina_amueblada=True, carpinteria_interior='Madera', carpinteria_exterior='Aluminio')
        OtrosEspacios.objects.create(inmueble=inm, vestidores=1, lavadero=1)
        Dotacion.objects.create(
            inmueble=inm, amueblado=True, armarios_empotrados=1, lavadora=1, lavavajillas=1, microondas=1,
            nevera=1, ropero=1, toldo=1, horno=1, utensilios_cocina=True, camas=3, sofas=2,
            vajilla=True, cuberteria=True)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, tipo_calefaccion='Central', subtipo_calefaccion='Gas natural',
            tvs=1, ascensor=1, instalacion_telefono=True)
        Entorno.objects.create(
            inmueble=inm, cerca_colegios=True, cerca_farmacia=True, cerca_guarderias=True, cerca_medico=True,
            cerca_centro_comercial=True, distancia_playa_m=2000, cerca_supermercado=True,
            cerca_restaurantes=True)
        Transporte.objects.create(inmueble=inm, cerca_bus=True, cerca_metro=True)
        Otros.objects.create(
            inmueble=inm, capacidad_personas=4, suelo_piso='Terrazo', altura_real_m='3',
            anio_ultima_reforma=2014, gastos_comunidad_incluidos=True,
            # The description says "32 días hasta 4-6 meses"; the structured field says 6 and 6 meses.
            estancia_minima=32, estancia_minima_unidad='dias', estancia_maxima=6)
        # Agency-only data that the page leaked into its public "Otros" block.
        DatosInternos.objects.create(
            inmueble=inm, exclusiva=True, gestion_comercial=True, administracion=True,
            tasacion_propietario='1200')

    def test_card_and_rooms(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'importe_alquiler': '2200.00', 'sup_construida': '90.00', 'n_habitaciones': 4, 'n_banios': 2})
        self.assertContiene(data['dormitorios'], {'dobles': 4, 'exteriores': 2})

    def test_living_areas_and_carpentry_material(self):
        data = self.detalle(self.inm)
        self.assertEqual(data['salon']['salon_m2'], '22.00')
        self.assertContiene(data['terraza'], {'balcones': 1, 'balcones_m2': '4.00'})
        self.assertContiene(data['cocina'], {'tipo_cocina': 'Office', 'cocina_amueblada': True})
        self.assertContiene(data['carpinteria'], {
            'carpinteria_interior': 'Madera', 'carpinteria_exterior': 'Aluminio'})
        self.assertContiene(data['otros_espacios'], {'vestidores': 1, 'lavadero': 1})

    def test_equipment_and_installations(self):
        data = self.detalle(self.inm)
        self.assertContiene(data['dotacion'], {
            'amueblado': True, 'armarios_empotrados': 1, 'ropero': 1, 'toldo': 1, 'camas': 3, 'sofas': 2})
        self.assertContiene(data['instalaciones'], {
            'calefaccion': True, 'tipo_calefaccion': 'Central', 'subtipo_calefaccion': 'Gas natural',
            'tvs': 1, 'ascensor': 1, 'instalacion_telefono': True})
        self.assertContiene(data['entorno'], {'cerca_centro_comercial': True, 'distancia_playa_m': 2000})

    def test_other_data_and_stay_with_days(self):
        self.assertContiene(self.detalle(self.inm)['otros'], {
            'capacidad_personas': 4, 'suelo_piso': 'Terrazo', 'altura_real_m': '3.00',
            'anio_ultima_reforma': 2014, 'gastos_comunidad_incluidos': True,
            'estancia_minima': 32, 'estancia_minima_unidad': 'dias',
            'estancia_maxima': 6, 'estancia_maxima_unidad': 'meses'})

    def test_internal_data_is_kept_but_never_published(self):
        datos = DatosInternos.objects.get(inmueble=self.inm)
        self.assertEqual((datos.exclusiva, str(datos.tasacion_propietario)), (True, '1200.00'))
        cuerpo = self.client.get(f'/api/inmuebles/{self.inm._id}/').content.decode()
        for secreto in ('1200.00', 'tasacion', 'exclusiva', 'gestion_comercial', 'administracion'):
            self.assertNotIn(secreto, cuerpo)

    # NO MODELADO (decided): "Empresas / Estudiantes / Particulares / Propietarios Serv. Alquiler" and
    # "Relación calidad precio" are not stored. The description says the balcony is 6 m2 while the
    # structured field says 4: the page contradicts itself; the structured value is used.


class Idealista01Test(EjemploTestCase):
    """Chalet adosado en C-vega 18, Vega, Gijón: terraced house for sale, in another province."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        gijon = Municipio.objects.create(provincia=cls.asturias, codigo_ine='33024', nombre='Gijón')
        periurbano = Distrito.objects.create(municipio=gijon, codigo='99', nombre='Periurbano')
        vega = Barrio.objects.create(distrito=periurbano, codigo='01', nombre='Vega')
        cls.inm = inm = Inmueble.objects.create(
            referencia='IDEA-01', municipio=gijon, distrito=periurbano, barrio=vega,
            direccion='C-vega, 18', dir_descripcion='Urb. Urbanización el Vaticano',
            tipo='Vivienda', subtipo='chalet_adosado', conservacion='buen_estado', anio_construccion=1955,
            n_plantas=2, sup_construida='154', sup_parcela='142', gtos_comunidad='50', ibi='210',
            consumo_energetico='470.1', emisiones_co2='83', publicar_web=True,
            descripcion_es='Chalet adosado de dos plantas con amplio jardín de 79 m2, dos trasteros y '
                           'porche trasero con vistas y acceso directo al jardín.')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.venta, precio='279000')
        # The page does not say which kind of bedroom the 3 are.
        Dormitorios.objects.create(inmueble=inm, dobles=3)
        Banios.objects.create(inmueble=inm, banios=1)
        Estancias.objects.create(inmueble=inm, terraza=1)
        Dotacion.objects.create(inmueble=inm, armarios_empotrados=1)
        OtrosEspacios.objects.create(inmueble=inm, trastero=2)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, tipo_calefaccion='Individual', subtipo_calefaccion='Eléctrica')
        Entorno.objects.create(inmueble=inm, jardin=True, jardin_m2='79')
        Otros.objects.create(inmueble=inm, orientacion='norte, sur')
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
            'tipo': 'Vivienda', 'subtipo': 'chalet_adosado', 'importe_venta': '279000.00',
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
        self.assertEqual(data['terraza']['terraza'], 1)
        self.assertContiene(data['instalaciones'], {
            'calefaccion': True, 'tipo_calefaccion': 'Individual', 'subtipo_calefaccion': 'Eléctrica'})
        self.assertEqual(data['otros']['orientacion'], 'norte, sur')

    def test_energy_certificate_with_emissions(self):
        self.assertContiene(self.detalle(self.inm), {'consumo_energetico': '470.10', 'emisiones_co2': '83.00'})

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
        cls.inm = inm = Inmueble.objects.create(
            referencia='IDEA-02', municipio=aviles, distrito=distrito, direccion='Calle Carmen',
            ocultar_direccion=True, tipo='Vivienda', subtipo='chalet_independiente',
            conservacion='buen_estado', anio_construccion=2008, n_plantas=2, sup_construida='265',
            sup_util='260', consumo_energetico='210', emisiones_co2='36',
            situacion_actual='Alquiler vacacional', publicar_web=True,
            descripcion_es='Edificio moderno (2008) con 2 dúplex reformados. Dúplex 1 (Planta baja + 1ª) '
                           '127M2. Dúplex 2 (3ª + 4ª planta) 138M2. Ambos con división horizontal.')
        InmuebleModalidad.objects.create(inmueble=inm, modalidad=cls.venta, precio='389500')
        Dormitorios.objects.create(inmueble=inm, dobles=6, suites=2)
        Banios.objects.create(inmueble=inm, banios=6)
        Dotacion.objects.create(inmueble=inm, armarios_empotrados=1)
        OtrosEspacios.objects.create(inmueble=inm, trastero=1)
        Instalaciones.objects.create(
            inmueble=inm, calefaccion=True, tipo_calefaccion='Individual', subtipo_calefaccion='Gas natural')
        Otros.objects.create(inmueble=inm, orientacion='sur, este')
        ImageInmueble.objects.create(inmueble=inm, image='p/1.jpg', tipo='fachada', default=True)
        ImageInmueble.objects.create(inmueble=inm, image='p/plan.jpg', tipo='plano', alt_text='Planta baja')
        MediaInmueble.objects.create(inmueble=inm, tipo='tour', url='https://example.com/tour/idea-02')

    def test_numbers(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'importe_venta': '389500.00', 'sup_construida': '265.00', 'sup_util': '260.00',
            'n_habitaciones': 6, 'n_banios': 6, 'n_plantas': 2, 'anio_construccion': 2008,
            'subtipo': 'chalet_independiente', 'consumo_energetico': '210.00', 'emisiones_co2': '36.00',
            'situacion_actual': 'Alquiler vacacional'})
        self.assertContiene(data['dormitorios'], {'dobles': 6, 'suites': 2})
        self.assertEqual(round(float(data['importe_venta']) / float(data['sup_construida'])), 1470)

    def test_exact_address_is_withheld_but_the_zone_is_shown(self):
        respuesta = self.client.get(f'/api/inmuebles/{self.inm._id}/')
        data = respuesta.json()
        self.assertContiene(data, {'ocultar_direccion': True, 'direccion': '', 'direccion_short': ''})
        self.assertNotIn('Calle Carmen', respuesta.content.decode())
        self.assertEqual(data['zona_ref'], 'El Pozón - Villalegre - La Luz')
        self.assertEqual(data['municipio']['nombre'], 'Avilés')
        listado = self.client.get('/api/inmuebles/').content.decode()
        self.assertNotIn('Calle Carmen', listado)

    def test_floor_plan_is_apart_from_the_photos(self):
        data = self.detalle(self.inm)
        self.assertEqual([i['tipo'] for i in data['images']], ['fachada'])
        self.assertEqual([(i['tipo'], i['alt_text']) for i in data['planos']], [('plano', 'Planta baja')])

    def test_the_two_duplexes_survive_in_the_description(self):
        descripcion = self.detalle(self.inm)['descripcion_es']
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
        garraf = Comarca.objects.create(provincia=cls.barcelona_prov, codigo='11', nombre='Garraf')
        sitges = Municipio.objects.create(
            provincia=cls.barcelona_prov, comarca=garraf, codigo_ine='08270', nombre='Sitges')
        centre = Distrito.objects.create(municipio=sitges, codigo='01', nombre='Centre')
        cls.inm = inm = Inmueble.objects.create(
            referencia='IDEA-03', municipio=sitges, distrito=centre, direccion='Calle de Sant Sebastià',
            ocultar_direccion=True, tipo='Vivienda', subtipo='piso', conservacion='buen_estado',
            anio_construccion=2009, sup_construida='55', sup_util='46', gran_tenedor=False,
            consumo_energetico='143', emisiones_co2='25', publicar_web=True,
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
        RegistroLegal.objects.create(inmueble=inm, tipo='certificado_energetico', numero='QWVL2082D')
        RegistroLegal.objects.create(inmueble=inm, tipo='aicat', numero='3366')
        # The page says the flat has a tourist licence but does not publish the number.
        RegistroLegal.objects.create(inmueble=inm, tipo='licencia_turistica')
        Dormitorios.objects.create(inmueble=inm, dobles=1)
        Banios.objects.create(inmueble=inm, banios=1)
        Dotacion.objects.create(inmueble=inm, amueblado=True)
        OtrosEspacios.objects.create(inmueble=inm, lavadero=1)
        Instalaciones.objects.create(inmueble=inm, calefaccion=False, aire_acondicionado=True, ascensor=1)
        Entorno.objects.create(inmueble=inm, zona_comunitaria=True)
        Otros.objects.create(inmueble=inm, orientacion='norte', exterior=True)

    def test_price_surfaces_and_energy(self):
        data = self.detalle(self.inm)
        self.assertContiene(data, {
            'importe_venta': '295000.00', 'sup_construida': '55.00', 'sup_util': '46.00',
            'anio_construccion': 2009, 'conservacion': 'buen_estado', 'gran_tenedor': False,
            'consumo_energetico': '143.00', 'emisiones_co2': '25.00', 'n_habitaciones': 1, 'n_banios': 1})
        self.assertEqual(round(float(data['importe_venta']) / float(data['sup_construida'])), 5364)

    def test_registry_numbers_and_the_licence_without_a_number(self):
        registros = {r['tipo']: r['numero'] for r in self.detalle(self.inm)['registros_legales']}
        self.assertEqual(registros, {
            'cedula_habitabilidad': 'CHB00523426001', 'certificado_energetico': 'QWVL2082D',
            'aicat': '3366', 'licencia_turistica': ''})

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
        self.assertEqual(data['otros']['exterior'], True)
        self.assertEqual(data['entorno']['zona_comunitaria'], True)
        self.assertEqual(data['direccion'], '')
        self.assertEqual(data['municipio']['nombre'], 'Sitges')

    # NO MODELADO: "Número API: A10580" is the agency's licence, not the listing's. "Enlace adicional"
    # (a link to the agency's own page) has no field. The page says both that it is sold furnished
    # and "sin muebles"; the model stores one answer (amueblado). The clause text about Ley 10/2025
    # stays in the description; only the amounts and bodies of the costs are structured.
