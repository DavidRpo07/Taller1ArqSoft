from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
import csv
from django.contrib import messages
from .models import Profesor, UploadCSVForm, ProfesorForm, Materia, MateriaForm  
from review.models import Comentario
from django.contrib import messages
import matplotlib.pyplot as plt
import matplotlib
import io 
import urllib, base64
from collections import Counter
from django.db.models import Avg, Count, Q
from collections import defaultdict
import numpy as np


def is_admin(user):
    return user.is_staff


def lista_profesores(request):
    searchNombre = request.GET.get('searchNombre', '').strip()  # Elimina espacios en blanco adicionales
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

    # Aplicar la ordenación según el criterio seleccionado
    if orden_field:
        if orden_field == 'mayor_rating':
            profesores = profesores.order_by('-calificacion_media')  # Ordena por mayor rating (descendente)
        elif orden_field == 'menor_rating':
            profesores = profesores.order_by('calificacion_media')   # Ordena por menor rating (ascendente)
        elif orden_field == 'mayor_comentarios':
            profesores = profesores.order_by('-numcomentarios')  # Ordena por más comentarios (descendente)
        elif orden_field == 'menor_comentarios':
            profesores = profesores.order_by('numcomentarios')   # Ordena por menos comentarios (ascendente)

    return render(request, 'lista_profesores.html', {
        'profesores': profesores,
        'searchNombre': searchNombre,
        'searchMateria': searchMateria,
        'orden_field': orden_field
    })


