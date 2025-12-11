from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from .models import Recetas, Ingredientes, RecetaIngredientes, TiposComida, Usuarios, Roles
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .decorators import login_personalizado_required
from django.contrib import messages
from django.db import transaction
from .forms import LoginForm, ValidarCorreoForm, NuevaPasswordForm, UsuarioAdminForm
import json
from .utils import render_to_pdf
from django.db.models import F
from datetime import datetime

@login_personalizado_required
@transaction.atomic # ⬅️ USAMOS EL DECORADOR PARA TRANSACCIÓN
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
        ingredientes_ids = request.POST.getlist("ingrediente") # Renombrado para claridad
        cantidades_str = request.POST.getlist("cantidad")      # Renombrado para claridad
        unidades = request.POST.getlist("unidad")

        errores = []  # Lista donde acumularemos errores
        
        # ---------------------------------------------------------
        # Pre-procesamiento de Ingredientes: 
        # Filtramos solo los que tienen Cantidad > 0 para validar y guardar.
        # ---------------------------------------------------------
        
        # ==============================================================================
        # COPIA DESDE AQUÍ EN TU VIEWS.PY (Reemplaza el bucle for anterior)
        # ==============================================================================
        
        print(f"DEBUG: Recibí listas del HTML -> IDs: {ingredientes_ids} | Cantidades: {cantidades_str}")

        ingredientes_validos = []
        
        for i, ing_id in enumerate(ingredientes_ids):
            ing_id = ing_id.strip()
            texto_cantidad = cantidades_str[i]
            
            print(f"--- Analizando Fila {i} ---")
            print(f"   1. ID Ingrediente: '{ing_id}'")
            print(f"   2. Texto Cantidad: '{texto_cantidad}'")

            try:
                # Intentamos convertir
                cantidad = float(texto_cantidad.replace(',', '.'))
                print(f"   3. Conversión Exitosa: El número es {cantidad}")
            except Exception as e:
                print(f"   3. ERROR DE CONVERSIÓN: {e}")
                cantidad = 0

            unidad = unidades[i].strip() if i < len(unidades) else ""
            
            # Verificación final
            if cantidad > 0 and ing_id:
                print("   RESULTADO: APROBADO ✅")
                ingredientes_validos.append({
                    'id': ing_id,
                    'cantidad': cantidad,
                    'unidad': unidad
                })
            else:
                print(f"   RESULTADO: RECHAZADO ❌ (Cant: {cantidad}, ID: '{ing_id}')")

        # ==============================================================================
        # ingredientes_validos = []
        
        # for i, ing_id in enumerate(ingredientes_ids):
        #     # Limpiamos espacios en blanco del ID
        #     ing_id = ing_id.strip() 
            
        #     # Obtenemos el texto de la cantidad
        #     texto_cantidad = cantidades_str[i]

        #     try:
        #         # AQUÍ ESTÁ EL ARREGLO PRINCIPAL:
        #         # Reemplazamos la coma por punto para que Python entienda el decimal
        #         cantidad = float(texto_cantidad.replace(',', '.'))
        #     except (ValueError, IndexError):
        #         cantidad = 0

        #     # Validar que exista la unidad (para evitar errores de índice)
        #     unidad = unidades[i].strip() if i < len(unidades) else ""
            
        #     # CONDICIÓN CORREGIDA:
        #     # 1. Cantidad debe ser mayor a 0
        #     # 2. Tiene que haber un ID de ingrediente (ing_id) seleccionado
        #     if cantidad > 0 and ing_id:  
        #         ingredientes_validos.append({
        #             'id': ing_id,
        #             'cantidad': cantidad,
        #             'unidad': unidad
        #         })


        # ======================================================================================
        # ===============                       VALIDACIONES                      =============================
        # ======================================================================================

        # Validación nombre
        if not nombre:
            errores.append("Debe ingresar un nombre para la receta.")

        # Validación de tipo comida
        if not tipo_comida or not TiposComida.objects.filter(id_tipo_comida=tipo_comida).exists():
            errores.append("Tipo de comida inválido.")

        # Validación de ingredientes válidos
        if not ingredientes_validos:
            errores.append("Debe ingresar al menos un ingrediente con cantidad mayor a cero.")
            
        usados = set()  # Para evitar ingredientes repetidos

        for ing_data in ingredientes_validos:

            ing_id = ing_data['id']
            cantidad = ing_data['cantidad']
            unidad = ing_data['unidad']

            # 1. Ingrediente repetido
            if ing_id in usados:
                errores.append("Hay ingredientes repetidos.")
            else:
                usados.add(ing_id)

            # 2. Validación unidad (la cantidad ya se filtró como > 0)
            if unidad == "":
                errores.append(f"Debe seleccionar una unidad para el ingrediente ID: {ing_id}.")
                
            # 3. Validación de existencia del ingrediente (Opcional, pero recomendado)
            if not Ingredientes.objects.filter(pk=ing_id).exists():
                 errores.append(f"El ingrediente ID '{ing_id}' no es válido o no existe.")

        # ======================================================================================
        # ===============     SI EXISTEN ERRORES, NO SE GUARDA (ROLLBACK)      ==================
        # ======================================================================================
        if errores:
            # Los mensajes de error se añaden y el código se redirige. 
            # La transacción no ha terminado, por lo que no hace falta rollback explícito.
            for e in errores:
                messages.error(request, e)  # Enviar mensajes al usuario
            return redirect("crear_receta") 


        # ======================================================================================
        # ===============             GUARDADO DE LA RECETA (COMMIT)            ==================
        # ======================================================================================

        # 1. Crear la receta en la tabla "recetas"
        receta = Recetas.objects.create(
            nombre=nombre,
            id_tipo_comida_id=tipo_comida, 
            estado=1,                      
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        # 2. Crear cada ingrediente asociado a la receta
        for ing_data in ingredientes_validos:
            RecetaIngredientes.objects.create(
                id_receta=receta,              
                id_ingrediente_id=ing_data['id'], 
                cantidad=ing_data['cantidad'],
                unidad=ing_data['unidad']
            )

        # Si llega aquí, la transacción se ha completado correctamente (COMMIT)
        messages.success(request, "Receta agregada correctamente.")
        
        # Redirigir nuevamente al formulario limpio
        return redirect("crear_receta")


    # ======================================================================================
    # ===============        SI ES GET → MOSTRAR FORMULARIO      =========================
    # ======================================================================================
    context = {
        "ingredientes": Ingredientes.objects.all(),  # Lista de ingredientes para el select
        "tipos_comida": TiposComida.objects.all()     # Lista de tipos de comida
    }

    return render(request, "creacion_recetas.html", context)



def recetas_por_tipo(request, id_tipo):
    recetas = Recetas.objects.filter(id_tipo_comida=id_tipo).values("id_receta", "nombre")
    return JsonResponse(list(recetas), safe=False)

@login_personalizado_required
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

def formatear_cantidad_inteligente(cantidad, nombre_unidad):
    """
    1. Convierte gr -> Kg y ml -> Litros si es >= 1000.
    2. Si el número final es entero (ej: 42.0), muestra "42" (sin ,00).
    3. Si tiene decimales (ej: 1.8), muestra "1,8" (quitando el 0 extra del final).
    """
    u = str(nombre_unidad).lower().strip()
    val = cantidad
    new_unit = nombre_unidad

    # --- 1. Lógica de Conversión de Unidad ---
    if u in ['gr', 'g', 'gramo', 'gramos'] and cantidad >= 1000:
        val = cantidad / 1000
        new_unit = "Kg"
    elif u in ['ml', 'cc', 'mililitro', 'mililitros'] and cantidad >= 1000:
        val = cantidad / 1000
        new_unit = "Litros"

    # --- 2. Lógica de Formateo Visual (EL ARREGLO) ---
    
    # Caso A: Es un número entero exacto (Ej: 42.0 o 600)
    if val == int(val):
        # Retornamos entero con punto de miles (Ej: "1.200" o "42")
        return f"{int(val):_}".replace('_', '.'), new_unit
    
    # Caso B: Tiene decimales reales (Ej: 1.8 o 1.25)
    else:
        # Formateamos a 2 decimales, cambiamos punto por coma, 
        # y quitamos los ceros a la derecha.
        # Ej: 1.8 -> "1.80" -> "1,80" -> "1,8"
        texto = f"{val:.2f}".replace('.', ',').rstrip('0').rstrip(',')
        return texto, new_unit
    
    
   
    u = str(nombre_unidad).lower().strip()
    
    # Lógica Kilos y Litros (Permite decimales útiles como 1,5)
    if u in ['gr', 'g', 'gramo', 'gramos'] and cantidad >= 1000:
        val = cantidad / 1000
        return f"{val:g}".replace('.', ','), "Kg"

    if u in ['ml', 'cc', 'mililitro', 'mililitros'] and cantidad >= 1000:
        val = cantidad / 1000
        return f"{val:g}".replace('.', ','), "Litros"

    # Lógica por defecto: SIEMPRE ENTERO (Sin decimales)
    return f"{int(cantidad):_}".replace('_', '.'), nombre_unidad


    
    # 1. Normalizar texto (minusculas y sin espacios)
    u = str(nombre_unidad).lower().strip()
    
    # 2. Lógica Gramos -> Kilos
    if u in ['gr', 'g', 'gramo', 'gramos'] and cantidad >= 1000:
        nueva_cant = cantidad / 1000
        # :g elimina ceros innecesarios (1.50 -> 1.5)
        return f"{nueva_cant:g}".replace('.', ','), "Kg"

    # 3. Lógica Mililitros -> Litros
    if u in ['ml', 'cc', 'mililitro', 'mililitros'] and cantidad >= 1000:
        nueva_cant = cantidad / 1000
        return f"{nueva_cant:g}".replace('.', ','), "Litros"

    # 4. Retorno por defecto (Entero con punto de miles)
    return f"{int(cantidad):_}".replace('_', '.'), nombre_unidad


def calcular_por_tipo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            receta_id = data.get("receta_id")
            try:
                comensales = int(data.get("comensales", 1))
            except (ValueError, TypeError):
                comensales = 1
            
            receta_dos_id = data.get("receta_dos") 

            if not receta_id:
                return JsonResponse({"error": "No se envió receta_id"}, status=400)

            # ========================================================
            # 1. CONSOLIDACIÓN (Sumar ingredientes iguales)
            # ========================================================
            # Diccionario: Clave=(Nombre, Unidad) -> Valor=CantidadTotal
            consolidador = {}

            # Función auxiliar para procesar ingredientes de cualquier receta
            def procesar_receta(id_receta):
                try:
                    r = Recetas.objects.get(id_receta=id_receta)
                    items = RecetaIngredientes.objects.filter(id_receta=r)
                    for item in items:
                        nombre = item.id_ingrediente.nombre
                        unidad = str(item.unidad) if item.unidad else ""
                        cantidad_total = item.cantidad * comensales
                        
                        llave = (nombre, unidad)
                        if llave in consolidador:
                            consolidador[llave] += cantidad_total
                        else:
                            consolidador[llave] = cantidad_total
                except Recetas.DoesNotExist:
                    pass

            # Procesamos Receta 1
            procesar_receta(receta_id)

            # Procesamos Receta 2 (si existe)
            if receta_dos_id:
                procesar_receta(receta_dos_id)

            # ========================================================
            # 2. GENERAR LISTA FINAL FORMATEADA
            # ========================================================
            calculo_final = []

            for (nombre, unidad_orig), cantidad_total_num in consolidador.items():
                
                # A. Formatear Total (convertir a Kg/Litros si corresponde)
                cant_total_fmt, unidad_total_fmt = formatear_cantidad_inteligente(cantidad_total_num, unidad_orig)

                # B. Calcular Base Teórica (Total / Comensales) para mostrar en la tabla
                # Esto es necesario porque al sumar, la "base" individual se pierde.
                base_teorica = cantidad_total_num / comensales
                base_fmt = f"{int(base_teorica):_}".replace("_", ".") + " " + unidad_orig

                calculo_final.append({
                    "ingrediente": nombre,
                    "cantidad_base": base_fmt,
                    "unidad": unidad_total_fmt,
                    "cantidad_total": cant_total_fmt
                })

            # Ordenar alfabéticamente
            calculo_final.sort(key=lambda x: x['ingrediente'])

            # Devolvemos TODO en 'calculo'. 'calculo_dos' va vacío.
            # Tu JS actual pintará 'calculo' y como 'calculo_dos' es null, no hará nada extra.
            return JsonResponse({"calculo": calculo_final, "calculo_dos": None})

        except Exception as e:
            print(f"Error servidor: {e}") 
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            receta_id = data.get("receta_id")
            try:
                comensales = int(data.get("comensales", 1))
            except (ValueError, TypeError):
                comensales = 1
            
            receta_dos_id = data.get("receta_dos") 
            tipo_dos_raw = data.get("tipo_dos")

            if not receta_id:
                return JsonResponse({"error": "No se envió receta_id"}, status=400)

            # --- RECETA 1 ---
            receta = Recetas.objects.get(id_receta=receta_id)
            ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)
            
            calculo = []
            for item in ingredientes_receta:
                cantidad_total = item.cantidad * comensales
                unidad_orig = str(item.unidad) if item.unidad else ""
                
                # 1. Formateamos el total (Conversión a Kg/Litros o Entero)
                cant_total_fmt, unidad_total_fmt = formatear_cantidad_inteligente(cantidad_total, unidad_orig)

                # 2. Formateamos la base (Número Entero + Unidad Original)
                base_fmt = f"{int(item.cantidad):_}".replace("_", ".") + " " + unidad_orig

                calculo.append({
                    "ingrediente": item.id_ingrediente.nombre,
                    "cantidad_base": base_fmt,        # Ej: "200 gr"
                    "unidad": unidad_total_fmt,       # Ej: "Kg" (La unidad del total)
                    "cantidad_total": cant_total_fmt  # Ej: "1,5"
                })

            # --- RECETA 2 ---
            calculo_dos = None
            if receta_dos_id: 
                try:
                    receta_dos = Recetas.objects.get(id_receta=receta_dos_id)
                    ingredientes_receta_dos = RecetaIngredientes.objects.filter(id_receta=receta_dos)
                    
                    calculo_dos = []
                    for item in ingredientes_receta_dos:
                        cantidad_total_dos = item.cantidad * comensales
                        unidad_orig_dos = str(item.unidad) if item.unidad else ""

                        cant_total_fmt, unidad_total_fmt = formatear_cantidad_inteligente(cantidad_total_dos, unidad_orig_dos)
                        base_fmt_dos = f"{int(item.cantidad):_}".replace("_", ".") + " " + unidad_orig_dos

                        calculo_dos.append({
                            "ingrediente": item.id_ingrediente.nombre,
                            "cantidad_base": base_fmt_dos,
                            "unidad": unidad_total_fmt,
                            "cantidad_total": cant_total_fmt
                        })
                except (Recetas.DoesNotExist, ValueError):
                     pass 

            return JsonResponse({"calculo": calculo, "calculo_dos": calculo_dos})

        except Recetas.DoesNotExist:
            return JsonResponse({"error": "La receta principal no existe"}, status=404)
        except Exception as e:
            print(f"Error servidor: {e}") 
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            receta_id = data.get("receta_id")
            try:
                comensales = int(data.get("comensales", 1))
            except (ValueError, TypeError):
                comensales = 1
            
            receta_dos_id = data.get("receta_dos") 
            tipo_dos_raw = data.get("tipo_dos")

            if not receta_id:
                return JsonResponse({"error": "No se envió receta_id"}, status=400)

            # --- RECETA 1 ---
            receta = Recetas.objects.get(id_receta=receta_id)
            ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)
            
            calculo = []
            for item in ingredientes_receta:
                cantidad_total = item.cantidad * comensales
                unidad_original = str(item.unidad) if item.unidad else ""
                
                # APLICAMOS LA CONVERSIÓN AQUÍ
                cant_fmt, unidad_fmt = formatear_cantidad_inteligente(cantidad_total, unidad_original)

                calculo.append({
                    "ingrediente": item.id_ingrediente.nombre,
                    "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                    "unidad": unidad_fmt,        # Unidad convertida (si aplica)
                    "cantidad_total": cant_fmt   # Cantidad convertida
                })

            # --- RECETA 2 ---
            calculo_dos = None
            if receta_dos_id: 
                try:
                    receta_dos = Recetas.objects.get(id_receta=receta_dos_id)
                    ingredientes_receta_dos = RecetaIngredientes.objects.filter(id_receta=receta_dos)
                    
                    calculo_dos = []
                    for item in ingredientes_receta_dos:
                        cantidad_total_dos = item.cantidad * comensales
                        unidad_original_dos = str(item.unidad) if item.unidad else ""

                        # APLICAMOS LA CONVERSIÓN AQUÍ TAMBIÉN
                        cant_fmt_dos, unidad_fmt_dos = formatear_cantidad_inteligente(cantidad_total_dos, unidad_original_dos)

                        calculo_dos.append({
                            "ingrediente": item.id_ingrediente.nombre,
                            "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                            "unidad": unidad_fmt_dos,
                            "cantidad_total": cant_fmt_dos
                        })
                except (Recetas.DoesNotExist, ValueError):
                     pass 

            return JsonResponse({"calculo": calculo, "calculo_dos": calculo_dos})

        except Recetas.DoesNotExist:
            return JsonResponse({"error": "La receta principal no existe"}, status=404)
        except Exception as e:
            print(f"Error servidor: {e}") 
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            receta_id = data.get("receta_id")
            # Protección para comensales
            try:
                comensales = int(data.get("comensales", 1))
            except (ValueError, TypeError):
                comensales = 1
            
            receta_dos_id = data.get("receta_dos") 
            tipo_dos_raw = data.get("tipo_dos")

            if not receta_id:
                return JsonResponse({"error": "No se envió receta_id"}, status=400)

            # --- CÁLCULO RECETA 1 ---
            receta = Recetas.objects.get(id_receta=receta_id)
            ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)
            
            calculo = []
            for item in ingredientes_receta:
                cantidad_total = item.cantidad * comensales
                calculo.append({
                    "ingrediente": item.id_ingrediente.nombre,
                    # FORZAMOS ENTERO EN CANTIDAD BASE
                    "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                    "unidad": str(item.unidad) if item.unidad else "", 
                    # FORZAMOS ENTERO EN CANTIDAD TOTAL
                    "cantidad_total": f"{int(cantidad_total):_}".replace("_", ".")
                })

            # --- CÁLCULO RECETA 2 ---
            calculo_dos = None
            
            if receta_dos_id: 
                try:
                    receta_dos = Recetas.objects.get(id_receta=receta_dos_id)
                    ingredientes_receta_dos = RecetaIngredientes.objects.filter(id_receta=receta_dos)
                    
                    calculo_dos = []
                    for item in ingredientes_receta_dos:
                        cantidad_total_dos = item.cantidad * comensales
                        calculo_dos.append({
                            "ingrediente": item.id_ingrediente.nombre,
                            # FORZAMOS ENTERO EN CANTIDAD BASE
                            "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                            "unidad": str(item.unidad) if item.unidad else "", 
                            # FORZAMOS ENTERO EN CANTIDAD TOTAL
                            "cantidad_total": f"{int(cantidad_total_dos):_}".replace("_", ".")
                        })
                except (Recetas.DoesNotExist, ValueError):
                     pass 

            return JsonResponse({"calculo": calculo, "calculo_dos": calculo_dos})

        except Recetas.DoesNotExist:
            return JsonResponse({"error": "La receta principal no existe"}, status=404)
        except Exception as e:
            print(f"Error servidor: {e}") 
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            receta_id = data.get("receta_id")
            # Protección para comensales
            try:
                comensales = int(data.get("comensales", 1))
            except (ValueError, TypeError):
                comensales = 1
            
            receta_dos_id = data.get("receta_dos") 
            tipo_dos_raw = data.get("tipo_dos")

            if not receta_id:
                return JsonResponse({"error": "No se envió receta_id"}, status=400)

            # --- CÁLCULO RECETA 1 ---
            receta = Recetas.objects.get(id_receta=receta_id)
            ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)
            
            calculo = []
            for item in ingredientes_receta:
                cantidad_total = item.cantidad * comensales
                calculo.append({
                    "ingrediente": item.id_ingrediente.nombre,
                    "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                    # CORRECCIÓN: Usamos str() para asegurar que sea texto, sin pedir .nombre
                    "unidad": str(item.unidad) if item.unidad else "", 
                    "cantidad_total": f"{int(cantidad_total):_}".replace("_", ".")
                })

            # --- CÁLCULO RECETA 2 ---
            calculo_dos = None
            
            # Solo procesamos si hay ID de segunda receta
            if receta_dos_id: 
                try:
                    # Buscamos directamente por ID de receta
                    receta_dos = Recetas.objects.get(id_receta=receta_dos_id)
                    ingredientes_receta_dos = RecetaIngredientes.objects.filter(id_receta=receta_dos)
                    
                    calculo_dos = []
                    for item in ingredientes_receta_dos:
                        cantidad_total_dos = item.cantidad * comensales
                        calculo_dos.append({
                            "ingrediente": item.id_ingrediente.nombre,
                            "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                            # CORRECCIÓN: Igual aquí, str(item.unidad)
                            "unidad": str(item.unidad) if item.unidad else "", 
                            "cantidad_total": f"{int(cantidad_total_dos):_}".replace("_", ".")
                        })
                except (Recetas.DoesNotExist, ValueError):
                     pass 

            return JsonResponse({"calculo": calculo, "calculo_dos": calculo_dos})

        except Recetas.DoesNotExist:
            return JsonResponse({"error": "La receta principal no existe"}, status=404)
        except Exception as e:
            print(f"Error servidor: {e}") 
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            receta_id = data.get("receta_id")
            # Protección para comensales
            try:
                comensales = int(data.get("comensales", 1))
            except (ValueError, TypeError):
                comensales = 1
            
            # Datos "crudos" para evitar el error de validación
            receta_dos_id = data.get("receta_dos") 
            tipo_dos_raw = data.get("tipo_dos")

            if not receta_id:
                return JsonResponse({"error": "No se envió receta_id"}, status=400)

            # --- CÁLCULO RECETA 1 ---
            receta = Recetas.objects.get(id_receta=receta_id)
            ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)
            
            calculo = []
            for item in ingredientes_receta:
                cantidad_total = item.cantidad * comensales
                calculo.append({
                    "ingrediente": item.id_ingrediente.nombre,
                    "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                    # CORRECCIÓN AQUÍ: Cambiado de id_unidad a unidad
                    "unidad": item.unidad, 
                    "cantidad_total": f"{int(cantidad_total):_}".replace("_", ".")
                })

            # --- CÁLCULO RECETA 2 ---
            calculo_dos = None
            
            # Solo procesamos si hay datos reales en la segunda fila
            if receta_dos_id and tipo_dos_raw: 
                try:
                    tipo_dos_int = int(tipo_dos_raw)
                    receta_dos = Recetas.objects.get(id_receta=receta_dos_id, id_tipo_comida=tipo_dos_int)
                    ingredientes_receta_dos = RecetaIngredientes.objects.filter(id_receta=receta_dos)
                    
                    calculo_dos = []
                    for item in ingredientes_receta_dos:
                        cantidad_total_dos = item.cantidad * comensales
                        calculo_dos.append({
                            "ingrediente": item.id_ingrediente.nombre,
                            "cantidad_base": f"{int(item.cantidad):_}".replace("_", "."),
                            # CORRECCIÓN AQUÍ TAMBIÉN
                            "unidad": item.unidad.nombre, 
                            "cantidad_total": f"{int(cantidad_total_dos):_}".replace("_", ".")
                        })
                except (Recetas.DoesNotExist, ValueError):
                     pass 

            return JsonResponse({"calculo": calculo, "calculo_dos": calculo_dos})

        except Recetas.DoesNotExist:
            return JsonResponse({"error": "La receta principal no existe"}, status=404)
        except Exception as e:
            print(f"Error servidor: {e}") 
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


