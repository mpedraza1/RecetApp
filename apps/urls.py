from django.urls import path
from . import views   # Importamos las views de ESTA app

urlpatterns = [
    path("creacion-recetas/", views.crear_receta, name="crear_receta"),
    path("resumen-calculos/", views.resumen_calculos, name="resumen_calculos"),
    path("recetas-por-tipo/<int:id_tipo>/", views.recetas_por_tipo, name="recetas_por_tipo"),
    path("calcular-por-tipo/", views.calcular_por_tipo, name="calcular_por_tipo")
]
