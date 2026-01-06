from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.timezone import now
from django.http import HttpResponse as httpResponse, JsonResponse, HttpResponseBadRequest
from .models import Project, Estudiante, Docente, ProjectStudent, DepartmentChoices
import json, re
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required, user_passes_test



# ==============================================================================
# 1. ZONA DE SEGURIDAD Y PERMISOS
# ==============================================================================

def es_super_admin(user):
    """Retorna True si es el Super Admin (Tú)."""
    return user.is_authenticated and user.is_superuser

def puede_editar(user):
    """
    Retorna True si es Super Admin O si es Staff (Editor).
    Los usuarios normales (Lectores) darán False.
    """
    return user.is_authenticated and (user.is_superuser or user.is_staff)

def acceso_denegado(request):
    """Vista para renderizar la pantalla de error 403."""
    return render(request, 'acceso_denegado.html')

# ==============================================================================
# 2. AUTENTICACIÓN Y USUARIOS
# ==============================================================================

def signup(request):
    """Registro de usuarios: Por defecto nacen SIN permisos (Solo Lectura)."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'signup.html')

        # Creación del usuario seguro
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = False      # No es editor
        user.is_superuser = False  # No es admin
        user.save()

        messages.success(request, 'Cuenta creada exitosamente. Tu cuenta es de SOLO LECTURA por defecto.')
        return redirect('login')

    return render(request, 'signup.html')

def inicio_sesion(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)

        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            
    return render(request, 'login.html')

def cierre_sesion(request):
    auth_logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')

# ==============================================================================
# 3. GESTIÓN DE USUARIOS (Solo Super Admin)
# ==============================================================================

@login_required
@user_passes_test(es_super_admin, login_url='acceso_denegado')
def gestionar_usuarios(request):
    # Excluye al propio admin para evitar auto-borrado
    users = User.objects.all().exclude(id=request.user.id).order_by('-date_joined')
    return render(request, 'gestionar_usuarios.html', {'users': users})

@login_required
@user_passes_test(es_super_admin, login_url='acceso_denegado')
def cambiar_permiso_usuario(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if user_to_edit.is_superuser:
        messages.error(request, 'No puedes degradar a otro Super Administrador.')
        return redirect('gestionar_usuarios')

    # Toggle de permisos Staff
    nuevo_estado = not user_to_edit.is_staff
    user_to_edit.is_staff = nuevo_estado
    user_to_edit.save()
    
    rol_msg = "EDITOR (Puede modificar)" if nuevo_estado else "LECTOR (Solo ver)"
    messages.success(request, f'Permisos actualizados. {user_to_edit.username} ahora es {rol_msg}.')
    return redirect('gestionar_usuarios')

@login_required
@user_passes_test(es_super_admin, login_url='acceso_denegado')
def eliminar_usuario(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    
    if user_to_delete.is_superuser:
        messages.error(request, 'No puedes eliminar a un Super Administrador.')
        return redirect('gestionar_usuarios')
        
    nombre = user_to_delete.username
    user_to_delete.delete()
    messages.success(request, f'El usuario {nombre} ha sido eliminado correctamente.')
    return redirect('gestionar_usuarios')

# ==============================================================================
# 4. PROYECTOS
# ==============================================================================

@login_required
def home(request):
    proyectos = (
        Project.objects
        .filter(is_deleted=False)
        .select_related('director', 'codirector')
        .prefetch_related('students__estudiante')
        .order_by('id')
    )
    docentes = Docente.objects.all()
    estudiantes = Estudiante.objects.all()
    return render(request, 'home.html', {
        'proyectos': proyectos,
        'docentes': docentes,
        'estudiantes': estudiantes,
    })

@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def agregar_proyecto(request):
    # --- LOGICA POST (GUARDAR) ---
    if request.method == 'POST':
        try:
            # 1. Recolección de datos básicos
            modalidad = request.POST.get('modalidad')
            title = request.POST.get('title')
            department = request.POST.get('department')
            director_id = request.POST.get('director_id') or None
            codirector_id = request.POST.get('codirector_id') or None
            notes = request.POST.get('notes')
            
            # Fechas
            start_date_str = request.POST.get('start_date')
            if not start_date_str:
                return JsonResponse({'success': False, 'error': 'La fecha de inicio es obligatoria.'})
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            expiry_date = start_date + timedelta(days=365) # Lógica de negocio: 1 año de vigencia

            # Números opcionales
            sesion_val = request.POST.get('sesion')
            sesion = int(sesion_val) if sesion_val else 0
            
            resolucion_val = request.POST.get('resolucion')
            resolucion = int(resolucion_val) if resolucion_val else None

            # 2. Validación de Estudiantes
            estudiantes_legajos = request.POST.getlist('estudiantes')
            
            if not estudiantes_legajos:
                 return JsonResponse({'success': False, 'error': 'Debe seleccionar al menos un estudiante.'})

            if modalidad == 'INVESTIGACION' and len(estudiantes_legajos) > 2:
                return JsonResponse({'success': False, 'error': 'Investigación permite máximo 2 estudiantes.'})

            if modalidad != 'INVESTIGACION' and len(estudiantes_legajos) > 1:
                return JsonResponse({'success': False, 'error': 'Esta modalidad permite solo 1 estudiante.'})

            # 3. Validación de Directores
            def validar_docente_en_depto(doc_id, depto_code):
                if not doc_id: return None
                try:
                    d = Docente.objects.get(id=int(doc_id))
                    doc_norm = _normalize_depto_for_compare(d.departamento)
                    dep_norm = _normalize_depto_for_compare(depto_code)
                    if doc_norm != dep_norm:
                        raise ValueError(f"El docente {d.nombre} no pertenece a {depto_code}")
                    return d
                except Docente.DoesNotExist:
                    raise ValueError("Docente no encontrado")

            director_obj = None
            codirector_obj = None

            if director_id:
                director_obj = validar_docente_en_depto(director_id, department)
            
            # Solo validar codirector si la modalidad lo permite (Investigación)
            if codirector_id and modalidad == 'INVESTIGACION':
                codirector_obj = validar_docente_en_depto(codirector_id, department)

            # 4. Crear el Proyecto
            proyecto = Project.objects.create(
                start_date=start_date,
                expiry_date=expiry_date,
                sesion=sesion,
                resolucion=resolucion,
                modalidad=modalidad,
                title=title,
                department=department,
                director=director_obj,
                codirector=codirector_obj,
                status='ACTIVO',
                notes=notes
            )

            # 5. Asociar Estudiantes
            for legajo in estudiantes_legajos:
                ProjectStudent.objects.create(
                    project=proyecto,
                    estudiante_id=legajo
                )

            messages.success(request, 'Proyecto creado con éxito.')
            return JsonResponse({'success': True})

        except ValueError as ve:
             return JsonResponse({'success': False, 'error': str(ve)})
        except Exception as e:
             return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

    # --- LOGICA GET (MOSTRAR MODAL) ---
    
    # Preparar datos necesarios para el formulario
    
    # Lista pura para el JSON script (Filtros JS)
    all_docentes_list = list(Docente.objects.values('id', 'nombre', 'departamento'))
    
    # Opciones de Departamento
    department_choices = DepartmentChoices.choices

    context = {
        'docentes_list': all_docentes_list,
        'estudiantes': Estudiante.objects.all(),
        'modalidad_choices': Project.MODALIDAD_CHOICES,
        'department_choices': department_choices,
    }

    # Si la petición es via AJAX/Modal
    if request.GET.get('modal'):
        return render(request, 'agregar_proyecto.html', context)
    
    # Si alguien entra directo a la URL (fallback), redirigir a home
    return redirect('home')


@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def modificar_proyecto(request, proyecto_id):
    # Obtenemos el proyecto
    proyecto = get_object_or_404(Project, id=proyecto_id, is_deleted=False)

    if request.method == 'POST':
        try:
            # ==========================================
            # 1. ACTUALIZACIÓN DATOS DEL PROYECTO
            # ==========================================
            departamento_post = request.POST.get('department') or ''
            
            # Fechas
            start_date_str = request.POST.get('start_date')
            expiry_date_str = request.POST.get('expiry_date')
            
            if start_date_str:
                proyecto.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            
            if expiry_date_str:
                proyecto.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            
            # Campos numéricos y textos
            val_sesion = request.POST.get('sesion')
            proyecto.sesion = int(val_sesion) if val_sesion else 0
            
            val_resolucion = request.POST.get('resolucion')
            proyecto.resolucion = int(val_resolucion) if val_resolucion else None
            
            proyecto.modalidad = request.POST.get('modalidad') or proyecto.modalidad
            proyecto.title = request.POST.get('title') or proyecto.title
            proyecto.department = departamento_post or proyecto.department
            proyecto.status = request.POST.get('status') or proyecto.status
            proyecto.notes = request.POST.get('notes') or proyecto.notes

            # === Lógica de Directores ===
            director_id = request.POST.get('director_id') or None
            codirector_id = request.POST.get('codirector_id') or None

            # Función interna de validación
            def validar_docente_en_depto(docente_id, depto_code):
                if not docente_id:
                    return None
                try:
                    d = Docente.objects.get(id=int(docente_id))
                except (Docente.DoesNotExist, ValueError):
                    raise ValueError('Docente no encontrado')

                if not depto_code:
                    raise ValueError('Seleccione un departamento antes de asignar docente')

                docente_norm = _normalize_depto_for_compare(d.departamento)
                depto_norm = _normalize_depto_for_compare(depto_code)

                if docente_norm != depto_norm:
                    raise ValueError(f'El docente {d.nombre} no pertenece a {depto_code}')
                return d

            # Asignaciones Directores
            if director_id:
                proyecto.director = validar_docente_en_depto(director_id, proyecto.department)
            else:
                proyecto.director = None

            if codirector_id:
                proyecto.codirector = validar_docente_en_depto(codirector_id, proyecto.department)
            else:
                proyecto.codirector = None

            # Guardar los cambios en la tabla 'projects'
            proyecto.save()
            

            # ==========================================
            # 2. ACTUALIZACIÓN DE ESTUDIANTES
            # ==========================================
            
            # Obtenemos la lista de legajos(codigo) desde el select multiple
            nuevos_estudiantes_legajos = request.POST.getlist('estudiantes')

            # Validación: No permitir proyectos sin estudiantes
            if not nuevos_estudiantes_legajos:
                 raise ValueError('Debe asignar al menos un estudiante al proyecto.')

            # A. Borramos las relaciones viejas en la tabla intermedia
            ProjectStudent.objects.filter(project=proyecto).delete()

            # B. Creamos las nuevas relaciones
            for legajo in nuevos_estudiantes_legajos:
                ProjectStudent.objects.create(
                    project=proyecto,
                    estudiante_id=legajo 
                )


            # ==========================================
            # 3. RESPUESTA FINAL
            # ==========================================
            messages.success(request, 'Proyecto actualizado con éxito.')
            return JsonResponse({'success': True})

        except ValueError as e:
            # Error de validación lógica
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception as e:
            # Error general
            return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)

    # --- GET request (Carga del Modal) ---
    
    # 1. Filtramos lista inicial
    if proyecto.department:
        depto_norm = _normalize_depto_for_compare(proyecto.department)
        docentes_filtered_qs = Docente.objects.all()
        docentes_filtered = [d for d in docentes_filtered_qs if _normalize_depto_for_compare(d.departamento) == depto_norm]
    else:
        docentes_filtered = []

    # 2. Lista completa para el JS
    all_docentes_list = list(Docente.objects.values('id', 'nombre', 'departamento'))

    context = {
        'proyecto': proyecto,
        'docentes_filtered': docentes_filtered,
        'docentes_list': all_docentes_list,
        'estudiantes': Estudiante.objects.all(),
        'modalidad_choices': Project.MODALIDAD_CHOICES,
        'status_choices': Project.STATUS_CHOICES,
    }

    return render(request, 'modificar_proyecto.html', context)


@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def eliminar_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Project, id=proyecto_id)
    proyecto.is_deleted = True
    proyecto.deleted_at = now()
    proyecto.save()
    messages.success(request, 'Proyecto eliminado correctamente.')
    return redirect('home')

@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def cambiar_estado_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Project, id=proyecto_id, is_deleted=False)
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('status')
    except Exception:
        return HttpResponseBadRequest('JSON inválido')

    estados_validos = [c[0] for c in Project.STATUS_CHOICES]
    if nuevo_estado not in estados_validos:
        return JsonResponse({'success': False, 'error': 'Estado inválido'}, status=400)

    proyecto.status = nuevo_estado
    proyecto.save(update_fields=['status'])
    return JsonResponse({'success': True, 'status': proyecto.status})

def actualizar_proyectos_vencidos():
    hoy = now().date()
    Project.objects.filter(status='ACTIVO', expiry_date__lt=hoy, is_deleted=False).update(status='INACTIVO')



# ==============================================================================
# 5. DOCENTES
# ==============================================================================

@login_required
def docentes(request):
    docentes = Docente.objects.all()
    return render(request, 'docentes.html', {'docentes': docentes})


@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def agregar_docente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        departamento = request.POST.get('departamento')
        facultad = request.POST.get('facultad')
        email = request.POST.get('email')
        docente = Docente(nombre=nombre, departamento=departamento, facultad=facultad, email=email)
        docente.save()
        messages.success(request, 'Docente agregado con éxito.')
        return redirect('docentes')
    messages.error(request, 'Método no permitido.')
    return redirect('docentes')

@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def modificar_docente(request, docente_id):
    try:
        docente = Docente.objects.get(id=docente_id)
    except Docente.DoesNotExist:
        messages.error(request, 'El docente no existe.')
        return redirect('docentes')

    if request.method == 'POST':
        docente.nombre = request.POST.get('nombre')
        docente.departamento = request.POST.get('departamento')
        docente.facultad = request.POST.get('facultad')
        docente.email = request.POST.get('email')
        docente.save()
        messages.success(request, 'Docente modificado con éxito.')
        return redirect('docentes')

    return render(request, 'modificar_docente.html', {'docente': docente})


@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def eliminar_docente(request, docente_id):
    try:
        docente = Docente.objects.get(id=docente_id)
        docente.delete()
        messages.success(request, 'Docente eliminado con éxito.')
    except Docente.DoesNotExist:
        messages.error(request, 'El docente no existe.')
    return redirect('docentes')

# ==============================================================================
# 6. ESTUDIANTES
# ==============================================================================

@login_required
def estudiantes(request):
    estudiantes = Estudiante.objects.all()
    return render(request, 'estudiantes.html', {'estudiantes': estudiantes})

@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def agregar_estudiante(request):
    if request.method == 'POST':
        legajo = request.POST.get('legajo')
        tipo_identificacion = request.POST.get('tipo_identificacion')
        identificacion = request.POST.get('identificacion')
        primer_apellido = request.POST.get('primer_apellido').upper()
        segundo_apellido = request.POST.get('segundo_apellido').upper()
        primer_nombre = request.POST.get('primer_nombre').upper()
        segundo_nombre = request.POST.get('segundo_nombre').upper()
        correo_institucional = request.POST.get('correo_institucional')
        telefono = request.POST.get('telefono')
        celular = request.POST.get('celular')
        facultad = "FACULTAD DE INGENIERIA CIVIL"
        programa = request.POST.get('programa')
        regionalizacion = request.POST.get('regionalizacion')
        sede = request.POST.get('sede')

        estudiante_obj = Estudiante(
            legajo=legajo,
            tipo_identificacion=tipo_identificacion,
            identificacion=identificacion,
            primer_apellido=primer_apellido,
            segundo_apellido=segundo_apellido,
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,
            correo_institucional=correo_institucional,
            telefono=telefono,
            celular=celular,
            facultad=facultad,
            programa=programa,
            regionalizacion=regionalizacion,
            sede=sede,
        )
        estudiante_obj.save()
        messages.success(request, 'Estudiante agregado con éxito.')
        return redirect('estudiantes')

    messages.error(request, 'Método no permitido.')
    return redirect('estudiantes')

@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def modificar_estudiante(request, estudiante_legajo):
    try:
        estudiante = Estudiante.objects.get(legajo=estudiante_legajo)
    except Estudiante.DoesNotExist:
        messages.error(request, 'El estudiante no existe.')
        return redirect('estudiantes')

    if request.method == 'POST':
        estudiante.tipo_identificacion = request.POST.get('tipo_identificacion')
        estudiante.identificacion = request.POST.get('identificacion')
        estudiante.primer_apellido = request.POST.get('primer_apellido')
        estudiante.segundo_apellido = request.POST.get('segundo_apellido')
        estudiante.primer_nombre = request.POST.get('primer_nombre')
        estudiante.segundo_nombre = request.POST.get('segundo_nombre')
        estudiante.correo_institucional = request.POST.get('correo_institucional')
        estudiante.telefono = request.POST.get('telefono')
        estudiante.celular = request.POST.get('celular')
        estudiante.facultad = request.POST.get('facultad')
        estudiante.programa = request.POST.get('programa')
        estudiante.regionalizacion = request.POST.get('regionalizacion')
        estudiante.sede = request.POST.get('sede')
        estudiante.save()
        messages.success(request, 'Estudiante modificado con éxito.')
        return redirect('estudiantes')

    return render(request, 'modificar_estudiante.html', {'estudiante': estudiante})

@login_required
@user_passes_test(puede_editar, login_url='acceso_denegado')
def eliminar_estudiante(request, estudiante_legajo):
    try:
        estudiante = Estudiante.objects.get(legajo=estudiante_legajo)
        estudiante.delete()
        messages.success(request, 'Estudiante eliminado con éxito.')
    except Estudiante.DoesNotExist:
        messages.error(request, 'El estudiante no existe.')
    return redirect('estudiantes')

# ==============================================================================
# 7. UTILIDADES
# ==============================================================================

def _normalize_depto_for_compare(raw: str) -> str:
    """
    Normaliza un nombre de departamento para comparaciones:
    - Pasa a mayúsculas
    - Quita prefijos comunes como 'DEPTO ' o 'DEPARTAMENTO '
    - Sustituye cualquier caracter no alfanumérico por '_' y colapsa guiones bajos repetidos
    Ejemplo: 'DEPTO VIAS Y TRANSPORTE' -> 'VIAS_Y_TRANSPORTE'
    """
    if not raw:
        return ''
    s = raw.upper()
    # Quitar prefijos que aparecen en la tabla 'docentes'
    s = re.sub(r'^(DEPTO|DEPARTAMENTO|DEPTO\.)\s+', '', s)
    # Reemplazar caracteres no alfanuméricos por underscore
    s = re.sub(r'[^A-Z0-9]+', '_', s)
    # Colapsar múltiples underscores y trim
    s = re.sub(r'_+', '_', s).strip('_')
    return s