from django.db import models
from django.conf import settings

# Create the following models for the Spellcast API:
# Library
# id (PK)
# user_id (FK → User)
# name
# created_at

class Library(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='libraries')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (User: {self.user.username})"

    class Meta:
        verbose_name = 'Library'
        verbose_name_plural = 'Libraries'
        ordering = ['created_at']

# Book
# id (PK)
# library_id (FK → Library)
# title
# pdf_file_path
# text_content
# created_at

class Book(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=255)
    pdf_file_path = models.FileField(upload_to='books/pdf/')
    # pdf_file_path apunta a la ruta del archivo PDF, el cual se encuentra en internet.
    # CORREGIR.
    # pdf_file_url = models.URLField(blank=True, null=True) POR EJEMPLO.
    text_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Library: {self.library.name})"

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['created_at']
        
# FileField es un tipo de campo en Django que permite subir y almacenar archivos.
# Se usa para guardar referencias a archivos (no el contenido en sí en la base de datos).
# Django manejará internamente el nombre del archivo, su ubicación, y validará que el archivo efectivamente exista en el sistema de archivos configurado.