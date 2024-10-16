from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
import csv
from django.contrib import messages
from review.models import Comentario
from .models import Profesor, UploadCSVForm, ProfesorForm
from django.conf import settings



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

def detalle_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    # Filtrar los comentarios del profesor para mostrar solo los aprobados por la IA
    comentarios = profesor.comentarios.filter(aprobado_por_ia=True)
    
    return render(request, 'profesores/detalle_profesor.html', {
        'profesor': profesor,
        'comentarios': comentarios
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