# ---------------------------------------------------
# 1. LOGIN (Solo para quienes YA tienen contraseña)
# ---------------------------------------------------
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            password = form.cleaned_data['password']

            try:
                usuario = Usuarios.objects.get(correo=correo)

                # 1. Verificar si sigue trabajando en la empresa
                # Asumo que 1 es activo y 0 es inactivo. Ajusta según tu lógica.
                if usuario.estado != 1: 
                    messages.error(request, "Tu usuario está inactivo. Contacta a RRHH.")
                    return redirect('login')

                # 2. Verificar si NO tiene contraseña configurada (Primer Ingreso)
                # Si el hash está vacío o es None, no debería estar logueándose por aquí
                if not usuario.password_hash:
                    messages.info(request, "Aún no tienes contraseña. Ve a 'Primer Ingreso'.")
                    return redirect('login')

                # 3. Verificar contraseña
                if check_password(password, usuario.password_hash):
                    request.session['usuario_id'] = usuario.id_usuario
                    request.session['usuario_nombre'] = usuario.nombre
                    role_id = usuario.id_rol.pk 

                    request.session['usuario_rol'] = role_id
                    
                    # CASO 1: Administradores (Rol 1 y 2) -> Gestión de Usuarios
                    if role_id == 1:
                        return redirect('usuarios')
                    
                    # CASO 2: Cocina/Chef (Rol 2 o 3) -> Cálculo de Recetas
                    elif role_id == 3:
                        return redirect('resumen_calculos')
                    
                    elif role_id == 2:
                        return redirect('crear_receta')
                    # CASO 3: Otros roles no definidos
                    else:
                        messages.warning(request, "Tu rol no tiene una página de inicio asignada.")
                        return redirect('login')
                     
                else:
                    messages.error(request, "Credenciales inválidas")
                    return redirect('login')
            
            except Usuarios.DoesNotExist:
                messages.error(request, "Credenciales inválidas")
    else:
        form = LoginForm()

    return render(request, 'registro/login.html', {'form': form})


