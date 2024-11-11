from django.db import models
from django import forms

# Create your models here.
class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    materias = models.ManyToManyField('Materia', related_name='profesores')
    calificacion_media = models.FloatField(default=0.0)  # Calificación general del profesor
    numcomentarios = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre

class UploadCSVForm(forms.Form):
    file = forms.FileField(label='Subir archivo CSV')


class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    calificacion_media = models.FloatField(default=0.0)
    numcomentarios = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre}"
    

class ProfesorForm(forms.ModelForm):
    materias = forms.ModelMultipleChoiceField(
        queryset=Materia.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',  # Clase adicional para integrar Select2
            'style': 'width: 100%;'  # Estilo opcional para ajustar el ancho
        }),
        required=False,
        label="Materias"
    )

    class Meta:
        model = Profesor
        fields = ['nombre', 'departamento', 'materias']

class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la materia',
            }),
        }
        labels = {
            'nombre': 'Nombre de la Materia',
        }