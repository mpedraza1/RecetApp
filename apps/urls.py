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
    path('usuarios/', views.gestion_usuarios, name='usuarios'),
        # Rutas ocultas (Acciones)
    path('usuarios/crear/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('usuarios/editar/<int:id_usuario>/', views.editar_usuario_admin, name='editar_usuario_admin'),
    path("resumen-calculos/", views.resumen_calculos, name="resumen_calculos"),
    path("recetas-por-tipo/<int:id_tipo>/", views.recetas_por_tipo, name="recetas_por_tipo"),
    path("calcular-por-tipo/", views.calcular_por_tipo, name="calcular_por_tipo"),
    path("generar-informe/", views.generar_informe_pdf, name="generar_informe")
    
]
