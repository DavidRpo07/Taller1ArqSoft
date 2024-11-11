from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
import csv
from django.contrib import messages
from .models import Profesor, UploadCSVForm, ProfesorForm, Materia, MateriaForm  # Importar el modelo Profesor
from review.models import Comentario
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib import messages
from account.models import UserProfile
from django.contrib.auth.models import User
import matplotlib.pyplot as plt
import matplotlib
import io 
from io import BytesIO
import urllib
import base64
import numpy as np
import os
#from bokeh.plotting import figure
#from bokeh.embed import components
from collections import Counter
from review.models import Comentario
from django.http import HttpResponse
from collections import defaultdict


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
