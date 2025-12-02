from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Recetas, Ingredientes, RecetaIngredientes, TiposComida
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
<<<<<<< HEAD
from .models import Usuarios
from .forms import LoginForm, ValidarCorreoForm, NuevaPasswordForm
from django.db import transaction
=======
from .models import Usuarios, Roles
from .forms import LoginForm, ValidarCorreoForm, NuevaPasswordForm, UsuarioAdminForm
>>>>>>> a6cff90f3278205f8c0648192075b6e3b5b31613

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
                    role_id = usuario.id_rol.pk 

                    request.session['usuario_rol'] = role_id
                    
                    # CASO 1: Administradores (Rol 1 y 2) -> Gestión de Usuarios
                    if role_id in [1, 2]:
                        return redirect('usuarios')
                    
                    # CASO 2: Cocina/Chef (Rol 2 o 3) -> Cálculo de Recetas
                    #elif role_id in [2, 3]:
                    elif role_id == 3:
                        return redirect('calculo_recetas')
                    
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

# 1. VISTA PRINCIPAL (Lista + Buscador)
def gestion_usuarios(request):
     # PASO 1: Verificar si siquiera está logueado
    if 'usuario_id' not in request.session:
        return redirect('login')  # <--- Si no hay sesión, mándalo al LOGIN, no al index
    user_role = request.session.get('usuario_rol')
    # PASO 2: Verificar si es Administrador (Rol 1)
    if user_role not in [1, 2]: 
        messages.error(request, "No tienes permisos de administrador para acceder a esta página.")
        
        # Redirigir según el rol, si no es 1 o 2
        if user_role == 3:
            return redirect('calculo_recetas')
        return redirect('login') # Si es un rol desconocido
    
    query = request.GET.get('q') # Lo que escribió en el buscador
    usuarios = Usuarios.objects.all().order_by('id_usuario')

    # Filtro del Buscador
    if query:
        # Busca por nombre O por correo
        usuarios = usuarios.filter(
            Q(nombre__icontains=query) | Q(correo__icontains=query)
        )

    # Cargamos los roles para poder usarlos en el HTML manual si es necesario
    roles = Roles.objects.all()
    
    # Pasamos el formulario vacío para el Modal de Crear
    form_crear = UsuarioAdminForm()

    return render(request, 'usuarios.html', {
        'usuarios': usuarios,
        'roles': roles,
        'form_crear': form_crear
    })


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