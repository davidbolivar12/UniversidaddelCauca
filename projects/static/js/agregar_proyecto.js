(function() {
    /* ----------------------------------------------------
       LÓGICA PARA DOCENTES Y REGLAS DE LA APLICACION
       ---------------------------------------------------- */
    const selectDept = document.getElementById('agg_departamento');
    const selectDirector = document.getElementById('agg_director');
    const selectCodirector = document.getElementById('agg_codirector');
    const selectModalidad = document.getElementById('agg_modalidad');
    const helpCodirector = document.getElementById('help_codirector');
    const dataScript = document.getElementById('docentes-data-agregar');

    if (!selectDept || !dataScript) return;

    let DOCENTES = [];
    try { DOCENTES = JSON.parse(dataScript.textContent); } catch (e) { console.error(e); }

    function poblarDocentes(depto) {
        selectDirector.innerHTML = '<option value="">-- Seleccione --</option>';
        selectCodirector.innerHTML = '<option value="">-- Seleccione --</option>';
        if (!depto) {
            selectDirector.disabled = true;
            return;
        }
        selectDirector.disabled = false;
        const filtrados = DOCENTES.filter(d => d.departamento === depto);
        filtrados.forEach(d => {
            selectDirector.add(new Option(d.nombre, d.id));
            selectCodirector.add(new Option(d.nombre, d.id));
        });
    }

    function gestionarCodirector() {
        const modalidad = selectModalidad.value;
        const depto = selectDept.value;
        if (modalidad === 'INVESTIGACION') {
            helpCodirector.style.display = 'block';
            selectCodirector.disabled = !depto;
        } else {
            helpCodirector.style.display = 'none';
            selectCodirector.disabled = true;
            selectCodirector.value = "";
        }
    }

    selectDept.addEventListener('change', function() { poblarDocentes(this.value); gestionarCodirector(); });
    selectModalidad.addEventListener('change', gestionarCodirector);

    
    /* ----------------------------------------------------
       BUSCADOR DE ESTUDIANTES
       ---------------------------------------------------- */
    const searchInput = document.getElementById('buscador_estudiantes');
    const resultsList = document.getElementById('lista_resultados');
    const selectedContainer = document.getElementById('contenedor_seleccionados');
    const realSelect = document.getElementById('select_real_estudiantes');
    const msgSinEstudiantes = document.getElementById('msg_sin_estudiantes');

    // Cargar todos los estudiantes en memoria desde el select oculto
    let ALL_STUDENTS = [];
    Array.from(realSelect.options).forEach(opt => {
        ALL_STUDENTS.push({
            id: opt.value,
            name: opt.dataset.nombre || opt.text,
            fullText: opt.text.toLowerCase() // Para búsqueda rápida
        });
    });

    // Función: Renderizar etiquetas de seleccionados
    function renderSelectedTags() {
        selectedContainer.innerHTML = '';
        let count = 0;
        
        Array.from(realSelect.options).forEach(opt => {
            if (opt.selected) {
                count++;
                // Crear Badge
                const badge = document.createElement('div');
                badge.className = 'badge bg-primary d-flex align-items-center p-2';
                badge.innerHTML = `
                    <span class="me-2">${opt.dataset.nombre || opt.text}</span>
                    <i class="btn-close btn-close-white" style="cursor:pointer; font-size: 0.5rem;"></i>
                `;
                // Evento borrar
                badge.querySelector('.btn-close').addEventListener('click', () => {
                    opt.selected = false;
                    renderSelectedTags();
                });
                selectedContainer.appendChild(badge);
            }
        });

        if (count === 0) selectedContainer.appendChild(msgSinEstudiantes);
    }

    // Evento: Escribir en buscador
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase().trim();
        resultsList.innerHTML = '';
        
        if (query.length < 2) {
            resultsList.style.display = 'none';
            return;
        }

        // Filtrar (excluyendo los ya seleccionados)
        const matches = ALL_STUDENTS.filter(s => {
            const isSelected = realSelect.querySelector(`option[value="${s.id}"]`).selected;
            return !isSelected && s.fullText.includes(query);
        }).slice(0, 8); // Mostrar máx 8 resultados

        if (matches.length > 0) {
            matches.forEach(s => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = s.name + ` (${s.id})`; // Nombre + Legajo
                
                item.addEventListener('click', () => {
                    // Marcar en select original
                    realSelect.querySelector(`option[value="${s.id}"]`).selected = true;
                    // Limpiar y actualizar UI
                    searchInput.value = '';
                    resultsList.style.display = 'none';
                    renderSelectedTags();
                });
                resultsList.appendChild(item);
            });
            resultsList.style.display = 'block';
        } else {
            resultsList.style.display = 'none';
        }
    });

    // Cerrar lista si click fuera
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsList.contains(e.target)) {
            resultsList.style.display = 'none';
        }
    });

    // Inicializar visualización
    renderSelectedTags();

})();