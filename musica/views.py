from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from .forms import CustomUserCreationForm
from .models import Ritmo, Artista, Perfil
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import base64
from io import BytesIO
from django.conf import settings
import os
from .spotify_client import (
    sp,
    buscar_artistas_por_nombre_o_genero,
    generar_grafico_genero_popularidad,
    generar_graficos_artistas_seleccionados,
    generar_grafico_top_artistas
)


@login_required
def index(request):
    query = request.GET.get('query', '')
    resultados = []
    artistas_con_canciones = []
    grafico_genero = None
    graficos_extra = {}

    if request.method == 'GET' and query:
        resultados = buscar_artistas_por_nombre_o_genero(query)

    elif request.method == 'POST':
        artistas_ids = request.POST.getlist('artistas')
        query = request.POST.get('query', '')
        resultados = buscar_artistas_por_nombre_o_genero(query) if query else []

        if artistas_ids:
            artistas_info = []
            canciones_para_grafico = []

            for art_id in artistas_ids:
                try:
                    artista = sp.artist(art_id)
                    artistas_info.append(artista)
                    canciones = obtener_canciones_desde_spotify_o_bd(artista['id'])
                    artistas_con_canciones.append({
                        'artista': artista,
                        'canciones': canciones
                    })

                    genero_str = ', '.join(artista.get('genres', [])) or 'Desconocido'
                    for cancion in canciones:
                        canciones_para_grafico.append({
                            'genero': genero_str,
                            'popularidad': sp.track(cancion['id'])['popularity']
                        })

                except Exception as e:
                    print(f"Error con artista {art_id}: {e}")

            grafico_genero = generar_grafico_genero_popularidad(canciones_para_grafico)
            graficos_extra = generar_graficos_artistas_seleccionados(artistas_info)

                # Gráficos adicionales: popularidad y seguidores
    if artistas_con_canciones:
        lista_artistas = [a['artista'] for a in artistas_con_canciones]
        grafico_popularidad = generar_grafico_top_artistas(lista_artistas, tipo='popularidad')
        grafico_seguidores = generar_grafico_top_artistas(lista_artistas, tipo='seguidores')
    else:
        grafico_popularidad = None
        grafico_seguidores = None


    contexto = {
    'query': query,
    'resultados': resultados,
    'artistas_con_canciones': artistas_con_canciones,
    'grafico_genero': grafico_genero,
    'grafico_popularidad': grafico_popularidad,
    'grafico_seguidores': grafico_seguidores,
    'graficos_extra': graficos_extra,
    'dataset_generado': request.session.get('dataset_generado', False),
}
    return render(request, 'musica/index.html', contexto)


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


def canciones_por_artista(request, artista_id):
    try:
        artista = sp.artist(artista_id)
        response = sp.artist_top_tracks(artista_id, country='US')
        canciones = response.get('tracks', [])
        lista_canciones = [{
            'titulo': c['name'],
            'spotify_url': c['uri'].replace('spotify:track:', 'https://open.spotify.com/track/'),
            'id': c['id']
        } for c in canciones]

        return render(request, 'musica/canciones_por_artista.html', {
            'artista': artista,
            'canciones': lista_canciones,
        })
    except Exception as e:
        print(f"Error en canciones_por_artista: {e}")
        return redirect('index')


def seleccionar_artistas(request):
    ritmos = Ritmo.objects.all().order_by('nombre')
    artistas = []
    ritmo_id = request.GET.get('ritmo')
    if ritmo_id:
        artistas = Artista.objects.filter(ritmo_id=ritmo_id)
    return render(request, 'musica/canciones_por_artista.html', {
        'ritmos': ritmos,
        'artistas': artistas,
        'ritmo_seleccionado': int(ritmo_id) if ritmo_id else None,
    })


def ver_artistas(request):
    if request.method == 'POST':
        artistas_ids = request.POST.getlist('artistas')
        artistas = Artista.objects.filter(spotify_id__in=artistas_ids)

        canciones = []
        for artista in artistas:
            if artista.spotify_id:
                canciones += obtener_canciones_desde_spotify_o_bd(artista.spotify_id)

        return render(request, 'musica/canciones_por_artista.html', {
            'artistas': artistas,
            'canciones': canciones,
        })

    return redirect('seleccionar_artistas')


class LoginView(auth_views.LoginView):
    template_name = 'musica/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('index')

    def get_success_url(self):
        return self.success_url


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            Perfil.objects.create(user=user, telefono=form.cleaned_data['telefono'])
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'musica/register.html', {'form': form})


def password_reset_view(request):
    return render(request, 'musica/password_reset.html')

