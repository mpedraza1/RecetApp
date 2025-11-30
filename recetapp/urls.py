from django.contrib import admin
from django.urls import path
from apps import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path("creacion-recetas/", views.crear_receta, name="crear_receta"),

    
]
