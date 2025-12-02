from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Recetas, Ingredientes, RecetaIngredientes, TiposComida
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from .models import Usuarios
from .forms import LoginForm, ValidarCorreoForm, NuevaPasswordForm
from django.db import transaction

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
                    return redirect('index') 
                else:
                    messages.error(request, "Contraseña incorrecta.")
            
            except Usuarios.DoesNotExist:
                messages.error(request, "Correo no registrado.")
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
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nombre'] = usuario.nombre
            
            messages.success(request, "Contraseña creada con éxito. Bienvenido.")
            return redirect('index')
    else:
        form = NuevaPasswordForm()

    return render(request, 'registro/primer_ingreso_b.html', {'form': form})

# ---------------------------------------------------
# 4. RECUPERAR CONTRASEÑA - PASO 1 (Validar Correo)
# ---------------------------------------------------
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