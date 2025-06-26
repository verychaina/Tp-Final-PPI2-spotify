# musica/admin.py

from django.contrib import admin
from .models import Ritmo, Artista, Video

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1

class ArtistaAdmin(admin.ModelAdmin):
    inlines = [VideoInline]

admin.site.register(Ritmo)
admin.site.register(Artista, ArtistaAdmin)
admin.site.register(Video)
