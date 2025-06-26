from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .views import (
    LoginView,
    index,
    canciones_por_artista,
    seleccionar_artistas,
    ver_artistas,
    logout_view,
    register_view,
    password_reset_view,
    ver_estadisticas,
    generar_dataset_backend
)

urlpatterns = [
    path('', lambda request: redirect('login'), name='root_redirect'),  # Redirige / a /login/
    path('login/', LoginView.as_view(), name='login'),
    path('index/', login_required(index), name='index'),
    path('canciones/<str:artista_id>/', login_required(canciones_por_artista), name='canciones_por_artista'),
    path('seleccionar-artistas/', login_required(seleccionar_artistas), name='seleccionar_artistas'),
    path('ver-artistas/', login_required(ver_artistas), name='ver_artistas'),
    path('logout/', logout_view, name='logout'),  # logout sin login_required
    path('register/', register_view, name='register'),
    path('password-reset/', password_reset_view, name='password_reset'),
    path('estadisticas/', login_required(ver_estadisticas), name='ver_estadisticas'),
    path('generar_dataset/', login_required(generar_dataset_backend), name='generar_dataset'),

]


