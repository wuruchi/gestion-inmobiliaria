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
            self.assertEqual(self.count(db, 'modalidad'), 4)
            codes = [r[0] for r in sqlite3.connect(db).execute(
                'select codigo from base_modalidad order by orden')]
            self.assertEqual(codes, ['temporal', 'habitual', 'venta', 'otros'])
            row = sqlite3.connect(db).execute(
                "select nombre from base_municipio where codigo_ine='08019'").fetchone()
            self.assertEqual(row[0], 'Barcelona')


if __name__ == '__main__':
    unittest.main()
