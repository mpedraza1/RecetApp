from django.urls import path
from . import views   # Importamos las views de ESTA app

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
        # Rutas de Primer Ingreso
    path('primer-ingreso/', views.primer_ingreso_a, name='primer_ingreso_a'),
    path('primer-ingreso/crear/', views.primer_ingreso_b, name='primer_ingreso_b'),
        # Ruta de Recuperar
    path('recuperar/', views.recuperar_a, name='recuperar_a'),
    path('recuperar/nueva/', views.recuperar_b, name='recuperar_b'),
    path("creacion-recetas/", views.crear_receta, name="crear_receta"),
]