# ---------------------------------------------------
# 2. PRIMER INGRESO - PASO 1 (Validar Correo y Estado)
# ---------------------------------------------------
def primer_ingreso_a(request):
    if request.method == 'POST':
        form = ValidarCorreoForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            try:
                usuario = Usuarios.objects.get(correo=correo)
                
                # A) Verificar si está activo en la empresa
                if usuario.estado != 1:
                    messages.error(request, "No estás autorizado (Usuario Inactivo).")
                    return redirect('primer_ingreso_a')

                # B) Verificar si YA tiene contraseña (si ya tiene, no es primer ingreso)
                # Si el campo tiene contenido, le decimos que vaya al login o a recuperar
                if usuario.password_hash and usuario.password_hash.strip() != '':
                    messages.info(request, "Ya tienes una contraseña creada. Inicia sesión o recupérala.")
                    return redirect('login')
                
                # C) Si pasa los filtros, permitimos crear contraseña
                request.session['usuario_temp_id'] = usuario.id_usuario
                return redirect('primer_ingreso_b')

            except Usuarios.DoesNotExist:
                messages.error(request, "Correo no encontrado en la nómina.")
    else:
        form = ValidarCorreoForm()

    return render(request, 'registro/primer_ingreso_a.html', {'form': form})


# ---------------------------------------------------
# 3. PRIMER INGRESO - PASO 2 (Crear Contraseña)
# ---------------------------------------------------
def primer_ingreso_b(request):
    # Seguridad: verificar que venimos del paso 1
    usuario_id = request.session.get('usuario_temp_id')
    if not usuario_id:
        return redirect('primer_ingreso_a')

    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            usuario = Usuarios.objects.get(pk=usuario_id)
            # Guardamos la nueva contraseña
            # NO tocamos el estado, porque ya verificamos que estaba activo
            usuario.password_hash = make_password(form.cleaned_data['password'])
            usuario.save()
            # Limpiamos temp y logueamos
            del request.session['usuario_temp_id']
            # Borraremos las líneas de 'request.session['usuario_id'] = ...'
            # Mensaje de éxito y redirigir al login para que el usuario inicie sesión
            messages.success(request, "Contraseña creada con éxito. Ya puedes iniciar sesión.")
            return redirect('login') # <--- ¡El cambio clave!
        else:
                messages.warning(request, "Tu rol no tiene una página de inicio asignada.")
                return redirect('login')
    else:
        form = NuevaPasswordForm()

    return render(request, 'registro/primer_ingreso_b.html', {'form': form})




