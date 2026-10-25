"""Photos and links of the saved example pages, reused by the fake offers.

The files are copied once into `MEDIA_ROOT/seed-examples/<example>/` (the backend serves that folder) and every
fake offer of that example points to the same copies, so a thousand offers cost the disk space of nine pages.
They are third-party images (portal watermarks included): this is a development tool, nothing here is committed.
"""
import json
import shutil
from pathlib import Path

from ..fetch import DATA_DIR

SUBCARPETA = 'seed-examples'
ALT = {
    'fachada': 'Fachada', 'salon': 'Salón', 'cocina': 'Cocina', 'dormitorio': 'Dormitorio', 'banio': 'Baño',
    'terraza': 'Terraza', 'jardin': 'Jardín', 'vistas': 'Vistas', 'piscina': 'Piscina', 'detalles': 'Detalles',
    'plano': 'Plano', 'otro': 'Interior',
}


def cargar_manifiesto():
    return json.loads((DATA_DIR / 'fake' / 'medios.json').read_text(encoding='utf-8'))['ejemplos']


class Medios:
    """Resolves the photos of an example and copies them into the media folder when needed."""

    def __init__(self, carpeta_ejemplos, media_root, copiar=True):
        self.carpeta_ejemplos = Path(carpeta_ejemplos)
        self.media_root = Path(media_root)
        self.copiar = copiar
        self.manifiesto = cargar_manifiesto()
        self._listos = {}
        self.copiados = 0

    def comprobar(self):
        if not self.carpeta_ejemplos.is_dir():
            raise SystemExit(
                f'Examples folder not found: {self.carpeta_ejemplos}. Pass --examples PATH, or --no-media.')

    def _origen(self, clave, archivo):
        for carpeta in sorted((self.carpeta_ejemplos / clave).glob('*_files')):
            candidato = carpeta / archivo
            if candidato.is_file():
                return candidato
        raise SystemExit(f'Photo {archivo} of {clave} not found in {self.carpeta_ejemplos / clave}.')

    def fotos(self, clave):
        """List of `(ruta_relativa, tipo, es_principal)` ready to store in `ImageInmueble.image`."""
        if clave in self._listos:
            return self._listos[clave]
        datos = self.manifiesto[clave]
        filas = []
        for foto in datos['fotos']:
            relativa = f'{SUBCARPETA}/{clave}/{foto["archivo"]}'
            destino = self.media_root / relativa
            if self.copiar:
                origen = self._origen(clave, foto['archivo'])
                if not destino.exists() or destino.stat().st_size != origen.stat().st_size:
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(origen, destino)
                    self.copiados += 1
            filas.append((relativa, foto['tipo'], foto['archivo'] == datos['defecto']))
        self._listos[clave] = filas
        return filas

    def enlaces(self, clave):
        return self.manifiesto[clave]['medios']
