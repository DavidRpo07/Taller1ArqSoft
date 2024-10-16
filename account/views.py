from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib import messages
from .forms import FormularioRegistro
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

def register(request):
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear el UserProfile para el nuevo usuario
            UserProfile.objects.create(user=user)
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')  # Redirige a la vista de inicio de sesión después del registro
    else:
        form = FormularioRegistro()
    return render(request, 'registro/register.html', {'form': form})

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
    })