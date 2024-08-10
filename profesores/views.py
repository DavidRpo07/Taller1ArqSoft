from django.shortcuts import render
from .models import Profesor

def lista_profesores(request):
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

    return render(request, 'lista_profesores.html', {
        'profesores': profesores,
        'searchNombre': searchNombre,
        'searchMateria': searchMateria,
        'searchDepartamento': searchDepartamento
    })
