import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SeedLocationsTest(unittest.TestCase):
    def run_seed(self, db, *args):
        env = {**os.environ, 'DB_SQLITE_PATH': db}
        env.pop('DB_NAME', None)
        return subprocess.run(
            [sys.executable, str(ROOT / 'seed.py'), *args],
            env=env, capture_output=True, text=True, check=True,
        )

    def count(self, db, table):
        return sqlite3.connect(db).execute(f'select count(*) from base_{table}').fetchone()[0]

    def counts(self, db):
        c = sqlite3.connect(db)
        return [c.execute(f'select count(*) from base_{t}').fetchone()[0]
                for t in ('provincia', 'comarca', 'municipio', 'distrito', 'barrio')]

    def test_seed_is_complete_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'locations', '--dry-run')
            self.assertEqual(self.counts(db), [0, 0, 0, 0, 0])
            self.run_seed(db, 'locations')
            self.assertEqual(self.counts(db), [1, 14, 311, 10, 73])
            self.run_seed(db, 'locations')
            self.assertEqual(self.counts(db), [1, 14, 311, 10, 73])
            self.run_seed(db, 'modalidades', '--dry-run')
            self.assertEqual(self.count(db, 'modalidad'), 0)
            self.run_seed(db, 'modalidades')
            self.run_seed(db, 'modalidades')
            self.assertEqual(self.count(db, 'modalidad'), 3)
            codes = [r[0] for r in sqlite3.connect(db).execute(
                'select codigo from base_modalidad order by orden')]
            self.assertEqual(codes, ['temporal', 'habitual', 'venta'])
            units = [r[0] for r in sqlite3.connect(db).execute(
                'select unidad_precio from base_modalidad order by orden')]
            self.assertEqual(units, ['mensual', 'mensual', 'total'])
            row = sqlite3.connect(db).execute(
                "select nombre from base_municipio where codigo_ine='08019'").fetchone()
            self.assertEqual(row[0], 'Barcelona')

    def test_default_conditions_need_the_modalidades_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            failed = subprocess.run(
                [sys.executable, str(ROOT / 'seed.py'), 'condiciones'],
                env={**os.environ, 'DB_SQLITE_PATH': db}, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('modalidades first', failed.stderr)
            self.assertEqual(self.count(db, 'condiciones'), 0)

            self.run_seed(db, 'modalidades')
            self.run_seed(db, 'condiciones', '--dry-run')
            self.assertEqual(self.count(db, 'condiciones'), 0)
            self.run_seed(db, 'condiciones')
            self.run_seed(db, 'condiciones')
            conn = sqlite3.connect(db)
            rows = conn.execute(
                'select m.codigo, c.por_defecto from base_condiciones c '
                'join base_modalidad m on m.id = c.modalidad_id order by m.orden').fetchall()
            self.assertEqual(rows, [('temporal', 1), ('habitual', 1), ('venta', 1)])
            venta = conn.execute(
                "select itp, notaria, gestoria from base_condiciones where nombre='Compraventa'").fetchone()
            self.assertTrue(all(venta))
            fianza = conn.execute(
                "select fianza from base_condiciones where nombre='Alquiler de temporada'").fetchone()[0]
            self.assertIn('2 mensualidades', fianza)

            # Staff edits survive another run.
            conn.execute("update base_condiciones set fianza='1 mes' where nombre='Alquiler de temporada'")
            conn.commit()
            conn.close()
            self.run_seed(db, 'condiciones')
            self.assertEqual(sqlite3.connect(db).execute(
                "select fianza from base_condiciones where nombre='Alquiler de temporada'").fetchone()[0], '1 mes')
            self.assertEqual(self.count(db, 'condiciones'), 3)

    def test_stressed_zone_declarations_load_what_exists_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'locations')
            self.run_seed(db, 'zonas-tensionadas', '--dry-run')
            self.assertEqual(self.count(db, 'declaracionzonatensionada'), 0)
            salida = self.run_seed(db, 'zonas-tensionadas').stdout
            self.assertIn('not loaded', salida)
            # 101 of the 140 and 58 of the 131 are in Barcelona province, the only one loaded.
            self.assertEqual(self.count(db, 'declaracionzonatensionada'), 159)
            conn = sqlite3.connect(db)
            filas = conn.execute(
                "select d.desde, d.hasta, d.referencia from base_declaracionzonatensionada d "
                "join base_municipio m on m.id = d.municipio_id where m.codigo_ine = '08019'").fetchall()
            self.assertEqual(filas, [('2024-03-16', None, 'TER/800/2024 (DOGC 9122, 14/03/2024)')])
            # An article written after the name ("Hospitalet de Llobregat, l'") still finds its municipio.
            self.assertEqual(conn.execute(
                "select count(*) from base_declaracionzonatensionada d join base_municipio m on m.id = d.municipio_id "
                "where m.nombre in (\"l'Hospitalet de Llobregat\", 'la Garriga', 'el Prat de Llobregat')").fetchone()[0], 3)

            # Staff edits survive another run, and nothing is duplicated.
            conn.execute("update base_declaracionzonatensionada set hasta='2025-01-01' "
                         "where desde='2024-03-16' and municipio_id = "
                         "(select id from base_municipio where codigo_ine = '08019')")
            conn.commit()
            conn.close()
            self.run_seed(db, 'zonas-tensionadas')
            conn = sqlite3.connect(db)
            self.assertEqual(self.count(db, 'declaracionzonatensionada'), 159)
            self.assertEqual(conn.execute(
                "select hasta from base_declaracionzonatensionada where desde='2024-03-16' and municipio_id = "
                "(select id from base_municipio where codigo_ine = '08019')").fetchone()[0], '2025-01-01')

    def test_municipality_names_are_compared_without_the_trailing_article(self):
        sys.path.insert(0, str(ROOT))
        from seedlib.zonas_tensionadas import clave
        self.assertEqual(clave("Bisbal d'Empordà, la"), "la bisbal d'empordà")
        self.assertEqual(clave("Hospitalet de Llobregat, l'"), "l'hospitalet de llobregat")
        self.assertEqual(clave("Franqueses del Vallès, les"), "les franqueses del vallès")
        self.assertEqual(clave("Sant Cugat del Vallès"), "sant cugat del vallès")

    def test_a_modalidad_that_already_has_a_default_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'modalidades')
            conn = sqlite3.connect(db)
            conn.execute(
                "insert into base_condiciones (nombre, modalidad_id, por_defecto, honorarios, itp, incluido, "
                "no_incluido, fianza, pago_adelantado, suministros, actualizacion_renta, limpieza_final, "
                "requisitos, notaria, registro, gestoria, honorarios_comprador, created_at, updated_at) "
                "select 'Mi venta', id, 1, '', '', '', '', '', '', '', '', '', '', '', '', '', '', "
                "datetime('now'), datetime('now') "
                "from base_modalidad where codigo='venta'")
            conn.commit()
            conn.close()
            self.run_seed(db, 'condiciones')
            names = [r[0] for r in sqlite3.connect(db).execute(
                'select nombre from base_condiciones order by nombre')]
            self.assertEqual(names, ['Alquiler de temporada', 'Alquiler de vivienda habitual', 'Mi venta'])

    def test_rent_defaults_carry_the_update_clause_and_sale_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'modalidades')
            self.run_seed(db, 'condiciones')
            rows = dict(sqlite3.connect(db).execute(
                'select m.codigo, c.actualizacion_renta from base_condiciones c '
                'join base_modalidad m on m.id = c.modalidad_id'))
            self.assertIn('IRAV', rows['temporal'])
            self.assertIn('IRAV', rows['habitual'])
            self.assertEqual(rows['venta'], '')

    def test_location_files_nest_properly(self):
        sys.path.insert(0, str(ROOT))
        from seedlib import locations
        self.assertEqual(locations.validate_locations(), [])

    def test_validation_reports_broken_nesting(self):
        sys.path.insert(0, str(ROOT))
        from unittest import mock
        from seedlib import locations
        data = {
            'provincias': [{'codigo_ine': '08', 'nombre': 'Barcelona'}],
            'comarcas': [{'codigo': '01', 'nombre': 'A'}],
            'municipios': [
                {'codigo_ine': '17001', 'comarca': '01'},
                {'codigo_ine': '08001', 'comarca': '99'},
            ],
            'distritos': [{'municipio_ine': '08777', 'codigo': '01'}],
            'barrios': [{'municipio_ine': '08001', 'distrito': '09', 'codigo': '01'}],
        }
        with mock.patch.object(locations, '_load', side_effect=data.__getitem__):
            problems = locations.validate_locations()
        self.assertEqual(len(problems), 4, problems)

    def test_a_comarca_may_group_municipios_of_several_provincias(self):
        sys.path.insert(0, str(ROOT))
        from unittest import mock
        from seedlib import locations
        data = {
            'provincias': [{'codigo_ine': '17', 'nombre': 'Girona'}, {'codigo_ine': '25', 'nombre': 'Lleida'}],
            'comarcas': [{'codigo': '21', 'nombre': 'Cerdanya'}],
            'municipios': [
                {'codigo_ine': '17005', 'comarca': '21'},
                {'codigo_ine': '25052', 'comarca': '21'},
            ],
            'distritos': [],
            'barrios': [],
        }
        with mock.patch.object(locations, '_load', side_effect=data.__getitem__):
            self.assertEqual(locations.validate_locations(), [])

    def test_a_comarca_with_a_provincia_key_is_reported_as_stale(self):
        sys.path.insert(0, str(ROOT))
        from unittest import mock
        from seedlib import locations
        data = {
            'provincias': [{'codigo_ine': '08', 'nombre': 'Barcelona'}],
            'comarcas': [{'codigo': '01', 'nombre': 'A', 'provincia': '08'}],
            'municipios': [], 'distritos': [], 'barrios': [],
        }
        with mock.patch.object(locations, '_load', side_effect=data.__getitem__):
            problems = locations.validate_locations()
        self.assertEqual(len(problems), 1, problems)

    def test_comarcas_have_no_province_column_after_seeding(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'locations')
            columns = [r[1] for r in sqlite3.connect(db).execute('pragma table_info(base_comarca)')]
            self.assertNotIn('provincia_id', columns)
            municipios = sqlite3.connect(db).execute(
                'select count(*) from base_municipio where comarca_id is null').fetchone()[0]
            self.assertEqual(municipios, 0)

    def test_seeded_locations_pass_the_backend_consistency_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            out = self.run_seed(db, 'locations').stdout
            self.assertIn('location check: consistent', out)
            self.assertIn('location check: consistent', self.run_seed(db, 'check-locations').stdout)

    def test_check_locations_fails_when_a_listing_does_not_nest(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'locations')
            # A bulk import skips the model checks: a Barcelona district on a Badalona listing.
            script = (
                'import sys; sys.path.insert(0, %r); import seed; seed.setup_django()\n'
                'from base.models import Distrito, Inmueble, Municipio\n'
                "Inmueble.objects.bulk_create([Inmueble(referencia='BAD1',\n"
                "    municipio=Municipio.objects.get(codigo_ine='08015'), distrito=Distrito.objects.first())])\n"
            ) % str(ROOT)
            subprocess.run(
                [sys.executable, '-c', script], env={**os.environ, 'DB_SQLITE_PATH': db},
                capture_output=True, text=True, check=True)
            result = subprocess.run(
                [sys.executable, str(ROOT / 'seed.py'), 'check-locations'],
                env={**os.environ, 'DB_SQLITE_PATH': db}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn('BAD1', result.stdout)


if __name__ == '__main__':
    unittest.main()
