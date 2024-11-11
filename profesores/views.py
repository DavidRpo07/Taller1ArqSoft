from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
import csv
from django.contrib import messages
from .models import Profesor, UploadCSVForm, ProfesorForm
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
    searchNombre = request.GET.get('searchNombre', '')
    searchMateria = request.GET.get('searchMateria', '')
    orden_field = request.GET.get('orden_field', '')

    # Inicialmente, selecciona todos los profesores
    profesores = Profesor.objects.all()

    # Filtrar por nombre
    if searchNombre:
        profesores = profesores.filter(nombre__icontains=searchNombre)
    
    # Filtrar por materia 
    if searchMateria:
        profesores = profesores.filter(materia__icontains=searchMateria)

    # Aplicar la ordenación según el criterio seleccionado
    if orden_field:
        if orden_field == 'mayor_rating':
            profesores = profesores.order_by('-calificacion_media')  # Ordena por mayor rating (descendente)
        elif orden_field == 'menor_rating':
            profesores = profesores.order_by('calificacion_media')   # Ordena por menor rating (ascendente)
        elif orden_field == 'mayor_comentarios':
            profesores = profesores.order_by('-numcomentarios')
        elif orden_field == 'menor_comentarios':
            profesores = profesores.order_by('numcomentarios')

    return render(request, 'lista_profesores.html', {
        'profesores': profesores,
        'searchNombre': searchNombre,
        'searchMateria': searchMateria,
        'orden_field': orden_field
    })



def generar_grafica_barras(ratings):
    """
    Genera una gráfica de barras basada en los ratings y devuelve su representación en base64.
    """
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
    # Obtener el profesor y comentarios aprobados por IA
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    comentarios = Comentario.objects.filter(profesor=profesor, aprobado_por_ia=True)

    # Obtener ratings para la gráfica
    ratings = [comentario.rating for comentario in comentarios]

    # Generar la gráfica de barras
    grafica_barras = generar_grafica_barras(ratings)

    # Generar la gráfica de calificaciones por semestre
    grafica_por_semestre = grafica_calificaciones_semestre(comentarios)

    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios,
        'grafica_barras': grafica_barras, 
        'grafica_por_semestre': grafica_por_semestre, # Base64 de la gráfica de barras
        # 'grafica_pie': grafica_pie,  # Agregar otras gráficas cuando las implementes
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

                next(reader)

                for row in reader:
                    Profesor.objects.create(
                        nombre=row[0], 
                        departamento=row[1], 
                        materia=row[2], 
                        calificacion_media=0.0, 
                        numcomentarios=0
                    )
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
            profesor_form.save()
            messages.success(request, 'Profesor editado correctamente.')
            return redirect('manage_profesor')  # Redirigir a una vista de lista de profesores o a donde prefieras
    else:
        # Si es GET, cargamos el formulario con los datos actuales del profesor
        profesor_form = ProfesorForm(instance=profesor)
    
    return render(request, 'profesores/editar_profesor.html', {
        'profesor_form': profesor_form,
        'profesor': profesor  # Pasamos el objeto profesor por si quieres mostrarlo en la plantilla
    })
