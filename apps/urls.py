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
    path('gestion-recetas/', views.gestion_recetas, name='gestion_recetas'),
    path('gestion-recetas/<int:id_receta>/', views.gestion_recetas, name='gestion_recetas_edit'),
    path('crear-ingrediente-ajax/', views.crear_ingrediente_ajax, name='crear_ingrediente_ajax'),
    path('limpiar-resumen-total/', views.limpiar_resumen_total, name='limpiar_resumen_total'),
    path('usuarios/', views.gestion_usuarios, name='usuarios'),
        # Rutas ocultas (Acciones)
    path('usuarios/crear/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('usuarios/editar/<int:id_usuario>/', views.editar_usuario_admin, name='editar_usuario_admin'),
    path("resumen-calculos/", views.resumen_calculos, name="resumen_calculos"),
    path("recetas-por-tipo/<int:id_tipo>/", views.recetas_por_tipo, name="recetas_por_tipo"),
    path("calcular-por-tipo/", views.calcular_por_tipo, name="calcular_por_tipo"),
    path("generar-informe/", views.generar_informe_pdf, name="generar_informe"),
    path('agregar-al-resumen/', views.agregar_al_resumen, name='agregar_al_resumen'),
    path('obtener-acumulados/', views.obtener_acumulados, name='obtener_acumulados'),
    path('eliminar-receta-resumen/<int:index>/', views.eliminar_receta_resumen, name='eliminar_receta_resumen'),
    
]
