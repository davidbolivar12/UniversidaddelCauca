from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.timezone import now
from projects.models import Project
from django.conf import settings
import datetime

#-------------------------------------------------------------------------------------------------
#COMANDO PARA EJECUTAR EL ENVIO DE CORREOS DESDE LA CONSOLA
#python manage.py verificar_vencimientos
#-------------------------------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Verifica proyectos próximos a vencer y envía correos de notificación'

    def handle(self, *args, **kwargs):
        hoy = now().date()
        print(f"--- Iniciando revisión de vencimientos: {hoy} ---")
        
        # Filtro de solo proyectos activos que no han sido borrados
        proyectos = Project.objects.filter(status='ACTIVO', is_deleted=False)
        enviados = 0

        for p in proyectos:
            if not p.expiry_date:
                continue

            # Calculo cuántos días faltan
            dias_restantes = (p.expiry_date - hoy).days
            
            destinatarios = []
            for ps in p.students.all():
                if ps.estudiante.correo_institucional:
                    destinatarios.append(ps.estudiante.correo_institucional)
            
            if not destinatarios:
                continue

            # -------------------------------------
            # LÓGICA DE 3 MESES
            # -------------------------------------
            if 60 < dias_restantes <= 90 and not p.aviso_3_meses_enviado:
                asunto = f"[ALERTA ACADÉMICA] Vencimiento Próximo de Proyecto de Grado - {p.title}"
                
                mensaje = (
                    f"Estimado(a) estudiante,\n\n"
                    f"Reciba un cordial saludo de la Universidad del Cauca.\n\n"
                    f"Por medio del presente se le notifica que el proyecto de grado titulado:\n"
                    f"\" {p.title.upper()} \"\n\n"
                    f"Se encuentra próximo a su fecha de vencimiento registrada en el sistema.\n\n"
                    f"DETALLES:\n"
                    f"- Fecha límite actual: {p.expiry_date.strftime('%d/%m/%Y')}\n"
                    f"- Tiempo restante aproximado: 3 meses ({dias_restantes} días)\n\n"
                    f"Le recordamos la importancia de gestionar con antelación los trámites pertinentes "
                    f"(entrega final o solicitud de prórroga) ante la coordinación correspondiente para "
                    f"evitar inconvenientes académicos.\n\n"
                    f"Atentamente,\n\n"
                    f"Sistema de Gestión de Proyectos de Grado\n"
                    f"Universidad del Cauca\n"
                    f"_________________________________________________\n"
                    f"(Este es un mensaje automático del sistema, por favor no responder a este correo)."
                )
                
                try:
                    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, destinatarios)
                    p.aviso_3_meses_enviado = True
                    p.save(update_fields=['aviso_3_meses_enviado'])
                    print(f"[OK] Aviso formal 3 meses enviado a: {p.title}")
                    enviados += 1
                except Exception as e:
                    print(f"[ERROR] ID {p.id}: {e}")

            # -----------------------------------------------
            # LÓGICA DE 1 MES
            # -----------------------------------------------
            elif 0 < dias_restantes <= 30 and not p.aviso_1_mes_enviado:
                asunto = f"[URGENTE] Vencimiento Inminente de Proyecto de Grado - {p.title}"
                
                mensaje = (
                    f"Estimado(a) estudiante,\n\n"
                    f"Se le notifica con carácter de URGENCIA que el plazo académico para la finalización de su proyecto de grado:\n"
                    f"\" {p.title.upper()} \"\n\n"
                    f"Está a punto de expirar.\n\n"
                    f"SITUACIÓN ACTUAL:\n"
                    f"- Fecha límite improrrogable: {p.expiry_date.strftime('%d/%m/%Y')}\n"
                    f"- Tiempo restante exacto: {dias_restantes} días\n\n"
                    f"Es imperativo que regularice su situación académica inmediatamente. "
                    f"Si no ha finalizado, debe gestionar una prórroga urgentemente o su proyecto podría "
                    f"cambiar de estado según el reglamento vigente.\n\n"
                    f"Atentamente,\n\n"
                    f"Universidad del Cauca\n"
                    f"_________________________________________________\n"
                    f"(Este es un aviso automático urgente)."
                )

                try:
                    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, destinatarios)
                    p.aviso_1_mes_enviado = True
                    p.save(update_fields=['aviso_1_mes_enviado'])
                    print(f"[OK] Aviso formal URGENTE 1 mes enviado a: {p.title}")
                    enviados += 1
                except Exception as e:
                    print(f"[ERROR] ID {p.id}: {e}")

        print(f"--- Fin del proceso. Correos enviados: {enviados} ---")