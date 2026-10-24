from django.db import models
from base.models.inmueble import Inmueble

class AreaRecreo(models.Model):
    inmueble = models.OneToOneField(Inmueble, on_delete=models.CASCADE, null=False)
    zona_deportiva = models.BooleanField(default=False)
    gimnasio = models.BooleanField(default=False)
    piscina = models.BooleanField(default=False)
    solarium = models.BooleanField(default=False)
    jardin_infantil = models.BooleanField(default=False)
    local_social = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.inmueble.referencia} - Area Recreo'