# ---------------------------------------------------
# 4. RECUPERAR CONTRASEÑA - PASO 1 (Validar Correo)
# ---------------------------------------------------
@login_personalizado_required
def recuperar_a(request):
    if request.method == 'POST':
        form = ValidarCorreoForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            try:
                usuario = Usuarios.objects.get(correo=correo)
                
                # Validar que siga activo
                if usuario.estado != 1:
                    messages.error(request, "Tu cuenta está inactiva. Contacta al administrador.")
                    return redirect('recuperar_step1')

                # ¡Éxito! Guardamos ID temporalmente para el paso 2
                request.session['recuperar_user_id'] = usuario.id_usuario
                return redirect('recuperar_b')

            except Usuarios.DoesNotExist:
                messages.error(request, "El correo ingresado no existe.")
    else:
        form = ValidarCorreoForm()

    return render(request, 'registro/recuperar_a.html', {'form': form})


# ---------------------------------------------------
# 5. RECUPERAR CONTRASEÑA - PASO 2 (Nueva Contraseña)
# ---------------------------------------------------
def recuperar_b(request):
    # Seguridad: Verificar que viene del paso 1
    usuario_id = request.session.get('recuperar_user_id')
    if not usuario_id:
        return redirect('recuperar_a')

    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            usuario = Usuarios.objects.get(pk=usuario_id)
            
            # Sobreescribimos la contraseña
            usuario.password_hash = make_password(form.cleaned_data['password'])
            usuario.save()

            # Limpiamos sesión de recuperación
            del request.session['recuperar_user_id']
            
            messages.success(request, "Contraseña restablecida correctamente. Inicia sesión.")
            return redirect('login')
    else:
        form = NuevaPasswordForm()

    return render(request, 'registro/recuperar_b.html', {'form': form})
    
