// proyects.js - Controlador Global del Home

$(document).ready(function () {
    /* =========================================
       1. CONFIGURACIÓN DATATABLE
       ========================================= */
    if ($('#datatable').length > 0) {
        const table = $('#datatable').DataTable({
            responsive: { details: false },
            pageLength: 10,
            columnDefs: [{ orderable: false, targets: -1 }],
            language: {
                url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
            }
        });

        /* =========================================
           2. MODAL VER DETALLES (SOLO LECTURA)
           ========================================= */
        const modalDetalleEl = document.getElementById('detalleModal');
        const modalDetalle = modalDetalleEl ? new bootstrap.Modal(modalDetalleEl) : null;

        function decodeBr(text) {
            return text ? text.replace(/&lt;br&gt;/g, '<br>') : '';
        }

        $('#datatable tbody').on('click', '.btn-detalle', function () {
            let tr = $(this).closest('tr');
            if (tr.hasClass('child')) tr = tr.prev();
            
            const ds = table.row(tr).node().dataset;

            if(document.getElementById('detalleModalTitle')) {
                document.getElementById('detalleModalTitle').textContent = `Detalles del Proyecto No. ${ds.id}`;
                document.getElementById('d-start').textContent = ds.start || '—';
                document.getElementById('d-expiry').textContent = ds.expiry || '—';
                document.getElementById('d-sesion').textContent = ds.sesion || '—';
                document.getElementById('d-resolucion').textContent = ds.resolucion || '—';
                document.getElementById('d-modalidad').textContent = ds.modalidad || '—';
                document.getElementById('d-department').textContent = ds.department || '—';
                document.getElementById('d-director').textContent = ds.director || '—';
                document.getElementById('d-codirector').textContent = ds.codirector || '—';
                document.getElementById('d-status').textContent = ds.status || '—';
                document.getElementById('d-title').textContent = ds.title || '—';
                
                document.getElementById('d-students-names').innerHTML = decodeBr(ds.studentsNames);
                document.getElementById('d-students-legajos').innerHTML = decodeBr(ds.studentsLegajos);
                document.getElementById('d-notes').textContent = 
                    (ds.notes === '__SIN_OBSERVACIONES__' || !ds.notes) ? 'Sin observaciones' : ds.notes;
            }

            if(modalDetalle) modalDetalle.show();
        });

        /* =========================================
           3. CAMBIO DE ESTADO (SELECT CON COLORES)
           ========================================= */
        const confirmarEstadoModalEl = document.getElementById('confirmarEstadoModal');
        if (confirmarEstadoModalEl) {
            const confirmarEstadoModal = new bootstrap.Modal(confirmarEstadoModalEl);
            let estadoPendiente = null;
            let selectPendiente = null;

            $('#datatable tbody').on('change', '.estado-select', function () {
                const select = this;
                const nuevoEstado = select.value;
                const projectId = select.dataset.projectId;

                aplicarColorEstado(select);

                estadoPendiente = {
                    projectId: projectId,
                    nuevoEstado: nuevoEstado,
                    estadoOriginal: select.dataset.original
                };
                selectPendiente = select;

                document.getElementById('confirmarEstadoTexto').textContent = 
                    `¿Cambiar estado del Proyecto ${projectId} a ${nuevoEstado}?`;
                confirmarEstadoModal.show();
            });

            document.getElementById('cancelarCambioEstado').addEventListener('click', () => {
                if (selectPendiente) {
                    selectPendiente.value = selectPendiente.dataset.original;
                    aplicarColorEstado(selectPendiente);
                }
                confirmarEstadoModal.hide();
            });

            document.getElementById('confirmarCambioEstado').addEventListener('click', () => {
                const csrfToken = document.getElementById('csrf_token_global')?.value || '';

                fetch(`/cambiar_estado_proyecto/${estadoPendiente.projectId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ status: estadoPendiente.nuevoEstado })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        selectPendiente.dataset.original = data.status;
                        aplicarColorEstado(selectPendiente);
                        confirmarEstadoModal.hide();
                    } else {
                        alert('Error: ' + data.error);
                        selectPendiente.value = selectPendiente.dataset.original;
                        aplicarColorEstado(selectPendiente);
                    }
                })
                .catch(() => {
                    alert('Error de conexión.');
                    selectPendiente.value = selectPendiente.dataset.original;
                    aplicarColorEstado(selectPendiente);
                    confirmarEstadoModal.hide();
                });
            });
        }
    }
    
    document.querySelectorAll('.estado-select').forEach(select => aplicarColorEstado(select));
});

function aplicarColorEstado(select) {
    select.classList.remove('estado-activo', 'estado-finalizado', 'estado-inactivo');
    if (select.value === 'ACTIVO') select.classList.add('estado-activo');
    else if (select.value === 'FINALIZADO') select.classList.add('estado-finalizado');
    else if (select.value === 'INACTIVO') select.classList.add('estado-inactivo');
}

/* =========================================
   4. GESTOR DE MODALES (CORE)
   ========================================= */

window.abrirModalModificar = function(proyectoId) {
    cargarModal(`/modificar_proyecto/${proyectoId}/?modal=1`);
};

window.abrirModalAgregar = function() {
    cargarModal(`/agregar_proyecto/?modal=1`);
};

function cargarModal(url) {
    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error("Error HTTP al cargar modal");
            return res.text();
        })
        .then(html => {
            const container = document.getElementById('modalModificarContenido');
            const modalEl = document.getElementById('modalModificarProyecto');
            
            // 1. Inyectar HTML
            container.innerHTML = html;

            const scripts = container.querySelectorAll("script");
            scripts.forEach(oldScript => {
                const newScript = document.createElement("script");
                Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });

            // 3. Mostrar Modal
            const modalInstance = new bootstrap.Modal(modalEl);
            modalInstance.show();
        })
        .catch(err => console.error(err));
}

/* =========================================
   5. SUBMIT AJAX
   ========================================= */
document.addEventListener('submit', function (e) {
    if (e.target.id === 'formModificarProyecto' || e.target.id === 'formAgregarProyecto') {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Atención: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(err => alert('Error de conexión al guardar.'));
    }
});