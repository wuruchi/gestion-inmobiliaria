"""The fake-offers development tool: what it creates, that a run is repeatable and what `--clean` removes."""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EJEMPLOS = Path(os.environ.get('ATB_EXAMPLES_PATH', ROOT.parent.parent / 'gestion-inmobiliaria-examples'))


class FakeOffersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = str(Path(cls.tmp.name) / 'base.sqlite3')
        for comando in ('migrate', 'locations', 'modalidades', 'condiciones', 'agencia', 'zonas-tensionadas'):
            cls.seed(cls.base, comando)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def seed(cls, db, *args, check=True):
        env = {**os.environ, 'DB_SQLITE_PATH': db, 'DJANGO_MEDIA_ROOT': str(Path(cls.tmp.name) / 'media')}
        env.pop('DB_NAME', None)
        return subprocess.run([sys.executable, str(ROOT / 'seed.py'), *args],
                              env=env, capture_output=True, text=True, check=check)

    def setUp(self):
        self.db = str(Path(self.tmp.name) / f'{self.id().split(".")[-1]}.sqlite3')
        shutil.copy(self.base, self.db)
        self.media = Path(self.tmp.name) / 'media'

    def consulta(self, sql, *params):
        return sqlite3.connect(self.db).execute(sql, params).fetchall()

    def fake(self, *args, **kwargs):
        return self.seed(self.db, 'fake-offers', *args, **kwargs)

    # ------------------------------------------------------------------ what it creates
    def test_it_needs_the_modalidades_and_the_agency(self):
        vacia = str(Path(self.tmp.name) / 'vacia.sqlite3')
        self.seed(vacia, 'migrate')
        fallo = self.seed(vacia, 'fake-offers', '--no-media', check=False)
        self.assertNotEqual(fallo.returncode, 0)
        self.assertIn('modalidades first', fallo.stderr)
        self.seed(vacia, 'modalidades')
        fallo = self.seed(vacia, 'fake-offers', '--no-media', check=False)
        self.assertIn('agency first', fallo.stderr)

    def test_each_example_is_used_in_turn_and_the_listing_is_complete(self):
        salida = self.fake('--count', '18', '--seed', '1', '--no-media').stdout
        self.assertIn('DEV-0001 to DEV-0018', salida)
        self.assertEqual(self.consulta('select count(*) from base_inmueble')[0][0], 18)
        tipos = self.consulta(
            "select referencia, tipo, subtipo from base_inmueble order by referencia")
        # Examples in order: atb-01, atb-02 (office), atb-03, idealista-01 (terraced house), -02, -03, locb-01..03.
        self.assertEqual([t[1] for t in tipos[:3]], ['vivienda', 'oficina', 'vivienda'])
        self.assertEqual(tipos[3][2], 'chalet_adosado')
        self.assertEqual(tipos[4][2], 'chalet_independiente')
        self.assertEqual(tipos[9][1:], tipos[0][1:])  # the tenth offer is built from the first example again
        for tabla in ('distribucion', 'certificadoenergetico', 'datosinternos', 'caracteristicas', 'instalaciones'):
            self.assertEqual(self.consulta(f'select count(*) from base_{tabla}')[0][0], 18, tabla)
        sin_precio = self.consulta(
            'select count(*) from base_inmueble i where not exists '
            '(select 1 from base_inmueblemodalidad m where m.inmueble_id = i.id)')
        self.assertEqual(sin_precio[0][0], 0)
        sin_propietario = self.consulta(
            'select count(*) from base_inmueble i where not exists '
            '(select 1 from base_inmueblepropietario p where p.inmueble_id = i.id)')
        self.assertEqual(sin_propietario[0][0], 0)
        self.assertEqual(self.consulta(
            "select count(*) from base_descripcioninmueble where idioma = 'es'")[0][0], 18)
        self.assertEqual(self.consulta(
            'select count(*) from base_inmueble where agencia_id is null')[0][0], 0)

    def test_the_fake_data_is_consistent_with_the_backend_checks(self):
        self.fake('--count', '45', '--seed', '3', '--no-media')
        self.assertEqual(self.seed(self.db, 'check-locations', check=False).returncode, 0)
        # Every fake listing is in Barcelona, in a barrio of its district, with a street and a postal code.
        malos = self.consulta(
            "select count(*) from base_inmueble i join base_municipio m on m.id = i.municipio_id "
            "left join base_barrio b on b.id = i.barrio_id "
            "where m.codigo_ine != '08019' or b.id is null or i.codigo_postal = '' or i.direccion = ''")
        self.assertEqual(malos[0][0], 0)
        # Rules the model leaves to the data: rentals carry rental data, sales do not.
        self.assertEqual(self.consulta(
            "select count(*) from base_regulacionalquiler r join base_inmueblemodalidad o on o.id = r.oferta_id "
            "join base_modalidad m on m.id = o.modalidad_id where m.unidad_precio != 'mensual'")[0][0], 0)
        self.assertEqual(self.consulta(
            "select count(*) from base_inmueblemodalidad o join base_modalidad m on m.id = o.modalidad_id "
            "where m.unidad_precio = 'mensual' and not exists "
            "(select 1 from base_terminosalquiler t where t.oferta_id = o.id)")[0][0], 0)
        # The latest price in the log is the current one.
        self.assertEqual(self.consulta(
            "select count(*) from base_inmueblemodalidad o where o.precio != (select h.importe from "
            "base_historialprecio h where h.inmueble_id = o.inmueble_id and h.modalidad_id = o.modalidad_id "
            "order by h.fecha desc limit 1)")[0][0], 0)

    def test_hidden_address_listings_still_have_a_point_to_blur(self):
        self.fake('--count', '9', '--seed', '2', '--no-media')
        # idealista-02 and idealista-03 (offers 5 and 6) always hide their address.
        self.assertEqual(self.consulta(
            "select ocultar_direccion from base_inmueble where referencia in ('DEV-0005', 'DEV-0006')"),
            [(1,), (1,)])

    # ------------------------------------------------------------------ repeatability and cleaning
    def test_the_same_seed_gives_the_same_offers(self):
        self.fake('--count', '12', '--seed', '42', '--no-media')
        primero = self.consulta(
            'select referencia, titulo, sup_construida, direccion from base_inmueble order by referencia')
        precios = self.consulta('select precio from base_inmueblemodalidad order by id')
        self.fake('--clean')
        self.fake('--count', '12', '--seed', '42', '--no-media')
        self.assertEqual(primero, self.consulta(
            'select referencia, titulo, sup_construida, direccion from base_inmueble order by referencia'))
        self.assertEqual(precios, self.consulta('select precio from base_inmueblemodalidad order by id'))

    def test_numbering_continues_and_clean_removes_only_the_fake_data(self):
        self.fake('--count', '3', '--seed', '1', '--no-media')
        self.assertIn('DEV-0004 to DEV-0005', self.fake('--count', '2', '--seed', '1', '--no-media').stdout)
        conn = sqlite3.connect(self.db)
        conn.execute("insert into base_propietario (nombre, nif, email, telefono, gran_tenedor) "
                     "values ('Real Owner', 'X1234567L', 'real@example.com', '', 0)")
        conn.commit()
        conn.close()
        salida = self.fake('--clean').stdout
        self.assertIn('deleted     5', salida)
        self.assertEqual(self.consulta('select count(*) from base_inmueble')[0][0], 0)
        self.assertEqual(self.consulta('select nombre from base_propietario'), [('Real Owner',)])
        self.assertEqual(self.consulta('select count(*) from base_historialprecio')[0][0], 0)

    def test_dry_run_writes_nothing_and_a_prefix_keeps_the_runs_apart(self):
        salida = self.fake('--count', '4', '--seed', '1', '--no-media', '--dry-run').stdout
        self.assertIn('dry run: nothing was written', salida)
        self.assertEqual(self.consulta('select count(*) from base_inmueble')[0][0], 0)
        self.fake('--count', '2', '--seed', '1', '--no-media', '--prefix', 'AAA')
        self.fake('--count', '2', '--seed', '1', '--no-media')
        self.fake('--clean')
        self.assertEqual(self.consulta('select referencia from base_inmueble order by referencia'),
                         [('AAA-0001',), ('AAA-0002',)])

    # ------------------------------------------------------------------ other municipios
    def test_another_municipio_by_name_or_code(self):
        self.fake('--count', '6', '--seed', '1', '--no-media', '--municipio', 'sabadell')
        filas = self.consulta(
            "select m.nombre, i.distrito_id, i.barrio_id, i.codigo_postal from base_inmueble i "
            "join base_municipio m on m.id = i.municipio_id")
        self.assertEqual({f[0] for f in filas}, {'Sabadell'})
        self.assertTrue(all(f[1] is None and f[2] is None for f in filas))
        self.assertTrue(all(f[3].startswith('082') for f in filas))
        sitges = self.consulta("select codigo_ine from base_municipio where nombre = 'Sitges'")[0][0]
        self.fake('--count', '2', '--seed', '1', '--no-media', '--municipio', sitges)
        self.assertEqual(self.consulta(
            "select count(*) from base_inmueble i join base_municipio m on m.id = i.municipio_id "
            "where m.nombre = 'Sitges'")[0][0], 2)

    def test_an_unknown_municipio_is_reported(self):
        fallo = self.fake('--municipio', 'Nowhere', '--no-media', check=False)
        self.assertNotEqual(fallo.returncode, 0)
        self.assertIn('not found', fallo.stderr)

    # ------------------------------------------------------------------ media
    @unittest.skipUnless(EJEMPLOS.is_dir(), 'the saved example pages are not next to the repository')
    def test_each_offer_reuses_the_media_of_its_example(self):
        salida = self.fake('--count', '9', '--seed', '1', '--examples', str(EJEMPLOS)).stdout
        self.assertIn('ImageInmueble', salida)
        fotos = dict(self.consulta(
            "select i.referencia, count(g.id) from base_inmueble i left join base_imageinmueble g "
            "on g.inmueble_id = i.id group by i.referencia"))
        # atb-01 25, atb-02 20, atb-03 33, idealista-01 36, idealista-02 2, idealista-03 2, locb 4, 3, 3.
        self.assertEqual([fotos[f'DEV-000{n}'] for n in range(1, 10)], [25, 20, 33, 36, 2, 2, 4, 3, 3])
        rutas = {r[0] for r in self.consulta('select image from base_imageinmueble')}
        self.assertTrue(all(r.startswith('seed-examples/') for r in rutas))
        for ruta in rutas:
            self.assertTrue((self.media / ruta).is_file(), ruta)
        self.assertEqual(self.consulta(
            "select url from base_mediainmueble m join base_inmueble i on i.id = m.inmueble_id "
            "where i.referencia = 'DEV-0003'"), [('https://my.matterport.com/show/?m=bium5vKYA1f',)])
        # One default photo per listing, and a floor plan is never the default.
        self.assertEqual(self.consulta(
            "select count(*) from base_inmueble i where (select count(*) from base_imageinmueble g "
            "where g.inmueble_id = i.id and g.\"default\" = 1) != 1")[0][0], 0)
        self.assertEqual(self.consulta(
            "select count(*) from base_imageinmueble where tipo = 'plano' and \"default\" = 1")[0][0], 0)
        # Offer 12 is the third example again and shares the same files: nothing is copied twice.
        copiados = len(list((self.media / 'seed-examples').rglob('*.jpg')))
        self.fake('--count', '3', '--seed', '2', '--examples', str(EJEMPLOS))
        self.assertEqual(len(list((self.media / 'seed-examples').rglob('*.jpg'))), copiados)

    def test_a_missing_examples_folder_is_an_error_unless_media_is_skipped(self):
        fallo = self.fake('--count', '1', '--examples', str(Path(self.tmp.name) / 'nada'), check=False)
        self.assertNotEqual(fallo.returncode, 0)
        self.assertIn('--no-media', fallo.stderr)
        self.fake('--count', '1', '--examples', str(Path(self.tmp.name) / 'nada'), '--no-media')

    @unittest.skipUnless(EJEMPLOS.is_dir(), 'the saved example pages are not next to the repository')
    def test_dry_run_copies_no_files(self):
        shutil.rmtree(self.media / 'seed-examples', ignore_errors=True)
        self.fake('--count', '2', '--seed', '1', '--examples', str(EJEMPLOS), '--dry-run')
        self.assertFalse((self.media / 'seed-examples').exists())


if __name__ == '__main__':
    unittest.main()
