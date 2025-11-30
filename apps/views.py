from django.shortcuts import render

def crear_receta(request):
    return render(request, "creacion_recetas.html")