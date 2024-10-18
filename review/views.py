from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Comentario, Profesor
from .forms import ComentarioForm
from django.http import HttpResponseForbidden
from django.contrib import messages
import openai
from django.conf import settings
from account.models import UserProfile
from django.contrib.auth.models import User
from django.db.models import Avg

# Inicializar el cliente de OpenAI
openai.api_key = settings.OPENAI_API_KEY
# Función para verificar si el usuario es administrador
def is_admin(user):
    return user.is_staff


def revisar_comentario_por_ia(contenido):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Revisa este comentario y determina si es apropiado."},
                  {"role": "user", "content": contenido}]
    )
    resultado = response.choices[0].message.content.strip()
    if resultado.lower() == 'aprobado':
        return True
    else:
        return False

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

# Vista para agregar un comentario a un profesor
@login_required
def agregar_comentario(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    
    # Obtener el UserProfile del usuario actual
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    
    # Verificar si el usuario está suspendido
    if user_profile.is_suspended:
        messages.error(request, 'Tu cuenta está suspendida y no puedes agregar comentarios.')
        return redirect('detalle_profesor', profesor_id=profesor.id)
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.profesor = profesor
            comentario.usuario = request.user  # Siempre asignar el usuario

            # Revisar si el comentario es anónimo
            es_anonimo = request.POST.get('anonimo') == 'on'
            comentario.anonimo = es_anonimo  # Marcar como anónimo
            
            # Revisamos el comentario con la IA
            aprobado = revisar_comentario_por_ia(comentario.contenido)
            if aprobado:
                comentario.aprobado_por_ia = True
                comentario.save()
                messages.success(request, 'Tu comentario ha sido aprobado y publicado.')
                return redirect('detalle_profesor', profesor_id=profesor.id)
            else:
                form.add_error(None, "Tu comentario ha sido rechazado por no cumplir con las normas.")
    else:
        form = ComentarioForm()
    
    return render(request, 'review/agregar_comentario.html', {
        'form': form,
        'profesor': profesor
    })



# Detalle de un profesor con sus comentarios aprobados
def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    comentarios = profesor.comentarios.filter(aprobado_por_ia=True)  # Solo mostrar comentarios aprobados
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
    messages.success(request, 'Comentario eliminado.')
    return redirect('manage_reviews')

# Vista para editar una reseña (solo si es el propietario)
@login_required
def edit_review(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verificar que el usuario actual sea el propietario del comentario
    if comentario.usuario != request.user and not request.user.is_staff:
        return HttpResponseForbidden()  # Retorna un error 403 si el usuario no es el propietario o admin
    
    # Si el método es POST, procesamos el formulario
    if request.method == 'POST':
        form = ComentarioForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()  # Guardar los cambios
            return redirect('mis_comentarios', user_id=request.user.id)  # Redirigir a la página de "Mis Comentarios"
    else:
        # Si es un GET, mostrar el formulario con los datos actuales del comentario
        form = ComentarioForm(instance=comentario)
    
    return render(request, 'review/edit_review.html', {'form': form, 'comentario': comentario, 'usuario': request.user})

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
def mis_comentarios(request, user_id):
    # Si se proporciona un user_id, buscar los comentarios de ese usuario
    if user_id:
        usuario = get_object_or_404(User, id=user_id)
    else:
        # Si no se proporciona user_id, usar el usuario autenticado
        usuario = request.user
    is_admin = request.user.is_staff
    comentarios = Comentario.objects.filter(usuario=usuario).order_by('-fecha')

    return render(request, 'review/mis_comentarios.html', {'comentarios': comentarios, 'usuario': usuario, 'is_admin': is_admin})

def estadisticas(request):
    profesores = Profesor.objects.all()  # Obtener todos los profesores para el selector
    profesor_seleccionado = None
    promedios_por_semestre = {}

    if request.method == 'POST':
        profesor_id = request.POST.get('profesor')  # Obtener el ID del profesor seleccionado

        if profesor_id:
            profesor_seleccionado = Profesor.objects.get(id=profesor_id)

            # Obtener el promedio de rating por cada semestre del profesor seleccionado
            promedios_por_semestre = (Comentario.objects
                                      .filter(profesor=profesor_seleccionado)
                                      .values('fecha')
                                      .annotate(promedio_rating=Avg('rating'))
                                      .order_by('fecha'))

            promedios_por_semestre = list(promedios_por_semestre)

    return render(request, 'statistics/estadisticas.html', {
        'profesores': profesores,
        'profesor_seleccionado': profesor_seleccionado,
        'promedios_por_semestre': promedios_por_semestre
    })