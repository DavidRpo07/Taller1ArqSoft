from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Comentario, Profesor
from .forms import ComentarioForm
from profesores.models import Profesor

# Create your views here.
def home(request):
    return render(request, 'home.html')


@login_required
def agregar_comentario(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.profesor = profesor
            comentario.usuario = request.user
            comentario.save()
            return redirect('detalle_profesor', profesor_id=profesor.id)
    else:
        form = ComentarioForm()
    return render(request, 'review/agregar_comentario.html', {
        'form': form,
        'profesor': profesor
    })


def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    comentarios = profesor.comentarios.all()
    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios
    })

@login_required
def user_profile(request):
    return render(request, 'review/user_profile.html', {'user': request.user})