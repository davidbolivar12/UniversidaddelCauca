    $(document).ready(function() {
      if (!$.fn.DataTable.isDataTable('#datatable')) {
        $('#datatable').DataTable({
          responsive: true,
          language: {
            url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
          }
        });
      }
    });
    
    document.addEventListener('DOMContentLoaded', function () {
      const deleteModal = document.getElementById('deleteModal');
      const deleteForm = document.getElementById('deleteForm');

      deleteModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // botón que abrió el modal
        const estudianteId = button.getAttribute('data-id'); // obtenemos el id
        deleteForm.action = `/eliminar_estudiante/${estudianteId}/`; // actualizamos el action dinámicamente
      });
    });



    document.addEventListener('DOMContentLoaded', function () {
      const editModal = document.getElementById('editModal');
      const editForm = document.getElementById('editForm');

      editModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const estudianteId = button.getAttribute('data-id');

        // Llenar los campos del formulario con los datos actuales
        document.getElementById('editTipo-identificacion').value = button.getAttribute('data-tipo-identificacion');
        document.getElementById('editIdentificacion').value = button.getAttribute('data-identificacion');
        document.getElementById('editPrimer-apellido').value = button.getAttribute('data-primer-apellido');
        document.getElementById('editSegundo-apellido').value = button.getAttribute('data-segundo-apellido');
        document.getElementById('editPrimer-nombre').value = button.getAttribute('data-primer-nombre');
        document.getElementById('editSegundo-nombre').value = button.getAttribute('data-segundo-nombre');
        document.getElementById('editCorreo-institucional').value = button.getAttribute('data-correo-institucional');
        document.getElementById('editTelefono').value = button.getAttribute('data-telefono');
        document.getElementById('editCelular').value = button.getAttribute('data-celular');
        document.getElementById('editFacultad').value = button.getAttribute('data-facultad');
        document.getElementById('editPrograma').value = button.getAttribute('data-programa');
        document.getElementById('editRegionalizacion').value = button.getAttribute('data-regionalizacion');
        document.getElementById('editSede').value = button.getAttribute('data-sede');
        // Actualizar la acción del formulario dinámicamente
        editForm.action = `/modificar_estudiante/${estudianteId}/`;
      });
    });

    document.addEventListener('DOMContentLoaded', function () {
      const detalleButtons = document.querySelectorAll('.btn-detalle');

      detalleButtons.forEach(button => {
        button.addEventListener('click', () => {
          document.getElementById('detalleLegajo').textContent = button.getAttribute('data-id');
          document.getElementById('detalleTipoIdentificacion').textContent = button.getAttribute('data-tipo-identificacion');
          document.getElementById('detalleIdentificacion').textContent = button.getAttribute('data-identificacion');
          document.getElementById('detallePrimerApellido').textContent = button.getAttribute('data-primer-apellido');
          document.getElementById('detalleSegundoApellido').textContent = button.getAttribute('data-segundo-apellido');
          document.getElementById('detallePrimerNombre').textContent = button.getAttribute('data-primer-nombre');
          document.getElementById('detalleSegundoNombre').textContent = button.getAttribute('data-segundo-nombre');
          document.getElementById('detalleCorreo').textContent = button.getAttribute('data-correo-institucional');
          document.getElementById('detalleTelefono').textContent = button.getAttribute('data-telefono');
          document.getElementById('detalleCelular').textContent = button.getAttribute('data-celular');
          document.getElementById('detalleFacultad').textContent = button.getAttribute('data-facultad');
          document.getElementById('detallePrograma').textContent = button.getAttribute('data-programa');
          document.getElementById('detalleRegionalizacion').textContent = button.getAttribute('data-regionalizacion');
          document.getElementById('detalleSede').textContent = button.getAttribute('data-sede');

          // Mostrar el modal
          const modal = new bootstrap.Modal(document.getElementById('detalleModal'));
          modal.show();
        });
      });

    });