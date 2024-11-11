from django import forms
from .models import Comentario

class ComentarioForm(forms.ModelForm):
    anonimo = forms.BooleanField(required=False)

    class Meta:
        model = Comentario
        fields = ['materia', 'contenido', 'rating', 'anonimo', 'fecha']

    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)  # Recibe el profesor desde la vista
        super().__init__(*args, **kwargs)
        if profesor:
            # Filtra las materias para que solo se muestren las asociadas al profesor
            self.fields['materia'].queryset = profesor.materias.all()
        self.fields['materia'].widget.attrs.update({'class': 'form-control'}) 
        self.fields['contenido'].widget.attrs.update({'class': 'form-control'})
        self.fields['rating'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha'].widget.attrs.update({'class': 'form-control'})

# Intentar que si escogen 0 no deje
    '''def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating == 0:
            raise forms.ValidationError("Por favor, seleccione una calificación válida.")
        return rating'''
