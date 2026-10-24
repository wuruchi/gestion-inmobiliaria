from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from base.models import Barrio, InmuebleModalidad, Modalidad, Condiciones, Distrito, Inmueble, Municipio, Provincia, RegistroLegal


def default_municipio():
    prov = Provincia.objects.get_or_create(codigo_ine='08', defaults={'nombre': 'Barcelona'})[0]
    return Municipio.objects.get_or_create(
        codigo_ine='08019', defaults={'provincia': prov, 'nombre': 'Barcelona'})[0]


def inmueble(**fields):
    """Create an Inmueble; `municipio` is required, so default to Barcelona."""
    fields.setdefault('municipio', default_municipio())
    return Inmueble.objects.create(**fields)


class LocationModelTests(TestCase):
    def setUp(self):
        self.prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        self.mun = Municipio.objects.create(
            provincia=self.prov, codigo_ine='08019', nombre='Barcelona'
        )
        self.dis = Distrito.objects.create(
            municipio=self.mun, codigo='02', nombre='Eixample'
        )

    def test_slug_is_generated(self):
        self.assertEqual(self.dis.slug, 'eixample')
        self.assertEqual(Municipio.objects.create(
            provincia=self.prov, codigo_ine='08101', nombre="l'Hospitalet de Llobregat"
        ).slug, 'lhospitalet-de-llobregat')

    def test_duplicate_ine_code_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Municipio.objects.create(provincia=self.prov, codigo_ine='08019', nombre='Otro')

    def test_duplicate_district_code_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Distrito.objects.create(municipio=self.mun, codigo='02', nombre='Otro')

    def test_parent_with_children_is_protected(self):
        with self.assertRaises(ProtectedError):
            self.prov.delete()

    def test_inmueble_location_must_be_consistent(self):
        other = Municipio.objects.create(
            provincia=self.prov, codigo_ine='08101', nombre="l'Hospitalet de Llobregat"
        )
        bad = Inmueble(referencia='X', municipio=other, distrito=self.dis)
        with self.assertRaises(ValidationError):
            bad.validate_location()
        with self.assertRaises(ValidationError):
            inmueble(referencia='X', municipio=other, distrito=self.dis)
        ok = inmueble(referencia='Y', municipio=self.mun, distrito=self.dis)
        self.assertEqual(ok.provincia, self.prov)

    def test_municipio_requires_matching_provincia_and_comarca(self):
        girona = Provincia.objects.create(codigo_ine='17', nombre='Girona')
        with self.assertRaises(ValidationError):
            Municipio.objects.create(provincia=girona, codigo_ine='08200', nombre='Mal codigo')
        from base.models import Comarca
        comarca = Comarca.objects.create(provincia=girona, codigo='01', nombre='Alt Emporda')
        with self.assertRaises(ValidationError):
            Municipio.objects.create(
                provincia=self.prov, comarca=comarca, codigo_ine='08300', nombre='Otra provincia')


class BarrioTests(TestCase):
    def setUp(self):
        prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        self.mun = Municipio.objects.create(provincia=prov, codigo_ine='08019', nombre='Barcelona')
        self.cv = Distrito.objects.create(municipio=self.mun, codigo='01', nombre='Ciutat Vella')
        self.ex = Distrito.objects.create(municipio=self.mun, codigo='02', nombre='Eixample')
        self.raval = Barrio.objects.create(distrito=self.cv, codigo='01', nombre='el Raval')

    def test_slug_and_unique_code(self):
        self.assertEqual(self.raval.slug, 'el-raval')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Barrio.objects.create(distrito=self.cv, codigo='01', nombre='Otro')

    def test_protect_and_consistency(self):
        with self.assertRaises(ProtectedError):
            self.cv.delete()
        inm = Inmueble(referencia='B1', municipio=self.mun, distrito=self.ex, barrio=self.raval)
        with self.assertRaises(ValidationError):
            inm.clean()
        inm.distrito = self.cv
        inm.clean()

    def test_api(self):
        inm = inmueble(referencia='B1', publicar_web=True, municipio=self.mun,
                                      distrito=self.cv, barrio=self.raval)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual(data['barrio']['nombre'], 'el Raval')
        self.assertEqual(len(self.client.get(f'/api/inmuebles/?barrio={self.raval._id}').json()['inmuebles']), 1)
        self.assertEqual(len(self.client.get(f'/api/inmuebles/?barrio={self.raval._id + 1}').json()['inmuebles']), 0)
        self.assertEqual(self.client.get(f'/api/distritos/{self.cv._id}/barrios').json()[0]['codigo'], '01')
        self.assertEqual(self.client.get('/api/inmuebles/?barrio=x').status_code, 400)


