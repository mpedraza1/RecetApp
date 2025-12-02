from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import Recetas, Ingredientes, RecetaIngredientes, TiposComida
import json


def crear_receta(request):
    """
    Vista encargada de:
    - Mostrar el formulario de creación de recetas (GET)
    - Procesar los datos enviados y guardar la receta (POST)
    """

    # ======================================================================================
    # ===============       SI EL USUARIO ENVÍA EL FORMULARIO (POST)      ==================
    # ======================================================================================
    if request.method == "POST":

        # ---------------------------------------------------------
        # 1. Obtener datos enviados desde el formulario HTML
        # ---------------------------------------------------------
        nombre = request.POST.get("nombre_receta", "").strip()
        tipo_comida = request.POST.get("tipo_comida")

        # Como hay varios ingredientes, Django recibe listas
        ingredientes = request.POST.getlist("ingrediente")
        cantidades = request.POST.getlist("cantidad")
        unidades = request.POST.getlist("unidad")

        errores = []  # Lista donde acumularemos errores


        # ======================================================================================
        # ===============                VALIDACIONES                =============================
        # ======================================================================================

        # Validación nombre
        if not nombre:
            errores.append("Debe ingresar un nombre para la receta.")

        # Validación de tipo comida
        # Se verifica que exista en la tabla TiposComida
        if not tipo_comida or not TiposComida.objects.filter(id_tipo_comida=tipo_comida).exists():
            errores.append("Tipo de comida inválido.")

        # Validación de ingredientes
        usados = set()  # Para evitar ingredientes repetidos

        for i, ing in enumerate(ingredientes):

            # ¿Ingrediente repetido?
            if ing in usados:
                errores.append("Hay ingredientes repetidos.")
            usados.add(ing)

            # Validación de cantidad
            try:
                cantidad = float(cantidades[i])
                if cantidad <= 0:
                    errores.append("Las cantidades deben ser mayores a 0.")
            except:
                errores.append("Cantidad inválida.")

            # Validación unidad
            if unidades[i].strip() == "":
                errores.append("Debe ingresar una unidad válida.")


        # ======================================================================================
        # ===============     SI EXISTEN ERRORES, NO SE GUARDA    ==============================
        # ======================================================================================
        if errores:
            for e in errores:
                messages.error(request, e)  # Enviar mensajes al usuario
            return redirect("crear_receta")  # Recarga la página sin guardar nada


        # ======================================================================================
        # ===============            GUARDADO DE LA RECETA          =============================
        # ======================================================================================

        # Crear la receta en la tabla "recetas"
        receta = Recetas.objects.create(
            nombre=nombre,
            id_tipo_comida_id=tipo_comida,  # ForeignKey con sufijo _id
            estado=1,                       # Estado activo
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        # Crear cada ingrediente asociado a la receta
        for i, ing in enumerate(ingredientes):
            RecetaIngredientes.objects.create(
                id_receta=receta,          # ForeignKey al objeto receta creado
                id_ingrediente_id=ing,     # ID del ingrediente
                cantidad=cantidades[i],
                unidad=unidades[i]
            )

        # Mensaje de éxito
        messages.success(request, "Receta agregada correctamente.")
        
        # Redirigir nuevamente al formulario limpio
        return redirect("crear_receta")


    # ======================================================================================
    # ===============           SI ES GET → MOSTRAR FORMULARIO     =========================
    # ======================================================================================
    context = {
        "ingredientes": Ingredientes.objects.all(),  # Lista de ingredientes para el select
        "tipos_comida": TiposComida.objects.all()     # Lista de tipos de comida
    }

    return render(request, "creacion_recetas.html", context)



def recetas_por_tipo(request, id_tipo):
    recetas = Recetas.objects.filter(id_tipo_comida=id_tipo).values("id_receta", "nombre")
    return JsonResponse(list(recetas), safe=False)

def resumen_calculos(request):
    tipos_comida = TiposComida.objects.all()
    ingredientes = Ingredientes.objects.all()

    calculo = None  # Aquí guardaremos los resultados

    if request.method == "POST":
        receta_id = request.POST.get("receta")
        comensales = int(request.POST.get("comensales", 1))

        # Obtener receta seleccionada
        receta = Recetas.objects.get(id_receta=receta_id)

        # Obtener ingredientes de la receta
        ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)

        # Calcular cantidades
        calculo = []
        for item in ingredientes_receta:
            cantidad_total = item.cantidad * comensales
            calculo.append({
                "ingrediente": item.id_ingrediente.nombre,
                "cantidad_base": item.cantidad,
                "unidad": item.id_unidad.nombre,
                "cantidad_total": cantidad_total
            })

    context = {
        "tipos_comida": tipos_comida,
        "ingredientes": ingredientes,
        "calculo": calculo
    }

    return render(request, "resumen_calculos.html", context)

def calcular_por_tipo(request):
    if request.method == "POST":

        data = json.loads(request.body.decode("utf-8"))

        receta_id = data.get("receta_id")
        comensales = int(data.get("comensales", 1))
        
        receta_dos = data.get("receta_dos")
        tipo_dos = int(data.get("tipo_dos"))

        if not receta_id:
            return JsonResponse({"error": "No se envió receta_id"}, status=400)

        try:
            receta = Recetas.objects.get(id_receta=receta_id)
            ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)
            
            calculo_dos = None
            
            if receta_dos and tipo_dos:
                receta_dos = Recetas.objects.get(id_receta=receta_dos, id_tipo_comida=tipo_dos)
                ingredientes_receta_dos = RecetaIngredientes.objects.filter(id_receta=receta_dos)
                calculo_dos = []
                for item in ingredientes_receta_dos:
                    cantidad_total_dos = item.cantidad * comensales
                    calculo_dos.append({
                        "ingrediente": item.id_ingrediente.nombre,
                        "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                        "unidad": item.unidad,  # ajusta si tu modelo usa id_unidad
                        "cantidad_total": f"{int(cantidad_total_dos):_}".replace("_", ".")
                    })
                    
        except Recetas.DoesNotExist:
            return JsonResponse({"error": f"La receta {receta_id} no existe"}, status=404)


        
        calculo = []
        for item in ingredientes_receta:
            cantidad_total = item.cantidad * comensales
            calculo.append({
                "ingrediente": item.id_ingrediente.nombre,
                "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                "unidad": item.unidad,  # ajusta si tu modelo usa id_unidad
                "cantidad_total": f"{int(cantidad_total):_}".replace("_", ".")
            })
        

            
        return JsonResponse({"calculo": calculo, "calculo_dos": calculo_dos})
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


