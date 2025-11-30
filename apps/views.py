from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Recetas, Ingredientes, RecetaIngredientes, TiposComida


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
