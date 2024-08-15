from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Comentario, Profesor
from .forms import ComentarioForm
from profesores.models import Profesor

# Create your views here
def home(request):
    searchNombre = request.GET.get('searchNombre', '')
    searchMateria = request.GET.get('searchMateria', '')
    searchDepartamento = request.GET.get('searchDepartamento', '')

    # Inicialmente, selecciona todos los profesores
    profesores = Profesor.objects.all()

    # Filtra por nombre si se proporciona un valor
    if searchNombre:
        profesores = profesores.filter(nombre__icontains=searchNombre)
    
    # Filtra por materia si se proporciona un valor
    if searchMateria:
        profesores = profesores.filter(materia__icontains=searchMateria)
    
    # Filtra por departamento si se proporciona un valor
    if searchDepartamento:
        profesores = profesores.filter(departamento__icontains=searchDepartamento)

    return render(request, 'home.html', {
        'profesores': profesores,
        'searchNombre': searchNombre,
        'searchMateria': searchMateria,
        'searchDepartamento': searchDepartamento
    })

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