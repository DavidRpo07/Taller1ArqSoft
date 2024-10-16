from django.db import models
from django.contrib.auth.models import User
from profesores.models import Profesor
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Comentario(models.Model):
    SEMESTRES = [
        ('2024-2', '2024-2'),
        ('2024-1', '2024-1'),
        ('2023-2', '2023-2'),
        ('2023-1', '2023-1'),
        ('2022-2', '2022-2'),
        ('2022-1', '2022-1'),
        ('2021-2', '2021-2'),
        ('2021-1', '2021-1'),
    ]
    profesor = models.ForeignKey(Profesor, related_name='comentarios', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField() 
    fecha = models.CharField(max_length=7, choices=SEMESTRES, default='2024-2')
    rating = models.IntegerField(choices=((0, 'Seleccione una'), (1, '1 Estrella'), (2, '2 Estrellas'),
                                          (3, '3 Estrellas'), (4, '4 Estrellas'), (5, '5 Estrellas')), default=0)
    aprobado_por_ia = models.BooleanField(default=False) 
    anonimo = models.BooleanField(default=False)

    def __str__(self):
        return f'Comentario de {self.usuario} sobre {self.profesor}'

@receiver(post_save, sender=Comentario)
def actualizar_calificacion_media(sender, instance, **kwargs):
    profesor = instance.profesor
    comentarios = Comentario.objects.filter(profesor=profesor)
    promedio = comentarios.aggregate(models.Avg('rating'))['rating__avg']
    profesor.calificacion_media = promedio if promedio is not None else 0.0
    cantidad_de_comentarios = comentarios.count()
    profesor.numcomentarios = cantidad_de_comentarios
    profesor.save()

@receiver(post_delete, sender=Comentario)
def actualizar_calificacion_media_eliminar(sender, instance, **kwargs):
    profesor = instance.profesor
    comentarios = Comentario.objects.filter(profesor=profesor)
    promedio = comentarios.aggregate(models.Avg('rating'))['rating__avg']
    profesor.calificacion_media = promedio if promedio is not None else 0.0
    cantidad_de_comentarios = comentarios.count()
    profesor.numcomentarios = cantidad_de_comentarios
    profesor.save()