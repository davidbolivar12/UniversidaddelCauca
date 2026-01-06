    document.addEventListener('DOMContentLoaded', function() {
      const deleteModal = document.getElementById('deleteModal');
      const deleteForm = document.getElementById('deleteForm');

      deleteModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget; // botón que abrió el modal
    const docenteId = button.getAttribute('data-id'); // obtenemos el id
    deleteForm.action = `/eliminar_docente/${docenteId}/`; // actualizamos el action dinámicamente
  });
    });



  document.addEventListener('DOMContentLoaded', function() {
    const editModal = document.getElementById('editModal');
    const editForm = document.getElementById('editForm'); 

    editModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const docenteId = button.getAttribute('data-id'); 

      // Llenar los campos del formulario con los datos actuales
      document.getElementById('editNombre').value = button.getAttribute('data-nombre');
      document.getElementById('editDepartamento').value = button.getAttribute('data-departamento');
      document.getElementById('editFacultad').value = button.getAttribute('data-facultad');
      document.getElementById('editEmail').value = button.getAttribute('data-email'); 

      // Actualizar la acción del formulario dinámicamente
      editForm.action = `/modificar_docente/${docenteId}/`;
    });
});