@login_required
def ver_estadisticas(request):
    print("Entramos a ver_estadisticas")

    if request.method == 'POST':
        artistas_ids = request.POST.getlist('artistas')
        print("Artistas recibidos:", artistas_ids)

        if artistas_ids:
            artistas_info = []
            for art_id in artistas_ids:
                try:
                    artista = sp.artist(art_id)
                    artistas_info.append(artista)
                except Exception as e:
                    print(f"Error al obtener artista {art_id}: {e}")

            graficos_extra = generar_graficos_artistas_seleccionados(artistas_info)

            # Agregar gráfico de popularidad y seguidores
            grafico_popularidad = generar_grafico_top_artistas(artistas_info, tipo='popularidad')
            grafico_seguidores = generar_grafico_top_artistas(artistas_info, tipo='seguidores')

            # Añadir al diccionario graficos_extra
            if grafico_popularidad:
                graficos_extra["grafico_popularidad"] = {
                    "titulo": "Comparación de popularidad",
                    "imagen": grafico_popularidad
                }
            if grafico_seguidores:
                graficos_extra["grafico_seguidores"] = {
                    "titulo": "Comparación de seguidores",
                    "imagen": grafico_seguidores
                }

            # Intentar agregar gráficos globales del dataset
            try:
                ruta_excel = os.path.join(settings.BASE_DIR, 'dataset.xlsx')  # o la ruta correcta donde esté
                df = pd.read_excel(ruta_excel)
                graficos_dataset = generar_graficos_dataset(df)
            except Exception as e:
                print(f"Error cargando dataset global: {e}")
                graficos_dataset = None

            return render(request, 'musica/estadisticas.html', {
                'graficos_extra': graficos_extra,
                'graficos_dataset': graficos_dataset
            })

    print("Redirigiendo a index desde ver_estadisticas")
    return redirect('index')


def fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()

def generar_graficos_dataset(df):
    graficos = {}

    # 1. Géneros más comunes
    df['genero_simplificado'] = df['genero'].astype(str).str.split(',').str[0]
    top_generos = df['genero_simplificado'].value_counts().head(10)
    fig1, ax1 = plt.subplots()
    top_generos.plot(kind='bar', ax=ax1, title='Top Géneros')
    graficos['generos'] = fig_to_base64(fig1)

    # 2. Histograma de popularidad
    fig2, ax2 = plt.subplots()
    sns.histplot(df['popularidad'], kde=True, ax=ax2)
    ax2.set_title('Distribución de Popularidad')
    graficos['popularidad'] = fig_to_base64(fig2)

    # 3. Promedio de popularidad por artista
    top_artistas = df.groupby('artistas')['popularidad'].mean().sort_values(ascending=False).head(10)
    fig3, ax3 = plt.subplots()
    top_artistas.plot(kind='bar', ax=ax3, title='Top Artistas por Popularidad')
    graficos['artistas_pop'] = fig_to_base64(fig3)

    # 4. Duración promedio por artista
    duracion_prom = df.groupby('artistas')['duracion_ms'].mean().sort_values(ascending=False).head(10)
    fig4, ax4 = plt.subplots()
    duracion_prom.plot(kind='bar', ax=ax4, title='Duración Promedio por Artista')
    graficos['duracion_artista'] = fig_to_base64(fig4)

    # 5. Canciones explícitas
    explicito = df['explicito'].value_counts()
    fig5, ax5 = plt.subplots()
    explicito.plot(kind='pie', ax=ax5, autopct='%1.1f%%', title='Canciones Explícitas')
    graficos['explicitas'] = fig_to_base64(fig5)

    # 6. Relación popularidad vs duración
    fig6, ax6 = plt.subplots()
    sns.scatterplot(x='duracion_ms', y='popularidad', data=df, ax=ax6)
    ax6.set_title('Duración vs Popularidad')
    graficos['pop_duracion'] = fig_to_base64(fig6)

    plt.close('all')  # libera memoria
    return graficos


from django.conf import settings
import os
from .generar_dataset import generar_dataset_para_artistas  # ya la tienes importada

@login_required
def generar_dataset_backend(request):
    if request.method == 'POST':
        artistas_ids = request.POST.getlist('artistas')
        query = request.POST.get('query', '')

        if not artistas_ids:
            # Si no seleccionaron artistas, volver a index con mensaje o sin dataset
            return redirect('index')

        # Generar dataframe y guardar dataset
        df = generar_dataset_para_artistas(artistas_ids)
        ruta_archivo = os.path.join(settings.BASE_DIR, 'dataset.xlsx')
        df.to_excel(ruta_archivo, index=False)

        # Guardar en sesión la info del dataset generado y artistas
        request.session['dataset_generado'] = True
        request.session['artistas_seleccionados'] = artistas_ids

        # Buscar información y canciones para mostrar en la misma página
        artistas_info = []
        artistas_con_canciones = []
        for art_id in artistas_ids:
            try:
                artista = sp.artist(art_id)
                artistas_info.append(artista)
                canciones = obtener_canciones_desde_spotify_o_bd(art_id)
                artistas_con_canciones.append({
                    'artista': artista,
                    'canciones': canciones
                })
            except Exception as e:
                print(f"Error con artista {art_id}: {e}")

        # También obtener resultados de búsqueda para mantener la lista visible
        resultados = buscar_artistas_por_nombre_o_genero(query) if query else []

        contexto = {
            'query': query,
            'resultados': resultados,
            'artistas_con_canciones': artistas_con_canciones,
            'dataset_generado': request.session.get('dataset_generado', False),
        }

        return render(request, 'musica/index.html', contexto)

    return redirect('index')



