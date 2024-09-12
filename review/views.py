from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Comentario, Profesor
from .forms import ComentarioForm
from django.http import HttpResponseForbidden

# Función para verificar si el usuario es administrador
def is_admin(user):
    return user.is_staff

# Home con búsqueda de profesores
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

# Agregar un comentario a un profesor
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

# Detalle de un profesor con sus comentarios
def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    comentarios = profesor.comentarios.all()
    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios
    })


# Vista para que los administradores gestionen las reseñas
@user_passes_test(is_admin)
def manage_reviews(request):
    comentarios = Comentario.objects.all()  # Mostrar todas las reseñas
    return render(request, 'review/manage_reviews.html', {
        'comentarios': comentarios
    })

# Vista para que los administradores eliminen una reseña inapropiada
@user_passes_test(is_admin)
def delete_review(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    comentario.delete()
    return redirect('manage_reviews')

# Vista para editar una reseña (solo si es el propietario)
@login_required
def edit_review(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verificar que el usuario actual sea el propietario del comentario
    if comentario.usuario != request.user:
        return HttpResponseForbidden()  # Retorna un error 403 si el usuario no es el propietario
    
    # Si el método es POST, procesamos el formulario
    if request.method == 'POST':
        form = ComentarioForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()  # Guardar los cambios
            return redirect('mis_comentarios')  # Redirigir a la página de "Mis Comentarios"
    else:
        # Si es un GET, mostrar el formulario con los datos actuales del comentario
        form = ComentarioForm(instance=comentario)
    
    return render(request, 'review/edit_review.html', {'form': form, 'comentario': comentario})


# Vista para eliminar una reseña (solo si es el propietario)
@login_required
def delete_own_review(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    if comentario.usuario != request.user:
        return HttpResponseForbidden()  # Solo el propietario del comentario puede eliminarlo
    
    comentario.delete()
    return redirect('detalle_profesor', profesor_id=comentario.profesor.id)

# Vista para mostrar "Mis comentarios"
@login_required
def mis_comentarios(request):
    # Filtrar comentarios que pertenecen al usuario autenticado
    comentarios = Comentario.objects.filter(usuario=request.user)
    return render(request, 'review/mis_comentarios.html', {'comentarios': comentarios})


