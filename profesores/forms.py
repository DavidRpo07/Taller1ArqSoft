# profesores/forms.py
"""
Formularios para la aplicación de profesores.
Movidos desde models.py para respetar el principio de separación de responsabilidades.
"""

from django import forms
from .models import Profesor, Materia


class UploadCSVForm(forms.Form):
    """Formulario para subir archivos CSV con datos de profesores"""
    file = forms.FileField(label='Subir archivo CSV')


class ProfesorForm(forms.ModelForm):
    """
    Formulario para crear y editar profesores.
    Incluye integración con Select2 para selección múltiple de materias.
    """
    materias = forms.ModelMultipleChoiceField(
        queryset=Materia.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'style': 'width: 100%;'
        }),
        required=False,
        label="Materias"
    )

    class Meta:
        model = Profesor
        fields = ['nombre', 'departamento', 'materias']


class MateriaForm(forms.ModelForm):
    """Formulario para crear y editar materias"""
    
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
