from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone
from django.test.utils import CaptureQueriesContext

from base.models import Agencia, AcuerdoAdministracion, CertificadoEnergetico, Propietario, DescripcionInmueble, Instalaciones, Suministro, TransporteInmueble, Barrio, InmuebleModalidad, Modalidad, Condiciones, Distrito, Inmueble, Municipio, Provincia, RegistroLegal


def default_municipio():
    prov = Provincia.objects.get_or_create(codigo_ine='08', defaults={'nombre': 'Barcelona'})[0]
    return Municipio.objects.get_or_create(
        codigo_ine='08019', defaults={'provincia': prov, 'nombre': 'Barcelona'})[0]


def inmueble(**fields):
    """Create an Inmueble; `municipio` is required, so default to Barcelona."""
    fields.setdefault('municipio', default_municipio())
    descripciones = {i: fields.pop(f'descripcion_{i}', '') for i, _ in DescripcionInmueble.IDIOMAS}
    inm = Inmueble.objects.create(**fields)
    for idioma, texto in descripciones.items():
        if texto:
            DescripcionInmueble.objects.create(inmueble=inm, idioma=idioma, texto=texto)
    return inm


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

    def test_municipio_code_must_start_with_the_provincia_code(self):
        girona = Provincia.objects.create(codigo_ine='17', nombre='Girona')
        with self.assertRaises(ValidationError):
            Municipio.objects.create(provincia=girona, codigo_ine='08200', nombre='Mal codigo')

    def test_comarca_can_span_provincias(self):
        """Cerdanya is split between Lleida and Girona: a comarca has no province of its own."""
        from base.models import Comarca
        lleida = Provincia.objects.create(codigo_ine='25', nombre='Lleida')
        girona = Provincia.objects.create(codigo_ine='17', nombre='Girona')
        cerdanya = Comarca.objects.create(codigo='21', nombre='Cerdanya')
        alp = Municipio.objects.create(provincia=girona, comarca=cerdanya, codigo_ine='17005', nombre='Alp')
        das = Municipio.objects.create(provincia=lleida, comarca=cerdanya, codigo_ine='25052', nombre='Das')
        self.assertEqual(set(cerdanya.municipios.all()), {alp, das})
        self.assertNotIn('provincia', {f.name for f in Comarca._meta.get_fields()})

    def test_comarca_code_and_slug_are_unique(self):
        from base.models import Comarca
        Comarca.objects.create(codigo='21', nombre='Cerdanya')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comarca.objects.create(codigo='21', nombre='Otra', slug='otra')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comarca.objects.create(codigo='22', nombre='Cerdanya')


