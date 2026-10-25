from django.conf import settings
from django.db import models


def _usuario():
    return models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        editable=False, related_name='+',
    )


class Auditoria(models.Model):
    """Who created and last changed a row, and when. The admin fills the users; `update()` and scripts do not."""

    created_by = _usuario()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = _usuario()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
