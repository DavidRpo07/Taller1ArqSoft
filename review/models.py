from django.db import models
from django.contrib.auth.models import User
from profesores.models import Profesor
from django.db.models.signals import post_save
from django.dispatch import receiver

class Comentario(models.Model):
    profesor = models.ForeignKey(Profesor, related_name='comentarios', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(choices=((0, 'Seleccione una'),(1, '1 Estrella'), (2, '2 Estrellas'), (3, '3 Estrellas'), (4, '4 Estrellas'), (5, '5 Estrellas')), default=0)

    def __str__(self):
        return f'Comentario de {self.usuario} sobre {self.profesor}'
    
@receiver(post_save, sender=Comentario)
def actualizar_calificacion_media(sender, instance, **kwargs):
    profesor = instance.profesor
    comentarios = Comentario.objects.filter(profesor=profesor)
    promedio = comentarios.aggregate(models.Avg('rating'))['rating__avg']
    profesor.calificacion_media = promedio
    profesor.save()