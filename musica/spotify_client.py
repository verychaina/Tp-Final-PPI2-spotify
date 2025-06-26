import os
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from musica.models import Artista
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict
import io

# Cargar variables de entorno desde .env
load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

client_credentials_manager = SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

sp = Spotify(client_credentials_manager=client_credentials_manager)

def buscar_artistas_por_nombre_o_genero(query):
    try:
        resultados_nombre = sp.search(q=query, type='artist', limit=20)['artists']['items']
        resultados_genero = sp.search(q=f'genre:"{query}"', type='artist', limit=20)['artists']['items']

        artistas_dict = {}
        for artista in resultados_nombre + resultados_genero:
            artistas_dict[artista['id']] = artista

        return list(artistas_dict.values())

    except Exception as e:
        print(f"Error buscando artistas por nombre o género '{query}': {e}")
        return []

def obtener_canciones(artista_id):
    top_tracks = sp.artist_top_tracks(artista_id, country='US')
    return top_tracks['tracks']

def obtener_canciones_desde_spotify_o_bd(spotify_id):
    if not spotify_id:
        return []

    try:
        response = sp.artist_top_tracks(spotify_id, country='US')
        canciones = response.get('tracks', [])
        return [{
            'titulo': c['name'],
            'spotify_url': c['uri'].replace('spotify:track:', 'https://open.spotify.com/track/'),
            'id': c['id']
        } for c in canciones]
    except Exception as e:
        print(f"Error obteniendo canciones: {e}")
        return []

def actualizar_spotify_ids():
    artistas = Artista.objects.filter(spotify_id__isnull=True)
    for artista in artistas:
        try:
            resultado = sp.search(q=f'artist:{artista.nombre}', type='artist', limit=1)
            items = resultado.get('artists', {}).get('items', [])
            if items:
                item = items[0]
                artista.spotify_id = item['id']
                artista.spotify_nombre = item['name']
                artista.spotify_url = item['external_urls']['spotify']
                artista.save()
                print(f"✅ {artista.nombre} → {item['name']} | {item['external_urls']['spotify']}")
            else:
                print(f"❌ No encontrado: {artista.nombre}")
        except Exception as e:
            print(f"⚠️ Error con {artista.nombre}: {e}")

def generar_graficos_artistas_seleccionados(artistas):
    if not artistas:
        return {}

    data = []
    for artista in artistas:
        data.append({
            'nombre': artista['name'],
            'popularidad': artista['popularity'],
            'seguidores': artista['followers']['total'],
            'generos': ', '.join(artista.get('genres', [])) or 'Desconocido'
        })

    df = pd.DataFrame(data)
    graficos = {}

    def generar_img(fig):
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    # Artista más popular
    artista_pop = df.loc[df['popularidad'].idxmax()]
    graficos['mas_popular'] = {
        'titulo': f"🎤 Artista más popular: {artista_pop['nombre']}"
    }

    # Más seguidores
    artista_seg = df.loc[df['seguidores'].idxmax()]
    graficos['mas_seguidores'] = {
        'titulo': f"👥 Más seguidores: {artista_seg['nombre']}"
    }

    # Comparativa popularidad
    fig1 = plt.figure(figsize=(10, 6))
    plt.barh(df['nombre'], df['popularidad'], color='#1DB954')
    plt.title("Popularidad de los artistas")
    plt.xlabel("Popularidad")
    plt.gca().invert_yaxis()
    graficos['grafico_popularidad'] = {
        'titulo': "📊 Comparativa de popularidad",
        'imagen': generar_img(fig1)
    }

    # Comparativa seguidores
    fig2 = plt.figure(figsize=(10, 6))
    plt.barh(df['nombre'], df['seguidores'], color='#1DB954')
    plt.title("Seguidores por artista")
    plt.xlabel("Seguidores")
    plt.gca().invert_yaxis()
    graficos['grafico_seguidores'] = {
        'titulo': "👥 Comparativa de seguidores",
        'imagen': generar_img(fig2)
    }

    # Distribución de géneros
    generos = df['generos'].str.split(', ').explode()
    fig3 = plt.figure(figsize=(10, 6))
    generos.value_counts().plot(kind='bar', color='#1DB954')
    plt.title("Distribución de géneros")
    plt.ylabel("Cantidad de artistas")
    plt.xticks(rotation=45, ha='right')
    graficos['grafico_generos'] = {
        'titulo': "🧬 Distribución de géneros",
        'imagen': generar_img(fig3)
    }

    return graficos

def generar_grafico_genero_popularidad(canciones):
    popularidad_por_genero = defaultdict(list)

    for cancion in canciones:
        genero = cancion.get('genero', 'Desconocido')
        popularidad = cancion.get('popularidad', 0)
        popularidad_por_genero[genero].append(popularidad)

    promedio_por_genero = {g: sum(p)/len(p) for g, p in popularidad_por_genero.items()}

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(list(promedio_por_genero.keys()), list(promedio_por_genero.values()), color="#1DB954")
    ax.set_xlabel('Popularidad Promedio')
    ax.set_title('Popularidad Promedio por Género')
    ax.invert_yaxis()
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    buffer.seek(0)
    imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    return imagen_base64

def generar_grafico_top_artistas(artistas, tipo='popularidad'):
    nombres = [a['name'] for a in artistas]
    if tipo == 'popularidad':
        valores = [a['popularity'] for a in artistas]
        titulo = 'Top Artistas por Popularidad'
        color = '#1DB954'
    else:
        valores = [a['followers']['total'] for a in artistas]
        titulo = 'Top Artistas por Seguidores'
        color = '#5353f1'

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(nombres, valores, color=color)
    ax.set_xlabel('Valor')
    ax.set_title(titulo)
    ax.invert_yaxis()
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    buffer.seek(0)
    imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    return imagen_base64

