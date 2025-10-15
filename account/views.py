from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import UserProfile, PendingUser
from django.contrib import messages
from .forms import FormularioRegistro
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
import random # Para generar un codigo de confirmación
from django.db import IntegrityError


def register(request):
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)
        if form.is_valid():
            # Verificar si el nombre de usuario o el correo ya existen
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']

            if PendingUser.objects.filter(username=username).exists():
                form.add_error('username', 'Este nombre de usuario ya está en uso.')
            elif PendingUser.objects.filter(email=email).exists():
                form.add_error('email', 'Este correo ya está en uso.')
            else:
                # Si no existen, procede a crear el usuario pendiente
                codigo = random.randint(100000, 999999)
                pending_user = PendingUser.objects.create(
                    email=email,
                    username=username,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=form.cleaned_data['password1'],  # La contraseña se encripta luego
                    confirmation_code=str(codigo),
                )

                # Enviar el correo con el código de confirmación
                send_mail(
                    'Código de Confirmación',
                    f'Tu código de confirmación es: {pending_user.confirmation_code}',
                    'profepulse@gmail.com',
                    [pending_user.email],
                    fail_silently=False,
                )

                messages.success(request, 'Hemos enviado un código de confirmación a tu correo. Por favor, verifica.')
                return redirect('confirmar_cuenta')  # Redirigir a la vista de confirmación
    else:
        form = FormularioRegistro()

    return render(request, 'registro/register.html', {'form': form})


def confirmar_cuenta(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        confirmation_code = request.POST.get('codigo')

        try:
            pending_user = PendingUser.objects.get(email=email, confirmation_code=confirmation_code)

            user = User.objects.create_user(
                username=pending_user.username,
                email=pending_user.email,
                first_name=pending_user.first_name,
                last_name=pending_user.last_name,
                password=pending_user.password,
            )
            pending_user.delete()

            # Añadir mensaje de éxito
            messages.success(request, 'Cuenta confirmada exitosamente. Ahora puedes iniciar sesión.')
            return redirect('login')  # Redirige al formulario de inicio de sesión
        except PendingUser.DoesNotExist:
            messages.error(request, 'El código de confirmación o el correo son incorrectos.')

    return render(request, 'registro/confirmar_cuenta.html')

# Perfil del usuario
@login_required
def user_profile(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    # Obtener el perfil del usuario, o devolver 404 si no existe
    user_profile = get_object_or_404(UserProfile, user__id=user_id)
    is_admin = request.user.is_superuser  # Verificar si el usuario actual es admin

    if request.method == 'POST' and is_admin:
        # Manejar la suspensión o activación del usuario
        if 'suspend' in request.POST:
            user_profile.is_suspended = True
            user_profile.save()
            messages.success(request, f'Usuario {user_profile.user.username} suspendido correctamente.')
            return redirect('user_profile', user_id=user_id)
        elif 'activate' in request.POST:
            user_profile.is_suspended = False
            user_profile.save()
            messages.success(request, f'Usuario {user_profile.user.username} reactivado correctamente.')
            return redirect('user_profile', user_id=user_id)

    return render(request, 'cuenta/user_profile.html', {
        'user_profile': user_profile,
        'is_admin': is_admin,
        'usuario': usuario,
        'mensaje_estado': user_profile.mensaje_estado(),
    })