def generar_grafica_barras(ratings):
    
    # Configurar matplotlib para trabajar sin entorno gráfico
    matplotlib.use('Agg')
    
    # Crear la figura
    plt.figure(figsize=(12, 6))
    
    # Contar las frecuencias de los ratings
    counts = dict(Counter(ratings))
    labels = list(range(1, 6))  # Posibles ratings (1 a 5)
    values = [counts.get(label, 0) for label in labels]  # Frecuencia por rating

    # Generar la gráfica
    plt.bar(labels, values, color='skyblue', edgecolor='black', width=0.8)
    plt.xlabel('Calificación', fontsize=14, fontweight='bold')
    plt.ylabel('Frecuencia', fontsize=14, fontweight='bold')
    plt.xticks(labels, fontsize=12)
    max_y = int(max(counts))
    plt.yticks(range(0, max_y + 1), fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Guardar la gráfica como base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close()


    image_png = buffer.getvalue()
    buffer.close()
    grafica_barras = base64.b64encode(image_png)
    grafica_barras = grafica_barras.decode('utf-8')

    return grafica_barras

def grafica_calificaciones_semestre(comentarios):

    # Configurar matplotlib para trabajar sin entorno gráfico
    matplotlib.use('Agg')

    # Agrupar calificaciones por semestre
    calificaciones_por_semestre = defaultdict(list)
    for comentario in comentarios:
        calificaciones_por_semestre[comentario.fecha].append(comentario.rating)

    # Calcular el promedio por semestre
    semestres_ordenados = sorted(calificaciones_por_semestre.keys(), reverse=False)  # Ordenar cronológicamente
    calificaciones_promedio = [
        sum(calificaciones_por_semestre[semestre]) / len(calificaciones_por_semestre[semestre])
        for semestre in semestres_ordenados
    ]

    # Generar la gráfica
    plt.figure(figsize=(10, 5))
    plt.plot(semestres_ordenados, calificaciones_promedio, marker='o', linestyle='-', color='blue')
    plt.xlabel('Semestre', fontsize=12)
    plt.ylabel('Rating Promedio', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)

    # Guardar la gráfica como base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return image_base64


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

    # Gráficas:
    # Mostrar ambas gráficas si no se filtra por semestre
    # Mostrar solo la gráfica de barras si hay filtro por semestre
    grafica_barras = generar_grafica_barras(ratings_grafica) if comentarios_grafica.exists() else None
    grafica_por_semestre = None
    if not semestre:
        grafica_por_semestre = (
            grafica_calificaciones_semestre(comentarios_grafica)
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

def generar_grafico_dispersion(materia):
    matplotlib.use('Agg')
    # Intentar obtener la materia seleccionada o devolver un error si no existe
    try:
        materia_obj = Materia.objects.get(nombre=materia)
    except Materia.DoesNotExist:
        return None  # Devolver None si la materia no existe

    # Obtener los profesores que imparten esta materia con sus calificaciones promedio
    profesores_con_calificacion = (
        Profesor.objects
        .filter(materias=materia_obj)
        .annotate(
            calificacion_promedio=Avg('comentarios__rating', filter=Q(comentarios__materia=materia_obj)),
            num_reviews=Count('comentarios', filter=Q(comentarios__materia=materia_obj))
        )
    )

    # Preparar datos para el gráfico
    nombres_profesores = [prof.nombre for prof in profesores_con_calificacion]
    calificaciones_promedio = [prof.calificacion_promedio for prof in profesores_con_calificacion]
    num_reviews = [prof.num_reviews for prof in profesores_con_calificacion]

    # Crear el gráfico de dispersión
    plt.figure(figsize=(10, 6))
    plt.scatter(nombres_profesores, calificaciones_promedio, s=[n * 10 for n in num_reviews], alpha=0.5)
    plt.xlabel("Profesor")
    plt.ylabel("Calificación promedio")
    plt.title(f"Calificación promedio de profesores en {materia}")
    plt.xticks(rotation=45, ha='right')

    # Guardar el gráfico en memoria para enviarlo al template
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    # Codificar la imagen en base64 para enviarla al HTML
    graph = base64.b64encode(image_png).decode('utf-8')

    return graph

def generar_grafico_distribucion_frecuencias(materia):
    # Obtener la materia seleccionada o devolver None si no existe
    try:
        materia_obj = Materia.objects.get(nombre=materia)
    except Materia.DoesNotExist:
        return None

    # Obtener los ratings de todos los comentarios asociados a la materia
    ratings = Comentario.objects.filter(materia=materia_obj).values_list('rating', flat=True)

    # Verificar si hay ratings para la materia
    if not ratings:
        return None

    # Contar la frecuencia de cada rating usando Counter
    rating_counts = Counter(ratings)
    ratings_list = [rating_counts.get(rating, 0) for rating in range(1, 6)]  # Frecuencia para ratings 1 a 5

    # Crear el gráfico de barras para la distribución de frecuencias
    plt.figure(figsize=(10, 6))
    plt.bar(range(1, 6), ratings_list, color='skyblue', edgecolor='black')
    plt.xlabel("Rating")
    plt.ylabel("Frecuencia")
    plt.title(f"Distribución de Frecuencias de Ratings para {materia}")
    plt.xticks(range(1, 6))
    max_y = max(ratings_list) + 1  # Definir el límite superior del eje y
    plt.yticks(np.arange(0, max_y + 1, 1))  # Crear ticks de 1 en 1 hasta el valor máximo

    # Guardar el gráfico en memoria para enviarlo al template
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    # Codificar la imagen en base64 para enviarla al HTML
    graph = base64.b64encode(image_png).decode('utf-8')

    return graph

def grafica_promedio_rating_por_semestre(materia):
    if not materia:
        return None  # Retorna None si la materia es None

    # Configurar matplotlib para trabajar sin entorno gráfico
    matplotlib.use('Agg')

    # Obtener los comentarios de la materia seleccionada y agrupar calificaciones por semestre
    comentarios = Comentario.objects.filter(materia=materia)
    calificaciones_por_semestre = defaultdict(list)
    for comentario in comentarios:
        calificaciones_por_semestre[comentario.fecha].append(comentario.rating)

    # Calcular el promedio por semestre
    semestres_ordenados = sorted(calificaciones_por_semestre.keys())  # Ordenar cronológicamente
    calificaciones_promedio = [
        sum(calificaciones_por_semestre[semestre]) / len(calificaciones_por_semestre[semestre])
        for semestre in semestres_ordenados
    ]

    # Generar la gráfica de líneas
    plt.figure(figsize=(10, 5))
    plt.plot(semestres_ordenados, calificaciones_promedio, marker='o', linestyle='-', color='blue')
    plt.xlabel('Semestre', fontsize=12)
    plt.ylabel('Rating Promedio', fontsize=12)
    plt.title(f'Promedio de Rating por Semestre para {materia.nombre}', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)

    # Guardar la gráfica en formato base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()
    return image_base64


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
            grafico_dispersion = generar_grafico_dispersion(materia_seleccionada)
            grafico_distribucion = generar_grafico_distribucion_frecuencias(materia_seleccionada)
            grafica_promedio = grafica_promedio_rating_por_semestre(materia_seleccionada)
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
