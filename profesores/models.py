from django.db import models

# Create your models here.
class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    materias = models.ManyToManyField('Materia', related_name='profesores')
    calificacion_media = models.FloatField(default=0.0)  # Calificación general del profesor
    numcomentarios = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    calificacion_media = models.FloatField(default=0.0)
    numcomentarios = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre}"
