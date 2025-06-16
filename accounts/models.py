from django.db import models
from django.contrib.auth.models import AbstractUser

# Modelos iniciales a definir:
# User
# id (PK)
# username
# email
# created_at

class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    # Corregir created_at, ya que viene por defecto

    def __str__(self):
        return self.username

# Userprofile: Estudiar para aplicar en el futuro.