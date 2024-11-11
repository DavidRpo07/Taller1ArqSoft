from django.contrib import admin
from .models import Profesor, Materia
# Register your models here.



@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'departamento', 'calificacion_media', 'numcomentarios')
    search_fields = ('nombre', 'departamento')
    filter_horizontal = ('materias',)  # Habilita selección de materias en el admin de Profesor

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'calificacion_media', 'numcomentarios')
    search_fields = ('nombre',)