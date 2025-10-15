from django.db import models
from django.contrib.auth.models import User
class UserState:
    def puede_acceder(self):
        raise NotImplementedError

    def mensaje_estado(self):
        raise NotImplementedError

class ActivoState(UserState):
    def puede_acceder(self):
        return True

    def mensaje_estado(self):
        return "Tu cuenta está activa."

class SuspendidoState(UserState):
    def puede_acceder(self):
        return False

    def mensaje_estado(self):
        return "Tu cuenta está suspendida. Contacta soporte."

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_suspended = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @property
    def estado(self):
        if self.is_suspended:
            return SuspendidoState()
        else:
            return ActivoState()

    def puede_acceder(self):
        return self.estado.puede_acceder()

    def mensaje_estado(self):
        return self.estado.mensaje_estado()

import uuid

class PendingUser(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)  # Almacena la contraseña encriptada
    confirmation_code= models.CharField(max_length=6)

    def __str__(self):
        return self.username