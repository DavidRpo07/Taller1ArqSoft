from django.db import models

# Create your models here.
class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    materia = models.CharField(max_length=100)
    calificacion_media = models.FloatField(default=0.0)  # Inicialmente 0.0

    def __str__(self):
        return self.nombre