from django.db import models
from django import forms

# Create your models here.
class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    materia = models.CharField(max_length=100)
    calificacion_media = models.FloatField(default=0.0)  # Inicialmente 0.0
    numcomentarios = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre

class UploadCSVForm(forms.Form):
    file = forms.FileField(label='Subir archivo CSV')


class ProfesorForm(forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ['nombre', 'departamento', 'materia']
        labels = {'departamento':'Área'}