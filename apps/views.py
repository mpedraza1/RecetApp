from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Recetas, Ingredientes, RecetaIngredientes, TiposComida
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from .models import Usuarios
from .forms import LoginForm, ValidarCorreoForm, NuevaPasswordForm


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