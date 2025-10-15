from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
import csv
from django.contrib import messages
from .models import Profesor, Materia
from .forms import UploadCSVForm, ProfesorForm, MateriaForm
from review.models import Comentario
from django.db.models import Avg, Count, Q
# Importar el ChartFactory para usar el patrón Factory
from .chart_factory import ChartFactory
# Importar el RecommendationEngine para usar el patrón Strategy
from .recommendation_strategies import RecommendationEngine


def is_admin(user):
    return user.is_staff


def lista_profesores(request):
    """
    Lista profesores con filtros y sistema de recomendación usando patrón Strategy.
    """
    searchNombre = request.GET.get('searchNombre', '').strip()
    searchMateria = request.GET.get('searchMateria', '').strip()
    orden_field = request.GET.get('orden_field', '')

    # Selecciona inicialmente todos los profesores
    profesores = Profesor.objects.all()

    # Filtrar por nombre del profesor
    if searchNombre:
        profesores = profesores.filter(nombre__icontains=searchNombre)
    
    # Filtrar por materias asociadas (ManyToMany)
    if searchMateria:
        profesores = profesores.filter(materias__nombre__icontains=searchMateria).distinct()

    # Sistema de Recomendación usando patrón Strategy
    if orden_field:
        # Mapeo de valores del frontend a estrategias
        strategy_map = {
            'mayor_rating': 'best_rated',
            'menor_rating': 'alphabetical',  # fallback
            'mayor_comentarios': 'most_reviewed',
            'menor_comentarios': 'alphabetical',  # fallback
            'recomendado': 'balanced',  # Nueva opción
        }
        
        strategy_name = strategy_map.get(orden_field, 'best_rated')
        
        # Crear motor de recomendación con la estrategia seleccionada
        recommendation_engine = RecommendationEngine(strategy_name)
        profesores = recommendation_engine.recommend(profesores)
    else:
        # Por defecto: usar estrategia de mejor calificados primero
        recommendation_engine = RecommendationEngine('best_rated')
        profesores = recommendation_engine.recommend(profesores)

    return render(request, 'lista_profesores.html', {
        'profesores': profesores,
        'searchNombre': searchNombre,
        'searchMateria': searchMateria,
        'orden_field': orden_field
    })


def detalle_profesor(request, profesor_id):
    # Obtener el profesor
    profesor = get_object_or_404(Profesor, pk=profesor_id)

    # Obtener todas las materias asociadas al profesor
    materias = profesor.materias.all()

    # Obtener los parámetros desde la URL
    materia_id = request.GET.get('materia', 'todas')  # Default: todas las materias
    semestre = request.GET.get('semestre', '')  # Default: todos los semestres
    rating = request.GET.get('rating', '')  # Default: todos los ratings

    # Filtrar comentarios para las gráficas (solo filtros de materia y semestre)
    comentarios_grafica = Comentario.objects.filter(profesor=profesor, aprobado_por_ia=True)
    if materia_id != 'todas':
        comentarios_grafica = comentarios_grafica.filter(materia_id=materia_id)
    if semestre:
        comentarios_grafica = comentarios_grafica.filter(fecha=semestre)

    # Extraer ratings para las gráficas
    ratings_grafica = [comentario.rating for comentario in comentarios_grafica]

    # Gráficas usando el patrón Factory:
    # Mostrar ambas gráficas si no se filtra por semestre
    # Mostrar solo la gráfica de barras si hay filtro por semestre
    grafica_barras = ChartFactory.create_chart('bar', ratings_grafica) if comentarios_grafica.exists() else None
    grafica_por_semestre = None
    if not semestre:
        grafica_por_semestre = (
            ChartFactory.create_chart('line', comentarios_grafica)
            if comentarios_grafica.exists()
            else None
        )

    # Filtrar comentarios para mostrar (todos los filtros: materia, semestre, rating)
    comentarios_display = Comentario.objects.filter(profesor=profesor, aprobado_por_ia=True)
    if materia_id != 'todas':
        comentarios_display = comentarios_display.filter(materia_id=materia_id)
    if semestre:
        comentarios_display = comentarios_display.filter(fecha=semestre)
    if rating:
        comentarios_display = comentarios_display.filter(rating=rating)

    # Generar lista de semestres disponibles
    semestres_disponibles = Comentario.objects.filter(profesor=profesor).values_list('fecha', flat=True).distinct()

    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'materias': materias,
        'comentarios_mostrados': comentarios_display,  # Comentarios para mostrar
        'grafica_barras': grafica_barras,
        'grafica_por_semestre': grafica_por_semestre,
        'materia_seleccionada': materia_id,
        'semestre_seleccionado': semestre,
        'rating_seleccionado': rating,
        'semestres_disponibles': semestres_disponibles,
    })

