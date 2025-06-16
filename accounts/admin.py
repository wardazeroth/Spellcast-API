from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Colocar todos los campos para que se muestren en el admin
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('date_joined',)
    ordering = ('-date_joined',)
    
