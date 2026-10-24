from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from base.models import Barrio, Modalidad, CondicionesAlquiler, Distrito, Inmueble, Municipio, Provincia


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
            CondicionesAlquiler, Entorno, Seguridad, Terraza, Transporte,
        )
        self.default = CondicionesAlquiler.objects.create(
            nombre='General', por_defecto=True, fianza='2 mensualidades'
        )
        self.inm = Inmueble.objects.create(
            referencia='G767', publicar_web=True, propietario='SECRETO',
            zona_tensionada=True, ultima_renta='1750.00',
            indice_referencia_min='839.99', indice_referencia_max='1153.53',
        )
        Terraza.objects.create(modulo=self.inm, terraza=2, balcones=1)
        Seguridad.objects.create(modulo=self.inm, puerta_blindada=True)
        Entorno.objects.create(modulo=self.inm, cerca_colegios=True)
        Transporte.objects.create(modulo=self.inm, cerca_metro=True, descripcion_metro='L2')

    def test_detail_exposes_new_sections(self):
        data = self.client.get(f'/api/inmuebles/{self.inm._id}/').json()
        self.assertEqual(data['terraza']['balcones'], 1)
        self.assertTrue(data['seguridad']['puerta_blindada'])
        self.assertEqual(data['entorno']['cerca_colegios'], True)
        self.assertEqual(data['transporte']['descripcion_metro'], 'L2')
        self.assertIsNone(data['salon'])
        self.assertTrue(data['zona_tensionada'])
        self.assertNotIn('propietario', data)

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
        inm = Inmueble.objects.create(referencia='P1', publicar_web=True, propietario='X',
                                      notas_internas='n', cat_nrc='c', valor_plz='1')
        data = self.client.get(f'/api/inmuebles/{inm._id}/').json()
        self.assertEqual([k for k in INMUEBLE_PRIVATE_FIELDS if k in data], [])


class ListQueryTests(TestCase):
    def make(self, n):
        from base.models import Banios, Cocina, Dormitorios, ImageInmueble, Otros, Terraza
        prov = Provincia.objects.get_or_create(codigo_ine='08', nombre='Barcelona')[0]
        mun = Municipio.objects.get_or_create(provincia=prov, codigo_ine='08019', nombre='Barcelona')[0]
        dis = Distrito.objects.get_or_create(municipio=mun, codigo='01', nombre='Ciutat Vella')[0]
        for i in range(n):
            inm = Inmueble.objects.create(
                referencia=f'L{Inmueble.objects.count()}', publicar_web=True,
                provincia=prov, municipio=mun, distrito=dis)
            inm.modalidades.add(Modalidad.objects.get_or_create(codigo='temporal', defaults={'nombre': 'Vivienda temporal'})[0])
            for model in (Banios, Cocina, Dormitorios, Otros, Terraza):
                model.objects.create(modulo=inm)
            ImageInmueble.objects.create(modulo=inm, image='x.jpg')

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
                        'n_banyos', 'max_personas', 'estancia_min', 'estancia_max',
                        'gtos_com_incluido'):
            self.assertNotIn(dropped, columns)

    def test_n_banyos_comes_from_banios(self):
        from base.models import Banios
        inm = Inmueble.objects.create(referencia='S1', publicar_web=True)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_banyos'], 0)
        Banios.objects.create(modulo=inm, banios=2)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm._id}/').json()['n_banyos'], 2)
        listed = self.client.get('/api/inmuebles/').json()['inmuebles'][0]
        self.assertEqual(listed['n_banyos'], 2)


class ModalidadTests(TestCase):
    def setUp(self):
        self.mod = {c: Modalidad.objects.create(codigo=c, nombre=n, orden=i) for i, (c, n) in enumerate(
            [('temporal', 'Vivienda temporal'), ('habitual', 'Vivienda habitual'),
             ('venta', 'Venta'), ('otros', 'Otros usos')])}
        prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        mun = Municipio.objects.create(provincia=prov, codigo_ine='08019', nombre='Barcelona')
        self.dis = Distrito.objects.create(municipio=mun, codigo='01', nombre='Ciutat Vella')
        self.both = Inmueble.objects.create(referencia='M1', publicar_web=True, distrito=self.dis)
        self.both.modalidades.set([self.mod['temporal'], self.mod['venta']])
        self.rent = Inmueble.objects.create(referencia='M2', publicar_web=True, distrito=self.dis)
        self.rent.modalidades.set([self.mod['habitual']])
        self.hidden = Inmueble.objects.create(referencia='M3', publicar_web=False, distrito=self.dis)
        self.hidden.modalidades.set([self.mod['temporal']])

    def refs(self, url):
        return sorted(i['referencia'] for i in self.client.get(url).json()['inmuebles'])

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
                         ['temporal', 'habitual', 'venta', 'otros'])
