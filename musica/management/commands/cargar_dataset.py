import pandas as pd
from django.core.management.base import BaseCommand
from musica.models import Ritmo, Artista, Album, Cancion

class Command(BaseCommand):
    help = 'Carga canciones desde un archivo Excel o CSV'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al archivo .xlsx o .csv')

    def handle(self, *args, **kwargs):
        archivo = kwargs['archivo']

        # Leer archivo
        if archivo.endswith('.xlsx'):
            df = pd.read_excel(archivo)
        elif archivo.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            self.stderr.write("Formato no soportado. Usa .xlsx o .csv")
            return

        for _, row in df.iterrows():
            # Obtener o crear Ritmo
            ritmo, _ = Ritmo.objects.get_or_create(nombre=row['genero'])

            # Obtener o crear Artista
            artista, _ = Artista.objects.get_or_create(nombre=row['artistas'], ritmo=ritmo)

            # Obtener o crear Album
            album, _ = Album.objects.get_or_create(nombre=row['album'], artista=artista)

            # Crear o actualizar Canción
            cancion, creada = Cancion.objects.get_or_create(
                track_id=row['track_id'],
                defaults={
                    'titulo': row['nombre'],
                    'artista': artista,
                    'video_url': row.get('video_url', None)  # si tu archivo lo tiene
                }
            )

            if creada:
                self.stdout.write(self.style.SUCCESS(f"✔ Canción agregada: {cancion.titulo}"))
            else:
                self.stdout.write(f"↪ Ya existía: {cancion.titulo}")


