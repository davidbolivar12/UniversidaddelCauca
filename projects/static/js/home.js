$(document).ready(function () {
    /* =========================================
       1. CONFIGURACIÓN DATATABLE
       ========================================= */
    const tabla = $('#datatable').DataTable({
        language: {
            url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
        },
        columnDefs: [
            { targets: -1, orderable: false }
        ],
        paging: true,
        searching: true
    });

    /* =========================================
       2. MODAL "DETALLES" (Solo lectura)
       ========================================= */
    $('#datatable tbody').on('click', '.verBtn', function () {
        let data = tabla.row($(this).parents('tr')).data();
        let headers = ["No", "Fecha", "Sesión", "Programa", "Estudiante", "Modalidad", "Asunto", "Director", "Resolución", "Profesor"];
        
        let contenido = "";
        if(data) {
             headers.forEach((h, i) => {
                let valor = data[i] !== undefined ? data[i] : ''; 
                contenido += `<tr><th>${h}</th><td>${valor}</td></tr>`;
            });
        }
        $("#detalleContenido").html(contenido);
        $("#detalleModal").modal("show");
    });

    /* =========================================
       3. CAMBIO DE ESTADO
       ========================================= */
    
    // Función segura para obtener el token CSRF desde el HTML
    function getCSRFToken() {
        const tokenInput = document.getElementById('csrf_token_global');
        return tokenInput ? tokenInput.value : '';
    }

    const confirmarEstadoModalEl = document.getElementById('confirmarEstadoModal');
    // Verificacion de que el modal exista antes de intentar instanciarlo
    if (confirmarEstadoModalEl) {
        const confirmarEstadoModal = new bootstrap.Modal(confirmarEstadoModalEl);
        
        let estadoPendiente = null;
        let selectPendiente = null;

        // Delegación de eventos para los selects
        $('#datatable tbody').on('change', '.estado-select', function () {
            const select = this;
            const nuevoEstado = select.value;
            const estadoOriginal = select.dataset.original;
            const projectId = select.dataset.projectId;

            aplicarColorEstado(select);

            estadoPendiente = {
                projectId,
                nuevoEstado,
                estadoOriginal
            };
            selectPendiente = select;

            const textoConfirmacion = document.getElementById('confirmarEstadoTexto');
            if (textoConfirmacion) {
                textoConfirmacion.textContent = `¿Confirmas cambiar el estado del Proyecto No. ${projectId} a ${nuevoEstado}?`;
            }

            confirmarEstadoModal.show();
        });

        // Botón Cancelar
        const btnCancelar = document.getElementById('cancelarCambioEstado');
        if (btnCancelar) {
            btnCancelar.addEventListener('click', () => {
                if (selectPendiente && estadoPendiente) {
                    // Revertir cambio visual
                    selectPendiente.value = estadoPendiente.estadoOriginal;
                    aplicarColorEstado(selectPendiente);
                }
                confirmarEstadoModal.hide();
            });
        }

        // Botón Confirmar
        const btnConfirmar = document.getElementById('confirmarCambioEstado');
        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', () => {
                fetch(`/cambiar_estado_proyecto/${estadoPendiente.projectId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        status: estadoPendiente.nuevoEstado
                    })
                })
                .then(res => {
                    if (!res.ok) throw new Error('Error HTTP: ' + res.status);
                    return res.json();
                })
                .then(data => {
                    if (data.success) {
                        selectPendiente.dataset.original = data.status;
                        
                        const tr = selectPendiente.closest('tr');
                        if (tr) tr.dataset.status = data.status;

                        aplicarColorEstado(selectPendiente);
                        confirmarEstadoModal.hide();
                    } else {
                        throw new Error(data.error || 'Error desconocido');
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert('No fue posible cambiar el estado. Verifique su conexión o permisos.');
                    
                    // Revertir en caso de error
                    selectPendiente.value = estadoPendiente.estadoOriginal;
                    aplicarColorEstado(selectPendiente);
                    confirmarEstadoModal.hide();
                });
            });
        }
    }

    /* =========================================
       4. GESTIÓN DE COLORES DE ESTADO
       ========================================= */
    function aplicarColorEstado(select) {
        select.classList.remove(
            'estado-activo',
            'estado-finalizado',
            'estado-inactivo'
        );

        if (select.value === 'ACTIVO') {
            select.classList.add('estado-activo');
        } else if (select.value === 'FINALIZADO') {
            select.classList.add('estado-finalizado');
        } else if (select.value === 'INACTIVO') {
            select.classList.add('estado-inactivo');
        }
    }

    // Inicializar colores al cargar la página
    document.querySelectorAll('.estado-select').forEach(select => {
        aplicarColorEstado(select);
    });
});