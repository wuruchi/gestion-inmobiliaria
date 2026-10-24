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

    def test_a_modalidad_that_already_has_a_default_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'modalidades')
            conn = sqlite3.connect(db)
            conn.execute(
                "insert into base_condiciones (nombre, modalidad_id, por_defecto, honorarios, itp, incluido, "
                "no_incluido, fianza, pago_adelantado, suministros, limpieza_final, requisitos, notaria, "
                "registro, gestoria, honorarios_comprador) "
                "select 'Mi venta', id, 1, '', '', '', '', '', '', '', '', '', '', '', '', '' "
                "from base_modalidad where codigo='venta'")
            conn.commit()
            conn.close()
            self.run_seed(db, 'condiciones')
            names = [r[0] for r in sqlite3.connect(db).execute(
                'select nombre from base_condiciones order by nombre')]
            self.assertEqual(names, ['Alquiler de temporada', 'Alquiler de vivienda habitual', 'Mi venta'])

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
        self.assertEqual(len(problems), 5, problems)

    def test_municipio_province_is_checked_on_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / 'test.sqlite3')
            self.run_seed(db, 'migrate')
            self.run_seed(db, 'locations')
            c = sqlite3.connect(db)
            bad = c.execute(
                "select count(*) from base_municipio m join base_provincia p on p._id = m.provincia_id "
                "where substr(m.codigo_ine, 1, 2) != p.codigo_ine").fetchone()[0]
            self.assertEqual(bad, 0)


if __name__ == '__main__':
    unittest.main()
