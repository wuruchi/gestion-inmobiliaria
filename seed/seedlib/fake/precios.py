"""Prices of fake offers: built-surface prices by district, adjusted per example and with some noise."""
from .lugares import _cargar, normalizar


class Precios:
    def __init__(self, municipio, es_barcelona):
        datos = _cargar('precios.json')
        self.es_barcelona = es_barcelona
        self.distritos = datos['barcelona_distritos']
        self.media_bcn = datos['barcelona_media']
        factor = datos['factor_por_defecto']
        for nombre, valores in datos['municipios'].items():
            if normalizar(nombre) == normalizar(municipio.nombre):
                factor = valores['factor']
        self.factor_municipio = factor

    def _base(self, distrito_codigo):
        if self.es_barcelona:
            return self.distritos.get(distrito_codigo or '', self.media_bcn)
        return {
            'venta_m2': self.media_bcn['venta_m2'] * self.factor_municipio,
            'alquiler_m2': self.media_bcn['alquiler_m2'] * self.factor_municipio,
            'indice_m2': [round(x * self.factor_municipio, 2) for x in self.media_bcn['indice_m2']],
        }

    def venta(self, rng, sup, distrito_codigo, factor):
        total = sup * self._base(distrito_codigo)['venta_m2'] * factor * rng.uniform(0.88, 1.14)
        paso = 5000 if total >= 500_000 else 1000
        return int(round(total / paso) * paso)

    def alquiler(self, rng, sup, distrito_codigo, factor, modalidad):
        mensual = sup * self._base(distrito_codigo)['alquiler_m2'] * factor * rng.uniform(0.88, 1.12)
        if modalidad == 'temporal':
            mensual *= 1.12  # furnished, short stays cost more per month
        return int(round(mensual / 5) * 5)

    def indice(self, rng, sup, distrito_codigo):
        """(minimum, maximum) of the state rent index for this surface, as the pages show it."""
        desde, hasta = self._base(distrito_codigo)['indice_m2']
        minimo = round(sup * desde * rng.uniform(0.97, 1.03), 2)
        maximo = round(minimo * rng.uniform(1.28, 1.40), 2)
        return minimo, maximo
