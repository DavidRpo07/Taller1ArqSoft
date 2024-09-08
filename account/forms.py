from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class FormularioRegistro(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre(s)',
            'last_name': 'Apellidos',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('El nombre de usuario ya está en uso. Por favor, elige otro.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@eafit.edu.co'):
            raise ValidationError('El correo electrónico debe terminar en @eafit.edu.co')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está en uso. Por favor, ingrese otro.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
