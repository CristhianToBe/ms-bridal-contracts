from django.db import models

class Dress(models.Model):
    notion_page_id = models.CharField(max_length=64, unique=True)
    referencia = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.referencia

class Client(models.Model):
    # si luego metes BD de clientes real, esto se vuelve tu “catálogo”
    nombre = models.CharField(max_length=255)
    telefono_1 = models.CharField(max_length=50, blank=True, null=True)
    telefono_2 = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("nombre", "telefono_1")
