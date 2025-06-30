from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Ritmo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    popularidad = models.IntegerField(default=0)  # Podés usarlo más adelante

    def __str__(self):
        return self.nombre

class Artista(models.Model):
    nombre = models.CharField(max_length=100)
    ritmo = models.ForeignKey(Ritmo, on_delete=models.CASCADE, related_name='artistas', null=True, blank=True)
    spotify_id = models.CharField(max_length=100, blank=True, null=True)
    spotify_nombre = models.CharField(max_length=255, blank=True, null=True)
    spotify_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Album(models.Model):
    nombre = models.CharField(max_length=255)
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name='albums')

    def __str__(self):
        return f"{self.nombre} - {self.artista.nombre}"

class Cancion(models.Model):
    titulo = models.CharField(max_length=255)
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name='canciones')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='canciones', null=True, blank=True)
    video_url = models.URLField(blank=True, null=True)
    track_id = models.CharField(max_length=100, blank=True, null=True)
    popularidad = models.IntegerField(default=0)
    duracion_ms = models.IntegerField(default=0)
    explicito = models.BooleanField(default=False)
    genero = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.titulo

class Video(models.Model):
    artista = models.ForeignKey(Artista, related_name='videos', on_delete=models.CASCADE)
    youtube_id = models.CharField(max_length=20)

    def __str__(self):
        return self.youtube_id

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    
class Dataset(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Dataset de {self.usuario.username} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"

class DatasetCancion(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='canciones')
    cancion = models.ForeignKey(Cancion, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.cancion.titulo} en dataset {self.dataset.id}"

class ArtistaFavorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artistas_favoritos')
    artista_id = models.CharField(max_length=255)  # id Spotify del artista
    nombre = models.CharField(max_length=255)      # nombre para mostrar
    imagen_url = models.URLField(blank=True, null=True)

    class Meta:
        unique_together = ('usuario', 'artista_id')

    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"