def logout_view(request):
    request.session.flush() # Borra todos los datos de la sesión (id, nombre, etc.)
    # Opcional: Agregar un mensaje para que aparezca en el login
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('login') # Te manda directo a la pantalla de entrada

@login_personalizado_required
def gestion_usuarios(request):
    form_crear = UsuarioAdminForm()
    query = request.GET.get('q')
    
    # Inicializamos la NUEVA variable de resultados como None.
    resultados_busqueda = None 
    
    if query:
        # Asignamos los resultados a la NUEVA variable solo si hay búsqueda.
        resultados_busqueda = Usuarios.objects.filter(
            Q(nombre__icontains=query) | Q(correo__icontains=query)
        ).order_by('nombre')
        
    roles = Roles.objects.all() 
    
    context = {
        'form_crear': form_crear,
        # Usamos el nuevo nombre en el contexto
        'resultados_busqueda': resultados_busqueda, 
        'roles': roles, 
        'query': query,
    }
    
    return render(request, 'usuarios.html', context)

def crear_usuario_admin(request):
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save(commit=False)
            # Importante: Password vacío para que funcione el flujo "Primer Ingreso"
            nuevo_usuario.password_hash = "" 
            nuevo_usuario.created_at = timezone.now()
            nuevo_usuario.save()
            messages.success(request, "Usuario creado correctamente.")
        else:
            messages.error(request, "Error al crear usuario. Revisa los datos.")
    
    return redirect('usuarios')