class ComprobarUbicacionesTests(TestCase):
    def setUp(self):
        self.prov = Provincia.objects.create(codigo_ine='08', nombre='Barcelona')
        self.bcn = Municipio.objects.create(provincia=self.prov, codigo_ine='08019', nombre='Barcelona')
        self.bdn = Municipio.objects.create(provincia=self.prov, codigo_ine='08015', nombre='Badalona')
        self.eix = Distrito.objects.create(municipio=self.bcn, codigo='02', nombre='Eixample')
        self.cv = Distrito.objects.create(municipio=self.bcn, codigo='01', nombre='Ciutat Vella')
        self.antoni = Barrio.objects.create(distrito=self.eix, codigo='07', nombre='Sant Antoni')

    def tipos(self):
        from base.comprobaciones import inconsistencias_ubicacion
        return sorted(t for t, _ in inconsistencias_ubicacion())

    def test_consistent_data_has_no_problems_and_the_command_succeeds(self):
        from io import StringIO
        from django.core.management import call_command
        inmueble(referencia='C1', municipio=self.bcn, distrito=self.eix, barrio=self.antoni)
        inmueble(referencia='C2', municipio=self.bcn, barrio=self.antoni)
        inmueble(referencia='C3', municipio=self.bdn)
        self.assertEqual(self.tipos(), [])
        out = StringIO()
        call_command('comprobar_ubicaciones', stdout=out)
        self.assertIn('consistent', out.getvalue())

    def test_bulk_writes_that_skip_the_model_checks_are_detected(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        a = inmueble(referencia='C4', municipio=self.bcn)
        b = inmueble(referencia='C5', municipio=self.bcn)
        c = inmueble(referencia='C6', municipio=self.bcn)
        Inmueble.objects.filter(pk=a.pk).update(municipio=self.bdn, distrito=self.eix)
        Inmueble.objects.filter(pk=b.pk).update(distrito=self.cv, barrio=self.antoni)
        Inmueble.objects.filter(pk=c.pk).update(municipio=self.bdn, barrio=self.antoni)
        self.assertEqual(
            self.tipos(),
            ['barrio_de_otro_distrito', 'barrio_de_otro_municipio', 'distrito_de_otro_municipio'])
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command('comprobar_ubicaciones', stdout=out)
        for ref in ('C4', 'C5', 'C6'):
            self.assertIn(ref, out.getvalue())

    def test_municipio_code_of_another_provincia_is_detected(self):
        girona = Provincia.objects.create(codigo_ine='17', nombre='Girona')
        Municipio.objects.filter(pk=self.bdn.pk).update(provincia=girona)
        self.assertEqual(self.tipos(), ['municipio_con_codigo_de_otra_provincia'])


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
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual(data['barrio']['nombre'], 'el Raval')
        self.assertEqual(len(self.client.get(f'/api/inmuebles/?barrio={self.raval.id}').json()['inmuebles']), 1)
        self.assertEqual(len(self.client.get(f'/api/inmuebles/?barrio={self.raval.id + 1}').json()['inmuebles']), 0)
        self.assertEqual(self.client.get(f'/api/distritos/{self.cv.id}/barrios').json()[0]['codigo'], '01')
        self.assertEqual(self.client.get('/api/inmuebles/?barrio=x').status_code, 400)


class DetailApiTests(TestCase):
    def setUp(self):
        from base.models import (
            Entorno, Estancias, Seguridad, TransporteInmueble,
        )
        self.temporal = Modalidad.objects.create(codigo='temporal', nombre='Temporal', orden=0)
        self.default = Condiciones.objects.create(
            nombre='General', modalidad=self.temporal, por_defecto=True, fianza='2 mensualidades'
        )
        self.inm = inmueble(referencia='G767', publicar_web=True)
        from base.models import DeclaracionZonaTensionada
        DeclaracionZonaTensionada.objects.create(municipio=self.inm.municipio, desde=date(2021, 9, 20))
        self.precio = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.temporal, precio='1750')
        Estancias.objects.create(inmueble=self.inm, n_terrazas=2, n_balcones=1, descripcion='Vistas')
        Seguridad.objects.create(inmueble=self.inm, puerta_blindada=True)
        Entorno.objects.create(inmueble=self.inm, cerca_colegios=True)
        TransporteInmueble.objects.create(inmueble=self.inm, tipo='metro', descripcion='L2')

    def test_detail_exposes_new_sections(self):
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual(data['terraza']['n_balcones'], 1)
        self.assertTrue(data['seguridad']['puerta_blindada'])
        self.assertEqual(data['entorno']['cerca_colegios'], True)
        self.assertEqual(data['transporte']['descripcion_metro'], 'L2')
        self.assertEqual(data['salon'], {'salon_m2': None, 'descripcion': 'Vistas'})
        self.assertEqual(data['terraza']['descripcion'], 'Vistas')
        self.assertFalse(data['carpinteria']['carpinteria_interior'])
        self.assertTrue(data['zona_tensionada'])

    def test_conditions_fall_back_to_default(self):
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual(data['modalidades'][0]['condiciones']['fianza'], '2 mensualidades')
        self.assertNotIn('condiciones', data)
        own = Condiciones.objects.create(nombre='Larga', modalidad=self.temporal, fianza='1 mes')
        self.precio.condiciones = own
        self.precio.save()
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual(data['modalidades'][0]['condiciones']['fianza'], '1 mes')

    def test_only_one_default_conditions_per_modalidad(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Condiciones.objects.create(nombre='Otra', modalidad=self.temporal, por_defecto=True)
        venta = Modalidad.objects.create(codigo='venta', nombre='Venta', orden=1, unidad_precio='total')
        Condiciones.objects.create(nombre='Venta general', modalidad=venta, por_defecto=True)

    def test_reservation_request(self):
        from base.models import SolicitudReserva
        url = f'/api/inmuebles/{self.inm.id}/reservas/'
        body = {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600000000',
                'fecha_desde': '2026-11-23', 'acepta_aviso_legal': True}
        self.assertEqual(self.client.post(url, body).status_code, 201)
        req = SolicitudReserva.objects.get()
        self.assertEqual((req.referencia, req.inmueble_id), ('G767', self.inm.id))
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
        relations = {'municipio', 'distrito', 'barrio', 'modalidades', 'propietarios', 'agencia'}
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
        DatosInternos.objects.create(inmueble=inm, notas_internas='n')
        Inmueble.objects.filter(pk=inm.pk).update(referencia_catastral='REF-CATASTRAL-SECRETA')
        self.assertNotIn('REF-CATASTRAL-SECRETA', self.client.get(f'/api/inmuebles/{inm.id}/').content.decode())
        response = self.client.get(f'/api/inmuebles/{inm.id}/')
        data = response.json()
        self.assertEqual([k for k in INMUEBLE_PRIVATE_FIELDS if k in data], [])
        self.assertNotIn('datos_internos', data)
        self.assertNotIn('SECRETO', response.content.decode())
        self.assertNotIn('propietarios', data)
        self.assertNotIn('12345.67', response.content.decode())
        self.assertNotIn('89.01', response.content.decode())


class ListQueryTests(TestCase):
    def make(self, n):
        from base.models import Caracteristicas, Distribucion, Estancias, ImageInmueble
        prov = Provincia.objects.get_or_create(codigo_ine='08', nombre='Barcelona')[0]
        mun = Municipio.objects.get_or_create(provincia=prov, codigo_ine='08019', nombre='Barcelona')[0]
        dis = Distrito.objects.get_or_create(municipio=mun, codigo='01', nombre='Ciutat Vella')[0]
        for i in range(n):
            inm = inmueble(
                referencia=f'L{Inmueble.objects.count()}', publicar_web=True,
                municipio=mun, distrito=dis)
            inm.modalidades.add(Modalidad.objects.get_or_create(codigo='temporal', defaults={'nombre': 'Vivienda temporal'})[0],
                                through_defaults={'precio': 800})
            for model in (Distribucion, Estancias, Caracteristicas):
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
        self.assertLessEqual(five, 7)


HOY = timezone.localdate().isoformat()


class SingleSourceTests(TestCase):
    def test_equipment_columns_live_only_in_detail_tables(self):
        columns = {f.name for f in Inmueble._meta.get_fields() if f.concrete}
        for dropped in ('ascensor', 'calefaccion', 'aire', 'piscina', 'parking',
                        'n_banios', 'max_personas', 'estancia_min', 'estancia_max',
                        'gtos_com_incluido'):
            self.assertNotIn(dropped, columns)

    def test_n_banios_comes_from_distribucion(self):
        from base.models import Distribucion
        inm = inmueble(referencia='S1', publicar_web=True)
        self.assertIsNone(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_banios'])
        Distribucion.objects.create(inmueble=inm, dobles=2)  # layout known, bathrooms not
        self.assertIsNone(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_banios'])
        Distribucion.objects.filter(inmueble=inm).update(banios=0)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_banios'], 0)
        Distribucion.objects.filter(inmueble=inm).update(banios=2)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_banios'], 2)
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


class ComprobarCondicionesTests(ModalidadFixture):

    def test_conditions_of_another_modalidad_are_detected_only_when_bypassing_save(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        from base.comprobaciones import inconsistencias_condiciones
        venta = Condiciones.objects.create(nombre='Venta estándar', modalidad=self.mod['venta'])
        oferta = self.both.precios.get(modalidad=self.mod['temporal'])
        oferta.condiciones = venta
        with self.assertRaises(ValidationError):
            oferta.save()
        out = StringIO()
        call_command('comprobar_condiciones', stdout=out)
        self.assertIn('consistent', out.getvalue())
        InmuebleModalidad.objects.filter(pk=oferta.pk).update(condiciones=venta)
        self.assertEqual([t for t, _ in inconsistencias_condiciones()], ['condiciones_de_otra_modalidad'])
        with self.assertRaises(CommandError):
            call_command('comprobar_condiciones', stdout=out)
        self.assertIn('M1', out.getvalue())


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
        url = f'/api/inmuebles/modalidad/%s/distrito/{self.dis.id}/count/'
        self.assertEqual(self.client.get(url % 'temporales').json()['count'], 1)
        self.assertEqual(self.client.get(url % 'ventas').json()['count'], 1)
        self.assertEqual(self.client.get(url % 'otros').status_code, 400)

    def test_api_shape(self):
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
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
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual([i['alt_text'] for i in data['images']], ['Cocina', 'Salón'])
        self.assertEqual([i['posicion'] for i in data['images']], [1, 2])

    def test_upload_path_uses_listing_id(self):
        from base.models.image_inmueble import content_file_name
        image = self.Image(inmueble=self.inm)
        self.assertEqual(content_file_name(image, 'x.jpg'), f'{self.inm.id}/x.jpg')


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
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
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
        oferta.tipo_iva = 21
        oferta.save()
        oferta.save(update_fields=['tipo_iva'])
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


class RegulacionAlquilerTests(ModalidadFixture):
    def setUp(self):
        super().setUp()
        from datetime import date
        from base.models import RegulacionAlquiler
        self.date = date
        self.Regulacion = RegulacionAlquiler
        self.inm = inmueble(referencia='RG1', publicar_web=True)
        self.alquiler = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod['habitual'], precio='1000')
        self.venta = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod['venta'], precio='250000')

    def regulacion(self, codigo='habitual'):
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        return {m['codigo']: m['regulacion'] for m in data['modalidades']}[codigo]

    def test_rental_without_a_record_is_unknown_and_sale_has_none(self):
        self.assertEqual(self.regulacion(), {
            'indice_referencia_min': None, 'indice_referencia_max': None,
            'indice_referencia_fecha': None, 'renta_previa': 'desconocida',
            'ultima_renta': None, 'ultima_renta_fin': None})
        self.assertIsNone(self.regulacion('venta'))

    def test_declared_values_reach_the_detail(self):
        self.Regulacion.objects.create(
            oferta=self.alquiler, indice_referencia_min='839.99', indice_referencia_max='1153.53',
            indice_referencia_fecha=self.date(2026, 10, 1), renta_previa='con_renta',
            ultima_renta='900', ultima_renta_fin=self.date(2025, 6, 30))
        self.assertEqual(self.regulacion(), {
            'indice_referencia_min': '839.99', 'indice_referencia_max': '1153.53',
            'indice_referencia_fecha': '2026-10-01', 'renta_previa': 'con_renta',
            'ultima_renta': '900.00', 'ultima_renta_fin': '2025-06-30'})

    def test_no_rental_in_5_years_is_distinct_from_unknown(self):
        self.Regulacion.objects.create(oferta=self.alquiler, renta_previa='sin_renta')
        self.assertEqual(self.regulacion()['renta_previa'], 'sin_renta')
        self.assertIsNone(self.regulacion()['ultima_renta'])

    def test_a_property_without_our_history_can_still_declare_a_last_rent(self):
        """The rent came from another agency: nothing in our price log, and it is still stated."""
        from base.models import HistorialPrecio
        HistorialPrecio.objects.filter(inmueble=self.inm).delete()
        self.Regulacion.objects.create(
            oferta=self.alquiler, renta_previa='con_renta', ultima_renta='820',
            ultima_renta_fin=self.date(2026, 2, 1))
        self.assertEqual(self.regulacion()['ultima_renta'], '820.00')

    def test_price_log_does_not_feed_the_last_rent(self):
        from base.models import HistorialPrecio
        HistorialPrecio.objects.create(
            inmueble=self.inm, modalidad=self.mod['habitual'], fecha=self.date(2024, 1, 1), importe='700')
        self.alquiler.precio = '1100'
        self.alquiler.save()
        self.assertEqual(self.regulacion()['renta_previa'], 'desconocida')
        self.assertIsNone(self.regulacion()['ultima_renta'])

    def test_amount_and_end_date_only_with_a_rental(self):
        for estado, extra in (('con_renta', {}), ('sin_renta', {'ultima_renta': '1'}),
                              ('desconocida', {'ultima_renta_fin': self.date(2025, 1, 1)})):
            reg = self.Regulacion(oferta=self.alquiler, renta_previa=estado, **extra)
            with self.assertRaises(ValidationError, msg=estado):
                reg.full_clean()
            with self.assertRaises((IntegrityError, ValidationError), msg=estado), transaction.atomic():
                reg.save()
        self.assertEqual(self.Regulacion.objects.count(), 0)

    def test_database_rejects_inconsistent_rows_that_skip_the_model(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Regulacion.objects.bulk_create([self.Regulacion(oferta=self.alquiler, ultima_renta='5')])
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Regulacion.objects.bulk_create([self.Regulacion(oferta=self.alquiler, renta_previa='con_renta')])

    def test_reference_index_range_and_sign(self):
        reg = self.Regulacion(oferta=self.alquiler, indice_referencia_min=10, indice_referencia_max=5)
        with self.assertRaises(ValidationError):
            reg.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Regulacion.objects.bulk_create([reg])
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Regulacion.objects.bulk_create([self.Regulacion(oferta=self.alquiler, indice_referencia_max=-1)])
        self.Regulacion.objects.create(
            oferta=self.alquiler, indice_referencia_min=5, indice_referencia_max=5)

    def test_a_sale_offer_cannot_have_regulation(self):
        with self.assertRaises(ValidationError):
            self.Regulacion(oferta=self.venta).full_clean()
        with self.assertRaises(ValidationError):
            self.Regulacion.objects.create(oferta=self.venta)

    def test_one_record_per_offer_and_it_goes_with_the_offer(self):
        self.Regulacion.objects.create(oferta=self.alquiler)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Regulacion.objects.create(oferta=self.alquiler)
        self.alquiler.delete()
        self.assertEqual(self.Regulacion.objects.count(), 0)

    def test_listing_no_longer_has_the_regulatory_columns(self):
        names = {f.name for f in Inmueble._meta.get_fields()}
        for gone in ('ultima_renta', 'indice_referencia_min', 'indice_referencia_max',
                     'actualizacion_renta', 'situacion_5_anios'):
            self.assertNotIn(gone, names)

    def test_update_clause_is_a_condition_of_the_offer(self):
        Condiciones.objects.create(
            nombre='Habitual', modalidad=self.mod['habitual'], por_defecto=True, actualizacion_renta='IRAV')
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        habitual = [m for m in data['modalidades'] if m['codigo'] == 'habitual'][0]
        self.assertEqual(habitual['condiciones']['actualizacion_renta'], 'IRAV')
        self.assertNotIn('actualizacion_renta', data)

    def test_reads_regulation_in_a_constant_number_of_queries(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        self.Regulacion.objects.create(oferta=self.alquiler, renta_previa='sin_renta')
        with CaptureQueriesContext(connection) as pocas:
            self.client.get(f'/api/inmuebles/{self.inm.id}/')
        extra = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod['temporal'], precio='500')
        self.Regulacion.objects.create(oferta=extra, renta_previa='sin_renta')
        with CaptureQueriesContext(connection) as muchas:
            self.client.get(f'/api/inmuebles/{self.inm.id}/')
        self.assertEqual(len(pocas), len(muchas))


class ComprobarRegulacionAlquilerTests(ModalidadFixture):
    def setUp(self):
        super().setUp()
        from datetime import date, timedelta
        from django.utils import timezone
        from base.comprobaciones import pendientes_regulacion_alquiler
        from base.models import DeclaracionZonaTensionada, RegulacionAlquiler
        self.Regulacion = RegulacionAlquiler
        self.pendientes = pendientes_regulacion_alquiler
        self.hoy = timezone.localdate()
        self.timedelta = timedelta
        self.municipio = self.both.municipio
        # The shared fixture publishes a habitual rental (M2) in the same municipality: leave it out.
        Inmueble.objects.filter(pk=self.rent.pk).update(publicar_web=False)
        self.inm = inmueble(referencia='CR1', publicar_web=True)
        self.oferta = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod['habitual'], precio='1000')

    def tipos(self):
        return sorted(t for t, _ in self.pendientes())

    def declarar(self):
        from base.models import DeclaracionZonaTensionada
        DeclaracionZonaTensionada.objects.create(municipio=self.municipio, desde=self.date(2000, 1, 1))

    @property
    def date(self):
        from datetime import date
        return date

    def completa(self, **extra):
        datos = dict(indice_referencia_max='1100', renta_previa='sin_renta')
        datos.update(extra)
        return self.Regulacion.objects.create(oferta=self.oferta, **datos)

    def test_outside_a_stressed_zone_nothing_is_required(self):
        Municipio.objects.filter(pk=self.municipio.pk).update(declaraciones_cargadas=True)
        self.assertEqual(self.tipos(), [])

    def test_unknown_stressed_zone_is_reported(self):
        self.assertEqual(self.tipos(), ['zona_tensionada_desconocida'])

    def test_stressed_zone_without_data_reports_both_gaps(self):
        self.declarar()
        self.assertEqual(self.tipos(), ['indice_sin_rellenar', 'renta_previa_sin_confirmar'])

    def test_complete_data_passes_and_the_command_succeeds(self):
        from io import StringIO
        from django.core.management import call_command
        self.declarar()
        self.completa()
        self.assertEqual(self.tipos(), [])
        out = StringIO()
        call_command('comprobar_regulacion_alquiler', stdout=out)
        self.assertIn('complete', out.getvalue())

    def test_unconfirmed_status_is_reported(self):
        self.declarar()
        self.completa(renta_previa='desconocida')
        self.assertEqual(self.tipos(), ['renta_previa_sin_confirmar'])

    def test_last_rent_needs_its_end_date_and_must_be_within_5_years(self):
        self.declarar()
        reg = self.completa(renta_previa='con_renta', ultima_renta='900')
        self.assertEqual(self.tipos(), ['renta_previa_sin_fecha_fin'])
        reg.ultima_renta_fin = self.hoy.replace(year=self.hoy.year - 6)
        reg.save()
        self.assertEqual(self.tipos(), ['renta_previa_fuera_de_5_anios'])
        reg.ultima_renta_fin = self.hoy - self.timedelta(days=400)
        reg.save()
        self.assertEqual(self.tipos(), [])

    def test_only_published_open_habitual_offers_are_checked(self):
        self.declarar()
        self.inm.publicar_web = False
        self.inm.save()
        self.assertEqual(self.tipos(), [])
        self.inm.publicar_web = True
        self.inm.save()
        self.oferta.estado = 'cerrado'
        self.oferta.save()
        self.assertEqual(self.tipos(), [])
        self.oferta.estado = 'disponible'
        self.oferta.save()
        InmuebleModalidad.objects.filter(pk=self.oferta.pk).update(modalidad=self.mod['venta'])
        self.assertEqual(self.tipos(), [])

    def test_the_command_fails_and_lists_the_offender(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        self.declarar()
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command('comprobar_regulacion_alquiler', stdout=out)
        self.assertIn('CR1', out.getvalue())


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
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
        self.assertNotIn('historial_precios', data)
        # The log is our own asking prices: none of it reaches the API.
        self.assertNotIn('950', str(data['modalidades']))
        self.assertNotIn('900', str(data['modalidades']))
        self.assertNotIn('importe', str(data['modalidades']))
        self.assertNotIn('2023-01-01', str(data['modalidades']))

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
        url = f'/api/inmuebles/{inm.id}/'
        # No owner recorded: unknown, not "no".
        self.assertIsNone(self.client.get(url).json()['gran_tenedor'])
        ana = self.Propietario.objects.create(nombre='Ana')
        self.Link.objects.create(inmueble=inm, propietario=ana)
        self.assertIs(self.client.get(url).json()['gran_tenedor'], False)
        empresa = self.Propietario.objects.create(nombre='Empresa SL', gran_tenedor=True)
        self.Link.objects.create(inmueble=inm, propietario=empresa)
        self.assertIs(self.client.get(url).json()['gran_tenedor'], True)
        otro = inmueble(referencia='PR8', publicar_web=True)
        self.Link.objects.create(inmueble=otro, propietario=ana)
        self.assertIs(self.client.get(f'/api/inmuebles/{otro.id}/').json()['gran_tenedor'], False)

    def test_detail_reads_owners_in_one_query(self):
        inm = inmueble(referencia='PR9', publicar_web=True)
        for n in range(3):
            self.Link.objects.create(
                inmueble=inm, propietario=self.Propietario.objects.create(nombre=f'P{n}'))
        with CaptureQueriesContext(connection) as sin:
            self.client.get(f'/api/inmuebles/{inm.id}/')
        for n in range(3, 6):
            self.Link.objects.create(
                inmueble=inm, propietario=self.Propietario.objects.create(nombre=f'P{n}'))
        with CaptureQueriesContext(connection) as con:
            self.client.get(f'/api/inmuebles/{inm.id}/')
        self.assertEqual(len(sin), len(con))


class ZonaTensionadaTests(TestCase):
    def setUp(self):
        from base.models import DeclaracionZonaTensionada
        self.Declaracion = DeclaracionZonaTensionada
        self.mun = default_municipio()
        self.otro = Municipio.objects.create(
            provincia=self.mun.provincia, codigo_ine='08020', nombre='Badalona')
        # Both municipios have their declarations loaded, so no declaration means "not stressed".
        Municipio.objects.update(declaraciones_cargadas=True)

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
        url = lambda i: f'/api/inmuebles/{i.id}/'
        self.assertIs(self.client.get(url(inm)).json()['zona_tensionada'], False)
        self.Declaracion.objects.create(municipio=self.mun, desde=date(2000, 1, 1))
        self.assertIs(self.client.get(url(inm)).json()['zona_tensionada'], True)
        self.assertIs(self.client.get(url(otro)).json()['zona_tensionada'], False)

    def test_ended_declaration_no_longer_applies(self):
        self.Declaracion.objects.create(
            municipio=self.mun, desde=date(2000, 1, 1), hasta=date(2001, 1, 1))
        inm = inmueble(referencia='Z3', publicar_web=True)
        self.assertIs(self.client.get(f'/api/inmuebles/{inm.id}/').json()['zona_tensionada'], False)

    def test_unloaded_declarations_mean_unknown_not_false(self):
        Municipio.objects.filter(pk=self.otro.pk).update(declaraciones_cargadas=False)
        inm = inmueble(referencia='Z4', municipio=self.fresh(self.otro), publicar_web=True)
        url = f'/api/inmuebles/{inm.id}/'
        self.assertIsNone(self.client.get(url).json()['zona_tensionada'])
        self.assertIsNone(self.fresh(self.otro).zona_tensionada())
        # A declaration in force is a fact even when the municipality was not marked as loaded.
        self.Declaracion.objects.create(municipio=self.otro, desde=date(2000, 1, 1))
        self.assertIs(self.client.get(url).json()['zona_tensionada'], True)

    def test_loaded_municipality_without_declaration_is_false(self):
        self.assertIs(self.fresh(self.mun).zona_tensionada(), False)

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
            self.client.get(f'/api/inmuebles/{inm.id}/')
        for year in range(2002, 2008):
            self.Declaracion.objects.create(
                municipio=self.mun, desde=date(year, 1, 1), hasta=date(year, 6, 1))
        with CaptureQueriesContext(connection) as muchas:
            self.client.get(f'/api/inmuebles/{inm.id}/')
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
        return self.client.get(f'/api/inmuebles/{inm.id}/').json()['estado']

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

    def test_valuation_date_needs_an_amount(self):
        datos = self.Datos(inmueble=self.inm, fecha_tasacion=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            datos.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            datos.save()
        datos.tasacion_propietario = '1200'
        datos.save()

    def test_owner_valuation_cannot_be_negative(self):
        datos = self.Datos(inmueble=self.inm, tasacion_propietario='-1')
        with self.assertRaises(ValidationError):
            datos.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            datos.save()
        self.Datos.objects.create(inmueble=self.inm, tasacion_propietario='1200')

    def test_none_of_it_reaches_the_public_api(self):
        from base.models import AcuerdoAdministracion
        self.Datos.objects.create(inmueble=self.inm, tasacion_propietario='123456.78', fecha_tasacion=date(2026, 1, 1))
        AcuerdoAdministracion.objects.create(
            inmueble=self.inm, exclusiva=True, gestion_comercial=True, administracion=True)
        for url in (f'/api/inmuebles/{self.inm.id}/', '/api/inmuebles/'):
            body = self.client.get(url).content.decode()
            for secret in ('123456.78', 'tasacion', 'exclusiva', 'gestion_comercial', 'administracion',
                           'acuerdo'):
                self.assertNotIn(secret, body, (url, secret))


SIN_REGULACION = {
    'indice_referencia_min': None, 'indice_referencia_max': None, 'indice_referencia_fecha': None,
    'renta_previa': 'desconocida', 'ultima_renta': None, 'ultima_renta_fin': None,
}


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
        self.assertFalse(InmuebleModalidad.objects.filter(inmueble_id=self.both.id).exists())

    def test_unit_is_set_per_modalidad(self):
        data = {m['codigo']: m['unidad_precio'] for m in self.client.get('/api/modalidades/').json()}
        self.assertEqual(data, {'temporal': 'mensual', 'habitual': 'mensual', 'venta': 'total'})

    def test_api_returns_price_and_unit_per_modalidad(self):
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
        self.assertEqual(data['modalidades'], [
            {'codigo': 'temporal', 'nombre': 'Vivienda temporal', 'unidad_precio': 'mensual',
             'precio': '1200.00', 'mas_iva': False, 'tipo_iva': None, 'fecha_disponibilidad': HOY,
             'fianza_meses': None, 'fianza_total': None,
             'regulacion': SIN_REGULACION,
             'terminos': None, 'inclusiones': None, 'condiciones': None},
            {'codigo': 'venta', 'nombre': 'Venta', 'unidad_precio': 'total',
             'precio': '300000.00', 'mas_iva': False, 'tipo_iva': None, 'fecha_disponibilidad': HOY,
             'fianza_meses': None, 'fianza_total': None,
             'regulacion': None,
             'terminos': None, 'inclusiones': None, 'condiciones': None},
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
        url = f'/api/inmuebles/{self.inm.id}/'
        self.assertEqual(self.client.get(url).json()['n_plz_garaje'], 0)
        self.Plaza.objects.create(inmueble=self.inm, numero='12')
        self.Plaza.objects.create(inmueble=self.inm, numero='13', tipo='moto')
        data = self.client.get(url).json()
        self.assertEqual(data['n_plz_garaje'], 2)
        self.assertEqual([p['numero'] for p in data['plazas']], ['12', '13'])

    def test_public_plaza_fields_exclude_value_and_rent(self):
        self.Plaza.objects.create(inmueble=self.inm, numero='1', superficie='11.5', valor='9000', renta='50')
        plaza = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()['plazas'][0]
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
        parking = inmueble(referencia='PK3', tipo='parking', publicar_web=True)
        self.Plaza.objects.create(inmueble=parking)
        self.assertEqual(self.client.get(f'/api/inmuebles/{parking.id}/').json()['n_plz_garaje'], 1)


class HabitacionesTests(TestCase):
    def make(self, ref, dobles=None, individuales=0, suites=0, exteriores=0):
        from base.models import Distribucion
        inm = inmueble(referencia=ref, publicar_web=True)
        if dobles is not None:
            Distribucion.objects.create(
                inmueble=inm, dobles=dobles, individuales=individuales,
                suites=suites, exteriores=exteriores)
        return inm

    def test_column_is_gone_and_total_is_dobles_individuales(self):
        self.assertNotIn('n_habitaciones', {f.name for f in Inmueble._meta.get_fields() if f.concrete})
        inm = self.make('H1', dobles=2, individuales=1, suites=1, exteriores=3)
        self.assertEqual(Inmueble.objects.get(pk=inm.pk).n_habitaciones, 3)

    def test_suites_are_a_subset_of_the_bedrooms(self):
        from base.models import Distribucion
        inm = self.make('H9', dobles=2, individuales=1, suites=3)
        Distribucion.objects.filter(inmueble=inm).update(suites=3)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Distribucion.objects.filter(inmueble=inm).update(suites=4)

    def test_listing_without_dormitorios_is_unknown_not_zero(self):
        inm = self.make('H2')
        self.assertIsNone(Inmueble.objects.get(pk=inm.pk).n_habitaciones)
        self.assertIsNone(Inmueble.objects.con_habitaciones().get(pk=inm.pk).n_habitaciones)
        self.assertIsNone(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_habitaciones'])

    def test_empty_counts_are_unknown_and_zeros_are_confirmed(self):
        from base.models import Distribucion
        inm = self.make('H8')
        detail = lambda: self.client.get(f'/api/inmuebles/{inm.id}/').json()
        Distribucion.objects.create(inmueble=inm)  # row without data
        self.assertIsNone(detail()['n_habitaciones'])
        self.assertIsNone(Inmueble.objects.con_habitaciones().get(pk=inm.pk).n_habitaciones)
        Distribucion.objects.filter(inmueble=inm).update(dobles=0, individuales=0)
        self.assertEqual(detail()['n_habitaciones'], 0)
        self.assertEqual(Inmueble.objects.con_habitaciones().get(pk=inm.pk).n_habitaciones, 0)
        Distribucion.objects.filter(inmueble=inm).update(dobles=2, individuales=None)  # one side unknown
        self.assertEqual(detail()['n_habitaciones'], 2)
        self.assertEqual(Inmueble.objects.con_habitaciones().get(pk=inm.pk).n_habitaciones, 2)

    def test_api_returns_the_computed_number_in_list_and_detail(self):
        inm = self.make('H3', dobles=1, individuales=2)
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_habitaciones'], 3)
        listed = self.client.get('/api/inmuebles/').json()['inmuebles'][0]
        self.assertEqual(listed['n_habitaciones'], 3)

    def test_filter_matches_the_computed_number_only(self):
        self.make('H4', dobles=2, individuales=1)
        self.make('H5', dobles=2, individuales=1, suites=1, exteriores=3)
        self.make('H6', dobles=1)
        self.make('H7')
        refs = lambda n: sorted(i['referencia'] for i in self.client.get(f'/api/inmuebles/?habitaciones={n}').json()['inmuebles'])
        self.assertEqual(refs(3), ['H4', 'H5'])
        self.assertEqual(refs(1), ['H6'])
        self.assertEqual(len(self.client.get('/api/inmuebles/').json()['inmuebles']), 4)

    def test_changing_dormitorios_changes_the_number(self):
        inm = self.make('H8', dobles=1)
        inm.distribucion.dobles = 3
        inm.distribucion.save()
        self.assertEqual(self.client.get(f'/api/inmuebles/{inm.id}/').json()['n_habitaciones'], 3)


class TextToNumbersTests(TestCase):
    def test_api_returns_numbers_with_units_in_the_name(self):
        from base.models import Caracteristicas, Entorno
        inm = inmueble(referencia='N1', publicar_web=True)
        Caracteristicas.objects.create(inmueble=inm, altura_real_m='2.70')
        Entorno.objects.create(inmueble=inm, distancia_playa_m=800)
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual(data['caracteristicas']['altura_real_m'], '2.70')
        self.assertEqual(data['entorno']['distancia_playa_m'], 800)
        self.assertNotIn('altura_real', data['caracteristicas'])
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
        zones = lambda i: tuple(self.client.get(f'/api/inmuebles/{i.id}/').json()[k] for k in ('zona', 'zona_ref'))
        self.assertEqual(zones(with_barrio), ('El Raval', 'Ciutat Vella'))
        self.assertEqual(zones(only_district), ('Ciutat Vella', 'Ciutat Vella'))
        self.assertEqual(zones(nowhere), (None, None))
        listed = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual(listed['Z1']['zona'], 'El Raval')


class DatabaseRulesTests(TestCase):
    def test_negative_amounts_are_rejected_by_validators_and_the_database(self):
        for field in ('sup_util', 'sup_construida', 'gtos_comunidad', 'ibi'):
            with self.assertRaises(ValidationError, msg=field):
                Inmueble(referencia='R', **{field: -1}).full_clean(exclude=['municipio'])
            with self.assertRaises(IntegrityError, msg=field), transaction.atomic():
                inmueble(referencia='R', **{field: -1})

    def test_counts_cannot_be_negative(self):
        from base.models import Distribucion
        inm = inmueble(referencia='R4')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Distribucion.objects.create(inmueble=inm, dobles=-1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Distribucion.objects.create(inmueble=inm, capacidad_personas=-2)


class DateAndSurfaceTypesTests(TestCase):
    def test_dates_are_dates(self):
        for name in ('fecha_alta', 'fecha_baja', 'fecha_entrega'):
            self.assertEqual(Inmueble._meta.get_field(name).get_internal_type(), 'DateField')
        self.assertEqual(InmuebleModalidad._meta.get_field('fecha_disponibilidad').get_internal_type(), 'DateField')

    def test_surfaces_allow_large_premises(self):
        inm = inmueble(referencia='T3', sup_construida='999999.99', sup_util='12345.67')
        inm.refresh_from_db()
        self.assertEqual((str(inm.sup_construida), str(inm.sup_util)), ('999999.99', '12345.67'))


class CoherenceChecksTests(TestCase):
    def test_usable_area_cannot_exceed_built_area(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            inmueble(referencia='C1', sup_construida='50', sup_util='60')
        with self.assertRaises(ValidationError) as ctx:
            Inmueble(referencia='C1', sup_construida='50', sup_util='60').full_clean(exclude=['municipio'])
        self.assertIn('superficie útil', str(ctx.exception))
        inmueble(referencia='C2', sup_construida='50', sup_util='50')
        inmueble(referencia='C3', sup_util='60')  # one of the two unknown: nothing to compare
        inmueble(referencia='C4', sup_construida='50')

    def test_removal_date_cannot_precede_the_creation_date(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            inmueble(referencia='C5', fecha_alta=date(2025, 5, 1), fecha_baja=date(2025, 4, 30))
        inmueble(referencia='C6', fecha_alta=date(2025, 5, 1), fecha_baja=date(2025, 5, 1))
        inmueble(referencia='C7', fecha_baja=date(2025, 4, 30))

    def test_exterior_bedrooms_are_a_subset_of_the_bedrooms(self):
        from base.models import Distribucion
        inm = inmueble(referencia='C8')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Distribucion.objects.create(inmueble=inm, dobles=1, individuales=1, exteriores=3)
        Distribucion.objects.create(inmueble=inm, dobles=1, individuales=1, exteriores=2)


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
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual((data['titulo'], data['descripciones']), ('', {}))

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
            f'/api/inmuebles/{self.inm.id}/reservas/',
            {'nombre': 'Ana', 'email': 'ana@example.com', 'telefono': '600', 'acepta_aviso_legal': True},
            content_type='application/json')

    def test_new_request_is_pending_and_estado_cannot_be_set_by_the_client(self):
        from base.models import SolicitudReserva
        response = self.client.post(
            f'/api/inmuebles/{self.inm.id}/reservas/',
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
        return InmuebleAdminForm(data={k: v.id for k, v in data.items()})

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
        self.assertEqual(names(get(tipo='distritos', municipio=self.mun.id)), ['Ciutat Vella', 'Eixample'])
        self.assertEqual(names(get(tipo='barrios', municipio=self.mun.id, distrito=self.dis2.id)), ['Dreta'])
        self.assertEqual(names(get(tipo='barrios', municipio=self.mun.id)), ['El Raval', 'Dreta'])
        self.assertEqual(get(tipo='x').status_code, 404)
        self.client.logout()
        self.assertEqual(get(tipo='distritos', municipio=self.mun.id).status_code, 302)

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
        RegistroLegal.objects.create(inmueble=self.inm, tipo='nrua', numero='ESFCNT0001')
        RegistroLegal.objects.create(
            inmueble=self.inm, tipo='cedula_habitabilidad', numero='CHB0333*******',
            organismo='Generalitat de Catalunya')
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual(
            [(r['tipo'], r['estado'], r['numero']) for r in data['registros_legales']],
            [('cedula_habitabilidad', 'vigente', 'CHB0333*******'), ('nrua', 'vigente', 'ESFCNT0001')],
        )
        self.assertNotIn('cedula', data)

    def test_one_registry_per_type_except_otro(self):
        RegistroLegal.objects.create(inmueble=self.inm, tipo='nrua', numero='1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegistroLegal.objects.create(inmueble=self.inm, tipo='nrua', numero='2')
        RegistroLegal.objects.create(inmueble=self.inm, tipo='otro', numero='a')
        RegistroLegal.objects.create(inmueble=self.inm, tipo='otro', numero='b')
        other = inmueble(referencia='R2')
        RegistroLegal.objects.create(inmueble=other, tipo='nrua', numero='1')

    def test_registries_go_with_the_listing(self):
        RegistroLegal.objects.create(inmueble=self.inm, tipo='nrua', numero='1')
        self.inm.delete()
        self.assertEqual(RegistroLegal.objects.count(), 0)

    def test_energy_certificate_and_aicat_are_not_registry_types(self):
        self.assertNotIn('certificado_energetico', dict(RegistroLegal.TIPOS))
        self.assertNotIn('aicat', dict(RegistroLegal.TIPOS))

    def test_a_registry_in_process_is_public_and_has_no_number(self):
        RegistroLegal.objects.create(inmueble=self.inm, tipo='nrua', estado='en_tramite')
        RegistroLegal.objects.create(inmueble=self.inm, tipo='licencia_turistica', estado='no_aplica')
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual(
            {r['tipo']: (r['estado'], r['numero']) for r in data['registros_legales']},
            {'nrua': ('en_tramite', ''), 'licencia_turistica': ('no_aplica', '')})

    def test_only_a_valid_registry_can_carry_a_number(self):
        for estado in ('en_tramite', 'no_aplica'):
            with self.assertRaises(IntegrityError), transaction.atomic():
                RegistroLegal.objects.create(inmueble=self.inm, tipo='nrua', estado=estado, numero='123')

    def test_a_valid_registry_may_omit_the_number(self):
        registro = RegistroLegal.objects.create(inmueble=self.inm, tipo='licencia_turistica')
        self.assertEqual((registro.estado, registro.numero), ('vigente', ''))


class AgenciaTests(TestCase):
    def test_the_agency_numbers_are_public_with_the_listing(self):
        agencia = Agencia.objects.create(nombre='Loca Barcelona', aicat='11525', numero_api='A13529',
                                         email='contact@locabarcelona.com')
        inm = inmueble(referencia='AG1', publicar_web=True, agencia=agencia)
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual(data['agencia'], {'nombre': 'Loca Barcelona', 'aicat': '11525', 'numero_api': 'A13529'})
        self.assertNotIn('contact@locabarcelona.com', self.client.get(f'/api/inmuebles/{inm.id}/').content.decode())

    def test_a_listing_without_agency_returns_null(self):
        inm = inmueble(referencia='AG2', publicar_web=True)
        self.assertIsNone(self.client.get(f'/api/inmuebles/{inm.id}/').json()['agencia'])

    def test_many_listings_share_one_agency(self):
        agencia = Agencia.objects.create(nombre='ATBarcelona', aicat='5205')
        inmueble(referencia='AG3', agencia=agencia)
        inmueble(referencia='AG4', agencia=agencia)
        self.assertEqual(agencia.inmuebles.count(), 2)

    def test_an_agency_in_use_cannot_be_deleted(self):
        agencia = Agencia.objects.create(nombre='ATBarcelona', aicat='5205')
        inmueble(referencia='AG5', agencia=agencia)
        with self.assertRaises(ProtectedError):
            agencia.delete()

    def test_filled_registry_numbers_are_unique_and_empty_ones_may_repeat(self):
        Agencia.objects.create(nombre='A', aicat='1', numero_api='X1')
        Agencia.objects.create(nombre='B')
        Agencia.objects.create(nombre='C')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Agencia.objects.create(nombre='D', aicat='1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Agencia.objects.create(nombre='E', numero_api='X1')


class CertificadoEnergeticoTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='CE1', publicar_web=True)

    def detalle(self):
        return self.client.get(f'/api/inmuebles/{self.inm.id}/').json()

    def test_listing_without_certificate_returns_null(self):
        self.assertIsNone(self.detalle()['certificado_energetico'])

    def test_certificate_is_public_and_nested(self):
        CertificadoEnergetico.objects.create(
            inmueble=self.inm, numero='QWVL2082D', eficiencia='D', consumo_energetico='71', emisiones_co2='36',
            fecha_emision=date(2024, 1, 1), fecha_vencimiento=date(2034, 1, 1))
        data = self.detalle()
        self.assertEqual(data['certificado_energetico'], {
            'numero': 'QWVL2082D', 'eficiencia': 'D', 'consumo_energetico': '71.00', 'emisiones_co2': '36.00',
            'fecha_emision': '2024-01-01', 'fecha_vencimiento': '2034-01-01'})
        for old in ('eficiencia', 'nombre_eficiencia', 'consumo_energetico', 'emisiones_co2'):
            self.assertNotIn(old, data)

    def test_only_letters_a_to_g_and_one_certificate_per_listing(self):
        with self.assertRaises(ValidationError):
            CertificadoEnergetico(inmueble=self.inm, eficiencia='H').full_clean()
        CertificadoEnergetico.objects.create(inmueble=self.inm, eficiencia='G')
        with self.assertRaises(IntegrityError), transaction.atomic():
            CertificadoEnergetico.objects.create(inmueble=self.inm)

    def test_amounts_cannot_be_negative_and_it_cannot_expire_before_issue(self):
        for campo in ('consumo_energetico', 'emisiones_co2'):
            with self.assertRaises(ValidationError, msg=campo):
                CertificadoEnergetico(inmueble=self.inm, **{campo: -1}).full_clean()
            with self.assertRaises(IntegrityError, msg=campo), transaction.atomic():
                CertificadoEnergetico.objects.create(inmueble=self.inm, **{campo: -1})
        malo = CertificadoEnergetico(
            inmueble=self.inm, fecha_emision=date(2024, 1, 1), fecha_vencimiento=date(2023, 1, 1))
        with self.assertRaises(ValidationError):
            malo.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            malo.save()


class AcuerdoAdministracionTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='AA1', publicar_web=True)

    def test_flags_default_to_no_and_a_listing_keeps_its_history(self):
        a = AcuerdoAdministracion.objects.create(
            inmueble=self.inm, fecha_firma=date(2023, 1, 1), fecha_fin=date(2024, 1, 1), exclusiva=True)
        self.assertEqual((a.gestion_comercial, a.administracion), (False, False))
        AcuerdoAdministracion.objects.create(inmueble=self.inm, fecha_firma=date(2024, 1, 2), administracion=True)
        self.assertEqual(
            [x.fecha_firma for x in self.inm.acuerdos_administracion.all()], [date(2024, 1, 2), date(2023, 1, 1)])

    def test_it_cannot_end_before_it_is_signed(self):
        malo = AcuerdoAdministracion(inmueble=self.inm, fecha_firma=date(2024, 1, 1), fecha_fin=date(2023, 1, 1))
        with self.assertRaises(ValidationError):
            malo.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            malo.save()


class PropietarioNifTests(TestCase):
    def test_nif_is_unique_when_set_and_blank_may_repeat(self):
        Propietario.objects.create(nombre='A', nif='X123')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Propietario.objects.create(nombre='B', nif='X123')
        with self.assertRaises(ValidationError):
            Propietario(nombre='C', nif='X123').validate_constraints()
        Propietario.objects.create(nombre='D')
        Propietario.objects.create(nombre='E')


class AuditoriaDeOfertasTests(ModalidadFixture):
    def test_admin_fills_who_changed_offers_and_conditions(self):
        from django.contrib.auth import get_user_model
        usuario = get_user_model().objects.create_superuser('staff', 's@example.com', 'pw')
        self.client.force_login(usuario)
        condiciones = Condiciones.objects.create(nombre='Alquiler', modalidad=self.mod['habitual'])
        self.assertIsNone(condiciones.created_by)
        respuesta = self.client.post(
            f'/admin/base/condiciones/{condiciones.pk}/change/',
            {'nombre': 'Alquiler 2', 'modalidad': self.mod['habitual'].pk, 'honorarios': '', 'itp': '',
             'incluido': '', 'no_incluido': '', 'fianza': '', 'pago_adelantado': '', 'suministros': '',
             'actualizacion_renta': '', 'limpieza_final': '', 'requisitos': '', 'notaria': '', 'registro': '',
             'gestoria': '', 'honorarios_comprador': ''})
        self.assertEqual(respuesta.status_code, 302)
        condiciones.refresh_from_db()
        self.assertEqual((condiciones.nombre, condiciones.updated_by), ('Alquiler 2', usuario))
        self.assertIsNone(condiciones.created_by)

    def test_offers_have_audit_columns_that_the_api_hides(self):
        oferta = self.rent.precios.get()
        self.assertIsNotNone(oferta.created_at)
        body = self.client.get(f'/api/inmuebles/{self.rent.id}/').content.decode()
        self.assertNotIn('created_at', body)
        self.assertNotIn('updated_by', body)


class OcultarDireccionTests(TestCase):
    def setUp(self):
        self.inm = inmueble(
            referencia='H1', publicar_web=True, direccion='Carrer de la Cera 12',
            direccion_short='Cera 12', dir_descripcion='Piso 3', codigo_postal='08001')

    def test_address_is_returned_by_default(self):
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual((data['direccion'], data['dir_descripcion']), ('Carrer de la Cera 12', 'Piso 3'))
        self.assertFalse(data['ocultar_direccion'])

    def test_hidden_address_is_blank_in_detail_and_list_but_zone_stays(self):
        self.inm.ocultar_direccion = True
        self.inm.save()
        detail = self.client.get(f'/api/inmuebles/{self.inm.id}/')
        data = detail.json()
        for name in ('direccion', 'direccion_short', 'dir_descripcion'):
            self.assertEqual(data[name], '', name)
        self.assertEqual(data['codigo_postal'], '08001')
        self.assertNotIn('Cera', detail.content.decode())
        listing = self.client.get('/api/inmuebles/')
        self.assertNotIn('Cera', listing.content.decode())
        self.assertEqual(listing.json()['inmuebles'][0]['dir_descripcion'], '')


class FianzaTests(ModalidadFixture):
    def setUp(self):
        super().setUp()
        self.oferta = self.both.precios.get(modalidad=self.mod['temporal'])
        self.venta = self.both.precios.get(modalidad=self.mod['venta'])

    def modalidades(self):
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
        return {m['codigo']: m for m in data['modalidades']}

    def test_the_deposit_amount_is_the_price_times_the_months(self):
        self.oferta.fianza_meses = 3
        self.oferta.precio = '1900'
        self.oferta.save()
        temporal = self.modalidades()['temporal']
        self.assertEqual((temporal['fianza_meses'], temporal['fianza_total']), (3, '5700.00'))

    def test_without_months_there_is_no_deposit_amount(self):
        temporal = self.modalidades()['temporal']
        self.assertEqual((temporal['fianza_meses'], temporal['fianza_total']), (None, None))

    def test_deposit_is_computed_on_the_net_price(self):
        self.oferta.fianza_meses, self.oferta.tipo_iva = 2, '21'
        self.oferta.save()
        self.assertEqual(self.modalidades()['temporal']['fianza_total'], '2400.00')

    def test_only_a_rental_has_a_deposit(self):
        self.venta.fianza_meses = 2
        with self.assertRaises(ValidationError):
            self.venta.full_clean()
        with self.assertRaises(ValidationError):
            self.venta.save()
        self.assertIsNone(self.modalidades()['venta']['fianza_meses'])

    def test_months_are_between_one_and_twelve(self):
        for malo in (0, 13):
            self.oferta.fianza_meses = malo
            with self.assertRaises(ValidationError):
                self.oferta.full_clean()
            with self.assertRaises(IntegrityError), transaction.atomic():
                InmuebleModalidad.objects.filter(pk=self.oferta.pk).update(fianza_meses=malo)
        self.oferta.fianza_meses = 12
        self.oferta.full_clean()


class CondicionesDeVentaTests(ModalidadFixture):
    def condiciones(self, modalidad, **campos):
        return Condiciones(nombre=f'C-{modalidad}', modalidad=self.mod[modalidad], **campos)

    def test_the_itp_rate_and_the_sellers_fee_are_public_in_a_sale(self):
        Condiciones.objects.create(
            nombre='Compraventa', modalidad=self.mod['venta'], por_defecto=True,
            itp_porcentaje='10', honorarios_incluidos_en_precio=True)
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
        sale = {m['codigo']: m for m in data['modalidades']}['venta']['condiciones']
        self.assertEqual((sale['itp_porcentaje'], sale['honorarios_incluidos_en_precio']), ('10.00', True))

    def test_a_rental_keeps_its_itp_in_the_text(self):
        self.condiciones('temporal', itp='0,5 % del alquiler del periodo').full_clean()
        for campos in ({'itp_porcentaje': '0.5'}, {'honorarios_incluidos_en_precio': True}):
            with self.assertRaises(ValidationError):
                self.condiciones('temporal', **campos).full_clean()
            with self.assertRaises(ValidationError):
                self.condiciones('temporal', **campos).save()

    def test_the_rate_is_a_percentage(self):
        for malo in ('-1', '100.01'):
            with self.assertRaises(ValidationError):
                self.condiciones('venta', itp_porcentaje=malo).full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Condiciones.objects.bulk_create([self.condiciones('venta', itp_porcentaje='101')])
        self.condiciones('venta', itp_porcentaje='0').full_clean()


class IndiceDeReferenciaUnicoTests(ModalidadFixture):
    def test_a_single_index_value_needs_no_minimum(self):
        from base.models import RegulacionAlquiler
        oferta = self.both.precios.get(modalidad=self.mod['temporal'])
        regulacion = RegulacionAlquiler(oferta=oferta, indice_referencia_max='1900', renta_previa='sin_renta')
        regulacion.full_clean()
        regulacion.save()
        temporal = {m['codigo']: m for m in
                    self.client.get(f'/api/inmuebles/{self.both.id}/').json()['modalidades']}['temporal']
        self.assertEqual(
            (temporal['regulacion']['indice_referencia_min'], temporal['regulacion']['indice_referencia_max']),
            (None, '1900.00'))


class CamposDeLocabarcelonaTests(ModalidadFixture):
    """Fields added after comparing the Locabarcelona pages (ADR 0021)."""

    def detalle(self):
        return self.client.get(f'/api/inmuebles/{self.both.id}/').json()

    def test_half_baths_do_not_add_to_the_bathrooms(self):
        from base.models import Distribucion
        Distribucion.objects.create(inmueble=self.both, dobles=2, banios=1, aseos=1)
        data = self.detalle()
        self.assertEqual((data['n_banios'], data['distribucion']['aseos']), (1, 1))
        sin = inmueble(referencia='M9', publicar_web=True)
        Distribucion.objects.create(inmueble=sin, dobles=1)
        self.assertIsNone(self.client.get(f'/api/inmuebles/{sin.id}/').json()['distribucion']['aseos'])

    def test_patio_and_porch_are_extra_spaces(self):
        from base.models import OtrosEspacios
        OtrosEspacios.objects.create(inmueble=self.both, patio=True)
        espacios = self.detalle()['otros_espacios']
        self.assertEqual((espacios['patio'], espacios['porche']), (True, False))

    def test_internet_speed_needs_internet(self):
        from base.models import Instalaciones
        Instalaciones(inmueble=self.both, internet=True, internet_velocidad_mbps=300).full_clean()
        with self.assertRaises(ValidationError):
            Instalaciones(inmueble=self.both, internet=False, internet_velocidad_mbps=300).full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Instalaciones.objects.create(inmueble=self.both, internet=False, internet_velocidad_mbps=300)
        with self.assertRaises(ValidationError):
            Instalaciones(inmueble=self.both, internet=True, internet_velocidad_mbps=0).full_clean()
        Instalaciones.objects.create(inmueble=self.both, internet=True, internet_velocidad_mbps=300)
        self.assertEqual(self.detalle()['instalaciones']['internet_velocidad_mbps'], 300)

    def test_short_let_equipment_is_public(self):
        from base.models import Dotacion
        Dotacion.objects.create(inmueble=self.both, cafetera=True, secador_pelo=True, sofa_cama=True)
        dotacion = self.detalle()['dotacion']
        self.assertTrue(dotacion['cafetera'] and dotacion['secador_pelo'] and dotacion['sofa_cama'])
        self.assertFalse(dotacion['plancha'] or dotacion['kit_limpieza'] or dotacion['papel_higienico'])

    def test_smoking_and_seasonal_purpose_are_terms_of_the_offer(self):
        from base.models import TerminosAlquiler
        temporal = self.both.precios.get(modalidad=self.mod['temporal'])
        TerminosAlquiler.objects.create(oferta=temporal, acepta_fumadores=True, uso_temporada='trabajo')
        terminos = self.detalle()['modalidades'][0]['terminos']
        self.assertEqual((terminos['acepta_fumadores'], terminos['uso_temporada']), (True, 'trabajo'))

    def test_the_seasonal_purpose_belongs_to_temporary_offers_and_a_closed_list(self):
        from base.models import TerminosAlquiler
        habitual = InmuebleModalidad.objects.create(inmueble=self.both, modalidad=self.mod['habitual'], precio=900)
        with self.assertRaises(ValidationError):
            TerminosAlquiler(oferta=habitual, uso_temporada='estudios').full_clean()
        with self.assertRaises(ValidationError):
            TerminosAlquiler(oferta=habitual, uso_temporada='estudios').save()
        TerminosAlquiler(oferta=habitual, acepta_fumadores=True).full_clean()
        temporal = self.both.precios.get(modalidad=self.mod['temporal'])
        with self.assertRaises(ValidationError):
            TerminosAlquiler(oferta=temporal, uso_temporada='vacaciones').full_clean()

    def test_photo_tags_and_description_languages(self):
        from base.models import ImageInmueble
        tipos = dict(ImageInmueble.TIPOS)
        self.assertTrue({'piscina', 'detalles'} <= set(tipos))
        for idioma in ('fr', 'it'):
            DescripcionInmueble(inmueble=self.both, idioma=idioma, texto='x').full_clean()
        DescripcionInmueble.objects.create(inmueble=self.both, idioma='it', texto='Ciao')
        self.assertEqual(self.detalle()['descripciones'], {'it': 'Ciao'})


class PanelDeAdministracionTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.client.force_login(get_user_model().objects.create_superuser('admin', 'a@example.com', 'x'))

    def secciones(self):
        response = self.client.get('/admin/')
        return {a['name']: [m['object_name'] for m in a['models']] for a in response.context['app_list']}

    def test_the_index_splits_the_base_app_into_sections(self):
        secciones = self.secciones()
        self.assertEqual(secciones['Inmuebles'], ['Inmueble', 'ImageInmueble', 'Distribucion'])
        self.assertEqual(secciones['Ofertas y condiciones'], ['InmuebleModalidad', 'Modalidad', 'Condiciones'])
        self.assertEqual(secciones['Agencia y propietarios'], ['Agencia', 'Propietario'])
        self.assertEqual(secciones['Solicitudes'], ['SolicitudReserva'])
        self.assertIn('Municipio', secciones['Ubicación'])
        self.assertNotIn('Base', secciones)

    def test_every_registered_model_has_a_section(self):
        """A new admin model must be added to `SECCIONES`; otherwise it lands in "Otros"."""
        self.assertNotIn('Otros', self.secciones())

    def test_other_apps_are_left_alone(self):
        self.assertIn(['Group', 'User'], self.secciones().values())

    def test_the_app_page_lists_the_sections(self):
        response = self.client.get('/admin/base/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ofertas y condiciones')

    def test_listing_form_groups_every_field_and_the_pages_open(self):
        from django.contrib import admin
        from base.admin import InmuebleAdminForm
        model_admin = admin.site._registry[Inmueble]
        agrupados = [c for _, opciones in model_admin.fieldsets for f in opciones['fields']
                     for c in (f if isinstance(f, tuple) else (f,))]
        # The two many-to-many fields go through link tables, which the admin edits as inlines.
        formulario = set(InmuebleAdminForm().fields) - {'modalidades', 'propietarios'}
        self.assertEqual(sorted(agrupados), sorted(formulario))
        self.assertEqual(len(agrupados), len(set(agrupados)))
        inm = inmueble(referencia='AD1')
        self.assertEqual(self.client.get('/admin/base/inmueble/add/').status_code, 200)
        response = self.client.get(f'/admin/base/inmueble/{inm.id}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Identificación')

    def test_detail_tables_are_collapsed_and_offers_stay_open(self):
        from django.contrib import admin
        inlines = {i.model.__name__: i for i in admin.site._registry[Inmueble].inlines}
        for nombre in ('Distribucion', 'Dotacion', 'Instalaciones', 'Caracteristicas', 'DatosInternos'):
            self.assertIn('collapse', inlines[nombre].classes, nombre)
        for nombre in ('InmuebleModalidad', 'ImageInmueble', 'RegistroLegal'):
            self.assertNotIn('collapse', tuple(getattr(inlines[nombre], 'classes', None) or ()), nombre)


class IdentificadoresUuidTests(ModalidadFixture):
    """Listings, offers and requests have UUIDv7 keys; the rest of the models keep integers (ADR 0022)."""

    def test_listing_offer_and_request_keys_are_uuid_v7(self):
        from uuid import UUID
        from base.models import SolicitudReserva
        solicitud = SolicitudReserva.objects.create(
            inmueble=self.both, referencia='M1', nombre='Ana', email='a@example.com', telefono='600000000',
            acepta_aviso_legal=True)
        oferta = self.both.precios.first()
        for objeto in (self.both, oferta, solicitud):
            self.assertIsInstance(objeto.pk, UUID)
            self.assertEqual(objeto.pk.version, 7)

    def test_keys_are_created_before_the_first_save_and_follow_creation_order(self):
        nuevo = Inmueble(referencia='U1', municipio=self.both.municipio)
        self.assertIsNotNone(nuevo.pk)
        primero, segundo = inmueble(referencia='U2'), inmueble(referencia='U3')
        self.assertLess(primero.pk, segundo.pk)

    def test_the_other_models_keep_integer_keys(self):
        from base.models import Condiciones, ImageInmueble, Municipio
        for modelo in (Municipio, Condiciones, ImageInmueble, Modalidad, RegistroLegal):
            self.assertEqual(modelo._meta.pk.get_internal_type() in ('AutoField', 'BigAutoField'), True, modelo)

    def test_the_api_uses_the_uuid_as_a_string_id(self):
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
        self.assertEqual(data['id'], str(self.both.id))
        listed = {i['referencia']: i['id'] for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual(listed['M1'], str(self.both.id))

    def test_only_a_uuid_addresses_a_listing(self):
        self.assertEqual(self.client.get('/api/inmuebles/1/').status_code, 404)
        self.assertEqual(self.client.get('/api/inmuebles/abc/').status_code, 404)
        self.assertEqual(self.client.get('/api/inmuebles/00000000-0000-7000-8000-000000000000/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/inmuebles/{self.hidden.id}/').status_code, 404)  # unpublished
        respuesta = self.client.post(
            f'/api/inmuebles/{self.both.id}/reservas/',
            {'nombre': 'Ana', 'email': 'a@example.com', 'telefono': '600000000', 'acepta_aviso_legal': True},
            content_type='application/json')
        self.assertEqual(respuesta.status_code, 201)

    def test_the_price_log_gets_one_row_per_change_with_a_uuid_key(self):
        from base.models import HistorialPrecio
        oferta = self.both.precios.get(modalidad=self.mod['temporal'])
        self.assertEqual(HistorialPrecio.objects.filter(inmueble=self.both, modalidad=oferta.modalidad).count(), 1)
        oferta.precio = 1300
        oferta.save()
        self.assertEqual(
            list(HistorialPrecio.objects.filter(inmueble=self.both, modalidad=oferta.modalidad)
                 .values_list('importe', flat=True)), [1300])  # same day: the day's row is replaced


class CoordenadasOcultasTests(TestCase):
    def setUp(self):
        self.inm = inmueble(
            referencia='H2', publicar_web=True, direccion='Carrer de la Cera 12',
            geo_latitude=41.380896, geo_longitude=2.168742)

    def coords(self):
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        return data['geo_latitude'], data['geo_longitude']

    def test_exact_point_is_returned_when_the_address_is_shown(self):
        self.assertEqual(self.coords(), (41.380896, 2.168742))

    def test_hidden_address_snaps_the_point_to_a_grid_cell(self):
        self.inm.ocultar_direccion = True
        self.inm.save()
        lat, lon = self.coords()
        self.assertEqual((lat, lon), (41.38, 2.17))
        self.assertLessEqual(abs(lat - 41.380896), 0.0025 + 1e-9)
        self.assertLessEqual(abs(lon - 2.168742), 0.0025 + 1e-9)
        self.assertNotIn('41.380896', self.client.get(f'/api/inmuebles/{self.inm.id}/').content.decode())

    def test_nearby_points_share_a_cell_and_a_missing_point_stays_missing(self):
        self.inm.ocultar_direccion = True
        self.inm.save()
        other = inmueble(referencia='H3', publicar_web=True, ocultar_direccion=True,
                         geo_latitude=41.3821, geo_longitude=2.1700)
        data = self.client.get(f'/api/inmuebles/{other.id}/').json()
        self.assertEqual((data['geo_latitude'], data['geo_longitude']), (41.38, 2.17))
        sin = inmueble(referencia='H4', publicar_web=True, ocultar_direccion=True)
        data = self.client.get(f'/api/inmuebles/{sin.id}/').json()
        self.assertEqual((data['geo_latitude'], data['geo_longitude']), (None, None))


class TerminosAlquilerTests(ModalidadFixture):
    """Stay limits and pets are terms of a rental offer."""

    def setUp(self):
        super().setUp()
        self.oferta = InmuebleModalidad.objects.get(inmueble=self.both, modalidad=self.mod['temporal'])
        self.venta = InmuebleModalidad.objects.get(inmueble=self.both, modalidad=self.mod['venta'])

    def terminos(self, **fields):
        from base.models import TerminosAlquiler
        return TerminosAlquiler(oferta=self.oferta, **fields)

    def test_limits_keep_their_unit_and_default_to_months(self):
        from base.models import TerminosAlquiler
        TerminosAlquiler.objects.create(
            oferta=self.oferta, estancia_minima=32, estancia_minima_unidad='dias',
            estancia_maxima=5, acepta_animales=True)
        modalidades = self.client.get(f'/api/inmuebles/{self.both.id}/').json()['modalidades']
        self.assertEqual(modalidades[0]['terminos'], {
            'acepta_animales': True, 'acepta_fumadores': False, 'uso_temporada': '',
            'estancia_minima': 32, 'estancia_minima_unidad': 'dias',
            'estancia_maxima': 5, 'estancia_maxima_unidad': 'meses'})
        self.assertIsNone(modalidades[1]['terminos'])  # the sale

    def test_each_offer_of_a_listing_has_its_own_terms(self):
        from base.models import TerminosAlquiler
        habitual = InmuebleModalidad.objects.create(inmueble=self.both, modalidad=self.mod['habitual'], precio=1000)
        TerminosAlquiler.objects.create(oferta=self.oferta, estancia_maxima=11)
        TerminosAlquiler.objects.create(oferta=habitual, estancia_minima=5, estancia_minima_unidad='anios')
        por_codigo = {m['codigo']: m['terminos'] for m in
                      self.client.get(f'/api/inmuebles/{self.both.id}/').json()['modalidades']}
        self.assertEqual((por_codigo['temporal']['estancia_maxima'], por_codigo['habitual']['estancia_minima']), (11, 5))
        self.assertIsNone(por_codigo['temporal']['estancia_minima'])

    def test_minimum_cannot_exceed_maximum_whatever_the_units(self):
        with self.assertRaises(ValidationError):
            self.terminos(estancia_minima=2, estancia_minima_unidad='anios',
                          estancia_maxima=18, estancia_maxima_unidad='meses').full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.terminos(estancia_minima=2, estancia_minima_unidad='anios',
                          estancia_maxima=18, estancia_maxima_unidad='meses').save()
        # 32 days is below 5 months, and a year equals 12 months.
        self.terminos(estancia_minima=32, estancia_minima_unidad='dias', estancia_maxima=5).full_clean()
        self.terminos(estancia_minima=1, estancia_minima_unidad='anios', estancia_maxima=5, estancia_maxima_unidad='anios').save()

    def test_one_limit_alone_is_fine_and_unit_must_be_known(self):
        self.terminos(estancia_minima=6).full_clean()
        with self.assertRaises(ValidationError):
            self.terminos(estancia_minima=6, estancia_minima_unidad='semanas').full_clean()

    def test_a_sale_offer_cannot_have_rental_terms(self):
        from base.models import TerminosAlquiler
        with self.assertRaises(ValidationError):
            TerminosAlquiler(oferta=self.venta, estancia_minima=1).full_clean()
        with self.assertRaises(ValidationError):
            TerminosAlquiler(oferta=self.venta, estancia_minima=1).save()

    def test_terms_are_deleted_with_the_offer(self):
        from base.models import TerminosAlquiler
        self.terminos(acepta_animales=True).save()
        self.oferta.delete()
        self.assertEqual(TerminosAlquiler.objects.count(), 0)


class EstanciasUnidadesTests(TestCase):
    def test_surfaces_and_counts_are_separate_and_not_negative(self):
        from base.models import Estancias
        inm = inmueble(referencia='U1', publicar_web=True)
        Estancias.objects.create(
            inmueble=inm, salon_m2='22', n_terrazas=2, terraza_m2='11.5', n_balcones=1, balcones_m2='4',
            carpinteria_interior='madera', carpinteria_exterior='aluminio')
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual(data['salon']['salon_m2'], '22.00')
        self.assertEqual((data['terraza']['n_terrazas'], data['terraza']['terraza_m2']), (2, '11.50'))
        self.assertEqual((data['terraza']['n_balcones'], data['terraza']['balcones_m2']), (1, '4.00'))
        self.assertEqual(
            (data['carpinteria']['carpinteria_interior'], data['carpinteria']['carpinteria_exterior']),
            ('madera', 'aluminio'))
        for field in ('salon_m2', 'terraza_m2', 'balcones_m2'):
            with self.assertRaises(IntegrityError, msg=field), transaction.atomic():
                Estancias.objects.filter(inmueble=inm).update(**{field: -1})


class DotacionYOtrosTests(TestCase):
    def test_tableware_and_linen_flags_and_exterior_boolean(self):
        from base.models import Caracteristicas, Dotacion
        inm = inmueble(referencia='D1', publicar_web=True)
        Dotacion.objects.create(
            inmueble=inm, vajilla=True, cuberteria=True, cristaleria=True, ropa_cama=True, toallas=True)
        Caracteristicas.objects.create(inmueble=inm, exterior=True)
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertTrue(all(data['dotacion'][k] for k in ('vajilla', 'cuberteria', 'cristaleria', 'ropa_cama', 'toallas')))
        self.assertIs(data['caracteristicas']['exterior'], True)


class IncluidoJuntoAlImporteTests(ModalidadFixture):
    """The amounts stay on the listing; what the rent includes belongs to each rental offer (ADR 0020)."""

    def test_amounts_are_on_the_listing_and_the_inclusions_on_the_offer(self):
        from base.models import Caracteristicas, InclusionesAlquiler
        self.both.ibi, self.both.gtos_comunidad = '210', '50'
        self.both.save()
        temporal = self.both.precios.get(modalidad=self.mod['temporal'])
        InclusionesAlquiler.objects.create(oferta=temporal, gastos_comunidad=True, ibi=True, wifi=True)
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
        self.assertEqual((data['ibi'], data['gtos_comunidad']), ('210.00', '50.00'))
        self.assertNotIn('ibi_incluido', data)
        self.assertNotIn('gastos_comunidad_incluidos', data)
        por_codigo = {m['codigo']: m['inclusiones'] for m in data['modalidades']}
        self.assertEqual(por_codigo['temporal'], {
            'gastos_comunidad': True, 'ibi': True, 'seguro': False, 'wifi': True, 'suministros': False})
        self.assertIsNone(por_codigo['venta'])
        self.assertIsNone(data['caracteristicas'])
        self.assertNotIn('ibi_incluido', {f.name for f in Caracteristicas._meta.get_fields()})

    def test_each_rental_offer_has_its_own_inclusions(self):
        from base.models import InclusionesAlquiler
        habitual = InmuebleModalidad.objects.create(
            inmueble=self.both, modalidad=self.mod['habitual'], precio=1000)
        temporal = self.both.precios.get(modalidad=self.mod['temporal'])
        InclusionesAlquiler.objects.create(oferta=temporal, seguro=True)
        InclusionesAlquiler.objects.create(oferta=habitual, suministros=True)
        por_codigo = {m['codigo']: m['inclusiones'] for m in
                      self.client.get(f'/api/inmuebles/{self.both.id}/').json()['modalidades']}
        self.assertTrue(por_codigo['temporal']['seguro'] and not por_codigo['temporal']['suministros'])
        self.assertTrue(por_codigo['habitual']['suministros'] and not por_codigo['habitual']['seguro'])

    def test_a_sale_has_no_inclusions(self):
        from base.models import InclusionesAlquiler
        venta = self.both.precios.get(modalidad=self.mod['venta'])
        with self.assertRaises(ValidationError):
            InclusionesAlquiler(oferta=venta, ibi=True).full_clean()
        with self.assertRaises(ValidationError):
            InclusionesAlquiler(oferta=venta, ibi=True).save()
        self.assertEqual(InclusionesAlquiler.objects.count(), 0)

    def test_inclusions_go_with_the_offer(self):
        from base.models import InclusionesAlquiler
        temporal = self.both.precios.get(modalidad=self.mod['temporal'])
        InclusionesAlquiler.objects.create(oferta=temporal, wifi=True)
        self.both.delete()
        self.assertEqual(InclusionesAlquiler.objects.count(), 0)

    def test_reform_year_is_next_to_the_construction_year(self):
        inm = inmueble(referencia='I2', publicar_web=True, anio_construccion=1960, anio_ultima_reforma=2015)
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual((data['anio_construccion'], data['anio_ultima_reforma']), (1960, 2015))
        with self.assertRaises(ValidationError):
            Inmueble(referencia='I3', anio_ultima_reforma=3000).full_clean(exclude=['municipio'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            inmueble(referencia='I4', anio_ultima_reforma=999)


class IvaTests(ModalidadFixture):
    def test_vat_rate_must_be_between_0_and_100(self):
        precio = InmuebleModalidad(inmueble=self.rent, modalidad=self.mod['temporal'], precio=450)
        precio.full_clean(exclude=['inmueble'])
        self.assertFalse(precio.mas_iva)
        for bad in (-1, 101):
            precio.tipo_iva = bad
            with self.assertRaises(ValidationError):
                precio.full_clean(exclude=['inmueble'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            InmuebleModalidad.objects.filter(pk=self.both.precios.first().pk).update(tipo_iva=101)
        precio.tipo_iva = 21
        precio.save()
        self.assertTrue(precio.mas_iva)

    def test_api_returns_vat_per_modalidad(self):
        InmuebleModalidad.objects.create(
            inmueble=self.rent, modalidad=self.mod['temporal'], precio=450, tipo_iva='21')
        data = self.client.get(f'/api/inmuebles/{self.rent.id}/').json()
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
        data = self.client.get(f'/api/inmuebles/{self.both.id}/').json()
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
                self.client.get(f'/api/inmuebles/{inm.id}/')
            return len(ctx)

        self.assertEqual(queries(self.both), queries(self.rent))  # two modalidades vs one


class PlazaOpcionalTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='O1', publicar_web=True)

    def test_optional_space_price_is_public_but_value_and_rent_stay_private(self):
        from base.models import PlazaAparcamiento
        PlazaAparcamiento.objects.create(
            inmueble=self.inm, opcional=True, precio_opcional='60',
            precio_opcional_tipo_iva='21', valor='9999.99', renta='88.77')
        response = self.client.get(f'/api/inmuebles/{self.inm.id}/')
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
        self.assertFalse(plaza.precio_opcional_mas_iva)
        plaza.precio_opcional_tipo_iva = 101
        with self.assertRaises(ValidationError):
            plaza.full_clean(exclude=['inmueble'])
        plaza.precio_opcional_tipo_iva = 21
        plaza.save()
        self.assertTrue(plaza.precio_opcional_mas_iva)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlazaAparcamiento.objects.filter(pk=plaza.pk).update(precio_opcional_tipo_iva=101)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlazaAparcamiento.objects.filter(pk=plaza.pk).update(precio_opcional='-1')


class CamposVentaTests(ModalidadFixture):
    """The idealista-01 listing: a terraced house for sale."""

    def setUp(self):
        super().setUp()
        from base.models import Entorno
        self.chalet = inmueble(
            referencia='V1', publicar_web=True, tipo='vivienda', subtipo='chalet_adosado',
            conservacion='buen_estado', anio_construccion=1955, n_plantas=2,
            sup_construida='154', sup_parcela='142', distrito=self.dis)
        self.price(self.chalet, venta=279000)
        Entorno.objects.create(inmueble=self.chalet, jardin=True, jardin_m2='79')

    def test_detail_returns_the_sale_fields(self):
        data = self.client.get(f'/api/inmuebles/{self.chalet.id}/').json()
        self.assertEqual(
            (data['subtipo'], data['conservacion'], data['anio_construccion'], data['n_plantas'],
             data['planta'], data['sup_parcela'], data['entorno']['jardin_m2']),
            ('chalet_adosado', 'buen_estado', 1955, 2, None, '142.00', '79.00'))

    def test_floor_level_of_a_flat_allows_ground_and_basement(self):
        piso = inmueble(referencia='V2', tipo='vivienda', subtipo='piso', planta=0)
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
        oficina = Inmueble(referencia='V3', municipio=self.chalet.municipio, tipo='oficina', subtipo='piso')
        with self.assertRaises(ValidationError):
            oficina.clean()
        with self.assertRaises(ValidationError):
            oficina.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inmueble.objects.filter(pk=self.chalet.pk).update(tipo='oficina')
        with self.assertRaises(ValidationError):
            Inmueble(referencia='V4', tipo='vivienda', subtipo='castillo').full_clean(exclude=['municipio'])
        inmueble(referencia='V5', tipo='oficina')

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
        piso = inmueble(referencia='V7', publicar_web=True, tipo='vivienda', subtipo='piso',
                        sup_construida='55', distrito=self.dis)
        self.price(piso, venta=295000)
        ventas = '/api/inmuebles/modalidad/ventas/'
        self.assertEqual(self.refs(f'{ventas}?subtipo=piso'), ['V7'])
        self.assertEqual(self.refs(f'{ventas}?subtipo=chalet_adosado'), ['V1'])
        self.assertEqual(self.refs(f'{ventas}?tipo=vivienda'), ['V1', 'V7'])
        self.assertEqual(self.refs(f'{ventas}?tipo=oficina'), [])
        self.assertEqual(self.refs(f'{ventas}?sup_min=100'), ['V1'])
        self.assertEqual(self.refs(f'{ventas}?sup_max=100'), ['V7'])
        self.assertEqual(self.refs(f'{ventas}?sup_min=50&sup_max=60&max_precio=300000'), ['V7'])
        self.assertEqual(self.refs(f'{ventas}?subtipo=piso&max_precio=100000'), [])
        listed = {i['referencia']: i for i in self.client.get(ventas).json()['inmuebles']}
        self.assertEqual((listed['V1']['subtipo'], listed['V1']['sup_construida']), ('chalet_adosado', '154.00'))

    def test_invalid_filter_values_are_rejected(self):
        for query in ('tipo=Castillo', 'tipo=Vivienda', 'subtipo=castillo', 'sup_min=abc', 'sup_max=x'):
            self.assertEqual(self.client.get(f'/api/inmuebles/?{query}').status_code, 400, query)


class DisponibilidadPorOfertaTests(ModalidadFixture):
    """`fecha_disponibilidad` belongs to each offer; the listing shows the earliest open one."""

    def setUp(self):
        super().setUp()
        self.inm = inmueble(referencia='D1', publicar_web=True, distrito=self.dis)
        self.alquiler = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod['habitual'], precio=900, fecha_disponibilidad=date(2026, 4, 1))
        self.venta = InmuebleModalidad.objects.create(
            inmueble=self.inm, modalidad=self.mod['venta'], precio=200000, fecha_disponibilidad=date(2026, 1, 15))

    def detail(self):
        return self.client.get(f'/api/inmuebles/{self.inm.id}/').json()

    def refs(self, url):
        """References of this test's listings (`D...`) only; the fixture's own listings are ignored."""
        return [r for r in super().refs(url) if r.startswith('D')]

    def orden(self):
        return [i['referencia'] for i in self.client.get('/api/inmuebles/').json()['inmuebles']
                if i['referencia'].startswith('D')]

    def test_an_offer_must_have_a_date_and_defaults_to_today(self):
        self.assertEqual(InmuebleModalidad(inmueble=self.inm, modalidad=self.mod['temporal'], precio=1).fecha_disponibilidad,
                         timezone.localdate())
        with self.assertRaises(IntegrityError), transaction.atomic():
            InmuebleModalidad.objects.filter(pk=self.venta.pk).update(fecha_disponibilidad=None)

    def test_listing_date_is_the_earliest_open_offer_and_each_offer_shows_its_own(self):
        data = self.detail()
        self.assertEqual(data['fecha_disponibilidad'], '2026-01-15')
        self.assertEqual({m['codigo']: m['fecha_disponibilidad'] for m in data['modalidades']},
                         {'habitual': '2026-04-01', 'venta': '2026-01-15'})

    def test_a_closed_offer_does_not_affect_the_listing(self):
        self.venta.estado = 'cerrado'
        self.venta.save()
        self.assertEqual(self.detail()['fecha_disponibilidad'], '2026-04-01')
        listed = {i['referencia']: i for i in self.client.get('/api/inmuebles/').json()['inmuebles']}
        self.assertEqual(listed['D1']['fecha_disponibilidad'], '2026-04-01')
        self.alquiler.estado = 'cerrado'
        self.alquiler.save()
        self.assertIsNone(self.detail()['fecha_disponibilidad'])

    def test_date_search_looks_at_one_open_offer(self):
        base = '/api/inmuebles/'
        self.assertEqual(self.refs(f'{base}?fecha_entrada=2026-02-01'), ['D1'])
        self.assertEqual(self.refs(f'{base}?fecha_entrada=2025-12-31'), [])
        # With a modalidad it is that offer's date: the rent starts in April, the sale was open in January.
        self.assertEqual(self.refs(f'{base}modalidad/habituales/?fecha_entrada=2026-02-01'), [])
        self.assertEqual(self.refs(f'{base}modalidad/habituales/?fecha_entrada=2026-04-01'), ['D1'])
        self.assertEqual(self.refs(f'{base}modalidad/ventas/?fecha_entrada=2026-02-01'), ['D1'])

    def test_closed_offers_never_match_a_date_search_and_listings_do_not_repeat(self):
        base = '/api/inmuebles/'
        self.assertEqual(self.refs(f'{base}?fecha_entrada=2026-12-01'), ['D1'])
        self.assertEqual(len(self.client.get(f'{base}?fecha_entrada=2026-12-01').json()['inmuebles']),
                         len({i['referencia'] for i in self.client.get(f'{base}?fecha_entrada=2026-12-01').json()['inmuebles']}))
        self.venta.estado = 'cerrado'
        self.venta.save()
        self.assertEqual(self.refs(f'{base}modalidad/ventas/?fecha_entrada=2026-12-01'), [])
        self.assertEqual(self.refs(f'{base}?fecha_entrada=2026-02-01'), [])
        self.assertEqual(self.refs(f'{base}?fecha_entrada=2026-04-01'), ['D1'])

    def test_invalid_date_is_rejected(self):
        for valor in ('2026-13-01', 'ayer'):
            self.assertEqual(self.client.get(f'/api/inmuebles/?fecha_entrada={valor}').status_code, 400, valor)

    def test_list_is_ordered_by_the_earliest_open_offer_ignoring_closed_ones(self):
        tarde = inmueble(referencia='D2', publicar_web=True, distrito=self.dis)
        InmuebleModalidad.objects.create(
            inmueble=tarde, modalidad=self.mod['habitual'], precio=1, fecha_disponibilidad=date(2026, 3, 1))
        cerrada = inmueble(referencia='D3', publicar_web=True, distrito=self.dis)
        InmuebleModalidad.objects.create(
            inmueble=cerrada, modalidad=self.mod['habitual'], precio=1, estado='cerrado',
            fecha_disponibilidad=date(2020, 1, 1))
        self.assertEqual(self.orden(), ['D1', 'D2', 'D3'])
        # An old date on a closed offer must not put its listing ahead of an open one.
        InmuebleModalidad.objects.create(
            inmueble=tarde, modalidad=self.mod['venta'], precio=1, estado='cerrado',
            fecha_disponibilidad=date(2000, 1, 1))
        self.assertEqual(self.orden(), ['D1', 'D2', 'D3'])

    def test_listing_date_costs_no_extra_queries(self):
        for n in range(3):
            otro = inmueble(referencia=f'Q{n}', publicar_web=True, distrito=self.dis)
            self.price(otro, habitual=100)
        with CaptureQueriesContext(connection) as uno:
            self.client.get('/api/inmuebles/')
        for n in range(3, 8):
            otro = inmueble(referencia=f'Q{n}', publicar_web=True, distrito=self.dis)
            self.price(otro, habitual=100)
        with CaptureQueriesContext(connection) as varios:
            self.client.get('/api/inmuebles/')
        self.assertEqual(len(uno), len(varios))


class MediaYPlanosTests(TestCase):
    def setUp(self):
        from base.models import ImageInmueble
        self.Image = ImageInmueble
        self.inm = inmueble(referencia='MP1', publicar_web=True)

    def test_every_photo_has_a_type_and_the_api_returns_it(self):
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', tipo='fachada', posicion=1)
        self.Image.objects.create(inmueble=self.inm, image='b.jpg', posicion=2)
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual([i['tipo'] for i in data['images']], ['fachada', 'otro'])
        with self.assertRaises(ValidationError):
            self.Image(inmueble=self.inm, image='c.jpg', tipo='sotano').full_clean()

    def test_plans_are_returned_apart_from_the_photos_in_detail_and_list(self):
        self.Image.objects.create(inmueble=self.inm, image='a.jpg', tipo='salon', posicion=1)
        self.Image.objects.create(inmueble=self.inm, image='p.jpg', tipo='plano', posicion=2, alt_text='Planta 1')
        self.Image.objects.create(inmueble=self.inm, image='q.jpg', tipo='plano', posicion=3)
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
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
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
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
                self.client.get(f'/api/inmuebles/{self.inm.id}/')
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
        self.url = f'/api/inmuebles/{self.inm.id}/reservas/'
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
        'CaracteristicasSerializer': 'suelo_piso exterior altura_real_m orientacion_norte orientacion_sur '
            'orientacion_este orientacion_oeste chimenea vistas_al_mar vistas_montania tipo_fachada',
        'DistribucionSerializer': 'dobles individuales exteriores suites banios aseos capacidad_personas suelo_banio',
        'InstalacionesSerializer': 'calefaccion tipo_calefaccion subtipo_calefaccion tvs '
            'tv_internacional antena_parabolica aire_acondicionado ascensor internet internet_velocidad_mbps telefono '
            'instalacion_telefono dvd hilo_musical acceso_silla_ruedas',
        'AreaRecreoSerializer': 'zona_deportiva gimnasio piscina solarium jardin_infantil local_social',
        'DotacionSerializer': 'amueblado armarios_empotrados jacuzzi_hidromasaje secadora lavadora '
            'lavavajillas microondas nevera radio ropero toldo horno utensilios_cocina vajilla cuberteria '
            'cristaleria ropa_cama toallas estufa ventilador camas sofas tendedero cafetera plancha kit_limpieza '
            'secador_pelo papel_higienico sofa_cama',
        'SeguridadSerializer': 'portero_conserje vigilancia_privada camaras_seguridad puerta_blindada '
            'caja_seguridad cristales_blindados sistema_alarma instalacion_antirrobo '
            'instalacion_contra_incendio video_portero portero_automatico',
        'EntornoSerializer': 'zona_comunitaria otras_areas_comunitarias jardin jardin_m2 cerca_colegios '
            'cerca_farmacia cerca_guarderias cerca_medico cerca_centro_comercial distancia_playa_m '
            'distancia_poblacion_m distancia_ciudad_m cerca_supermercado cerca_restaurantes cerca_discotecas',
        'OtrosEspaciosSerializer': 'despachos vestidores altillo galeria trastero buhardilla bodega '
            'lavadero patio porche estudios bibliotecas',
        'CondicionesSerializer': 'nombre honorarios itp incluido no_incluido fianza pago_adelantado '
            'suministros actualizacion_renta limpieza_final requisitos notaria registro gestoria honorarios_comprador '
            'itp_porcentaje honorarios_incluidos_en_precio',
        'RegistroLegalSerializer': 'tipo estado numero organismo',
        'AgenciaSerializer': 'nombre aicat numero_api',
        'CertificadoEnergeticoSerializer': 'numero eficiencia consumo_energetico emisiones_co2 fecha_emision '
            'fecha_vencimiento',
        'MediaInmuebleSerializer': 'tipo url titulo',
        'SingleImageSerializer': 'id image default alt_text posicion tipo',
        'PlazaAparcamientoSerializer': 'id numero tipo superficie notas opcional precio_opcional '
            'precio_opcional_unidad precio_opcional_mas_iva precio_opcional_tipo_iva',
        'CocinaSerializer': 'cocina cocina_amueblada tipo_cocina suelo_cocina',
        'TerrazaSerializer': 'n_terrazas terraza_m2 n_balcones balcones_m2 descripcion',
        'SalonSerializer': 'salon_m2 descripcion',
        'CarpinteriaSerializer': 'carpinteria_interior carpinteria_exterior',
        'PrecioModalidadSerializer': 'codigo nombre unidad_precio precio mas_iva tipo_iva fecha_disponibilidad',
        'PrecioModalidadDetalleSerializer': 'codigo nombre unidad_precio precio mas_iva tipo_iva fecha_disponibilidad '
            'fianza_meses fianza_total regulacion terminos inclusiones condiciones',
        'InclusionesAlquilerSerializer': 'gastos_comunidad ibi seguro wifi suministros',
        'TerminosAlquilerSerializer': 'acepta_animales acepta_fumadores uso_temporada estancia_minima estancia_minima_unidad estancia_maxima '
            'estancia_maxima_unidad',
        'RegulacionAlquilerSerializer': 'indice_referencia_min indice_referencia_max indice_referencia_fecha '
            'renta_previa ultima_renta ultima_renta_fin',
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
            AcuerdoAdministracion, DatosInternos, DeclaracionZonaTensionada, HistorialPrecio, InmueblePropietario,
            Propietario,
        )
        private = {AcuerdoAdministracion, DatosInternos, DeclaracionZonaTensionada, HistorialPrecio,
                   InmueblePropietario, Propietario}
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


class DescripcionesTests(TestCase):
    def test_api_returns_the_descriptions_by_language_and_skips_missing_ones(self):
        inm = inmueble(referencia='D1', publicar_web=True, descripcion_es='Hola', descripcion_ca='Hola!')
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual(data['descripciones'], {'es': 'Hola', 'ca': 'Hola!'})
        with self.assertRaises(IntegrityError), transaction.atomic():
            DescripcionInmueble.objects.create(inmueble=inm, idioma='es', texto='Otra')

    def test_unknown_language_is_rejected(self):
        inm = inmueble(referencia='D2')
        with self.assertRaises(ValidationError):
            DescripcionInmueble(inmueble=inm, idioma='de', texto='Guten Tag').full_clean()

    def test_list_shows_the_descriptions_without_extra_queries(self):
        inmueble(referencia='D3', publicar_web=True, descripcion_es='Uno', descripcion_en='One')
        inmueble(referencia='D4', publicar_web=True, descripcion_es='Dos')
        data = self.client.get('/api/inmuebles/').json()['inmuebles']
        self.assertEqual({d['descripciones']['es'] for d in data}, {'Uno', 'Dos'})


class TransportePorModoTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='T1', publicar_web=True)

    def detail(self):
        return self.client.get(f'/api/inmuebles/{self.inm.id}/').json()

    def test_no_rows_means_no_transport_section(self):
        self.assertIsNone(self.detail()['transporte'])

    def test_rows_are_flattened_to_a_flag_and_a_description_per_mode(self):
        TransporteInmueble.objects.create(inmueble=self.inm, tipo='metro', descripcion='L2')
        TransporteInmueble.objects.create(inmueble=self.inm, tipo='bus')
        self.assertEqual(self.detail()['transporte'], {
            'cerca_bus': True, 'descripcion_bus': '', 'cerca_metro': True, 'descripcion_metro': 'L2',
            'cerca_tranvia': False, 'descripcion_tranvia': '', 'cerca_tren': False, 'descripcion_tren': '',
            'cerca_ferrocarril': False, 'descripcion_ferrocarril': ''})

    def test_one_row_per_mode_and_only_known_modes(self):
        TransporteInmueble.objects.create(inmueble=self.inm, tipo='bus')
        with self.assertRaises(IntegrityError), transaction.atomic():
            TransporteInmueble.objects.create(inmueble=self.inm, tipo='bus')
        with self.assertRaises(ValidationError):
            TransporteInmueble(inmueble=self.inm, tipo='funicular').full_clean()


class SuministrosTests(TestCase):
    def setUp(self):
        self.inm = inmueble(referencia='S1', publicar_web=True)

    def detail(self):
        return self.client.get(f'/api/inmuebles/{self.inm.id}/').json()

    def test_no_installations_and_no_supplies_means_no_section(self):
        self.assertIsNone(self.detail()['instalaciones'])

    def test_supplies_are_flattened_next_to_the_installation_columns(self):
        Instalaciones.objects.create(inmueble=self.inm, calefaccion=True, tipo_calefaccion='central')
        Suministro.objects.create(inmueble=self.inm, tipo='agua', contador=True, compania='Aigües')
        Suministro.objects.create(inmueble=self.inm, tipo='gas', compania='Nedgia', tipo_suministro='natural')
        data = self.detail()['instalaciones']
        self.assertEqual(
            (data['contador_agua'], data['compania_agua'], data['contador_electricidad'], data['compania_electricidad']),
            (True, 'Aigües', False, ''))
        self.assertEqual(
            (data['gas'], data['tipo_gas'], data['contador_gas'], data['compania_gas']), (True, 'natural', False, 'Nedgia'))
        self.assertEqual(data['tipo_calefaccion'], 'central')

    def test_a_supply_without_an_installation_row_is_still_shown(self):
        Suministro.objects.create(inmueble=self.inm, tipo='electricidad', contador=True)
        data = self.detail()['instalaciones']
        self.assertTrue(data['contador_electricidad'])
        self.assertFalse(data['gas'])

    def test_gas_flag_is_derived_from_the_gas_row(self):
        Instalaciones.objects.create(inmueble=self.inm)
        self.assertFalse(self.detail()['instalaciones']['gas'])
        Suministro.objects.create(inmueble=self.inm, tipo='gas')
        self.assertTrue(self.detail()['instalaciones']['gas'])

    def test_one_row_per_supply_and_gas_type_only_for_gas(self):
        Suministro.objects.create(inmueble=self.inm, tipo='agua')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Suministro.objects.create(inmueble=self.inm, tipo='agua')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Suministro.objects.create(inmueble=self.inm, tipo='electricidad', tipo_suministro='natural')

    def test_heating_uses_choices(self):
        with self.assertRaises(ValidationError):
            Instalaciones(inmueble=self.inm, tipo_calefaccion='Mixta').full_clean()


class PresenciaOCantidadTests(TestCase):
    """Presence-only equipment is a flag; only items where the number matters are counts."""

    FLAGS = {
        'Dotacion': ['jacuzzi_hidromasaje', 'secadora', 'lavadora', 'lavavajillas', 'microondas', 'nevera', 'radio',
                     'toldo', 'horno', 'tendedero', 'cafetera', 'plancha', 'kit_limpieza', 'secador_pelo',
                     'papel_higienico', 'sofa_cama'],
        'OtrosEspacios': ['altillo', 'galeria', 'buhardilla', 'bodega', 'lavadero', 'patio', 'porche'],
    }
    COUNTS = {
        'Dotacion': ['armarios_empotrados', 'ropero', 'estufa', 'ventilador', 'camas', 'sofas'],
        'OtrosEspacios': ['despachos', 'vestidores', 'trastero', 'estudios', 'bibliotecas'],
    }

    def test_each_item_has_the_type_the_rule_gives_it(self):
        from django.apps import apps
        for modelo, nombres in self.FLAGS.items():
            for n in nombres:
                self.assertEqual(apps.get_model('base', modelo)._meta.get_field(n).get_internal_type(), 'BooleanField', n)
        for modelo, nombres in self.COUNTS.items():
            for n in nombres:
                self.assertEqual(
                    apps.get_model('base', modelo)._meta.get_field(n).get_internal_type(), 'PositiveIntegerField', n)

    def test_every_equipment_column_is_classified(self):
        from django.apps import apps
        for modelo in ('Dotacion', 'OtrosEspacios'):
            columnas = {
                f.name for f in apps.get_model('base', modelo)._meta.concrete_fields
                if f.get_internal_type() in ('BooleanField', 'PositiveIntegerField')
            }
            clasificadas = set(self.FLAGS[modelo]) | set(self.COUNTS[modelo])
            self.assertEqual(columnas - clasificadas - {'amueblado', 'utensilios_cocina', 'vajilla', 'cuberteria',
                                                       'cristaleria', 'ropa_cama', 'toallas'}, set(), modelo)

    def test_api_returns_flags_and_counts(self):
        from base.models import Dotacion, OtrosEspacios
        inm = inmueble(referencia='P1', publicar_web=True)
        Dotacion.objects.create(inmueble=inm, lavadora=True, camas=3)
        OtrosEspacios.objects.create(inmueble=inm, bodega=True, trastero=2)
        data = self.client.get(f'/api/inmuebles/{inm.id}/').json()
        self.assertEqual((data['dotacion']['lavadora'], data['dotacion']['camas']), (True, 3))
        self.assertEqual((data['otros_espacios']['bodega'], data['otros_espacios']['trastero']), (True, 2))


class OpcionesCerradasTests(TestCase):
    """Columns that used to be free text now take a value from a closed list."""

    def setUp(self):
        self.inm = inmueble(referencia='O1', publicar_web=True)

    def test_widened_lists_accept_their_new_values(self):
        from base.models import Caracteristicas, Instalaciones
        from base.models.opciones import MATERIALES_SUELO
        for tipo in ('terreno', 'trastero', 'edificio', 'nave'):
            Inmueble(referencia='N', tipo=tipo, municipio=self.inm.municipio).full_clean(exclude=['referencia'])
        for subtipo in ('loft', 'planta_baja', 'chalet_pareado', 'casa_pueblo', 'masia'):
            Inmueble(referencia='N', tipo='vivienda', subtipo=subtipo, municipio=self.inm.municipio).full_clean(
                exclude=['referencia'])
        Inmueble(referencia='N', conservacion='reformado', municipio=self.inm.municipio).full_clean(
            exclude=['referencia'])
        self.assertTrue({'laminado', 'vinilico', 'ceramica', 'moqueta', 'cemento_pulido'}
                        <= {valor for valor, _ in MATERIALES_SUELO})
        Caracteristicas(inmueble=self.inm, tipo_fachada='metalica').full_clean()
        Instalaciones(inmueble=self.inm, calefaccion=True, subtipo_calefaccion='solar').full_clean()
        with self.assertRaises(ValidationError):
            Inmueble(referencia='N', tipo='terreno', subtipo='loft', municipio=self.inm.municipio).full_clean(
                exclude=['referencia'])
        self.assertEqual(self.client.get('/api/inmuebles/?tipo=terreno').status_code, 200)

    def test_each_closed_column_rejects_text_outside_its_list(self):
        from base.models import Caracteristicas, Distribucion, Estancias
        casos = [
            (Caracteristicas, 'suelo_piso'), (Caracteristicas, 'tipo_fachada'), (Distribucion, 'suelo_banio'),
            (Estancias, 'tipo_cocina'), (Estancias, 'suelo_cocina'),
            (Estancias, 'carpinteria_interior'), (Estancias, 'carpinteria_exterior'),
        ]
        for modelo, campo in casos:
            with self.subTest(f'{modelo.__name__}.{campo}'):
                fila = modelo(inmueble=self.inm, **{campo: 'Cualquier cosa'})
                with self.assertRaises(ValidationError) as ctx:
                    fila.full_clean()
                self.assertIn(campo, ctx.exception.message_dict)
                modelo(inmueble=self.inm, **{campo: ''}).full_clean()

    def test_valid_values_are_accepted_and_returned_by_the_api(self):
        from base.models import Caracteristicas, Distribucion, Estancias
        Caracteristicas.objects.create(inmueble=self.inm, suelo_piso='parquet', tipo_fachada='piedra')
        Distribucion.objects.create(inmueble=self.inm, banios=1, suelo_banio='gres')
        Estancias.objects.create(inmueble=self.inm, tipo_cocina='abierta', carpinteria_exterior='pvc')
        self.inm.situacion_actual = 'libre'
        self.inm.full_clean()
        self.inm.save()
        data = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()
        self.assertEqual((data['caracteristicas']['suelo_piso'], data['caracteristicas']['tipo_fachada']), ('parquet', 'piedra'))
        self.assertEqual(data['distribucion']['suelo_banio'], 'gres')
        self.assertEqual((data['cocina']['tipo_cocina'], data['carpinteria']['carpinteria_exterior']), ('abierta', 'pvc'))
        self.assertEqual(data['situacion_actual'], 'libre')

    def test_situacion_actual_rejects_text_outside_its_list(self):
        self.inm.situacion_actual = 'Alquiler vacacional'
        with self.assertRaises(ValidationError) as ctx:
            self.inm.full_clean()
        self.assertIn('situacion_actual', ctx.exception.message_dict)

    def test_orientation_is_one_flag_per_direction(self):
        from base.models import Caracteristicas
        Caracteristicas.objects.create(inmueble=self.inm, orientacion_norte=True, orientacion_oeste=True)
        otros = self.client.get(f'/api/inmuebles/{self.inm.id}/').json()['caracteristicas']
        self.assertEqual(
            [otros[f'orientacion_{lado}'] for lado in ('norte', 'sur', 'este', 'oeste')],
            [True, False, False, True])
        self.assertNotIn('orientacion', otros)