def upload_csv(request):
    form = UploadCSVForm()
    profesor_form = ProfesorForm()

    if request.method == 'POST':
        if 'upload_csv' in request.POST:
            form = UploadCSVForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.reader(decoded_file)

                # Saltar la fila de encabezado
                next(reader)

                for row in reader:
                    # Normalizar el nombre del profesor y departamento
                    profesor_nombre = row[0].strip().title()  # Formato de título
                    departamento = row[1].strip().title()

                    # Buscar o crear el profesor
                    profesor, created = Profesor.objects.get_or_create(
                        nombre=profesor_nombre,
                        departamento=departamento,
                        defaults={'calificacion_media': 0.0, 'numcomentarios': 0}
                    )

                    # Procesar materias
                    materias_nombres = row[2].strip()[1:-1].split(';')  # Quitar corchetes y dividir por punto y coma
                    for materia_nombre in materias_nombres:
                        materia_nombre = materia_nombre.strip().title()  # Normalizar cada materia
                        if materia_nombre:
                            # Crear o obtener la materia
                            materia, _ = Materia.objects.get_or_create(nombre=materia_nombre)

                            # Asociar la materia al profesor
                            profesor.materias.add(materia)

                messages.success(request, 'Archivo CSV subido y procesado correctamente.')
                return redirect('agregar_profesor')

        elif 'add_profesor' in request.POST:
            profesor_form = ProfesorForm(request.POST)
            if profesor_form.is_valid():
                profesor_form.save()
                messages.success(request, 'Profesor agregado correctamente.')
                return redirect('agregar_profesor')

    return render(request, 'profesores/agregar_profesor.html', {
        'form': form,
        'profesor_form': profesor_form
    })


@user_passes_test(is_admin)
def manage_profesor(request):
    profesores = Profesor.objects.all()  # Mostrar todas las reseñas
    return render(request, 'profesores/eliminar_profesor.html', {
        'profesores': profesores
    })

@user_passes_test(is_admin)
def delete_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, id=profesor_id)
    profesor.delete()
    messages.success(request, 'Profesor eliminado.')
    return redirect('manage_profesor')

@user_passes_test(is_admin)
def edit_profesor(request, profesor_id):
    # Obtener el profesor por ID, o devolver un 404 si no existe
    profesor = get_object_or_404(Profesor, id=profesor_id)
    
    # Si el formulario se envía (POST), procesamos los datos
    if request.method == 'POST':
        profesor_form = ProfesorForm(request.POST, instance=profesor)
        if profesor_form.is_valid():
            # Guardar los datos básicos del profesor sin afectar las materias
            profesor = profesor_form.save(commit=False)

            # Obtener las materias seleccionadas del formulario
            materias_seleccionadas = profesor_form.cleaned_data.get('materias')

            # Guardar el profesor antes de modificar las materias
            profesor.save()

            # Actualizar las materias del profesor
            if materias_seleccionadas:
                profesor.materias.add(*materias_seleccionadas)  # Agregar materias sin eliminar las existentes
            
            messages.success(request, 'Profesor editado correctamente.')
            return redirect('manage_profesor')  # Redirigir a una vista de lista de profesores o a donde prefieras
    else:
        # Si es GET, cargamos el formulario con los datos actuales del profesor
        profesor_form = ProfesorForm(instance=profesor)
    
    return render(request, 'profesores/editar_profesor.html', {
        'profesor_form': profesor_form,
        'profesor': profesor  # Pasamos el objeto profesor por si quieres mostrarlo en la plantilla
    })
@user_passes_test(is_admin)
def agregar_materia(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia agregada correctamente.')
            return redirect('agregar_materia')  # Redirige para evitar reenvío de formulario
    else:
        form = MateriaForm()
    
    return render(request, 'profesores/agregar_materia.html', {'form': form})


def estadisticas(request):
    # Obtener todas las materias para la lista desplegable
    materias = Materia.objects.all()

    # Obtener la materia seleccionada del formulario o una por defecto
    materia_nombre = request.GET.get('materia')
    
    # Intentar obtener el objeto de la materia seleccionada
    materia_seleccionada = Materia.objects.filter(nombre=materia_nombre).first()

    # Inicializar variables
    grafico_dispersion = None
    grafico_distribucion = None
    grafica_promedio = None
    error_message = None

    # Generar los gráficos solo si la materia existe y tiene comentarios asociados
    if materia_seleccionada:
        comentarios = Comentario.objects.filter(materia=materia_seleccionada, aprobado_por_ia=True)
        if comentarios.exists():
            # Usar ChartFactory con patrón Factory para generar gráficas
            
            # Gráfico de dispersión: profesores vs calificaciones
            profesores_con_calificacion = (
                Profesor.objects
                .filter(materias=materia_seleccionada)
                .annotate(
                    calificacion_promedio=Avg('comentarios__rating', filter=Q(comentarios__materia=materia_seleccionada)),
                    num_reviews=Count('comentarios', filter=Q(comentarios__materia=materia_seleccionada))
                )
            )
            grafico_dispersion = ChartFactory.create_chart('scatter', profesores_con_calificacion)
            
            # Gráfico de distribución de frecuencias
            ratings = list(comentarios.values_list('rating', flat=True))
            grafico_distribucion = ChartFactory.create_chart('frequency', ratings)
            
            # Gráfico de promedio por semestre
            grafica_promedio = ChartFactory.create_chart('semester_line', {
                'comentarios': comentarios,
                'titulo': f'Promedio de Rating por Semestre para {materia_seleccionada.nombre}'
            })
        else:
            error_message = "No hay comentarios disponibles para generar gráficos estadísticos de esta materia."
    else:
        error_message = "Selecciona una materia válida."

    context = {
        'grafico_dispersion': grafico_dispersion,
        'grafico_distribucion': grafico_distribucion,
        'grafica_promedio': grafica_promedio,
        'materia_seleccionada': materia_nombre,
        'materias': materias,
        'error_message': error_message,
    }
    return render(request, 'profesores/estadisticas.html', context)
