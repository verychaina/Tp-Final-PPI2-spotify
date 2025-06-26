import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = Spotify(client_credentials_manager=client_credentials_manager)

def buscar_artistas_por_query(query, max_artistas=50):
    artistas = []
    offset = 0
    while len(artistas) < max_artistas:
        resultados = sp.search(q=query, type='artist', limit=50, offset=offset)
        items = resultados['artists']['items']
        if not items:
            break
        artistas.extend(items)
        offset += 50
        if offset >= resultados['artists']['total']:
            break
        time.sleep(0.2)
    return artistas[:max_artistas]

def obtener_canciones_top(artist_id):
    try:
        response = sp.artist_top_tracks(artist_id, country='US')
        return response['tracks']
    except:
        return []

import pandas as pd

def main():
    queries = ['Metallica', 'Nirvana']  # Mezcla de nombres y géneros
    artistas_unicos = {}

    for q in queries:
        print(f"Buscando artistas con query: {q}")
        artistas = buscar_artistas_por_query(q, max_artistas=50)

        for art in artistas:
            nombre_artista = art['name'].lower()
            generos_artista = [g.lower() for g in art.get('genres', [])]

            # Si la query coincide exactamente con el nombre del artista
            if nombre_artista == q.lower():
                artistas_unicos[art['id']] = art

            # O si la query está en la lista de géneros del artista
            elif q.lower() in generos_artista:
                artistas_unicos[art['id']] = art

    print(f"Total artistas únicos encontrados: {len(artistas_unicos)}")

    # Armar dataset con canciones
    rows = []
    for artist_id, artist in artistas_unicos.items():
        generos = artist.get('genres', [])
        canciones = obtener_canciones_top(artist_id)
        nombre_artista = artist.get('name', '')
        generos_str = ', '.join(generos) if generos else 'Desconocido'

        for c in canciones:
            rows.append({
                'track_id': c['id'],
                'artistas': nombre_artista,
                'album': c['album']['name'],
                'nombre': c['name'],
                'popularidad': c['popularity'],
                'duracion_ms': c['duration_ms'],
                'explicito': c['explicit'],
                'genero': generos_str,
            })

    df = pd.DataFrame(rows)
    archivo_salida = 'dataset.xlsx'
    df.to_excel(archivo_salida, index=False)
    print(f"Archivo guardado como {archivo_salida}")

if __name__ == '__main__':
    main()

# Al final del archivo generar_dataset.py
def generar_dataset_para_artistas(artistas_ids):
    rows = []
    for artist_id in artistas_ids:
        artist = sp.artist(artist_id)
        nombre = artist['name']
        generos = artist.get('genres', [])
        generos_str = ', '.join(generos) if generos else 'Desconocido'
        canciones = obtener_canciones_top(artist_id)

        for c in canciones:
            rows.append({
                'track_id': c['id'],
                'artistas': nombre,
                'album': c['album']['name'],
                'nombre': c['name'],
                'popularidad': c['popularity'],
                'duracion_ms': c['duration_ms'],
                'explicito': c['explicit'],
                'genero': generos_str,
            })

    return pd.DataFrame(rows)
