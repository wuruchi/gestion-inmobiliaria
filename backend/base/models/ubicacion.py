from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class SlugMixin(models.Model):
    """Fills `slug` from `nombre` when it is left empty."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Provincia(SlugMixin):
    _id = models.AutoField(primary_key=True, editable=False)
    codigo_ine = models.CharField(max_length=2, unique=True)  # '08'
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self) -> str:
        return self.nombre


class Comarca(SlugMixin):
    _id = models.AutoField(primary_key=True, editable=False)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, related_name='comarcas'
    )
    codigo = models.CharField(max_length=2)  # official code, e.g. '21'
    nombre = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['provincia', 'codigo'], name='uniq_comarca_codigo'
            ),
            models.UniqueConstraint(
                fields=['provincia', 'slug'], name='uniq_comarca_slug'
            ),
        ]

    def __str__(self) -> str:
        return self.nombre


class Municipio(SlugMixin):
    _id = models.AutoField(primary_key=True, editable=False)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, related_name='municipios'
    )
    comarca = models.ForeignKey(
        Comarca,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='municipios',
    )
    # 5-digit INE code: 2 digits province + 3 digits municipality ('08019').
    codigo_ine = models.CharField(max_length=5, unique=True)
    nombre = models.CharField(max_length=150)
    slug = models.SlugField()
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['provincia', 'slug'], name='uniq_municipio_slug'
            ),
        ]

    def validate_location(self):
        """The code starts with the province's and the comarca is in the same province."""
        if self.provincia_id and not self.codigo_ine.startswith(
            self.provincia.codigo_ine
        ):
            raise ValidationError(
                {'codigo_ine': 'El código INE no empieza por el de la provincia.'}
            )
        if self.comarca_id and self.comarca.provincia_id != self.provincia_id:
            raise ValidationError(
                {'comarca': 'La comarca no pertenece a la provincia.'}
            )

    def clean(self):
        super().clean()
        self.validate_location()

    def save(self, *args, **kwargs):
        self.validate_location()
        super().save(*args, **kwargs)

    def es_zona_tensionada(self, fecha=None):
        """A declaration is in force on `fecha` (today); uses prefetched `declaraciones_tensionada`."""
        fecha = fecha or timezone.localdate()
        return any(d.en_vigor(fecha) for d in self.declaraciones_tensionada.all())

    def __str__(self) -> str:
        return self.nombre


class Distrito(SlugMixin):
    _id = models.AutoField(primary_key=True, editable=False)
    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, related_name='distritos'
    )
    codigo = models.CharField(max_length=3)  # official local code, e.g. '02'
    nombre = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        ordering = ['codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['municipio', 'codigo'], name='uniq_distrito_codigo'
            ),
            models.UniqueConstraint(
                fields=['municipio', 'slug'], name='uniq_distrito_slug'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.nombre} ({self.municipio.nombre})'


class Barrio(SlugMixin):
    _id = models.AutoField(primary_key=True, editable=False)
    distrito = models.ForeignKey(
        Distrito, on_delete=models.PROTECT, related_name='barrios'
    )
    codigo = models.CharField(max_length=3)  # official local code, e.g. '01'
    nombre = models.CharField(max_length=150)
    slug = models.SlugField()

    class Meta:
        ordering = ['codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['distrito', 'codigo'], name='uniq_barrio_codigo'
            ),
            models.UniqueConstraint(
                fields=['distrito', 'slug'], name='uniq_barrio_slug'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.nombre} ({self.distrito.nombre})'