class DetailApiTests(TestCase):
    def setUp(self):
        from base.models import (
            Entorno, Estancias, Seguridad, Transporte,
        )
        self.temporal = Modalidad.objects.create(codigo='temporal', nombre='Temporal', orden=0)
        self.default = Condiciones.objects.create(
            nombre='General', modalidad=self.temporal, por_defecto=True, fianza='2 mensualidades'
        )
        self.inm = inmueble(
            referencia='G767', publicar_web=True,
            indice_referencia_min='839.99', indice_referencia_max='1153.53',
        )
        from base.models import DeclaracionZonaTensionada
        DeclaracionZonaTensionada.objects.create(municipio=self.inm.municipio, desde=date(2021, 9, 20))
        self.precio = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.temporal, precio='1750')
        Estancias.objects.create(inmueble=self.inm, terraza=2, balcones=1, descripcion='Vistas')
        Seguridad.objects.create(inmueble=self.inm, puerta_blindada=True)
        Entorno.objects.create(inmueble=self.inm, cerca_colegios=True)
        Transporte.objects.create(inmueble=self.inm, cerca_metro=True, descripcion_metro='L2')

    def test_detail_exposes_new_sections(self):
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['terraza']['balcones'], 1)
        self.assertTrue(data['seguridad']['puerta_blindada'])
        self.assertEqual(data['entorno']['cerca_colegios'], True)
        self.assertEqual(data['transporte']['descripcion_metro'], 'L2')
        self.assertEqual(data['salon'], {'id': data['terraza']['id'], 'salon_m2': None, 'descripcion': 'Vistas', 'inmueble': self.inm._id})
        self.assertEqual(data['terraza']['descripcion'], 'Vistas')
        self.assertFalse(data['carpinteria']['carpinteria_interior'])
        self.assertTrue(data['zona_tensionada'])

    def test_conditions_fall_back_to_default(self):
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['modalidades'][0]['condiciones']['fianza'], '2 mensualidades')
        self.assertNotIn('condiciones', data)
        own = Condiciones.objects.create(nombre='Larga', modalidad=self.temporal, fianza='1 mes')
        self.precio.condiciones = own
        self.precio.save()
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['modalidades'][0]['condiciones']['fianza'], '1 mes')

    def test_only_one_default_conditions_per_modalidad(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Condiciones.objects.create(nombre='Otra', modalidad=self.temporal, por_defecto=True)
        venta = Modalidad.objects.create(codigo='venta', nombre='Venta', orden=1, unidad_precio='total')
        Condiciones.objects.create(nombre='Venta general', modalidad=venta, por_defecto=True)

    def test_reference_index_range_validated(self):
        self.inm.indice_referencia_min = '2000'
        with self.assertRaises(ValidationError):
            self.inm.clean()

    def test_reservation_request(self):
        from base.models import SolicitudReserva
        url = f'/api/inmuebles/{self.inm._id}/reservas/'
        body = {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600000000',
                'fecha_desde': '2026-11-23', 'acepta_aviso_legal': True}
        self.assertEqual(self.client.post(url, body).status_code, 201)
        req = SolicitudReserva.objects.get()
        self.assertEqual((req.referencia, req.inmueble_id), ('G767', self.inm._id))
        self.assertEqual(self.client.post(url, {**body, 'acepta_aviso_legal': False}).status_code, 400)
        self.assertEqual(self.client.post(url, {**body, 'email': 'x'}).status_code, 400)
        self.assertEqual(self.client.post('/api/inmuebles/999/reservas/', body).status_code, 404)
        self.inm.publicar_web = False
        self.inm.save()
        self.assertEqual(self.client.post(url, body).status_code, 404)
        self.assertEqual(SolicitudReserva.objects.count(), 1)


class PublicFieldsTests(TestCase):
    def test_every_column_is_classified_public_or_private(self):
        from base.serializers import (
            INMUEBLE_NESTED_FIELDS, INMUEBLE_PRIVATE_FIELDS, INMUEBLE_PUBLIC_FIELDS,
        )
        relations = {'municipio', 'distrito', 'barrio', 'modalidades', 'propietarios'}
        columns = {f.name for f in Inmueble._meta.get_fields() if f.concrete} - relations
        self.assertEqual(
            columns,
            set(INMUEBLE_PUBLIC_FIELDS) | set(INMUEBLE_PRIVATE_FIELDS),
            'Classify every new Inmueble column as public or private in serializers.py',
        )
        self.assertFalse(set(INMUEBLE_PUBLIC_FIELDS) & set(INMUEBLE_PRIVATE_FIELDS))
        self.assertFalse(set(INMUEBLE_NESTED_FIELDS) & set(INMUEBLE_PRIVATE_FIELDS))

    def test_private_fields_never_in_detail_response(self):
        from base.serializers import INMUEBLE_PRIVATE_FIELDS
        from base.models import DatosInternos, InmueblePropietario, Propietario
        from base.models import PlazaAparcamiento
        inm = inmueble(referencia='P1', publicar_web=True)
        PlazaAparcamiento.objects.create(inmueble=inm, valor='12345.67', renta='89.01')
        InmueblePropietario.objects.create(
            inmueble=inm, propietario=Propietario.objects.create(nombre='SECRETO', nif='SECRETO-NIF'))
        DatosInternos.objects.create(inmueble=inm, notas_internas='n', cat_nrc='c')
        response = self.client.get(f'/api/inmuebles/{inm._id}/')
        data = response.json()
        self.assertEqual([k for k in INMUEBLE_PRIVATE_FIELDS if k in data], [])
        self.assertNotIn('datos_internos', data)
        self.assertNotIn('SECRETO', response.content.decode())
        self.assertNotIn('propietarios', data)
        self.assertNotIn('12345.67', response.content.decode())
        self.assertNotIn('89.01', response.content.decode())


class ListQueryTests(TestCase):
    def make(self, n):
        from base.models import Banios, Dormitorios, Estancias, ImageInmueble, Otros
        prov = Provincia.objects.get_or_create(codigo_ine='08', nombre='Barcelona')[0]
        mun = Municipio.objects.get_or_create(provincia=prov, codigo_ine='08019', nombre='Barcelona')[0]
        dis = Distrito.objects.get_or_create(municipio=mun, codigo='01', nombre='Ciutat Vella')[0]
        for i in range(n):
            inm = inmueble(
                referencia=f'L{Inmueble.objects.count()}', publicar_web=True,
                municipio=mun, distrito=dis)
            inm.modalidades.add(Modalidad.objects.get_or_create(codigo='temporal', defaults={'nombre': 'Vivienda temporal'})[0],
                                through_defaults={'precio': 800})
            for model in (Banios, Dormitorios, Estancias, Otros):
                model.objects.create(inmueble=inm)
            ImageInmueble.objects.create(inmueble=inm, image='x.jpg')

    def count_queries(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(ctx)

    def test_list_query_count_does_not_grow_with_page_size(self):
        url = '/api/inmuebles/modalidad/temporales/'
        self.make(1)
        one = self.count_queries(url)
        self.make(4)
        five = self.count_queries(url)
        self.assertEqual(one, five)
        self.assertLessEqual(five, 5)


class SingleSourceTests(TestCase):
    def test_equipment_columns_live_only_in_detail_tables(self):
        columns = {f.name for f in Inmueble._meta.get_fields() if f.concrete}
        for dropped in ('ascensor', 'calefaccion', 'aire', 'piscina', 'parking',
                        'n_banios', 'max_personas', 'estancia_min', 'estancia_max',
                        'gtos_com_incluido'):
            self.assertNotIn(dropped, columns)

    def test_n_banios_comes_from_banios(self):
        from base.models import Banios
        inm = inmueble(referencia='S1', publicar_web=True)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_banios'], 0)
        Banios.objects.create(inmueble=inm, banios=2)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_banios'], 2)
        listed = self.client.get('/api/inmuebles/').json()['inmuebles'][0]
        self.assertEqual(listed['n_banios'], 2)


class ModalidadFixture(TestCase):
    def setUp(self):
        units = {'temporal': 'mensual', 'habitual': 'mensual', 'venta': 'total'}
        self.mod = {c: Modalidad.objects.create(codigo=c, nombre=n, orden=i, unidad_precio=units[c])
                    for i, (c, n) in enumerate(
            [('temporal', 'Vivienda temporal'), ('habitual', 'Vivienda habitual'),
             ('venta', 'Venta')])}
        prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        mun = Municipio.objects.create(provincia=prov, codigo_ine='08019', nombre='Barcelona')
        self.dis = Distrito.objects.create(municipio=mun, codigo='01', nombre='Ciutat Vella')
        self.both = inmueble(referencia='M1', publicar_web=True, distrito=self.dis)
        self.price(self.both, temporal=1200, venta=300000)
        self.rent = inmueble(referencia='M2', publicar_web=True, distrito=self.dis)
        self.price(self.rent, habitual=900)
        self.hidden = inmueble(referencia='M3', publicar_web=False, distrito=self.dis)
        self.price(self.hidden, temporal=500)

    def price(self, inmueble, **precios):
        for codigo, precio in precios.items():
            InmuebleModalidad.objects.create(
                inmueble=inmueble, modalidad=self.mod[codigo], precio=precio)

    def refs(self, url):
        return sorted(i['referencia'] for i in self.client.get(url).json()['inmuebles'])


class ModalidadTests(ModalidadFixture):

    def test_unique_code(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Modalidad.objects.create(codigo='venta', nombre='Otra')

    def test_listing_can_have_several_modalidades(self):
        self.assertEqual(self.both.modalidades.count(), 2)

    def test_filters_by_modalidad_and_hide_unpublished(self):
        self.assertEqual(self.refs('/api/inmuebles/modalidad/temporales/'), ['M1'])
        self.assertEqual(self.refs('/api/inmuebles/modalidad/habituales/'), ['M2'])
        self.assertEqual(self.refs('/api/inmuebles/modalidad/ventas/'), ['M1'])
        self.assertEqual(self.refs('/api/inmuebles/'), ['M1', 'M2'])

    def test_counts(self):
        url = f'/api/inmuebles/modalidad/%s/distrito/{self.dis._id}/count/'
        self.assertEqual(self.client.get(url % 'temporales').json()['count'], 1)
        self.assertEqual(self.client.get(url % 'ventas').json()['count'], 1)
        self.assertEqual(self.client.get(url % 'otros').status_code, 400)

    def test_api_shape(self):
        data = self.client.get(f'/api/inmuebles/{self.both._id}/').json()
        self.assertEqual([m['codigo'] for m in data['modalidades']], ['temporal', 'venta'])
        self.assertTrue(data['es_venta'])
        self.assertNotIn('es_temporal', data)
        listed = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertTrue(listed['M1']['es_venta'])
        self.assertFalse(listed['M2']['es_venta'])
        self.assertEqual([m['codigo'] for m in self.client.get('/api/modalidades/').json()],
                         ['temporal', 'habitual', 'venta'])


class ImageInmuebleTests(TestCase):
    def setUp(self):
        from base.models import ImageInmueble
        self.Image = ImageInmueble
        self.inm = inmueble(referencia='I1', publicar_web=True)

    def test_only_one_default_photo_per_listing(self):
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', default=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Image.objects.create(inmueble=self.inm, image='b.jpg', default=True)
        other = inmueble(referencia='I2')
        self.Image.objects.create(inmueble=other, image='c.jpg', default=True)
        self.Image.objects.create(inmueble=self.inm, image='d.jpg')

    def test_listing_is_required(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Image.objects.create(image='a.jpg')

    def test_position_orders_photos_and_api_exposes_alt_text(self):
        self.Image.objects.create(inmueble=self.inm, image='b.jpg', posicion=2, alt_text='Salón')
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', posicion=1, alt_text='Cocina')
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual([i['alt_text'] for i in data['images']], ['Cocina', 'Salón'])
        self.assertEqual([i['posicion'] for i in data['images']], [1, 2])

    def test_upload_path_uses_listing_id(self):
        from base.models.image_inmueble import content_file_name
        image = self.Image(inmueble=self.inm)
        self.assertEqual(content_file_name(image, 'x.jpg'), f'{self.inm._id}/x.jpg')


class AuditTests(TestCase):
    def test_admin_save_records_who_created_and_updated(self):
        from django.contrib.auth.models import User
        creator = User.objects.create_superuser('creator', 'c@example.com', 'x')
        editor = User.objects.create_superuser('editor', 'e@example.com', 'x')
        from django.contrib import admin
        from django.test import RequestFactory
        model_admin = admin.site._registry[Inmueble]
        request = RequestFactory().post('/')
        request.user = creator
        inm = Inmueble(referencia='A1', municipio=default_municipio())
        model_admin.save_model(request, inm, form=None, change=False)
        request.user = editor
        model_admin.save_model(request, inm, form=None, change=True)
        inm.refresh_from_db()
        self.assertEqual(inm.created_by, creator)
        self.assertEqual(inm.updated_by, editor)

    def test_audit_columns_never_in_detail_response(self):
        inm = inmueble(referencia='A2', publicar_web=True)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertNotIn('created_by', data)
        self.assertNotIn('updated_by', data)


class HistorialPrecioAutomaticoTests(ModalidadFixture):
    def setUp(self):
        super().setUp()
        from base.models import HistorialPrecio
        self.Historial = HistorialPrecio
        self.inm = inmueble(referencia='HA1', publicar_web=True)

    def filas(self, modalidad='temporal'):
        return [(r.fecha, str(r.importe)) for r in
                self.Historial.objects.filter(inmueble=self.inm, modalidad=self.mod[modalidad])]

    def oferta(self, precio='1000', modalidad='temporal'):
        return InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod[modalidad], precio=precio)

    def test_new_price_is_recorded_today(self):
        from django.utils import timezone
        self.oferta('1000')
        self.assertEqual(self.filas(), [(timezone.localdate(), '1000.00')])

    def test_changed_price_replaces_todays_row_and_keeps_older_ones(self):
        from datetime import date, timedelta
        from django.utils import timezone
        hoy = timezone.localdate()
        oferta = self.oferta('1000')
        self.Historial.objects.filter(inmueble=self.inm).update(fecha=date(2024, 1, 1))
        oferta.precio = '1100'
        oferta.save()
        oferta.precio = '1150'
        oferta.save()
        self.assertEqual(self.filas(), [(hoy, '1150.00'), (date(2024, 1, 1), '1000.00')])

    def test_saving_without_changing_the_price_adds_nothing(self):
        oferta = self.oferta('1000')
        oferta.precio = '1000.00'
        oferta.mas_iva, oferta.tipo_iva = True, 21
        oferta.save()
        oferta.save(update_fields=['mas_iva'])
        self.assertEqual(len(self.filas()), 1)

    def test_latest_row_always_equals_the_current_price(self):
        oferta = self.oferta('1000')
        for precio in ('1200', '900', '1300'):
            oferta.precio = precio
            oferta.save()
            self.assertEqual(self.filas()[0][1], f'{precio}.00')
            self.assertEqual(self.filas()[0][1], str(InmuebleModalidad.objects.get(pk=oferta.pk).precio))

    def test_each_modalidad_has_its_own_history(self):
        self.oferta('1000', 'temporal')
        self.oferta('250000', 'venta')
        self.assertEqual([i for _, i in self.filas('temporal')], ['1000.00'])
        self.assertEqual([i for _, i in self.filas('venta')], ['250000.00'])


class UltimaRentaTests(ModalidadFixture):
    def setUp(self):
        super().setUp()
        from datetime import date
        from base.models import HistorialPrecio
        self.Historial = HistorialPrecio
        self.date = date
        self.inm = inmueble(referencia='UR1', publicar_web=True)

    def ultima(self, codigo='temporal'):
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        return {m['codigo']: m['ultima_renta'] for m in data['modalidades']}[codigo]

    def alta(self, historial=(), modalidad='temporal', precio='1000'):
        for fecha, importe in historial:
            self.Historial.objects.create(
                inmueble=self.inm, modalidad=self.mod[modalidad], fecha=fecha, importe=importe)
        return InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod[modalidad], precio=precio)

    def test_none_without_a_previous_price(self):
        self.alta()
        self.assertIsNone(self.ultima())

    def test_is_the_price_before_the_current_one(self):
        self.alta([(self.date(2023, 1, 1), '800'), (self.date(2024, 1, 1), '900')], precio='1000')
        self.assertEqual(self.ultima(), '900.00')

    def test_follows_a_price_change(self):
        oferta = self.alta([(self.date(2024, 1, 1), '900')], precio='1000')
        # A correction on the same day replaces the day's price; a change on a later day keeps it.
        oferta.precio = '1050'
        oferta.save()
        self.assertEqual(self.ultima(), '900.00')
        self.Historial.objects.filter(importe='1050').update(fecha=self.date(2025, 1, 1))
        oferta.precio = '1100'
        oferta.save()
        self.assertEqual(self.ultima(), '1050.00')

    def test_is_per_modalidad(self):
        self.alta([(self.date(2024, 1, 1), '900')], 'temporal', '1000')
        self.alta([(self.date(2024, 1, 1), '700')], 'habitual', '750')
        self.assertEqual((self.ultima('temporal'), self.ultima('habitual')), ('900.00', '700.00'))

    def test_sale_offers_have_none_even_with_history(self):
        self.alta([(self.date(2024, 1, 1), '200000')], 'venta', '250000')
        self.assertIsNone(self.ultima('venta'))

    def test_future_dated_prices_are_ignored(self):
        self.alta([(self.date(2024, 1, 1), '900'), (self.date(2999, 1, 1), '5000')], precio='1000')
        self.assertEqual(self.ultima(), '900.00')

    def test_listing_has_no_such_column_and_detail_does_not_leak_history(self):
        self.assertNotIn('ultima_renta', {f.name for f in Inmueble._meta.get_fields()})
        self.alta([(self.date(2023, 1, 1), '800'), (self.date(2024, 1, 1), '900')])
        body = self.client.get(f'/api/inmuebles/{self.inm._id}/').content.decode()
        self.assertNotIn('800', body)
        self.assertNotIn('historial', body)

    def test_reads_history_in_a_constant_number_of_queries(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        self.alta([(self.date(2024, 1, 1), '900')])
        with CaptureQueriesContext(connection) as pocas:
            self.client.get(f'/api/inmuebles/{self.inm._id}/')
        for year in range(2010, 2020):
            self.Historial.objects.create(
                inmueble=self.inm, modalidad=self.mod['temporal'], fecha=self.date(year, 1, 1), importe='500')
        self.alta([(self.date(2024, 1, 1), '600')], 'habitual', '650')
        with CaptureQueriesContext(connection) as muchas:
            self.client.get(f'/api/inmuebles/{self.inm._id}/')
        self.assertEqual(len(pocas), len(muchas))


class HistorialPrecioTests(ModalidadFixture):
    def test_history_is_newest_first_and_private(self):
        from datetime import date
        from base.models import HistorialPrecio
        temporal = self.mod['temporal']
        HistorialPrecio.objects.create(inmueble=self.both, modalidad=temporal, fecha=date(2023, 1, 1), importe='900')
        HistorialPrecio.objects.create(inmueble=self.both, modalidad=temporal, fecha=date(2024, 1, 1), importe='950')
        # The first entry is the current price, recorded automatically when the offer was created.
        self.assertEqual(
            [str(r.importe) for r in self.both.historial_precios.filter(modalidad=temporal)],
            ['1200.00', '950.00', '900.00'])
        data = self.client.get(f'/api/inmuebles/{self.both._id}/').json()
        self.assertNotIn('historial_precios', data)
        # Only the previous rent is derived from it; older prices never reach the API.
        self.assertEqual(data['modalidades'][0]['ultima_renta'], '950.00')
        self.assertNotIn('900', str(data['modalidades']))
        self.assertNotIn('fecha', str(data['modalidades']))

    def test_one_entry_per_modalidad_and_date_and_no_negative_price(self):
        from datetime import date
        from base.models import HistorialPrecio
        temporal, venta = self.mod['temporal'], self.mod['venta']
        HistorialPrecio.objects.create(inmueble=self.both, modalidad=temporal, fecha=date(2023, 1, 1), importe='900')
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistorialPrecio.objects.create(inmueble=self.both, modalidad=temporal, fecha=date(2023, 1, 1), importe='950')
        # The same date is fine for another modalidad (sale price history).
        HistorialPrecio.objects.create(inmueble=self.both, modalidad=venta, fecha=date(2023, 1, 1), importe='310000')
        with self.assertRaises(ValidationError):
            HistorialPrecio(inmueble=self.both, modalidad=temporal, fecha=date(2022, 1, 1), importe='-1').full_clean()

    def test_modalidad_with_history_cannot_be_deleted(self):
        from datetime import date
        from base.models import HistorialPrecio
        HistorialPrecio.objects.create(
            inmueble=self.both, modalidad=self.mod['venta'], fecha=date(2023, 1, 1), importe='1')
        self.mod['venta'].precios.all().delete()
        with self.assertRaises(ProtectedError):
            self.mod['venta'].delete()


class PropietarioTests(TestCase):
    def setUp(self):
        from base.models import InmueblePropietario, Propietario
        self.Link = InmueblePropietario
        self.Propietario = Propietario

    def test_owner_exists_without_any_listing(self):
        owner = self.Propietario.objects.create(nombre='Ana', email='ana@example.com')
        self.assertEqual(owner.inmuebles.count(), 0)
        self.assertFalse(owner.gran_tenedor)

    def test_listing_has_many_owners_and_owner_has_many_listings(self):
        ana = self.Propietario.objects.create(nombre='Ana')
        luis = self.Propietario.objects.create(nombre='Luis')
        uno, dos = inmueble(referencia='PR1'), inmueble(referencia='PR2')
        self.Link.objects.create(inmueble=uno, propietario=ana, porcentaje='60')
        self.Link.objects.create(inmueble=uno, propietario=luis, porcentaje='40')
        self.Link.objects.create(inmueble=dos, propietario=ana)
        self.assertEqual(set(uno.propietarios.all()), {ana, luis})
        self.assertEqual(set(ana.inmuebles.all()), {uno, dos})

    def test_owner_with_listings_is_protected_and_links_go_with_the_listing(self):
        ana = self.Propietario.objects.create(nombre='Ana')
        inm = inmueble(referencia='PR3')
        self.Link.objects.create(inmueble=inm, propietario=ana)
        with self.assertRaises(ProtectedError):
            ana.delete()
        inm.delete()
        self.assertEqual(self.Link.objects.count(), 0)
        ana.delete()

    def test_same_owner_once_per_listing(self):
        ana = self.Propietario.objects.create(nombre='Ana')
        inm = inmueble(referencia='PR4')
        self.Link.objects.create(inmueble=inm, propietario=ana)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Link.objects.create(inmueble=inm, propietario=ana)

    def test_share_is_optional_and_between_0_exclusive_and_100(self):
        ana = self.Propietario.objects.create(nombre='Ana')
        inm = inmueble(referencia='PR5')
        self.Link.objects.create(inmueble=inm, propietario=ana, porcentaje=None)
        for bad in ('0', '100.01', '-5'):
            link = self.Link(inmueble=inmueble(referencia=f'PR5{bad}'), propietario=ana, porcentaje=bad)
            with self.assertRaises(ValidationError):
                link.full_clean()
            with self.assertRaises(IntegrityError), transaction.atomic():
                link.save()
        self.Link.objects.create(inmueble=inmueble(referencia='PR6'), propietario=ana, porcentaje='100')

    def test_large_holder_is_set_on_the_owner_and_shows_in_the_listing(self):
        inm = inmueble(referencia='PR7', publicar_web=True)
        url = f'/api/inmuebles/{inm._id}/'
        self.assertIs(self.client.get(url).json()['gran_tenedor'], False)
        ana = self.Propietario.objects.create(nombre='Ana')
        self.Link.objects.create(inmueble=inm, propietario=ana)
        self.assertIs(self.client.get(url).json()['gran_tenedor'], False)
        empresa = self.Propietario.objects.create(nombre='Empresa SL', gran_tenedor=True)
        self.Link.objects.create(inmueble=inm, propietario=empresa)
        self.assertIs(self.client.get(url).json()['gran_tenedor'], True)
        otro = inmueble(referencia='PR8', publicar_web=True)
        self.Link.objects.create(inmueble=otro, propietario=ana)
        self.assertIs(self.client.get(f'/api/inmuebles/{otro._id}/').json()['gran_tenedor'], False)

    def test_detail_reads_owners_in_one_query(self):
        inm = inmueble(referencia='PR9', publicar_web=True)
        for n in range(3):
            self.Link.objects.create(
                inmueble=inm, propietario=self.Propietario.objects.create(nombre=f'P{n}'))
        with CaptureQueriesContext(connection) as sin:
            self.client.get(f'/api/inmuebles/{inm._id}/')
        for n in range(3, 6):
            self.Link.objects.create(
                inmueble=inm, propietario=self.Propietario.objects.create(nombre=f'P{n}'))
        with CaptureQueriesContext(connection) as con:
            self.client.get(f'/api/inmuebles/{inm._id}/')
        self.assertEqual(len(sin), len(con))


class ZonaTensionadaTests(TestCase):
    def setUp(self):
        from base.models import DeclaracionZonaTensionada
        self.Declaracion = DeclaracionZonaTensionada
        self.mun = default_municipio()
        self.otro = Municipio.objects.create(
            provincia=self.mun.provincia, codigo_ine='08020', nombre='Badalona')

    def fresh(self, mun):
        return Municipio.objects.get(pk=mun.pk)

    def test_in_force_between_the_dates_and_open_ended_when_no_end(self):
        self.Declaracion.objects.create(
            municipio=self.mun, desde=date(2024, 3, 14), hasta=date(2025, 3, 13))
        m = self.fresh(self.mun)
        self.assertFalse(m.es_zona_tensionada(date(2024, 3, 13)))
        self.assertTrue(m.es_zona_tensionada(date(2024, 3, 14)))
        self.assertTrue(m.es_zona_tensionada(date(2025, 3, 13)))
        self.assertFalse(m.es_zona_tensionada(date(2025, 3, 14)))
        self.Declaracion.objects.create(municipio=self.mun, desde=date(2026, 1, 1))
        m = self.fresh(self.mun)
        self.assertTrue(m.es_zona_tensionada(date(2099, 1, 1)))

    def test_listing_follows_its_municipality_and_today(self):
        inm = inmueble(referencia='Z1', publicar_web=True)
        otro = inmueble(referencia='Z2', municipio=self.otro, publicar_web=True)
        url = lambda i: f'/api/inmuebles/{i._id}/'
        self.assertIs(self.client.get(url(inm)).json()['zona_tensionada'], False)
        self.Declaracion.objects.create(municipio=self.mun, desde=date(2000, 1, 1))
        self.assertIs(self.client.get(url(inm)).json()['zona_tensionada'], True)
        self.assertIs(self.client.get(url(otro)).json()['zona_tensionada'], False)

    def test_ended_declaration_no_longer_applies(self):
        self.Declaracion.objects.create(
            municipio=self.mun, desde=date(2000, 1, 1), hasta=date(2001, 1, 1))
        inm = inmueble(referencia='Z3', publicar_web=True)
        self.assertIs(self.client.get(f'/api/inmuebles/{inm._id}/').json()['zona_tensionada'], False)

    def test_end_before_start_is_rejected_and_start_is_unique_per_municipality(self):
        mala = self.Declaracion(municipio=self.mun, desde=date(2024, 1, 2), hasta=date(2024, 1, 1))
        with self.assertRaises(ValidationError):
            mala.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            mala.save()
        self.Declaracion.objects.create(municipio=self.mun, desde=date(2024, 1, 1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Declaracion.objects.create(municipio=self.mun, desde=date(2024, 1, 1))

    def test_municipality_with_declarations_is_protected(self):
        self.Declaracion.objects.create(municipio=self.otro, desde=date(2024, 1, 1))
        with self.assertRaises(ProtectedError):
            self.otro.delete()

    def test_detail_reads_declarations_in_a_constant_number_of_queries(self):
        inm = inmueble(referencia='Z4', publicar_web=True)
        self.Declaracion.objects.create(municipio=self.mun, desde=date(2000, 1, 1), hasta=date(2001, 1, 1))
        with CaptureQueriesContext(connection) as pocas:
            self.client.get(f'/api/inmuebles/{inm._id}/')
        for year in range(2002, 2008):
            self.Declaracion.objects.create(
                municipio=self.mun, desde=date(year, 1, 1), hasta=date(year, 6, 1))
        with CaptureQueriesContext(connection) as muchas:
            self.client.get(f'/api/inmuebles/{inm._id}/')
        self.assertEqual(len(pocas), len(muchas))


class EstadoPorOfertaTests(TestCase):
    def setUp(self):
        self.temporal = Modalidad.objects.create(codigo='temporal', nombre='Temporal', orden=1)
        self.venta = Modalidad.objects.create(
            codigo='venta', nombre='Venta', orden=2, unidad_precio=Modalidad.TOTAL)

    def listing(self, ref, **estados):
        """A published listing with one offer per keyword (`temporal`, `venta`) in that state."""
        inm = inmueble(referencia=ref, publicar_web=True)
        for codigo, estado in estados.items():
            InmuebleModalidad.objects.create(
                inmueble=inm, modalidad=getattr(self, codigo), precio='100', estado=estado)
        return inm

    def estado(self, inm):
        return self.client.get(f'/api/inmuebles/{inm._id}/').json()['estado']

    def test_offer_defaults_to_available(self):
        inm = self.listing('E0', temporal='disponible')
        self.assertEqual(inm.precios.get().estado, 'disponible')
        self.assertEqual(InmuebleModalidad.objects.create(
            inmueble=inmueble(referencia='E0b'), modalidad=self.venta, precio='1').estado, 'disponible')

    def test_offer_state_is_validated(self):
        inm = inmueble(referencia='E1')
        with self.assertRaises(ValidationError):
            InmuebleModalidad(
                inmueble=inm, modalidad=self.venta, precio='1', estado='alquilado'
            ).full_clean()

    def test_rented_but_still_for_sale_stays_available(self):
        inm = self.listing('E2', temporal='cerrado', venta='disponible')
        self.assertEqual(self.estado(inm), 'Disponible')

    def test_reserved_when_none_available_and_one_reserved(self):
        inm = self.listing('E3', temporal='cerrado', venta='reservado')
        self.assertEqual(self.estado(inm), 'Reservado')

    def test_closed_is_rented_if_a_monthly_offer_else_sold(self):
        self.assertEqual(self.estado(self.listing('E4', temporal='cerrado')), 'Alquilado')
        self.assertEqual(self.estado(self.listing('E5', temporal='cerrado', venta='cerrado')), 'Alquilado')
        self.assertEqual(self.estado(self.listing('E6', venta='cerrado')), 'Vendido')

    def test_listing_without_offers_is_available(self):
        self.assertEqual(self.estado(self.listing('E7')), 'Disponible')

    def test_listing_column_is_gone(self):
        self.assertNotIn('estado', {f.name for f in Inmueble._meta.get_fields()})

    def test_list_returns_the_derived_state(self):
        self.listing('E8', temporal='cerrado', venta='reservado')
        items = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual(items['E8']['estado'], 'Reservado')

    def test_list_orders_available_then_reserved_then_closed(self):
        self.listing('Z-cerrado', temporal='cerrado')
        self.listing('Y-reservado', venta='reservado')
        self.listing('X-parcial', temporal='cerrado', venta='disponible')
        self.listing('W-sin-ofertas')
        refs = [i['referencia'] for i in self.client.get('/api/inmuebles/').json()['inmuebles']]
        self.assertEqual(refs[-2:], ['Y-reservado', 'Z-cerrado'])
        self.assertEqual(set(refs[:2]), {'X-parcial', 'W-sin-ofertas'})

    def test_state_does_not_add_queries_per_listing(self):
        self.listing('Q1', temporal='cerrado', venta='disponible')
        with CaptureQueriesContext(connection) as pocas:
            self.client.get('/api/inmuebles/')
        for n in range(5):
            self.listing(f'Q-{n}', temporal='cerrado', venta='reservado')
        with CaptureQueriesContext(connection) as muchas:
            self.client.get('/api/inmuebles/')
        self.assertEqual(len(pocas), len(muchas))


class DatosInternosTests(TestCase):
    def test_one_internal_record_per_listing_and_deleted_with_it(self):
        from base.models import DatosInternos
        inm = inmueble(referencia='D3')
        DatosInternos.objects.create(inmueble=inm, notas_internas='llaves en recepción')
        with self.assertRaises(IntegrityError), transaction.atomic():
            DatosInternos.objects.create(inmueble=inm)
        inm.delete()
        self.assertEqual(DatosInternos.objects.count(), 0)


class DatosInternosServicioTests(TestCase):
    def setUp(self):
        from base.models import DatosInternos
        self.Datos = DatosInternos
        self.inm = inmueble(referencia='DS1', publicar_web=True)

    def test_service_flags_are_independent_and_default_to_no(self):
        datos = self.Datos.objects.create(inmueble=self.inm)
        self.assertEqual(
            (datos.exclusiva, datos.gestion_comercial, datos.administracion, datos.tasacion_propietario),
            (False, False, False, None))
        datos = self.Datos.objects.get()
        datos.gestion_comercial = True
        datos.save()
        datos.refresh_from_db()
        self.assertEqual((datos.gestion_comercial, datos.administracion, datos.exclusiva), (True, False, False))

    def test_owner_valuation_cannot_be_negative(self):
        datos = self.Datos(inmueble=self.inm, tasacion_propietario='-1')
        with self.assertRaises(ValidationError):
            datos.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            datos.save()
        self.Datos.objects.create(inmueble=self.inm, tasacion_propietario='1200')

    def test_none_of_it_reaches_the_public_api(self):
        self.Datos.objects.create(
            inmueble=self.inm, exclusiva=True, gestion_comercial=True, administracion=True,
            tasacion_propietario='123456.78')
        for url in (f'/api/inmuebles/{self.inm._id}/', '/api/inmuebles/'):
            body = self.client.get(url).content.decode()
            for secret in ('123456.78', 'tasacion', 'exclusiva', 'gestion_comercial', 'administracion'):
                self.assertNotIn(secret, body, (url, secret))


class PrecioModalidadTests(ModalidadFixture):
    """Price per modalidad: required, unique, non-negative, unit set by the modalidad."""

    def test_price_is_required(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InmuebleModalidad.objects.create(inmueble=self.rent, modalidad=self.mod['venta'])

    def test_one_price_per_modalidad(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InmuebleModalidad.objects.create(
                inmueble=self.rent, modalidad=self.mod['habitual'], precio=1000)

    def test_price_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InmuebleModalidad.objects.create(
                inmueble=self.rent, modalidad=self.mod['venta'], precio=-1)
        with self.assertRaises(ValidationError):
            InmuebleModalidad(
                inmueble=self.rent, modalidad=self.mod['venta'], precio=-1).full_clean()

    def test_modalidad_in_use_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.mod['venta'].delete()
        self.assertTrue(InmuebleModalidad.objects.filter(modalidad=self.mod['venta']).exists())

    def test_unused_modalidad_can_be_deleted_and_listing_deletes_its_prices(self):
        from base.models import HistorialPrecio
        InmuebleModalidad.objects.filter(modalidad=self.mod['habitual']).delete()
        # Its price history still refers to it, so it is not unused until that is gone too.
        with self.assertRaises(ProtectedError):
            self.mod['habitual'].delete()
        HistorialPrecio.objects.filter(modalidad=self.mod['habitual']).delete()
        self.mod['habitual'].delete()
        self.both.delete()
        self.assertFalse(InmuebleModalidad.objects.filter(inmueble_id=self.both._id).exists())

    def test_unit_is_set_per_modalidad(self):
        data = {m['codigo']: m['unidad_precio'] for m in self.client.get('/api/modalidades/').json()}
        self.assertEqual(data, {'temporal': 'mensual', 'habitual': 'mensual', 'venta': 'total'})

    def test_api_returns_price_and_unit_per_modalidad(self):
        data = self.client.get(f'/api/inmuebles/{self.both._id}/').json()
        self.assertEqual(data['modalidades'], [
            {'codigo': 'temporal', 'nombre': 'Vivienda temporal', 'unidad_precio': 'mensual',
             'precio': '1200.00', 'mas_iva': False, 'tipo_iva': None, 'ultima_renta': None,
             'condiciones': None},
            {'codigo': 'venta', 'nombre': 'Venta', 'unidad_precio': 'total',
             'precio': '300000.00', 'mas_iva': False, 'tipo_iva': None, 'ultima_renta': None,
             'condiciones': None},
        ])
        self.assertEqual((data['importe_alquiler'], data['importe_venta']), ('1200.00', '300000.00'))
        listed = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual((listed['M2']['importe_alquiler'], listed['M2']['importe_venta']), ('900.00', None))

    def test_max_precio_compares_that_modalidads_price(self):
        ventas = '/api/inmuebles/modalidad/ventas/?max_precio=%s'
        self.assertEqual(self.refs(ventas % 200000), [])
        self.assertEqual(self.refs(ventas % 400000), ['M1'])
        # M1 rents at 1200: a 2000 limit must not match its 300000 sale price.
        self.assertEqual(self.refs('/api/inmuebles/modalidad/temporales/?max_precio=1000'), [])
        self.assertEqual(self.refs('/api/inmuebles/modalidad/temporales/?max_precio=2000'), ['M1'])

    def test_max_precio_without_modalidad_uses_monthly_prices_once_per_listing(self):
        self.price(self.rent, temporal=700)
        self.assertEqual(self.refs('/api/inmuebles/?max_precio=1000'), ['M2'])
        self.assertEqual(self.refs('/api/inmuebles/?max_precio=5000'), ['M1', 'M2'])
        self.assertEqual(len(self.client.get('/api/inmuebles/?max_precio=5000').json()['inmuebles']), 2)


class PlazaAparcamientoTests(TestCase):
    def setUp(self):
        from base.models import PlazaAparcamiento
        self.Plaza = PlazaAparcamiento
        self.inm = inmueble(referencia='PK1', publicar_web=True)

    def test_parking_columns_are_gone_from_inmueble(self):
        columns = {f.name for f in Inmueble._meta.get_fields() if f.concrete}
        for dropped in ('n_plz_garaje', 'sup_parking', 'valor_plz', 'renta_plz'):
            self.assertNotIn(dropped, columns)

    def test_count_is_computed_from_the_plazas(self):
        url = f'/api/inmuebles/{self.inm._id}/'
        self.assertEqual(self.client.get(url).json()['n_plz_garaje'], 0)
        self.Plaza.objects.create(inmueble=self.inm, numero='12')
        self.Plaza.objects.create(inmueble=self.inm, numero='13', tipo='moto')
        data = self.client.get(url).json()
        self.assertEqual(data['n_plz_garaje'], 2)
        self.assertEqual([p['numero'] for p in data['plazas']], ['12', '13'])

    def test_public_plaza_fields_exclude_value_and_rent(self):
        self.Plaza.objects.create(inmueble=self.inm, numero='1', superficie='11.5', valor='9000', renta='50')
        plaza = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()['plazas'][0]
        self.assertEqual(set(plaza), {
            'id', 'numero', 'tipo', 'superficie', 'notas', 'opcional', 'precio_opcional',
            'precio_opcional_unidad', 'precio_opcional_mas_iva', 'precio_opcional_tipo_iva'})
        self.assertEqual(plaza['superficie'], '11.50')

    def test_number_is_unique_per_listing_when_given(self):
        self.Plaza.objects.create(inmueble=self.inm, numero='7')
        self.Plaza.objects.create(inmueble=self.inm)
        self.Plaza.objects.create(inmueble=self.inm)
        self.Plaza.objects.create(inmueble=inmueble(referencia='PK2'), numero='7')
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Plaza.objects.create(inmueble=self.inm, numero='7')

    def test_amounts_cannot_be_negative_and_plazas_go_with_the_listing(self):
        with self.assertRaises(ValidationError):
            self.Plaza(inmueble=self.inm, valor='-1').full_clean()
        self.Plaza.objects.create(inmueble=self.inm)
        self.inm.delete()
        self.assertEqual(self.Plaza.objects.count(), 0)

    def test_parking_listing_may_have_plazas_too(self):
        parking = inmueble(referencia='PK3', tipo='Parking', publicar_web=True)
        self.Plaza.objects.create(inmueble=parking)
        self.assertEqual(self.client.get(f'/api/inmuebles/{parking._id}/').json()['n_plz_garaje'], 1)


class HabitacionesTests(TestCase):
    def make(self, ref, dobles=None, individuales=0, suites=0, exteriores=0):
        from base.models import Dormitorios
        inm = inmueble(referencia=ref, publicar_web=True)
        if dobles is not None:
            Dormitorios.objects.create(
                inmueble=inm, dobles=dobles, individuales=individuales,
                suites=suites, exteriores=exteriores)
        return inm

    def test_column_is_gone_and_total_is_dobles_individuales(self):
        self.assertNotIn('n_habitaciones', {f.name for f in Inmueble._meta.get_fields() if f.concrete})
        inm = self.make('H1', dobles=2, individuales=1, suites=1, exteriores=3)
        self.assertEqual(Inmueble.objects.get(pk=inm.pk).n_habitaciones, 3)

    def test_suites_are_a_subset_of_the_bedrooms(self):
        from base.models import Dormitorios
        inm = self.make('H9', dobles=2, individuales=1, suites=3)
        Dormitorios.objects.filter(inmueble=inm).update(suites=3)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Dormitorios.objects.filter(inmueble=inm).update(suites=4)

    def test_listing_without_dormitorios_has_zero(self):
        inm = self.make('H2')
        self.assertEqual(Inmueble.objects.get(pk=inm.pk).n_habitaciones, 0)
        self.assertEqual(Inmueble.objects.con_habitaciones().get(pk=inm.pk).n_habitaciones, 0)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_habitaciones'], 0)

    def test_api_returns_the_computed_number_in_list_and_detail(self):
        inm = self.make('H3', dobles=1, individuales=2)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_habitaciones'], 3)
        listed = self.client.get('/api/inmuebles/').json()['inmuebles'][0]
        self.assertEqual(listed['n_habitaciones'], 3)

    def test_filter_matches_the_computed_number_only(self):
        self.make('H4', dobles=2, individuales=1)
        self.make('H5', dobles=2, individuales=1, suites=1, exteriores=5)
        self.make('H6', dobles=1)
        self.make('H7')
        refs = lambda n: sorted(i['referencia'] for i in self.client.get(f'/api/inmuebles/?habitaciones={n}').json()['inmuebles'])
        self.assertEqual(refs(3), ['H4', 'H5'])
        self.assertEqual(refs(1), ['H6'])
        self.assertEqual(len(self.client.get('/api/inmuebles/').json()['inmuebles']), 4)

    def test_changing_dormitorios_changes_the_number(self):
        inm = self.make('H8', dobles=1)
        inm.dormitorios.dobles = 3
        inm.dormitorios.save()
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_habitaciones'], 3)


class TextToNumbersTests(TestCase):
    def test_api_returns_numbers_with_units_in_the_name(self):
        from base.models import Entorno, Otros
        inm = inmueble(referencia='N1', publicar_web=True)
        Otros.objects.create(inmueble=inm, estancia_minima=2, altura_real_m='2.70')
        Entorno.objects.create(inmueble=inm, distancia_playa_m=800)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual((data['otros']['estancia_minima'], data['otros']['altura_real_m']), (2, '2.70'))
        self.assertEqual(data['entorno']['distancia_playa_m'], 800)
        for old in ('estancia_minima_meses', 'altura_real'):
            self.assertNotIn(old, data['otros'])
        self.assertNotIn('distancia_playa', data['entorno'])


class LocationFromLinksTests(TestCase):
    def test_text_columns_are_gone_and_zone_names_come_from_the_links(self):
        columns = {f.name for f in Inmueble._meta.get_fields() if f.concrete}
        for dropped in ('poblacion', 'ubicacion', 'zona', 'zona_ref'):
            self.assertNotIn(dropped, columns)
        prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        mun = Municipio.objects.create(provincia=prov, codigo_ine='08019', nombre='Barcelona')
        dis = Distrito.objects.create(municipio=mun, codigo='01', nombre='Ciutat Vella')
        bar = Barrio.objects.create(distrito=dis, codigo='01', nombre='El Raval')
        with_barrio = inmueble(
            referencia='Z1', publicar_web=True, municipio=mun, distrito=dis, barrio=bar)
        only_district = inmueble(
            referencia='Z2', publicar_web=True, municipio=mun, distrito=dis)
        nowhere = inmueble(referencia='Z3', publicar_web=True)
        zones = lambda i: tuple(self.client.get(f'/api/inmuebles/{i._id}/').json()[k] for k in ('zona', 'zona_ref'))
        self.assertEqual(zones(with_barrio), ('El Raval', 'Ciutat Vella'))
        self.assertEqual(zones(only_district), ('Ciutat Vella', 'Ciutat Vella'))
        self.assertEqual(zones(nowhere), (None, None))
        listed = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual(listed['Z1']['zona'], 'El Raval')


class DatabaseRulesTests(TestCase):
    def test_negative_amounts_are_rejected_by_validators_and_the_database(self):
        for field in ('sup_util', 'sup_construida', 'gtos_comunidad', 'ibi', 'consumo_energetico'):
            with self.assertRaises(ValidationError, msg=field):
                Inmueble(referencia='R', **{field: -1}).full_clean(exclude=['municipio'])
            with self.assertRaises(IntegrityError, msg=field), transaction.atomic():
                inmueble(referencia='R', **{field: -1})

    def test_reference_index_range_is_a_database_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            inmueble(referencia='R1', indice_referencia_min=10, indice_referencia_max=5)
        inmueble(referencia='R2', indice_referencia_min=5)
        inmueble(referencia='R3', indice_referencia_min=5, indice_referencia_max=5)

    def test_counts_cannot_be_negative(self):
        from base.models import Dormitorios, Otros
        inm = inmueble(referencia='R4')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Dormitorios.objects.create(inmueble=inm, dobles=-1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Otros.objects.create(inmueble=inm, capacidad_personas=-2)


class DateAndSurfaceTypesTests(TestCase):
    def test_availability_is_a_date_and_filters_by_date(self):
        from datetime import date
        inmueble(referencia='T1', publicar_web=True, fecha_disponibilidad=date(2025, 3, 1))
        inmueble(referencia='T2', publicar_web=True, fecha_disponibilidad=date(2025, 6, 1))
        data = self.client.get('/api/inmuebles/?fecha_entrada=2025-04-01').json()
        self.assertEqual([i['referencia'] for i in data['inmuebles']], ['T1'])
        self.assertEqual(data['inmuebles'][0]['fecha_disponibilidad'], '2025-03-01')
        for name in ('fecha_disponibilidad', 'fecha_alta', 'fecha_baja', 'fecha_entrega'):
            self.assertEqual(Inmueble._meta.get_field(name).get_internal_type(), 'DateField')

    def test_surfaces_allow_large_premises(self):
        inm = inmueble(referencia='T3', sup_construida='12345.67', sup_util='999999.99')
        inm.refresh_from_db()
        self.assertEqual(str(inm.sup_construida), '12345.67')


class NullableColumnsTests(TestCase):
    def test_text_columns_have_one_empty_state(self):
        from django.apps import apps
        nullable = [
            f'{m.__name__}.{f.name}'
            for m in apps.get_app_config('base').get_models()
            for f in m._meta.get_fields()
            if f.concrete and f.get_internal_type() in ('CharField', 'TextField', 'SlugField') and f.null
        ]
        self.assertEqual(nullable, [])

    def test_optional_columns_are_optional_in_forms_too(self):
        for name in ('sup_construida', 'sup_cont_comun', 'sup_util', 'situacion_actual',
                     'ibi', 'gtos_comunidad', 'geo_latitude', 'geo_longitude'):
            field = Inmueble._meta.get_field(name)
            self.assertEqual((field.null or field.blank), True, name)
            self.assertTrue(field.blank, name)

    def test_text_cannot_be_null_and_api_returns_empty_strings(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            inmueble(referencia='NN1', titulo=None)
        inm = inmueble(referencia='NN2', publicar_web=True)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual((data['titulo'], data['descripcion_es']), ('', ''))

    def test_boolean_columns_are_never_null(self):
        from django.apps import apps
        nullable = [
            f'{m.__name__}.{f.name}'
            for m in apps.get_app_config('base').get_models()
            for f in m._meta.get_fields()
            if f.concrete and f.get_internal_type() == 'BooleanField' and f.null
        ]
        self.assertEqual(nullable, [])


class SolicitudEstadoTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='SR1', publicar_web=True)

    def post(self):
        return self.client.post(
            f'/api/inmuebles/{self.inm._id}/reservas/',
            {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600', 'acepta_aviso_legal': True},
            content_type='application/json')

    def test_new_request_is_pending_and_estado_cannot_be_set_by_the_client(self):
        from base.models import SolicitudReserva
        response = self.client.post(
            f'/api/inmuebles/{self.inm._id}/reservas/',
            {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600',
             'acepta_aviso_legal': True, 'estado': 'cerrada'},
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SolicitudReserva.objects.get().estado, 'pendiente')
        self.assertNotIn('estado', response.json())

    def test_estado_choices(self):
        from base.models import SolicitudReserva
        self.assertEqual([c for c, _ in SolicitudReserva.ESTADOS],
                         ['pendiente', 'contactada', 'cerrada', 'descartada'])
        self.assertFalse(hasattr(SolicitudReserva, 'atendida'))


class PurgarSolicitudesTests(TestCase):
    def make(self, days_old, **kw):
        from datetime import timedelta
        from django.utils import timezone
        from base.models import SolicitudReserva
        r = SolicitudReserva.objects.create(
            referencia='X', nombre='Ana', email='ana@example.com', telefono='600',
            mensaje='Me llamo Ana y vivo en la calle X', acepta_aviso_legal=True, **kw)
        SolicitudReserva.objects.filter(pk=r.pk).update(created_at=timezone.now() - timedelta(days=days_old))
        return r.pk

    def run_command(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('purgar_solicitudes', *args, stdout=out)
        return out.getvalue()

    def test_blanks_personal_data_after_twelve_months_and_keeps_the_row(self):
        from base.models import SolicitudReserva
        old = self.make(400, estado='cerrada')
        recent = self.make(100)
        self.assertIn('blanked personal data on 1 request', self.run_command())
        old_row = SolicitudReserva.objects.get(pk=old)
        self.assertEqual((old_row.nombre, old_row.email, old_row.telefono), ('', '', ''))
        self.assertIsNotNone(old_row.datos_borrados)
        self.assertEqual(old_row.mensaje, '')
        self.assertEqual((old_row.referencia, old_row.estado), ('X', 'cerrada'))
        self.assertEqual(SolicitudReserva.objects.get(pk=recent).email, 'ana@example.com')

    def test_dry_run_changes_nothing_and_second_run_finds_nothing(self):
        from base.models import SolicitudReserva
        pk = self.make(400)
        self.assertIn('would blank personal data on 1 request', self.run_command('--dry-run'))
        self.assertEqual(SolicitudReserva.objects.get(pk=pk).email, 'ana@example.com')
        self.run_command()
        self.assertIn('on 0 request', self.run_command())

    def test_months_option(self):
        from base.models import SolicitudReserva
        pk = self.make(200)
        self.run_command()
        self.assertEqual(SolicitudReserva.objects.get(pk=pk).email, 'ana@example.com')
        self.run_command('--meses', '6')
        self.assertEqual(SolicitudReserva.objects.get(pk=pk).email, '')


class AdminLocationChoicesTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.mun = default_municipio()
        self.other = Municipio.objects.create(
            provincia=self.mun.provincia, codigo_ine='08101', nombre="l'Hospitalet")
        self.dis = Distrito.objects.create(municipio=self.mun, codigo='01', nombre='Ciutat Vella')
        self.dis2 = Distrito.objects.create(municipio=self.mun, codigo='02', nombre='Eixample')
        self.far = Distrito.objects.create(municipio=self.other, codigo='01', nombre='Centre')
        self.bar = Barrio.objects.create(distrito=self.dis, codigo='01', nombre='El Raval')
        self.bar2 = Barrio.objects.create(distrito=self.dis2, codigo='01', nombre='Dreta')
        self.client.force_login(User.objects.create_superuser('admin', 'a@example.com', 'x'))

    def form(self, **data):
        from base.admin import InmuebleAdminForm
        return InmuebleAdminForm(data={k: v._id for k, v in data.items()})

    def test_choices_follow_the_selected_municipio_and_distrito(self):
        f = self.form(municipio=self.mun)
        self.assertEqual(set(f.fields['distrito'].queryset), {self.dis, self.dis2})
        self.assertEqual(set(f.fields['barrio'].queryset), {self.bar, self.bar2})
        f = self.form(municipio=self.mun, distrito=self.dis)
        self.assertEqual(list(f.fields['barrio'].queryset), [self.bar])
        self.assertEqual(list(InmuebleAdminFormUnbound().fields['distrito'].queryset), [])

    def test_a_distrito_of_another_municipio_is_not_a_valid_choice(self):
        f = self.form(municipio=self.mun, distrito=self.far)
        f.is_valid()
        self.assertIn('distrito', f.errors)

    def test_options_endpoint(self):
        get = lambda **q: self.client.get('/admin/base/inmueble/ubicacion/', q)
        names = lambda r: [i['nombre'] for i in r.json()['items']]
        self.assertEqual(names(get(tipo='distritos', municipio=self.mun._id)), ['Ciutat Vella', 'Eixample'])
        self.assertEqual(names(get(tipo='barrios', municipio=self.mun._id, distrito=self.dis2._id)), ['Dreta'])
        self.assertEqual(names(get(tipo='barrios', municipio=self.mun._id)), ['El Raval', 'Dreta'])
        self.assertEqual(get(tipo='x').status_code, 404)
        self.client.logout()
        self.assertEqual(get(tipo='distritos', municipio=self.mun._id).status_code, 302)

    def test_add_page_loads_the_script(self):
        response = self.client.get('/admin/base/inmueble/add/')
        self.assertContains(response, 'base/admin/ubicacion.js')
        self.assertContains(response, 'data-url="/admin/base/inmueble/ubicacion/"')


def InmuebleAdminFormUnbound():
    from base.admin import InmuebleAdminForm
    return InmuebleAdminForm()


class RegistroLegalTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='R1', publicar_web=True)

    def test_registry_numbers_are_public_and_listed_with_the_listing(self):
        RegistroLegal.objects.create(inmueble=self.inm, tipo='aicat', numero='5205')
        RegistroLegal.objects.create(
            inmueble=self.inm, tipo='cedula_habitabilidad', numero='CHB0333*******',
            organismo='Generalitat de Catalunya')
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(
            [(r['tipo'], r['numero']) for r in data['registros_legales']],
            [('aicat', '5205'), ('cedula_habitabilidad', 'CHB0333*******')],
        )
        self.assertNotIn('cedula', data)

    def test_one_registry_per_type_except_otro(self):
        RegistroLegal.objects.create(inmueble=self.inm, tipo='aicat', numero='1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegistroLegal.objects.create(inmueble=self.inm, tipo='aicat', numero='2')
        RegistroLegal.objects.create(inmueble=self.inm, tipo='otro', numero='a')
        RegistroLegal.objects.create(inmueble=self.inm, tipo='otro', numero='b')
        other = inmueble(referencia='R2')
        RegistroLegal.objects.create(inmueble=other, tipo='aicat', numero='1')

    def test_registries_go_with_the_listing(self):
        RegistroLegal.objects.create(inmueble=self.inm, tipo='aicat', numero='1')
        self.inm.delete()
        self.assertEqual(RegistroLegal.objects.count(), 0)

    def test_emissions_cannot_be_negative(self):
        self.inm.emisiones_co2 = '-1'
        with self.assertRaises(ValidationError):
            self.inm.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inmueble.objects.filter(pk=self.inm.pk).update(emisiones_co2='-1')

    def test_emissions_are_public(self):
        self.inm.emisiones_co2 = '36.00'
        self.inm.save()
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['emisiones_co2'], '36.00')


class OcultarDireccionTests(TestCase):
    def setUp(self):
        self.inm = inmueble(
            referencia='H1', publicar_web=True, direccion='Carrer de la Cera 12',
            direccion_short='Cera 12', dir_descripcion='Piso 3', codigo_postal='08001')

    def test_address_is_returned_by_default(self):
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual((data['direccion'], data['dir_descripcion']), ('Carrer de la Cera 12', 'Piso 3'))
        self.assertFalse(data['ocultar_direccion'])

    def test_hidden_address_is_blank_in_detail_and_list_but_zone_stays(self):
        self.inm.ocultar_direccion = True
        self.inm.save()
        detail = self.client.get(f'/api/inmuebles/{self.inm._id}/')
        data = detail.json()
        for name in ('direccion', 'direccion_short', 'dir_descripcion'):
            self.assertEqual(data[name], '', name)
        self.assertEqual(data['codigo_postal'], '08001')
        self.assertNotIn('Cera', detail.content.decode())
        listing = self.client.get('/api/inmuebles/')
        self.assertNotIn('Cera', listing.content.decode())
        self.assertEqual(listing.json()['inmuebles'][0]['dir_descripcion'], '')


class EstanciaLimitesTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='E1', publicar_web=True)

    def otros(self, **fields):
        from base.models import Otros
        return Otros(inmueble=self.inm, **fields)

    def test_limits_keep_their_unit_and_default_to_months(self):
        from base.models import Otros
        Otros.objects.create(
            inmueble=self.inm, estancia_minima=32, estancia_minima_unidad='dias',
            estancia_maxima=5)
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()['otros']
        self.assertEqual(
            (data['estancia_minima'], data['estancia_minima_unidad'],
             data['estancia_maxima'], data['estancia_maxima_unidad']),
            (32, 'dias', 5, 'meses'))

    def test_minimum_cannot_exceed_maximum_whatever_the_units(self):
        with self.assertRaises(ValidationError):
            self.otros(estancia_minima=2, estancia_minima_unidad='anios',
                       estancia_maxima=18, estancia_maxima_unidad='meses').full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.otros(estancia_minima=2, estancia_minima_unidad='anios',
                       estancia_maxima=18, estancia_maxima_unidad='meses').save()
        # 32 days is below 5 months, and a year equals 12 months.
        self.otros(estancia_minima=32, estancia_minima_unidad='dias', estancia_maxima=5).full_clean(exclude=['inmueble'])
        self.otros(estancia_minima=1, estancia_minima_unidad='anios', estancia_maxima=5, estancia_maxima_unidad='anios').save()

    def test_one_limit_alone_is_fine_and_unit_must_be_known(self):
        self.otros(estancia_minima=6).full_clean(exclude=['inmueble'])
        with self.assertRaises(ValidationError):
            self.otros(estancia_minima=6, estancia_minima_unidad='semanas').full_clean(exclude=['inmueble'])


class EstanciasUnidadesTests(TestCase):
    def test_surfaces_and_counts_are_separate_and_not_negative(self):
        from base.models import Estancias
        inm = inmueble(referencia='U1', publicar_web=True)
        Estancias.objects.create(
            inmueble=inm, salon_m2='22', terraza=2, terraza_m2='11.5', balcones=1, balcones_m2='4',
            carpinteria_interior='Madera', carpinteria_exterior='Aluminio')
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual(data['salon']['salon_m2'], '22.00')
        self.assertEqual((data['terraza']['terraza'], data['terraza']['terraza_m2']), (2, '11.50'))
        self.assertEqual((data['terraza']['balcones'], data['terraza']['balcones_m2']), (1, '4.00'))
        self.assertEqual(
            (data['carpinteria']['carpinteria_interior'], data['carpinteria']['carpinteria_exterior']),
            ('Madera', 'Aluminio'))
        for field in ('salon_m2', 'terraza_m2', 'balcones_m2'):
            with self.assertRaises(IntegrityError, msg=field), transaction.atomic():
                Estancias.objects.filter(inmueble=inm).update(**{field: -1})


class DotacionYOtrosTests(TestCase):
    def test_tableware_and_linen_flags_and_exterior_boolean(self):
        from base.models import Dotacion, Otros
        inm = inmueble(referencia='D1', publicar_web=True)
        Dotacion.objects.create(
            inmueble=inm, vajilla=True, cuberteria=True, cristaleria=True, ropa_cama=True, toallas=True)
        Otros.objects.create(inmueble=inm, exterior=True)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertTrue(all(data['dotacion'][k] for k in ('vajilla', 'cuberteria', 'cristaleria', 'ropa_cama', 'toallas')))
        self.assertIs(data['otros']['exterior'], True)


class IncluidoEnOtrosTests(TestCase):
    def test_included_flags_live_together_in_otros(self):
        from base.models import Otros
        columns = {f.name for f in Inmueble._meta.get_fields() if f.concrete}
        self.assertNotIn('ibi_incluido', columns)
        inm = inmueble(referencia='I1', publicar_web=True, ibi='210', gtos_comunidad='50')
        Otros.objects.create(inmueble=inm, ibi_incluido=True, gastos_comunidad_incluidos=True)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual((data['ibi'], data['gtos_comunidad']), ('210.00', '50.00'))
        self.assertTrue(data['otros']['ibi_incluido'] and data['otros']['gastos_comunidad_incluidos'])


class IvaTests(ModalidadFixture):
    def test_price_without_vat_flag_has_no_rate(self):
        precio = InmuebleModalidad(inmueble=self.rent, modalidad=self.mod['temporal'], precio=450)
        precio.full_clean(exclude=['inmueble'])
        precio.tipo_iva = 21
        with self.assertRaises(ValidationError):
            precio.full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            precio.save()

    def test_price_with_vat_needs_a_rate_between_0_and_100(self):
        precio = InmuebleModalidad(inmueble=self.rent, modalidad=self.mod['temporal'], precio=450, mas_iva=True)
        with self.assertRaises(ValidationError):
            precio.full_clean(exclude=['inmueble'])
        for bad in (-1, 101):
            precio.tipo_iva = bad
            with self.assertRaises(ValidationError):
                precio.full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            InmuebleModalidad.objects.filter(pk=self.both.precios.first().pk).update(mas_iva=True)
        precio.tipo_iva = 21
        precio.save()

    def test_api_returns_vat_per_modalidad(self):
        InmuebleModalidad.objects.create(
            inmueble=self.rent, modalidad=self.mod['temporal'], precio=450, mas_iva=True, tipo_iva='21')
        data = self.client.get(f'/api/inmuebles/{self.rent._id}/').json()
        by_code = {m['codigo']: m for m in data['modalidades']}
        self.assertEqual((by_code['temporal']['mas_iva'], by_code['temporal']['tipo_iva']), (True, '21.00'))
        self.assertEqual((by_code['habitual']['mas_iva'], by_code['habitual']['tipo_iva']), (False, None))
        listed = self.client.get('/api/inmuebles/').json()['inmuebles']
        self.assertIn('mas_iva', listed[0]['modalidades'][0])


class CondicionesPorModalidadTests(ModalidadFixture):
    def setUp(self):
        super().setUp()
        self.alquiler = Condiciones.objects.create(
            nombre='Alquiler', modalidad=self.mod['temporal'], por_defecto=True,
            fianza='2 mensualidades', requisitos='DNI y nóminas')
        self.venta = Condiciones.objects.create(
            nombre='Venta', modalidad=self.mod['venta'], por_defecto=True,
            itp='10 %', notaria='Arancel', registro='Arancel', gestoria='350 € + IVA',
            honorarios_comprador='Ninguno')

    def conditions(self):
        data = self.client.get(f'/api/inmuebles/{self.both._id}/').json()
        return {m['codigo']: m['condiciones'] for m in data['modalidades']}

    def test_each_modalidad_gets_its_own_default(self):
        got = self.conditions()
        self.assertEqual(got['temporal']['fianza'], '2 mensualidades')
        self.assertEqual(got['temporal']['requisitos'], 'DNI y nóminas')
        self.assertEqual((got['venta']['itp'], got['venta']['gestoria']), ('10 %', '350 € + IVA'))
        self.assertNotIn('por_defecto', got['venta'])
        self.assertNotIn('modalidad', got['venta'])

    def test_a_modalidad_without_any_conditions_returns_null(self):
        self.venta.delete()
        self.assertIsNone(self.conditions()['venta'])

    def test_own_conditions_must_belong_to_the_same_modalidad(self):
        precio = self.both.precios.get(modalidad=self.mod['temporal'])
        precio.condiciones = self.venta
        with self.assertRaises(ValidationError):
            precio.full_clean()
        with self.assertRaises(ValidationError):
            precio.save()
        precio.condiciones = Condiciones.objects.create(nombre='Corta', modalidad=self.mod['temporal'])
        precio.save()
        self.assertEqual(self.conditions()['temporal']['nombre'], 'Corta')

    def test_conditions_in_use_or_of_a_modalidad_cannot_be_deleted(self):
        precio = self.both.precios.get(modalidad=self.mod['temporal'])
        precio.condiciones = self.alquiler
        precio.save()
        with self.assertRaises(ProtectedError):
            self.alquiler.delete()
        sin_uso = Modalidad.objects.create(codigo='otra', nombre='Otra', orden=9)
        Condiciones.objects.create(nombre='Otra general', modalidad=sin_uso)
        with self.assertRaises(ProtectedError):
            sin_uso.delete()

    def test_detail_queries_do_not_grow_with_the_modalidades(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def queries(inm):
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(f'/api/inmuebles/{inm._id}/')
            return len(ctx)

        self.assertEqual(queries(self.both), queries(self.rent))  # two modalidades vs one


class PlazaOpcionalTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='O1', publicar_web=True)

    def test_optional_space_price_is_public_but_value_and_rent_stay_private(self):
        from base.models import PlazaAparcamiento
        PlazaAparcamiento.objects.create(
            inmueble=self.inm, opcional=True, precio_opcional='60', precio_opcional_mas_iva=True,
            precio_opcional_tipo_iva='21', valor='9999.99', renta='88.77')
        response = self.client.get(f'/api/inmuebles/{self.inm._id}/')
        plaza = response.json()['plazas'][0]
        self.assertEqual(
            (plaza['opcional'], plaza['precio_opcional'], plaza['precio_opcional_unidad'],
             plaza['precio_opcional_mas_iva'], plaza['precio_opcional_tipo_iva']),
            (True, '60.00', 'mensual', True, '21.00'))
        self.assertNotIn('9999.99', response.content.decode())
        self.assertNotIn('88.77', response.content.decode())

    def test_price_only_when_optional_and_vat_rules(self):
        from base.models import PlazaAparcamiento
        plaza = PlazaAparcamiento(inmueble=self.inm, precio_opcional='60')
        with self.assertRaises(ValidationError):
            plaza.full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            plaza.save()
        plaza.opcional = True
        plaza.full_clean(exclude=['inmueble'])
        plaza.precio_opcional_mas_iva = True
        with self.assertRaises(ValidationError):
            plaza.full_clean(exclude=['inmueble'])
        plaza.precio_opcional_tipo_iva = 21
        plaza.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlazaAparcamiento.objects.filter(pk=plaza.pk).update(precio_opcional='-1')


class CamposVentaTests(ModalidadFixture):
    """The idealista-01 listing: a terraced house for sale."""

    def setUp(self):
        super().setUp()
        from base.models import Entorno
        self.chalet = inmueble(
            referencia='V1', publicar_web=True, tipo='Vivienda', subtipo='chalet_adosado',
            conservacion='buen_estado', anio_construccion=1955, n_plantas=2,
            sup_construida='154', sup_parcela='142', distrito=self.dis)
        self.price(self.chalet, venta=279000)
        Entorno.objects.create(inmueble=self.chalet, jardin=True, jardin_m2='79')

    def test_detail_returns_the_sale_fields(self):
        data = self.client.get(f'/api/inmuebles/{self.chalet._id}/').json()
        self.assertEqual(
            (data['subtipo'], data['conservacion'], data['anio_construccion'], data['n_plantas'],
             data['planta'], data['sup_parcela'], data['entorno']['jardin_m2']),
            ('chalet_adosado', 'buen_estado', 1955, 2, None, '142.00', '79.00'))

    def test_floor_level_of_a_flat_allows_ground_and_basement(self):
        piso = inmueble(referencia='V2', tipo='Vivienda', subtipo='piso', planta=0)
        piso.planta = -1
        piso.save()
        for bad in (-6, 101):
            piso.planta = bad
            with self.assertRaises(ValidationError):
                piso.full_clean(exclude=['municipio'])
            with self.assertRaises(IntegrityError), transaction.atomic():
                Inmueble.objects.filter(pk=piso.pk).update(planta=bad)

    def test_ranges_are_enforced_by_validators_and_the_database(self):
        for field, bad in (('anio_construccion', 999), ('anio_construccion', 2101),
                           ('n_plantas', 0), ('sup_parcela', -1)):
            with self.assertRaises(ValidationError, msg=(field, bad)):
                Inmueble(referencia='X', **{field: bad}).full_clean(exclude=['municipio'])
            with self.assertRaises(IntegrityError, msg=(field, bad)), transaction.atomic():
                Inmueble.objects.filter(pk=self.chalet.pk).update(**{field: bad})

    def test_subtipo_only_for_viviendas_and_must_be_a_known_kind(self):
        oficina = Inmueble(referencia='V3', municipio=self.chalet.municipio, tipo='Oficina', subtipo='piso')
        with self.assertRaises(ValidationError):
            oficina.clean()
        with self.assertRaises(ValidationError):
            oficina.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inmueble.objects.filter(pk=self.chalet.pk).update(tipo='Oficina')
        with self.assertRaises(ValidationError):
            Inmueble(referencia='V4', tipo='Vivienda', subtipo='castillo').full_clean(exclude=['municipio'])
        inmueble(referencia='V5', tipo='Oficina')

    def test_conservacion_is_separate_from_availability(self):
        with self.assertRaises(ValidationError):
            Inmueble(referencia='V6', conservacion='disponible').full_clean(exclude=['municipio'])
        self.assertEqual(self.chalet.estado, 'Disponible')

    def test_garden_area_needs_a_garden_and_cannot_be_negative(self):
        from base.models import Entorno
        entorno = self.chalet.entorno
        entorno.jardin = False
        with self.assertRaises(ValidationError):
            entorno.full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            entorno.save()
        entorno.jardin, entorno.jardin_m2 = True, -1
        with self.assertRaises(ValidationError):
            entorno.full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            Entorno.objects.filter(pk=entorno.pk).update(jardin_m2=-1)

    def test_list_and_filters_by_tipo_subtipo_and_surface(self):
        piso = inmueble(referencia='V7', publicar_web=True, tipo='Vivienda', subtipo='piso',
                        sup_construida='55', distrito=self.dis)
        self.price(piso, venta=295000)
        ventas = '/api/inmuebles/modalidad/ventas/'
        self.assertEqual(self.refs(f'{ventas}?subtipo=piso'), ['V7'])
        self.assertEqual(self.refs(f'{ventas}?subtipo=chalet_adosado'), ['V1'])
        self.assertEqual(self.refs(f'{ventas}?tipo=Vivienda'), ['V1', 'V7'])
        self.assertEqual(self.refs(f'{ventas}?tipo=Oficina'), [])
        self.assertEqual(self.refs(f'{ventas}?sup_min=100'), ['V1'])
        self.assertEqual(self.refs(f'{ventas}?sup_max=100'), ['V7'])
        self.assertEqual(self.refs(f'{ventas}?sup_min=50&sup_max=60&max_precio=300000'), ['V7'])
        self.assertEqual(self.refs(f'{ventas}?subtipo=piso&max_precio=100000'), [])
        listed = {i['referencia']: i for i in self.client.get(ventas).json()['inmuebles']}
        self.assertEqual((listed['V1']['subtipo'], listed['V1']['sup_construida']), ('chalet_adosado', '154.00'))

    def test_invalid_filter_values_are_rejected(self):
        for query in ('tipo=Castillo', 'subtipo=castillo', 'sup_min=abc', 'sup_max=x'):
            self.assertEqual(self.client.get(f'/api/inmuebles/?{query}').status_code, 400, query)


class MediaYPlanosTests(TestCase):
    def setUp(self):
        from base.models import ImageInmueble
        self.Image = ImageInmueble
        self.inm = inmueble(referencia='MP1', publicar_web=True)

    def test_every_photo_has_a_type_and_the_api_returns_it(self):
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', tipo='fachada', posicion=1)
        self.Image.objects.create(inmueble=self.inm, image='b.jpg', posicion=2)
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual([i['tipo'] for i in data['images']], ['fachada', 'otro'])
        with self.assertRaises(ValidationError):
            self.Image(inmueble=self.inm, image='c.jpg', tipo='sotano').full_clean()

    def test_plans_are_returned_apart_from_the_photos_in_detail_and_list(self):
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', tipo='salon', posicion=1)
        self.Image.objects.create(inmueble=self.inm, image='p.jpg', tipo='plano', posicion=2, alt_text='Planta 1')
        self.Image.objects.create(inmueble=self.inm, image='q.jpg', tipo='plano', posicion=3)
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual([i['tipo'] for i in data['images']], ['salon'])
        self.assertEqual([i['tipo'] for i in data['planos']], ['plano', 'plano'])
        self.assertEqual(data['planos'][0]['alt_text'], 'Planta 1')
        listed = self.client.get('/api/inmuebles/').json()['inmuebles'][0]
        self.assertEqual([i['tipo'] for i in listed['images']], ['salon'])
        self.assertNotIn('planos', listed)

    def test_a_plan_cannot_be_the_default_photo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Image.objects.create(inmueble=self.inm, image='p.jpg', tipo='plano', default=True)
        photo = self.Image.objects.create(inmueble=self.inm, image='a.jpg', tipo='fachada', default=True)
        self.Image.objects.create(inmueble=self.inm, image='p.jpg', tipo='plano')
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Image.objects.filter(pk=photo.pk).update(tipo='plano')

    def test_videos_and_tours_are_listed_in_order_with_their_links(self):
        from base.models import MediaInmueble
        MediaInmueble.objects.create(
            inmueble=self.inm, tipo='video', url='https://example.com/v2', titulo='Recorrido', posicion=2)
        MediaInmueble.objects.create(
            inmueble=self.inm, tipo='tour', url='https://my.matterport.com/show/?m=abc', posicion=1)
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(
            data['medios'],
            [{'tipo': 'tour', 'url': 'https://my.matterport.com/show/?m=abc', 'titulo': ''},
             {'tipo': 'video', 'url': 'https://example.com/v2', 'titulo': 'Recorrido'}])
        self.assertNotIn('matterport_url', data)

    def test_media_rules(self):
        from base.models import MediaInmueble
        MediaInmueble.objects.create(inmueble=self.inm, url='https://example.com/v')
        with self.assertRaises(IntegrityError), transaction.atomic():
            MediaInmueble.objects.create(inmueble=self.inm, url='https://example.com/v')
        MediaInmueble.objects.create(inmueble=inmueble(referencia='MP2'), url='https://example.com/v')
        with self.assertRaises(ValidationError):
            MediaInmueble(inmueble=self.inm, url='no es un enlace').full_clean()
        with self.assertRaises(ValidationError):
            MediaInmueble(inmueble=self.inm, url='https://example.com/x', tipo='gif').full_clean()
        self.inm.delete()
        self.assertEqual(MediaInmueble.objects.count(), 1)

    def test_detail_queries_do_not_grow_with_photos_and_media(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from base.models import MediaInmueble

        def queries():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(f'/api/inmuebles/{self.inm._id}/')
            return len(ctx)

        before = queries()
        for i in range(3):
            self.Image.objects.create(inmueble=self.inm, image=f'{i}.jpg', tipo='plano' if i else 'fachada')
            MediaInmueble.objects.create(inmueble=self.inm, url=f'https://example.com/{i}')
        self.assertEqual(queries(), before)


class SolicitudTipoTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        from base.models import SolicitudReserva
        cache.clear()  # the throttle counts requests in the cache, shared across tests
        self.addCleanup(cache.clear)
        self.Solicitud = SolicitudReserva
        self.inm = inmueble(referencia='ST1', publicar_web=True)
        self.url = f'/api/inmuebles/{self.inm._id}/reservas/'
        self.body = {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600',
                     'acepta_aviso_legal': True}

    def post(self, **extra):
        return self.client.post(self.url, {**self.body, **extra}, content_type='application/json')

    def test_a_request_without_a_type_is_a_reservation(self):
        self.assertEqual(self.post().status_code, 201)
        solicitud = self.Solicitud.objects.get()
        self.assertEqual((solicitud.tipo, solicitud.mensaje, solicitud.fecha_desde), ('reserva', '', None))

    def test_visit_and_information_requests_keep_their_message(self):
        response = self.post(tipo='visita', fecha_desde='2026-11-02', mensaje='Me interesa visitarlo.')
        self.assertEqual(response.status_code, 201)
        self.assertEqual((response.json()['tipo'], response.json()['mensaje']), ('visita', 'Me interesa visitarlo.'))
        self.assertEqual(self.post(tipo='informacion', mensaje='¿Admiten mascotas?').status_code, 201)
        self.assertEqual(
            list(self.Solicitud.objects.order_by('pk').values_list('tipo', 'mensaje')),
            [('visita', 'Me interesa visitarlo.'), ('informacion', '¿Admiten mascotas?')])

    def test_unknown_type_and_overlong_message_are_rejected(self):
        self.assertEqual(self.post(tipo='compra').status_code, 400)
        self.assertEqual(self.post(mensaje='x' * 2001).status_code, 400)
        self.assertEqual(self.post(mensaje='x' * 2000).status_code, 201)
        self.assertEqual(self.Solicitud.objects.count(), 1)

    def test_the_legal_notice_is_still_required_for_every_type(self):
        for tipo in ('reserva', 'visita', 'informacion'):
            self.assertEqual(self.post(tipo=tipo, acepta_aviso_legal=False).status_code, 400, tipo)

    def test_requests_are_still_write_only_and_the_state_is_not_client_set(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.post(tipo='visita', estado='cerrada')
        self.assertEqual(self.Solicitud.objects.get().estado, 'pendiente')


class DetailTablesAllowListTests(TestCase):
    """Detail tables are serialized with `fields = '__all__'`, so a new column would go public on its own.

    Each public field is pinned here: adding a column to one of these models fails this test until the
    column is added below (public) or the serializer is changed to withhold it (private).
    """

    PUBLIC = {
        'OtrosSerializer': 'id capacidad_personas suelo_piso exterior altura_real_m anio_ultima_reforma '
            'gastos_comunidad_incluidos ibi_incluido orientacion chimenea vistas_al_mar vistas_montania '
            'tipo_fachada office acepta_animales estancia_minima estancia_minima_unidad estancia_maxima '
            'estancia_maxima_unidad inmueble',
        'BaniosSerializer': 'id banios suelo inmueble',
        'DormitoriosSerializer': 'id dobles individuales exteriores suites inmueble',
        'InstalacionesSerializer': 'id contador_agua compania_agua contador_electricidad compania_electricidad '
            'gas tipo_gas contador_gas compania_gas calefaccion tipo_calefaccion subtipo_calefaccion tvs '
            'tv_internacional antena_parabolica aire_acondicionado ascensor internet telefono '
            'instalacion_telefono dvd hilo_musical acceso_silla_ruedas inmueble',
        'AreaRecreoSerializer': 'id zona_deportiva gimnasio piscina solarium jardin_infantil local_social inmueble',
        'DotacionSerializer': 'id amueblado armarios_empotrados jacuzzi_hidromasaje secadora lavadora '
            'lavavajillas microondas nevera radio ropero toldo horno utensilios_cocina vajilla cuberteria '
            'cristaleria ropa_cama toallas estufa ventilador camas sofas tendedero inmueble',
        'SeguridadSerializer': 'id portero_conserje vigilancia_privada camaras_seguridad puerta_blindada '
            'caja_seguridad cristales_blindados sistema_alarma instalacion_antirrobo '
            'instalacion_contra_incendio video_portero portero_automatico inmueble',
        'EntornoSerializer': 'id zona_comunitaria otras_areas_comunitarias jardin jardin_m2 cerca_colegios '
            'cerca_farmacia cerca_guarderias cerca_medico cerca_centro_comercial distancia_playa_m '
            'distancia_poblacion_m distancia_ciudad_m cerca_supermercado cerca_restaurantes cerca_discotecas '
            'inmueble',
        'TransporteSerializer': 'id cerca_bus descripcion_bus cerca_metro descripcion_metro cerca_tranvia '
            'descripcion_tranvia cerca_tren descripcion_tren cerca_ferrocarril descripcion_ferrocarril inmueble',
        'OtrosEspaciosSerializer': 'id despachos vestidores altillo galeria trastero buhardilla bodega '
            'lavadero estudios bibliotecas inmueble',
        'CondicionesSerializer': 'id nombre honorarios itp incluido no_incluido fianza pago_adelantado '
            'suministros limpieza_final requisitos notaria registro gestoria honorarios_comprador',
        'RegistroLegalSerializer': 'tipo numero organismo',
        'MediaInmuebleSerializer': 'tipo url titulo',
        'SingleImageSerializer': '_id image default alt_text posicion tipo',
        'PlazaAparcamientoSerializer': 'id numero tipo superficie notas opcional precio_opcional '
            'precio_opcional_unidad precio_opcional_mas_iva precio_opcional_tipo_iva',
        'CocinaSerializer': 'id cocina cocina_amueblada tipo_cocina suelo_cocina inmueble',
        'TerrazaSerializer': 'id terraza terraza_m2 balcones balcones_m2 descripcion inmueble',
        'SalonSerializer': 'id salon_m2 descripcion inmueble',
        'CarpinteriaSerializer': 'id carpinteria_interior carpinteria_exterior inmueble',
        'PrecioModalidadSerializer': 'codigo nombre unidad_precio precio mas_iva tipo_iva',
        'PrecioModalidadDetalleSerializer': 'codigo nombre unidad_precio precio mas_iva tipo_iva ultima_renta condiciones',
    }

    def test_every_public_field_is_listed(self):
        from base import serializers
        for name, expected in self.PUBLIC.items():
            self.assertEqual(
                list(getattr(serializers, name)().fields), expected.split(), name)

    def test_private_models_have_no_serializer(self):
        from rest_framework import serializers as drf
        from base import serializers
        from base.models import (
            DatosInternos, DeclaracionZonaTensionada, HistorialPrecio, InmueblePropietario, Propietario,
        )
        private = {DatosInternos, DeclaracionZonaTensionada, HistorialPrecio, InmueblePropietario, Propietario}
        used = {
            getattr(obj.Meta, 'model', None)
            for obj in vars(serializers).values()
            if isinstance(obj, type) and issubclass(obj, drf.ModelSerializer) and hasattr(obj, 'Meta')
        }
        self.assertEqual(used & private, set())

    def test_new_serializers_are_pinned_too(self):
        """A ModelSerializer added to serializers.py must be pinned above (or be a location list)."""
        from rest_framework import serializers as drf
        from base import serializers
        pinned = set(self.PUBLIC)
        # Reference lists and the two listing serializers have their own tests.
        elsewhere = {
            'ProvinciasSerializer', 'MunicipiosSerializer', 'MunicipiosListItemSerializer',
            'DistritosSerializer', 'DistritosListItemSerializer', 'BarriosSerializer', 'ModalidadSerializer',
            'SolicitudReservaSerializer', 'InmuebleSerializer', 'SingleInmuebleSerializer',
        }
        found = {
            name for name, obj in vars(serializers).items()
            if isinstance(obj, type) and issubclass(obj, drf.ModelSerializer)
            and obj is not drf.ModelSerializer and obj.__module__ == serializers.__name__
        }
        self.assertEqual(found - pinned - elsewhere, set())
