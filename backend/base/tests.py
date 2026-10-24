from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from base.models import Barrio, InmuebleModalidad, Modalidad, CondicionesAlquiler, Distrito, Inmueble, Municipio, Provincia


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
        other = Provincia.objects.create(codigo_ine='17', nombre='Girona')
        bad = Inmueble(referencia='X', provincia=other, municipio=self.mun)
        with self.assertRaises(ValidationError):
            bad.full_clean(exclude=[f.name for f in Inmueble._meta.fields if f.name not in ('provincia', 'municipio', 'distrito')])
        ok = Inmueble(referencia='Y', provincia=self.prov, municipio=self.mun, distrito=self.dis)
        ok.full_clean(exclude=[f.name for f in Inmueble._meta.fields if f.name not in ('provincia', 'municipio', 'distrito')])


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
        inm = Inmueble.objects.create(referencia='B1', publicar_web=True, municipio=self.mun,
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
            CondicionesAlquiler, Entorno, Estancias, Seguridad, Transporte,
        )
        self.default = CondicionesAlquiler.objects.create(
            nombre='General', por_defecto=True, fianza='2 mensualidades'
        )
        self.inm = Inmueble.objects.create(
            referencia='G767', publicar_web=True,
            zona_tensionada=True, ultima_renta='1750.00',
            indice_referencia_min='839.99', indice_referencia_max='1153.53',
        )
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
        self.assertEqual(data['salon'], {'id': data['terraza']['id'], 'salon': 0, 'descripcion': 'Vistas', 'inmueble': self.inm._id})
        self.assertEqual(data['terraza']['descripcion'], 'Vistas')
        self.assertFalse(data['carpinteria']['carpinteria_interior'])
        self.assertTrue(data['zona_tensionada'])

    def test_conditions_fall_back_to_default(self):
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['condiciones']['fianza'], '2 mensualidades')
        own = CondicionesAlquiler.objects.create(nombre='Larga', fianza='1 mes')
        self.inm.condiciones = own
        self.inm.save()
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['condiciones']['fianza'], '1 mes')

    def test_only_one_default_conditions(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CondicionesAlquiler.objects.create(nombre='Otra', por_defecto=True)

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
        relations = {'provincia', 'municipio', 'distrito', 'barrio', 'condiciones', 'modalidades'}
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
        from base.models import DatosInternos, Propietario
        from base.models import PlazaAparcamiento
        inm = Inmueble.objects.create(referencia='P1', publicar_web=True)
        PlazaAparcamiento.objects.create(inmueble=inm, valor='12345.67', renta='89.01')
        DatosInternos.objects.create(
            inmueble=inm, propietario=Propietario.objects.create(nombre='SECRETO'),
            notas_internas='n', cat_nrc='c')
        response = self.client.get(f'/api/inmuebles/{inm._id}/')
        data = response.json()
        self.assertEqual([k for k in INMUEBLE_PRIVATE_FIELDS if k in data], [])
        self.assertNotIn('datos_internos', data)
        self.assertNotIn('SECRETO', response.content.decode())
        self.assertNotIn('12345.67', response.content.decode())
        self.assertNotIn('89.01', response.content.decode())


class ListQueryTests(TestCase):
    def make(self, n):
        from base.models import Banios, Dormitorios, Estancias, ImageInmueble, Otros
        prov = Provincia.objects.get_or_create(codigo_ine='08', nombre='Barcelona')[0]
        mun = Municipio.objects.get_or_create(provincia=prov, codigo_ine='08019', nombre='Barcelona')[0]
        dis = Distrito.objects.get_or_create(municipio=mun, codigo='01', nombre='Ciutat Vella')[0]
        for i in range(n):
            inm = Inmueble.objects.create(
                referencia=f'L{Inmueble.objects.count()}', publicar_web=True,
                provincia=prov, municipio=mun, distrito=dis)
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
        inm = Inmueble.objects.create(referencia='S1', publicar_web=True)
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
        self.both = Inmueble.objects.create(referencia='M1', publicar_web=True, distrito=self.dis)
        self.price(self.both, temporal=1200, venta=300000)
        self.rent = Inmueble.objects.create(referencia='M2', publicar_web=True, distrito=self.dis)
        self.price(self.rent, habitual=900)
        self.hidden = Inmueble.objects.create(referencia='M3', publicar_web=False, distrito=self.dis)
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
        self.inm = Inmueble.objects.create(referencia='I1', publicar_web=True)

    def test_only_one_default_photo_per_listing(self):
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', default=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Image.objects.create(inmueble=self.inm, image='b.jpg', default=True)
        other = Inmueble.objects.create(referencia='I2')
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
        inm = Inmueble(referencia='A1')
        model_admin.save_model(request, inm, form=None, change=False)
        request.user = editor
        model_admin.save_model(request, inm, form=None, change=True)
        inm.refresh_from_db()
        self.assertEqual(inm.created_by, creator)
        self.assertEqual(inm.updated_by, editor)

    def test_audit_columns_never_in_detail_response(self):
        inm = Inmueble.objects.create(referencia='A2', publicar_web=True)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertNotIn('created_by', data)
        self.assertNotIn('updated_by', data)


class HistorialRentaTests(TestCase):
    def setUp(self):
        self.inm = Inmueble.objects.create(referencia='H1', publicar_web=True)

    def test_history_is_newest_first_and_private(self):
        from datetime import date
        from base.models import HistorialRenta
        HistorialRenta.objects.create(inmueble=self.inm, fecha=date(2023, 1, 1), importe='900')
        HistorialRenta.objects.create(inmueble=self.inm, fecha=date(2024, 1, 1), importe='950')
        self.assertEqual([str(r.importe) for r in self.inm.historial_renta.all()], ['950.00', '900.00'])
        self.assertNotIn('historial_renta', self.client.get(f'/api/inmuebles/{self.inm._id}/').json())

    def test_one_entry_per_date_and_no_negative_rent(self):
        from datetime import date
        from base.models import HistorialRenta
        HistorialRenta.objects.create(inmueble=self.inm, fecha=date(2023, 1, 1), importe='900')
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistorialRenta.objects.create(inmueble=self.inm, fecha=date(2023, 1, 1), importe='950')
        with self.assertRaises(ValidationError):
            HistorialRenta(inmueble=self.inm, fecha=date(2022, 1, 1), importe='-1').full_clean()


class DatosInternosTests(TestCase):
    def test_owner_has_many_listings_and_is_protected(self):
        from base.models import DatosInternos, Propietario
        owner = Propietario.objects.create(nombre='Ana', email='ana@example.com')
        for ref in ('D1', 'D2'):
            DatosInternos.objects.create(
                inmueble=Inmueble.objects.create(referencia=ref), propietario=owner)
        self.assertEqual(owner.inmuebles.count(), 2)
        with self.assertRaises(ProtectedError):
            owner.delete()

    def test_one_internal_record_per_listing_and_deleted_with_it(self):
        from base.models import DatosInternos
        inm = Inmueble.objects.create(referencia='D3')
        DatosInternos.objects.create(inmueble=inm, notas_internas='llaves en recepción')
        with self.assertRaises(IntegrityError), transaction.atomic():
            DatosInternos.objects.create(inmueble=inm)
        inm.delete()
        self.assertEqual(DatosInternos.objects.count(), 0)


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
        InmuebleModalidad.objects.filter(modalidad=self.mod['habitual']).delete()
        self.mod['habitual'].delete()
        self.both.delete()
        self.assertFalse(InmuebleModalidad.objects.filter(inmueble_id=self.both._id).exists())

    def test_unit_is_set_per_modalidad(self):
        data = {m['codigo']: m['unidad_precio'] for m in self.client.get('/api/modalidades/').json()}
        self.assertEqual(data, {'temporal': 'mensual', 'habitual': 'mensual', 'venta': 'total'})

    def test_api_returns_price_and_unit_per_modalidad(self):
        data = self.client.get(f'/api/inmuebles/{self.both._id}/').json()
        self.assertEqual(data['modalidades'], [
            {'codigo': 'temporal', 'nombre': 'Vivienda temporal', 'unidad_precio': 'mensual', 'precio': '1200.00'},
            {'codigo': 'venta', 'nombre': 'Venta', 'unidad_precio': 'total', 'precio': '300000.00'},
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
        self.inm = Inmueble.objects.create(referencia='PK1', publicar_web=True)

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
        self.assertEqual(set(plaza), {'id', 'numero', 'tipo', 'superficie', 'notas'})
        self.assertEqual(plaza['superficie'], '11.50')

    def test_number_is_unique_per_listing_when_given(self):
        self.Plaza.objects.create(inmueble=self.inm, numero='7')
        self.Plaza.objects.create(inmueble=self.inm)
        self.Plaza.objects.create(inmueble=self.inm)
        self.Plaza.objects.create(inmueble=Inmueble.objects.create(referencia='PK2'), numero='7')
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Plaza.objects.create(inmueble=self.inm, numero='7')

    def test_amounts_cannot_be_negative_and_plazas_go_with_the_listing(self):
        with self.assertRaises(ValidationError):
            self.Plaza(inmueble=self.inm, valor='-1').full_clean()
        self.Plaza.objects.create(inmueble=self.inm)
        self.inm.delete()
        self.assertEqual(self.Plaza.objects.count(), 0)

    def test_parking_listing_may_have_plazas_too(self):
        parking = Inmueble.objects.create(referencia='PK3', tipo='Parking', publicar_web=True)
        self.Plaza.objects.create(inmueble=parking)
        self.assertEqual(self.client.get(f'/api/inmuebles/{parking._id}/').json()['n_plz_garaje'], 1)


class HabitacionesTests(TestCase):
    def make(self, ref, dobles=None, individuales=0, suites=0, exteriores=0):
        from base.models import Dormitorios
        inm = Inmueble.objects.create(referencia=ref, publicar_web=True)
        if dobles is not None:
            Dormitorios.objects.create(
                inmueble=inm, dobles=dobles, individuales=individuales,
                suites=suites, exteriores=exteriores)
        return inm

    def test_column_is_gone_and_total_is_dobles_individuales_suites(self):
        self.assertNotIn('n_habitaciones', {f.name for f in Inmueble._meta.get_fields() if f.concrete})
        inm = self.make('H1', dobles=2, individuales=1, suites=1, exteriores=3)
        self.assertEqual(Inmueble.objects.get(pk=inm.pk).n_habitaciones, 4)

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
        self.make('H5', dobles=1, individuales=1, suites=1, exteriores=5)
        self.make('H6', dobles=1)
        self.make('H7')
        refs = lambda n: sorted(i['referencia'] for i in self.client.get(f'/api/inmuebles/?habitaciones={n}').json()['inmuebles'])
        self.assertEqual(refs(3), ['H4', 'H5'])
        self.assertEqual(refs(1), ['H6'])
        self.assertEqual(len(self.client.get('/api/inmuebles/').json()['inmuebles']), 4)

    def test_changing_dormitorios_changes_the_number(self):
        inm = self.make('H8', dobles=1)
        inm.dormitorios.suites = 2
        inm.dormitorios.save()
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_habitaciones'], 3)


class TextToNumbersTests(TestCase):
    def test_api_returns_numbers_with_units_in_the_name(self):
        from base.models import Entorno, Otros
        inm = Inmueble.objects.create(referencia='N1', publicar_web=True)
        Otros.objects.create(inmueble=inm, estancia_minima_meses=2, altura_real_m='2.70')
        Entorno.objects.create(inmueble=inm, distancia_playa_m=800)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual((data['otros']['estancia_minima_meses'], data['otros']['altura_real_m']), (2, '2.70'))
        self.assertEqual(data['entorno']['distancia_playa_m'], 800)
        for old in ('estancia_minima', 'altura_real'):
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
        with_barrio = Inmueble.objects.create(
            referencia='Z1', publicar_web=True, municipio=mun, distrito=dis, barrio=bar)
        only_district = Inmueble.objects.create(
            referencia='Z2', publicar_web=True, municipio=mun, distrito=dis)
        nowhere = Inmueble.objects.create(referencia='Z3', publicar_web=True)
        zones = lambda i: tuple(self.client.get(f'/api/inmuebles/{i._id}/').json()[k] for k in ('zona', 'zona_ref'))
        self.assertEqual(zones(with_barrio), ('El Raval', 'Ciutat Vella'))
        self.assertEqual(zones(only_district), ('Ciutat Vella', 'Ciutat Vella'))
        self.assertEqual(zones(nowhere), (None, None))
        listed = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual(listed['Z1']['zona'], 'El Raval')


class DatabaseRulesTests(TestCase):
    def test_negative_amounts_are_rejected_by_validators_and_the_database(self):
        for field in ('sup_util', 'sup_construida', 'gtos_comunidad', 'ibi', 'ultima_renta', 'consumo_energetico'):
            with self.assertRaises(ValidationError, msg=field):
                Inmueble(referencia='R', **{field: -1}).full_clean(exclude=['provincia'])
            with self.assertRaises(IntegrityError, msg=field), transaction.atomic():
                Inmueble.objects.create(referencia='R', **{field: -1})

    def test_reference_index_range_is_a_database_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inmueble.objects.create(referencia='R1', indice_referencia_min=10, indice_referencia_max=5)
        Inmueble.objects.create(referencia='R2', indice_referencia_min=5)
        Inmueble.objects.create(referencia='R3', indice_referencia_min=5, indice_referencia_max=5)

    def test_counts_cannot_be_negative(self):
        from base.models import Dormitorios, Otros
        inm = Inmueble.objects.create(referencia='R4')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Dormitorios.objects.create(inmueble=inm, dobles=-1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Otros.objects.create(inmueble=inm, capacidad_personas=-2)


class DateAndSurfaceTypesTests(TestCase):
    def test_availability_is_a_date_and_filters_by_date(self):
        from datetime import date
        Inmueble.objects.create(referencia='T1', publicar_web=True, fecha_disponibilidad=date(2025, 3, 1))
        Inmueble.objects.create(referencia='T2', publicar_web=True, fecha_disponibilidad=date(2025, 6, 1))
        data = self.client.get('/api/inmuebles/?fecha_entrada=2025-04-01').json()
        self.assertEqual([i['referencia'] for i in data['inmuebles']], ['T1'])
        self.assertEqual(data['inmuebles'][0]['fecha_disponibilidad'], '2025-03-01')
        for name in ('fecha_disponibilidad', 'fecha_alta', 'fecha_baja', 'fecha_entrega'):
            self.assertEqual(Inmueble._meta.get_field(name).get_internal_type(), 'DateField')

    def test_surfaces_allow_large_premises(self):
        inm = Inmueble.objects.create(referencia='T3', sup_construida='12345.67', sup_util='999999.99')
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
        for name in ('sup_construida', 'sup_cont_comun', 'sup_util', 'cedula', 'situacion_actual',
                     'ibi', 'gtos_comunidad', 'geo_latitude', 'geo_longitude'):
            field = Inmueble._meta.get_field(name)
            self.assertEqual((field.null or field.blank), True, name)
            self.assertTrue(field.blank, name)

    def test_text_cannot_be_null_and_api_returns_empty_strings(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inmueble.objects.create(referencia='NN1', titulo=None)
        inm = Inmueble.objects.create(referencia='NN2', publicar_web=True)
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual((data['titulo'], data['descripcion_es'], data['cedula']), ('', '', ''))

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
        self.inm = Inmueble.objects.create(referencia='SR1', publicar_web=True)

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
            acepta_aviso_legal=True, **kw)
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
