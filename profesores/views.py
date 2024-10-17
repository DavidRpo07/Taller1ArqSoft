from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
import csv
from django.contrib import messages
from .models import Profesor, UploadCSVForm, ProfesorForm
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib import messages
from account.models import UserProfile
from django.contrib.auth.models import User
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io 
from io import BytesIO
import base64
import numpy as np
import os
from bokeh.plotting import figure
from bokeh.embed import components
from collections import Counter
from review.models import Comentario


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

'''def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    # Filtrar los comentarios aprobados por IA
    comentarios = profesor.comentarios.filter(aprobado_por_ia=True)

    # Contar la cantidad de comentarios por cada rating
    ratings = [1, 2, 3, 4, 5]
    frecuencia = [comentarios.filter(rating=rating).count() for rating in ratings]

    # Crear la gráfica de barras
    plt.figure(figsize=(6, 4))
    plt.bar(ratings, frecuencia, color='skyblue')
    plt.xlabel('Rating')
    plt.ylabel('Cantidad de Comentarios')
    plt.title(f'Distribución de Comentarios por Rating para {profesor.nombre}')
    plt.xticks(ratings)
    plt.tight_layout()

    # Guardar la gráfica en un buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.cose()
    # Convertir la imagen a base64 para incrustarla en el HTML
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    # Renderizar la vista con la gráfica incluida en el contexto
    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios,
        'grafica': image_base64  # Enviar la imagen al template
    })'''
'''def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    comentarios = profesor.comentarios.filter(aprobado_por_ia=True)  # Solo mostrar comentarios aprobados

    ratings = [1, 2, 3, 4, 5]
    frecuencia = [comentarios.filter(rating=rating).count() for rating in ratings]

    plot = figure(height=350,
                x_axis_label="Rating",
                y_axis_label="Cantidad Comentarios",
                background_fill_alpha=0,
                border_fill_alpha=0,
                tools="pan,wheel_zoom,box_zoom,save,reset")
    bars = plot.vbar(x=ratings, top=frecuencia, width=0.9)
    graph_script, graph_div = components(plot)
    context = {"graph_script": graph_script,
                "graph_div": graph_div}

    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios,
        'context': context
    })'''

def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    # Filtrar los comentarios del profesor para mostrar solo los aprobados por la IA
    #comentarios =  Comentario.objects.filter(profesor=profesor)
    comentarios = Comentario.objects.filter(profesor=profesor, aprobado_por_ia=True)
    # Contar comentarios por rating
    ratings = [comentario.rating for comentario in comentarios]
    ratings_data = dict(Counter(ratings))  # Contador de ratings

    # Asegurar que todas las calificaciones de 1 a 5 tengan un valor, incluso si no hay comentarios con esa calificación
    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios,
        'ratings_data': ratings_data  # Pasar los datos al template
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
