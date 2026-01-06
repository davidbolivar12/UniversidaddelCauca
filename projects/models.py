from django.db import models

class DepartmentChoices(models.TextChoices):
    CONSTRUCCION = 'CONSTRUCCION', 'Arquitectura y Construcción'
    VIAS_Y_TRANSPORTE = 'VIAS_Y_TRANSPORTE', 'Vías y Transporte'
    HIDRAULICA = 'HIDRAULICA', 'Hidráulica'
    GEOTECNIA = 'GEOTECNIA', 'Geotecnia'
    ESTRUCTURAS = 'ESTRUCTURAS', 'Estructuras'
    ING_AMBIENTAL_SANITARIA = 'ING_AMBIENTAL_SANITARIA', 'Ing. Ambiental y Sanitaria'


class Docente(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    departamento = models.CharField(
        max_length=50,
        choices=DepartmentChoices.choices
    )

    facultad = models.CharField(max_length=100)
    email = models.CharField(max_length=100)


    class Meta:
        db_table = "docentes"
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"

    def __str__(self):
        return f"{self.nombre} ({self.departamento})"
    

class Estudiante(models.Model):
    legajo = models.CharField(max_length=20, primary_key=True)
    tipo_identificacion = models.CharField(max_length=5)
    identificacion = models.CharField(max_length=20)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True)
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50, blank=True, null=True)
    correo_institucional = models.CharField(max_length=100, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    facultad = models.CharField(max_length=100)
    programa = models.CharField(max_length=100)
    regionalizacion = models.CharField(max_length=1)
    sede = models.CharField(max_length=50)

    class Meta:
        db_table = "estudiantes"
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"

    def nombre_completo(self):
        return " ".join(filter(None, [
            self.primer_nombre,
            self.segundo_nombre,
            self.primer_apellido,
            self.segundo_apellido
        ]))

    def __str__(self):
        return f"{self.nombre_completo()} ({self.legajo})"



class Project(models.Model):
    # === Fechas ===
    start_date = models.DateField(
        help_text="Fecha de inicio del proyecto"
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de vencimiento del proyecto"
    )

    # === Datos académicos ===
    sesion = models.IntegerField(
        help_text="Número de sesión"
    )

    resolucion = models.IntegerField(
        null=True,
        blank=True,
        help_text="Número de resolución"
    )

    MODALIDAD_CHOICES = [
        ('PRACTICA', 'Práctica profesional'),
        ('INVESTIGACION', 'Investigación'),
        ('COTERMINAL', 'Plan Coterminal'),
        ('PROFUNDIZACION', 'Profundización'),
        ('TRABAJO_SOCIAL', 'Trabajo Social'),
    ]

    modalidad = models.CharField(
        max_length=20,
        choices=MODALIDAD_CHOICES
    )

    title = models.CharField(
        max_length=500,
        help_text="Título del proyecto"
    )

    department = models.CharField(
        max_length=50,
        choices=DepartmentChoices.choices,
        help_text="Departamento académico"
    )

    # === Docentes ===
    director = models.ForeignKey(
        'Docente',
        on_delete=models.SET_NULL,
        null=True,
        related_name='projects_directed'
    )

    codirector = models.ForeignKey(
        'Docente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_codirected'
    )

    # === Estado ===
    STATUS_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('FINALIZADO', 'Finalizado'),
    ]

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='ACTIVO'
    )

    # === Borrado lógico ===
    is_deleted = models.BooleanField(
        default=False
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # === Auditoría ===
    updated_at = models.DateTimeField(
        auto_now=True
    )

    # === Observaciones ===
    notes = models.TextField(
        null=True,
        blank=True
    )

    aviso_3_meses_enviado = models.BooleanField(default=False)
    aviso_1_mes_enviado = models.BooleanField(default=False)

    class Meta:
        db_table = 'projects'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Proyecto #{self.id} - {self.title}"


    
class ProjectStudent(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='students',
        db_column='project_id'
    )

    estudiante = models.ForeignKey(
        Estudiante,
        to_field='legajo',
        on_delete=models.CASCADE,
        related_name='project_links',
        db_column='estudiante_legajo'
    )

    role = models.CharField(max_length=20, default='miembro')

    class Meta:
        db_table = 'projects_students'


