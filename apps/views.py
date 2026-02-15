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
from .utils import render_to_pdf, obtener_calculo_receta, formatear_cantidad_inteligente
from django.db.models import F
from datetime import datetime

@login_personalizado_required
@transaction.atomic # ⬅️ USAMOS EL DECORADOR PARA TRANSACCIÓN
def crear_receta(request):
   
    if request.method == "POST":

      
        nombre = request.POST.get("nombre_receta", "").strip()
        tipo_comida = request.POST.get("tipo_comida")

        ingredientes_ids = request.POST.getlist("ingrediente") 
        cantidades_str = request.POST.getlist("cantidad")      
        unidades = request.POST.getlist("unidad")

        errores = []  
        
       
        print(f"DEBUG: Recibí listas del HTML -> IDs: {ingredientes_ids} | Cantidades: {cantidades_str}")

        ingredientes_validos = []
        
        for i, ing_id in enumerate(ingredientes_ids):
            ing_id = ing_id.strip()
            texto_cantidad = cantidades_str[i]
            
            print(f"--- Analizando Fila {i} ---")
            print(f"   1. ID Ingrediente: '{ing_id}'")
            print(f"   2. Texto Cantidad: '{texto_cantidad}'")

            try:
                
                cantidad = float(texto_cantidad.replace(',', '.'))
                print(f"   3. Conversión Exitosa: El número es {cantidad}")
            except Exception as e:
                print(f"   3. ERROR DE CONVERSIÓN: {e}")
                cantidad = 0

            unidad = unidades[i].strip() if i < len(unidades) else ""
            
      
            if cantidad > 0 and ing_id:
                print("   RESULTADO: APROBADO ✅")
                ingredientes_validos.append({
                    'id': ing_id,
                    'cantidad': cantidad,
                    'unidad': unidad
                })
            else:
                print(f"   RESULTADO: RECHAZADO ❌ (Cant: {cantidad}, ID: '{ing_id}')")

        if not nombre:
            errores.append("Debe ingresar un nombre para la receta.")

        if not tipo_comida or not TiposComida.objects.filter(id_tipo_comida=tipo_comida).exists():
            errores.append("Tipo de comida inválido.")

   
        if not ingredientes_validos:
            errores.append("Debe ingresar al menos un ingrediente con cantidad mayor a cero.")
            
        usados = set()  

        for ing_data in ingredientes_validos:

            ing_id = ing_data['id']
            cantidad = ing_data['cantidad']
            unidad = ing_data['unidad']

         
            if ing_id in usados:
                errores.append("Hay ingredientes repetidos.")
            else:
                usados.add(ing_id)

            if unidad == "":
                errores.append(f"Debe seleccionar una unidad para el ingrediente ID: {ing_id}.")
                
          
            if not Ingredientes.objects.filter(pk=ing_id).exists():
                 errores.append(f"El ingrediente ID '{ing_id}' no es válido o no existe.")

        
        if errores:
            
            for e in errores:
                messages.error(request, e)  
            return redirect("crear_receta") 


        
        receta = Recetas.objects.create(
            nombre=nombre,
            id_tipo_comida_id=tipo_comida, 
            estado=1,                      
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

  
        for ing_data in ingredientes_validos:
            RecetaIngredientes.objects.create(
                id_receta=receta,              
                id_ingrediente_id=ing_data['id'], 
                cantidad=ing_data['cantidad'],
                unidad=ing_data['unidad']
            )

       
        messages.success(request, "Receta agregada correctamente.")
        
       
        return redirect("crear_receta")


    
    context = {
        "ingredientes": Ingredientes.objects.all(), 
        "tipos_comida": TiposComida.objects.all()    
    }

    return render(request, "creacion_recetas.html", context)



def recetas_por_tipo(request, id_tipo):
    recetas = Recetas.objects.filter(id_tipo_comida=id_tipo).values("id_receta", "nombre")
    return JsonResponse(list(recetas), safe=False)

@login_personalizado_required
def resumen_calculos(request):
    if request.method == "GET":
        request.session['resumen_recetas'] = []
        request.session.modified = True
        
    tipos_comida = TiposComida.objects.all()
    ingredientes = Ingredientes.objects.all()

    # 1. Recuperamos la lista de recetas que ya hemos guardado en la sesión
    # Si no existe, creamos una lista vacía []
    resumen_acumulado = request.session.get('resumen_recetas', [])

    calculo = None  

    if request.method == "POST":
        receta_id = request.POST.get("receta")
        receta_dos_id = request.POST.get("receta_dos") # Por si eliges acompañamiento
        
        # Captura segura de comensales (tu lógica)
        raw_comensales = request.POST.get("comensales", "1")
        try:
            comensales = int(raw_comensales) if raw_comensales.strip() != "" else 1
        except ValueError:
            comensales = 1

        # --- NUEVO: Captura de Fecha (Punto 2) ---
        fecha_receta = request.POST.get("fecha_receta")
        if not fecha_receta:
            from django.utils import timezone
            fecha_receta = timezone.now().strftime("%Y-%m-%d")

        # Obtenemos la receta para el cálculo inmediato
        receta = Recetas.objects.get(id_receta=receta_id)
        ingredientes_receta = RecetaIngredientes.objects.filter(id_receta=receta)

        # Tu lógica de cálculo para la receta actual (el botón "Calcula")
        calculo = []
        for item in ingredientes_receta:
            cantidad_total = item.cantidad * comensales
            calculo.append({
                "ingrediente": item.id_ingrediente.nombre,
                "cantidad_base": item.cantidad,
                "unidad": item.id_unidad.nombre,
                "cantidad_total": cantidad_total
            })

        # --- NUEVO: Guardar en el resumen para el Informe (Punto 1 y 2) ---
        # Guardamos los datos mínimos para poder procesar el informe después
# 1. Creamos la estructura de la receta (Punto 1 y 2)
        nueva_entrada = {
            'fecha': fecha_receta,
            'comensales': comensales,
            'receta_id': receta_id,
            'receta_dos_id': receta_dos_id,
            'nombres': receta.nombre + (f" + {Recetas.objects.get(id_receta=receta_dos_id).nombre}" if receta_dos_id else "")
        }
        
        # 2. La agregamos a la lista que recuperamos al principio de la función
        resumen_acumulado.append(nueva_entrada)
        
        # 3. ORDENAR POR FECHA (Vital para el requerimiento Punto 2)
        # Esto asegura que el separador gris en el HTML y el PDF funcione bien
        resumen_acumulado.sort(key=lambda x: x['fecha'])
        
        # 4. GUARDAR EN LA SESIÓN (Aquí estaba tu error anterior)
        # Debes asignar la lista a la sesión, no al revés.
        request.session['resumen_recetas'] = resumen_acumulado
        request.session.modified = True  # Avisamos a Django que la sesión cambió

    # Fuera del IF del POST, el contexto envía la lista actualizada
    context = {
        "tipos_comida": tipos_comida,
        "ingredientes": ingredientes,
        "calculo": calculo,
        "resumen_recetas": resumen_acumulado 
    }

    return render(request, "resumen_calculos.html", context)

def calcular_por_tipo(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        receta_id = data.get("receta_id")
        receta_dos_id = data.get("receta_dos")
        
        # Limpieza de comensales
        try:
            comensales = int(data.get("comensales", 1))
        except (ValueError, TypeError):
            comensales = 1

        if not receta_id:
            return JsonResponse({"error": "Falta el ID de la receta principal"}, status=400)


        calculo_uno = obtener_calculo_receta(receta_id, comensales)
        calculo_dos = obtener_calculo_receta(receta_dos_id, comensales)

        if calculo_uno is None:
            return JsonResponse({"error": "La receta principal no existe"}, status=404)

        return JsonResponse({
            "calculo": calculo_uno,
            "calculo_dos": calculo_dos 
        })

    except Exception as e:
        print(f"Error en servidor: {e}")
        return JsonResponse({"error": "Error interno del servidor"}, status=500)

def agregar_al_resumen(request):
    """Guarda la selección actual en la sesión del servidor."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            resumen = request.session.get('resumen_recetas', [])
            
            nombres = data.get('nombre1', 'Receta')
            if data.get('nombre2') and data.get('nombre2') != "Seleccione una receta":
                nombres += f" + {data['nombre2']}"

            resumen.append({
                'fecha': data.get('fecha', timezone.now().strftime("%Y-%m-%d")),
                'comensales': data.get('comensales', 1),
                'receta_id': data.get('receta_id'),
                'receta_dos_id': data.get('receta_dos_id'),
                'nombres': nombres
            })
            
            # --- PUNTO 2: ORDENAR POR FECHA ---
            resumen.sort(key=lambda x: x['fecha']) 
            
            request.session['resumen_recetas'] = resumen
            request.session.modified = True
            return JsonResponse({'status': 'ok', 'recetas': resumen})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def obtener_acumulados(request):
    """Devuelve lo que hay en el 'carrito' actual."""
    return JsonResponse({'recetas': request.session.get('resumen_recetas', [])})

def eliminar_receta_resumen(request, index):
    """Permite quitar una receta de la lista antes de generar el PDF."""
    resumen = request.session.get('resumen_recetas', [])
    if 0 <= index < len(resumen):
        resumen.pop(index)
        request.session['resumen_recetas'] = resumen
        request.session.modified = True
    return JsonResponse({'status': 'ok', 'recetas': resumen})




def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            password = form.cleaned_data['password']

            try:
                usuario = Usuarios.objects.get(correo=correo)

                if usuario.estado != 1: 
                    messages.error(request, "Tu usuario está inactivo. Contacta a RRHH.")
                    return redirect('login')

                
                if not usuario.password_hash:
                    messages.info(request, "Aún no tienes contraseña. Ve a 'Primer Ingreso'.")
                    return redirect('login')

                
                if check_password(password, usuario.password_hash):
                    request.session['usuario_id'] = usuario.id_usuario
                    request.session['usuario_nombre'] = usuario.nombre
                    role_id = usuario.id_rol.pk 

                    request.session['usuario_rol'] = role_id
                    
                    
                    if role_id == 1:
                        return redirect('usuarios')
                    
                    
                    elif role_id == 3:
                        return redirect('resumen_calculos')
                    
                    elif role_id == 2:
                        return redirect('crear_receta')
                    
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



def primer_ingreso_a(request):
    if request.method == 'POST':
        form = ValidarCorreoForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            try:
                usuario = Usuarios.objects.get(correo=correo)
                
                
                if usuario.estado != 1:
                    messages.error(request, "No estás autorizado (Usuario Inactivo).")
                    return redirect('primer_ingreso_a')

                
                if usuario.password_hash and usuario.password_hash.strip() != '':
                    messages.info(request, "Ya tienes una contraseña creada. Inicia sesión o recupérala.")
                    return redirect('login')
                
               
                request.session['usuario_temp_id'] = usuario.id_usuario
                return redirect('primer_ingreso_b')

            except Usuarios.DoesNotExist:
                messages.error(request, "Correo no encontrado en la nómina.")
    else:
        form = ValidarCorreoForm()

    return render(request, 'registro/primer_ingreso_a.html', {'form': form})


def primer_ingreso_b(request):
  
    usuario_id = request.session.get('usuario_temp_id')
    if not usuario_id:
        return redirect('primer_ingreso_a')

    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            usuario = Usuarios.objects.get(pk=usuario_id)
            
            usuario.password_hash = make_password(form.cleaned_data['password'])
            usuario.save()
           
            del request.session['usuario_temp_id']
            
            messages.success(request, "Contraseña creada con éxito. Ya puedes iniciar sesión.")
            return redirect('login') 
        else:
                messages.warning(request, "Tu rol no tiene una página de inicio asignada.")
                return redirect('login')
    else:
        form = NuevaPasswordForm()

    return render(request, 'registro/primer_ingreso_b.html', {'form': form})

@login_personalizado_required
def recuperar_a(request):
    if request.method == 'POST':
        form = ValidarCorreoForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            try:
                usuario = Usuarios.objects.get(correo=correo)
                
        
                if usuario.estado != 1:
                    messages.error(request, "Tu cuenta está inactiva. Contacta al administrador.")
                    return redirect('recuperar_step1')

                request.session['recuperar_user_id'] = usuario.id_usuario
                return redirect('recuperar_b')

            except Usuarios.DoesNotExist:
                messages.error(request, "El correo ingresado no existe.")
    else:
        form = ValidarCorreoForm()

    return render(request, 'registro/recuperar_a.html', {'form': form})



def recuperar_b(request):
    
    usuario_id = request.session.get('recuperar_user_id')
    if not usuario_id:
        return redirect('recuperar_a')

    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            usuario = Usuarios.objects.get(pk=usuario_id)                
            usuario.password_hash = make_password(form.cleaned_data['password'])
            usuario.save()
           
            del request.session['recuperar_user_id']
            
            messages.success(request, "Contraseña restablecida correctamente. Inicia sesión.")
            return redirect('login')
    else:
        form = NuevaPasswordForm()

    return render(request, 'registro/recuperar_b.html', {'form': form})
    
def logout_view(request):
    request.session.flush() 
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('login') 

@login_personalizado_required
def gestion_usuarios(request):
    form_crear = UsuarioAdminForm()
    query = request.GET.get('q')
    resultados_busqueda = None 
    
    if query:
        
        resultados_busqueda = Usuarios.objects.filter(
            Q(nombre__icontains=query) | Q(correo__icontains=query)
        ).order_by('nombre')
        
    roles = Roles.objects.all() 
    
    context = {
        'form_crear': form_crear,
      
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
           
            nuevo_usuario.password_hash = "" 
            nuevo_usuario.created_at = timezone.now()
            nuevo_usuario.save()
            messages.success(request, "Usuario creado correctamente.")
        else:
            messages.error(request, "Error al crear usuario. Revisa los datos.")
    
    return redirect('usuarios')


def editar_usuario_admin(request, id_usuario):
    usuario = get_object_or_404(Usuarios, pk=id_usuario)
    
    if request.method == 'POST':
        
        usuario.nombre = request.POST.get('nombre')
        usuario.correo = request.POST.get('correo')
        usuario.estado = request.POST.get('estado')

        rol_id = request.POST.get('rol')
        usuario.id_rol = Roles.objects.get(pk=rol_id)
        
        usuario.save()
        messages.success(request, f"Usuario {usuario.nombre} actualizado.")
    
    return redirect('usuarios')

def generar_informe_pdf(request):
    resumen_sesion = request.session.get('resumen_recetas', [])
    tipo_reporte = request.GET.get('tipo', 'total')

    if not resumen_sesion:
        return HttpResponse("No hay datos en la sesión.", status=400)

    # 1. Siempre ordenamos por fecha para que el agrupamiento funcione
    resumen_sesion.sort(key=lambda x: x['fecha'])

    if tipo_reporte == 'total':
        # --- RESUMEN TOTAL: AGRUPADO POR DÍA ---
        reporte_final_por_dia = []
        from itertools import groupby
        
        for fecha, registros in groupby(resumen_sesion, key=lambda x: x['fecha']):
            totales_del_dia = {}
            for reg in registros:
                # Procesamos receta principal y acompañamiento
                for r_id in [reg['receta_id'], reg.get('receta_dos_id')]:
                    if r_id:
                        # Usamos la función que ya arreglamos en utils.py
                        ingredientes_calculados = obtener_calculo_receta(r_id, reg['comensales'])
                        if ingredientes_calculados:
                            for ing in ingredientes_calculados:
                                llave = (ing['ingrediente'], ing['unidad'])
                                # Quitamos formato (. y ,) para sumar el número puro
                                valor_limpio = float(ing['cantidad_total'].replace('.', '').replace(',', '.'))
                                totales_del_dia[llave] = totales_del_dia.get(llave, 0) + valor_limpio

            # Formateamos los resultados de este día
            lista_formateada = []
            for (nombre, unidad), total in totales_del_dia.items():
                cant_fmt, uni_fmt = formatear_cantidad_inteligente(total, unidad)
                lista_formateada.append({'nombre': nombre, 'cantidad': cant_fmt, 'unidad': uni_fmt})
            
            reporte_final_por_dia.append({
                'fecha': fecha,
                'ingredientes': sorted(lista_formateada, key=lambda x: x['nombre'])
            })

        return render_to_pdf('reporte_total_pdf.html', {
            'reporte_por_dia': reporte_final_por_dia,
            'fecha_actual': datetime.now().strftime("%d/%m/%Y")
        })

    else:
        # --- RESUMEN POR RECETA: (Ya mencionaste que funciona bien) ---
        reporte_detalle = []
        for item in resumen_sesion:
            ing_1 = obtener_calculo_receta(item['receta_id'], item['comensales']) or []
            ing_2 = obtener_calculo_receta(item['receta_dos_id'], item['comensales']) or []
            reporte_detalle.append({
                'fecha': item['fecha'],
                'nombres': item['nombres'],
                'comensales': item['comensales'],
                'ingredientes': ing_1 + ing_2
            })

        return render_to_pdf('reporte_detalle_pdf.html', {
            'reporte': reporte_detalle,
            'fecha_actual': datetime.now().strftime("%d/%m/%Y")
        })