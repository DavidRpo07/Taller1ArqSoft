from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Comentario
from profesores.models import Profesor, Materia
from django.http import HttpResponseForbidden
from django.contrib import messages
import openai
import os
from account.models import UserProfile
from django.contrib.auth.models import User
from django.db.models import Avg
from dotenv import load_dotenv, find_dotenv
# Importar la Facade para usar el patrón Facade
from .facades import ComentarioFacade

_ = load_dotenv('keys.env')
# Inicializar el cliente de OpenAI

openai.api_key = os.environ.get('OPENAI_API_KEY')

# Función para verificar si el usuario es administrador
def is_admin(user):
    return user.is_staff


class ComentarioAprobador:
    def aprobar(self, comentario):
        raise NotImplementedError("Debes implementar el método aprobar.")

class ComentarioAprobadorManual(ComentarioAprobador):
    def aprobar(self, comentario):
        return True

class ComentarioAprobadorIA(ComentarioAprobador):
    def aprobar(self, comentario):
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        respuesta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente que revisa comentarios para identificar si contienen palabras ofensivas."},
                {"role": "user", "content": f"Revisa el siguiente comentario y devuelve 'aprobado' si es apropiado o 'no' si contiene palabras ofensivas:\n\nComentario: \"{comentario}\""}
            ],
            max_tokens=3,
            temperature=0
        )
        resultado = respuesta['choices'][0]['message']['content'].strip().lower()
        return resultado == 'aprobado'


def revisar_comentario_por_ia(contenido):    
        respuesta = openai.ChatCompletion.create(
        model="gpt-4",  
        messages=[
            {"role": "system", "content": "Eres un asistente que revisa comentarios para identificar si contienen palabras ofensivas."},
            {"role": "user", "content": f"Revisa el siguiente comentario y devuelve 'aprobado' si es apropiado o 'no' si contiene palabras ofensivas:\n\nComentario: \"{contenido}\""}
        ],
        max_tokens=3,  # Reducido para ahorrar tokens
        temperature=0
    )
        resultado = respuesta['choices'][0]['message']['content'].strip().lower()
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
    """
    Vista simplificada usando el patrón Facade.
    La lógica compleja se delega a ComentarioFacade.
    """
    from review.forms import ComentarioForm
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    
    # Crear instancia de la fachada
    facade = ComentarioFacade()
    
    # Verificar permisos usando la fachada (que usa el patrón State internamente)
    puede_comentar, mensaje = facade.puede_usuario_comentar(request.user)
    if not puede_comentar:
        messages.error(request, mensaje)
        return redirect('detalle_profesor', profesor_id=profesor.id)
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST, profesor=profesor)
        if form.is_valid():
            es_anonimo = request.POST.get('anonimo') == 'on'
            
            # Delegar toda la lógica compleja a la fachada
            exito, comentario, mensaje = facade.crear_comentario(
                form_data=form.cleaned_data,
                profesor=profesor,
                usuario=request.user,
                es_anonimo=es_anonimo
            )
            
            if exito:
                messages.success(request, mensaje)
                return redirect('detalle_profesor', profesor_id=profesor.id)
            else:
                messages.error(request, mensaje)
    else:
        form = ComentarioForm(profesor=profesor)
    
    return render(request, 'review/agregar_comentario.html', {
        'form': form,
        'profesor': profesor
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
    """
    Vista simplificada usando el patrón Facade.
    La lógica de edición se delega a ComentarioFacade.
    """
    from review.forms import ComentarioForm
    
    # Crear instancia de la fachada
    facade = ComentarioFacade()
    
    # Obtener el comentario para mostrar en el formulario
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    # Verificar permisos básicos antes de procesar
    if comentario.usuario != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST, instance=comentario, profesor=comentario.profesor)
        if form.is_valid():
            # Usar la fachada para editar el comentario
            exito, comentario_editado, mensaje = facade.editar_comentario(
                comentario_id=comentario_id,
                usuario=request.user,
                nuevos_datos=form.cleaned_data
            )
            
            if exito:
                messages.success(request, mensaje)
                return redirect('mis_comentarios', user_id=request.user.id)
            else:
                messages.error(request, mensaje)
    else:
        form = ComentarioForm(instance=comentario, profesor=comentario.profesor)
    
    return render(request, 'review/edit_review.html', {
        'form': form,
        'comentario': comentario,
        'usuario': request.user
    })

# Vista para eliminar una reseña (solo si es el propietario)
@login_required
def delete_own_review(request, comentario_id):
    """
    Vista simplificada usando el patrón Facade.
    La lógica de eliminación se delega a ComentarioFacade.
    """
    # Crear instancia de la fachada
    facade = ComentarioFacade()
    
    # Usar la fachada para eliminar el comentario
    exito, profesor_id, mensaje = facade.eliminar_comentario(
        comentario_id=comentario_id,
        usuario=request.user
    )
    
    if exito:
        messages.success(request, mensaje)
        if profesor_id:
            return redirect('detalle_profesor', profesor_id=profesor_id)
        else:
            return redirect('home')
    else:
        messages.error(request, mensaje)
        return redirect('home')

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
