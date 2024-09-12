from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
# Create your views here.
from django.shortcuts import render, redirect
from .forms import FormularioRegistro

def register(request):
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirige a la vista de inicio de sesión después del registro
    else:
        form = FormularioRegistro()
    return render(request, 'registro/register.html', {'form': form})

# Perfil del usuario
@login_required
def user_profile(request):
    return render(request, 'cuenta/user_profile.html', {'user': request.user})