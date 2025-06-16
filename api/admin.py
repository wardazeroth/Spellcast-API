from django.contrib import admin
from .models import Library, Book

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'library')