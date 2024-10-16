from django import forms
from .models import Comentario

class ComentarioForm(forms.ModelForm):
    anonimo = forms.BooleanField(required=False)
    class Meta:
        model = Comentario
        fields = ['contenido', 'rating','anonimo']

# Intentar que si escogen 0 no deje
    '''def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating == 0:
            raise forms.ValidationError("Por favor, seleccione una calificación válida.")
        return rating'''
