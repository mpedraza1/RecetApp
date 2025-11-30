from django.urls import path
from . import views   # Importamos las views de ESTA app

urlpatterns = [
    path("creacion-recetas/", views.crear_receta, name="crear_receta"),
]
