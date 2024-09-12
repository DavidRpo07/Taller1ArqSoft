from django.shortcuts import render

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
