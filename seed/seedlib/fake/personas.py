"""Fake owners (people and companies) for the fake offers. Every one uses an `@dev.example` e-mail, which is how
`--clean` recognises them."""
import json

from ..fetch import DATA_DIR

DOMINIO = 'dev.example'
LETRAS_DNI = 'TRWAGMYFPDXBNJZSQVHLCKE'


def _nombres():
    return json.loads((DATA_DIR / 'fake' / 'nombres.json').read_text(encoding='utf-8'))


def _sin_tildes(texto):
    import unicodedata
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode().lower().replace(' ', '')


class Propietarios:
    def __init__(self, rng):
        from base.models import Propietario

        self.rng = rng
        self.datos = _nombres()
        self.existentes = list(Propietario.objects.filter(email__endswith='@' + DOMINIO))
        self.nifs = set(Propietario.objects.exclude(nif='').values_list('nif', flat=True))
        self.creados = 0

    def _nif(self, empresa):
        while True:
            if empresa:
                nif = 'B' + ''.join(str(self.rng.randint(0, 9)) for _ in range(7)) + str(self.rng.randint(0, 9))
            else:
                n = self.rng.randint(10_000_000, 99_999_999)
                nif = f'{n}{LETRAS_DNI[n % 23]}'
            if nif not in self.nifs:
                self.nifs.add(nif)
                return nif

    def nuevo(self):
        from base.models import Propietario

        rng, d = self.rng, self.datos
        empresa = rng.random() < 0.15
        if empresa:
            nombre = f'{rng.choice(d["empresas"])} {rng.choice(d["sufijos_empresa"])}'
        else:
            nombre = f'{rng.choice(d["nombres"])} {rng.choice(d["apellidos"])} {rng.choice(d["apellidos"])}'
        correo = f'{_sin_tildes(nombre)[:24]}{rng.randint(1, 99)}@{DOMINIO}'
        propietario = Propietario.objects.create(
            nombre=nombre, nif=self._nif(empresa), email=correo,
            telefono=f'+34 {rng.choice("67")}{rng.randint(10_000_000, 99_999_999)}',
            gran_tenedor=empresa and rng.random() < 0.3,
        )
        self.existentes.append(propietario)
        self.creados += 1
        return propietario

    def elegir(self):
        """A new owner, or (30 %) one that already owns another fake listing."""
        if self.existentes and self.rng.random() < 0.3:
            return self.rng.choice(self.existentes)
        return self.nuevo()
