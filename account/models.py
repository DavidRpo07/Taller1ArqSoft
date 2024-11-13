from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_suspended = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

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