# 3. ACCIÓN DE EDITAR (Viene de la tabla)

def editar_usuario_admin(request, id_usuario):
    usuario = get_object_or_404(Usuarios, pk=id_usuario)
    
    if request.method == 'POST':
        # Actualizamos nombre, rol y estado manualmente para ser directos
        usuario.nombre = request.POST.get('nombre')
        usuario.correo = request.POST.get('correo')
        usuario.estado = request.POST.get('estado')
        
        # Para el rol, buscamos la instancia
        rol_id = request.POST.get('rol')
        usuario.id_rol = Roles.objects.get(pk=rol_id)
        
        usuario.save()
        messages.success(request, f"Usuario {usuario.nombre} actualizado.")
    
    return redirect('usuarios')

def generar_informe_pdf(request):
    try:
        cant_comensales = int(request.GET.get('comensales', 1))
    except ValueError:
        cant_comensales = 1

    fecha_raw = request.GET.get('fecha', '')
    fecha_final = timezone.now().strftime("%d/%m/%Y")
    if fecha_raw:
        try:
            fecha_final = datetime.strptime(fecha_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            pass

    raw_ids = request.GET.get('recetas', '')
    receta_ids = [int(x) for x in raw_ids.split(',') if x.isdigit()] if raw_ids else []

    ingredientes_consolidados = {}
    nombres_recetas_str = "Ninguna"

    if receta_ids:
        recetas = Recetas.objects.filter(id_receta__in=receta_ids)
        nombres_recetas_str = ", ".join([r.nombre for r in recetas])
        
        items_receta = RecetaIngredientes.objects.filter(id_receta__in=recetas).select_related('id_ingrediente')

        # --- LÓGICA DE SUMA ---
        for item in items_receta:
            nombre = item.id_ingrediente.nombre
            unidad = str(item.unidad) if item.unidad else "Unidad"
            cantidad_total = item.cantidad * cant_comensales
            
            llave = (nombre, unidad)
            
            if llave in ingredientes_consolidados:
                ingredientes_consolidados[llave] += cantidad_total
            else:
                ingredientes_consolidados[llave] = cantidad_total

    # --- LÓGICA DE FORMATO ---
    lista_final = []
    for (nombre, unidad), cantidad in ingredientes_consolidados.items():
        
        # Usamos la misma función inteligente que la tabla
        cant_fmt, unidad_fmt = formatear_cantidad_inteligente(cantidad, unidad)

        lista_final.append({
            'nombre': nombre,
            'cantidad_total': cant_fmt,
            'unidad': unidad_fmt
        })

    lista_final.sort(key=lambda x: x['nombre'])

    data = {
        'comensales': cant_comensales,
        'nombres_recetas': nombres_recetas_str,
        'ingredientes': lista_final,
        'fecha': fecha_final,
    }

    pdf = render_to_pdf('reporte_pdf.html', data)
    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')
    
    return HttpResponse("Error al generar el PDF", status=500)
    # 1. Datos básicos
    try:
        cant_comensales = int(request.GET.get('comensales', 1))
    except ValueError:
        cant_comensales = 1

    fecha_raw = request.GET.get('fecha', '')
    fecha_final = timezone.now().strftime("%d/%m/%Y")
    if fecha_raw:
        try:
            fecha_final = datetime.strptime(fecha_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            pass

    # 2. Recetas
    raw_ids = request.GET.get('recetas', '')
    receta_ids = [int(x) for x in raw_ids.split(',') if x.isdigit()] if raw_ids else []

    ingredientes_consolidados = {}
    nombres_recetas_str = "Ninguna"

    if receta_ids:
        recetas = Recetas.objects.filter(id_receta__in=receta_ids)
        nombres_recetas_str = ", ".join([r.nombre for r in recetas])
        
        items_receta = RecetaIngredientes.objects.filter(id_receta__in=recetas).select_related('id_ingrediente')

        for item in items_receta:
            nombre = item.id_ingrediente.nombre
            unidad = str(item.unidad) if item.unidad else "Unidad"
            cantidad_total = item.cantidad * cant_comensales
            llave = (nombre, unidad)
            
            if llave in ingredientes_consolidados:
                ingredientes_consolidados[llave] += cantidad_total
            else:
                ingredientes_consolidados[llave] = cantidad_total

    # 3. Formateo Final (AQUÍ ESTÁ EL CAMBIO)
    lista_final = []
    for (nombre, unidad), cantidad in ingredientes_consolidados.items():
        
        # Usamos la función inteligente para convertir si es necesario
        cant_fmt, unidad_fmt = formatear_cantidad_inteligente(cantidad, unidad)

        lista_final.append({
            'nombre': nombre,
            'cantidad_total': cant_fmt,
            'unidad': unidad_fmt
        })

    lista_final.sort(key=lambda x: x['nombre'])

    # 4. Render
    data = {
        'comensales': cant_comensales,
        'nombres_recetas': nombres_recetas_str,
        'ingredientes': lista_final,
        'fecha': fecha_final,
    }

    pdf = render_to_pdf('reporte_pdf.html', data)
    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')
    
    return HttpResponse("Error al generar el PDF", status=500)


    # 1. Obtener y validar comensales
    try:
        cant_comensales = int(request.GET.get('comensales', 1))
    except ValueError:
        cant_comensales = 1

    # 2. Fecha
    fecha_raw = request.GET.get('fecha', '')
    if fecha_raw:
        try:
            fecha_obj = datetime.strptime(fecha_raw, "%Y-%m-%d")
            fecha_final = fecha_obj.strftime("%d/%m/%Y")
        except ValueError:
            fecha_final = timezone.now().strftime("%d/%m/%Y")
    else:
        fecha_final = timezone.now().strftime("%d/%m/%Y")

    # 3. Obtener IDs
    raw_ids = request.GET.get('recetas', '')
    if raw_ids:
        receta_ids = [int(x) for x in raw_ids.split(',') if x.isdigit()]
    else:
        receta_ids = []

    ingredientes_consolidados = {}
    nombres_recetas_str = "Ninguna"

    if receta_ids:
        recetas = Recetas.objects.filter(id_receta__in=receta_ids)
        nombres_recetas_str = ", ".join([r.nombre for r in recetas])
        
        items_receta = RecetaIngredientes.objects.filter(id_receta__in=recetas).select_related('id_ingrediente')

        for item in items_receta:
            nombre = item.id_ingrediente.nombre
            unidad = str(item.unidad) if item.unidad else "Unidad"
            cantidad_total = item.cantidad * cant_comensales
            llave = (nombre, unidad)
            
            if llave in ingredientes_consolidados:
                ingredientes_consolidados[llave] += cantidad_total
            else:
                ingredientes_consolidados[llave] = cantidad_total

    # 4. Convertir a lista y formatear números
    lista_final = []
    for (nombre, unidad), cantidad in ingredientes_consolidados.items():
        lista_final.append({
            'nombre': nombre,
            # CAMBIO AQUÍ: Convertimos a int() y formateamos con puntos de mil
            'cantidad_total': f"{int(cantidad):_}".replace("_", "."),
            'unidad': unidad
        })

    lista_final.sort(key=lambda x: x['nombre'])

    # 5. Preparar contexto
    data = {
        'comensales': cant_comensales,
        'nombres_recetas': nombres_recetas_str,
        'ingredientes': lista_final,
        'fecha': fecha_final,
    }

    # 6. Generar PDF
    pdf = render_to_pdf('reporte_pdf.html', data)
    
    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')
    
    return HttpResponse("Error al generar el PDF", status=500)
    # 1. Obtener y validar comensales
    try:
        cant_comensales = int(request.GET.get('comensales', 1))
    except ValueError:
        cant_comensales = 1

    # =========================================================
    # 2. NUEVO: Obtener y formatear la fecha seleccionada
    # =========================================================
    fecha_raw = request.GET.get('fecha', '') # Viene como "YYYY-MM-DD"
    
    if fecha_raw:
        try:
            # Convertimos de formato HTML (2023-12-31) a objeto fecha
            fecha_obj = datetime.strptime(fecha_raw, "%Y-%m-%d")
            # Lo convertimos al formato chileno (31/12/2023)
            fecha_final = fecha_obj.strftime("%d/%m/%Y")
        except ValueError:
            # Si la fecha viene malformada, usamos la de hoy
            fecha_final = timezone.now().strftime("%d/%m/%Y")
    else:
        # Si el usuario no seleccionó fecha, usamos la de hoy
        fecha_final = timezone.now().strftime("%d/%m/%Y")

    # 3. Obtener y limpiar IDs de recetas
    raw_ids = request.GET.get('recetas', '')
    
    if raw_ids:
        receta_ids = [int(x) for x in raw_ids.split(',') if x.isdigit()]
    else:
        receta_ids = []

    ingredientes_consolidados = {}
    nombres_recetas_str = "Ninguna"

    if receta_ids:
        recetas = Recetas.objects.filter(id_receta__in=receta_ids)
        
        # Nombres para el reporte
        nombres_recetas_str = ", ".join([r.nombre for r in recetas])
        
        items_receta = RecetaIngredientes.objects.filter(id_receta__in=recetas).select_related('id_ingrediente')

        for item in items_receta:
            nombre = item.id_ingrediente.nombre
            unidad = str(item.unidad) if item.unidad else "Unidad"
            cantidad_total = item.cantidad * cant_comensales
            llave = (nombre, unidad)
            
            if llave in ingredientes_consolidados:
                ingredientes_consolidados[llave] += cantidad_total
            else:
                ingredientes_consolidados[llave] = cantidad_total

    # 4. Convertir a lista y ordenar
    lista_final = []
    for (nombre, unidad), cantidad in ingredientes_consolidados.items():
        lista_final.append({
            'nombre': nombre,
            'cantidad_total': f"{cantidad:g}".replace('.', ','),
            'unidad': unidad
        })

    lista_final.sort(key=lambda x: x['nombre'])

    # 5. Preparar contexto
    data = {
        'comensales': cant_comensales,
        'nombres_recetas': nombres_recetas_str,
        'ingredientes': lista_final,
        'fecha': fecha_final, # <--- Aquí pasamos la fecha procesada
    }

    # 6. Generar PDF
    pdf = render_to_pdf('reporte_pdf.html', data)
    
    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')
    
    return HttpResponse("Error al generar el PDF", status=500)
    # 1. Obtener y validar comensales
    try:
        cant_comensales = int(request.GET.get('comensales', 1))
    except ValueError:
        cant_comensales = 1

    # 2. Obtener y limpiar IDs de recetas
    raw_ids = request.GET.get('recetas', '')
    
    if raw_ids:
        receta_ids = [int(x) for x in raw_ids.split(',') if x.isdigit()]
    else:
        receta_ids = []

    ingredientes_consolidados = {}
    nombres_recetas_str = "Ninguna" # Valor por defecto

    if receta_ids:
        # Filtramos las recetas
        recetas = Recetas.objects.filter(id_receta__in=receta_ids)
        
        # --- NUEVO: Creamos una cadena de texto con los nombres ---
        # Esto crea algo como: "Cazuela, Ensalada Surtida"
        nombres_recetas_str = ", ".join([r.nombre for r in recetas])
        
        # Buscamos TODOS los ingredientes
        items_receta = RecetaIngredientes.objects.filter(id_receta__in=recetas).select_related('id_ingrediente')

        for item in items_receta:
            nombre = item.id_ingrediente.nombre
            # Usamos str() para evitar el error de .nombre en objetos que no lo tienen
            unidad = str(item.unidad) if item.unidad else "Unidad"

            cantidad_total = item.cantidad * cant_comensales

            llave = (nombre, unidad)
            
            if llave in ingredientes_consolidados:
                ingredientes_consolidados[llave] += cantidad_total
            else:
                ingredientes_consolidados[llave] = cantidad_total

    # 3. Convertir a lista
    lista_final = []
    for (nombre, unidad), cantidad in ingredientes_consolidados.items():
        lista_final.append({
            'nombre': nombre,
            'cantidad_total': f"{cantidad:g}".replace('.', ','),
            'unidad': unidad
        })

    lista_final.sort(key=lambda x: x['nombre'])

    # 4. Preparar contexto (Agregamos 'nombres_recetas')
    data = {
        'comensales': cant_comensales,
        'nombres_recetas': nombres_recetas_str, # <--- AQUÍ PASAMOS LOS NOMBRES
        'ingredientes': lista_final,
        'fecha': timezone.now().strftime("%d/%m/%Y"),
    }

    # 5. Generar PDF
    pdf = render_to_pdf('reporte_pdf.html', data)
    
    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')
    
    return HttpResponse("Error al generar el PDF", status=500)    # 1. Obtener y validar comensales
    try:
        cant_comensales = int(request.GET.get('comensales', 1))
    except ValueError:
        cant_comensales = 1

    # 2. Obtener y limpiar IDs de recetas
    raw_ids = request.GET.get('recetas', '')
    
    # Esto convierte "1,2,3" en [1, 2, 3] y evita errores con strings vacíos
    if raw_ids:
        receta_ids = [int(x) for x in raw_ids.split(',') if x.isdigit()]
    else:
        receta_ids = []

    # Diccionario para consolidar (Sumar ingredientes iguales)
    # Clave: (nombre_ingrediente, unidad) -> Valor: cantidad_acumulada
    ingredientes_consolidados = {}

    if receta_ids:
        # Filtramos las recetas
        recetas = Recetas.objects.filter(id_receta__in=receta_ids)
        
        # Buscamos TODOS los ingredientes de esas recetas
        items_receta = RecetaIngredientes.objects.filter(id_receta__in=recetas).select_related('id_ingrediente')

        for item in items_receta:
            nombre = item.id_ingrediente.nombre
            
            # INTENTO DE OBTENER LA UNIDAD (Manejo de errores por inconsistencia de modelos)
            # Prioridad 1: La unidad guardada en la relación (como en crear_receta)
            # Prioridad 2: La unidad del ingrediente base
            unidad = str(item.unidad) if item.unidad else "Unidad"

            # Calculamos el total para este ítem
            cantidad_total = item.cantidad * cant_comensales

            # Lógica de Suma (Agrupación)
            llave = (nombre, unidad)
            
            if llave in ingredientes_consolidados:
                ingredientes_consolidados[llave] += cantidad_total
            else:
                ingredientes_consolidados[llave] = cantidad_total

    # 3. Convertir el diccionario a una lista para el HTML
    lista_final = []
    for (nombre, unidad), cantidad in ingredientes_consolidados.items():
        lista_final.append({
            'nombre': nombre,
            'cantidad_total': f"{cantidad:g}".replace('.', ','), # Formato bonito (elimina ceros extra)
            'unidad': unidad
        })

    # Ordenar alfabéticamente
    lista_final.sort(key=lambda x: x['nombre'])

    # 4. Preparar contexto
    data = {
        'comensales': cant_comensales,
        'ingredientes': lista_final,
        'fecha': timezone.now().strftime("%d/%m/%Y"), # Fecha actual automática
    }

    # 5. Generar PDF
    pdf = render_to_pdf('reporte_pdf.html', data)
    
    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')
    
    return HttpResponse("Error al generar el PDF", status=500)