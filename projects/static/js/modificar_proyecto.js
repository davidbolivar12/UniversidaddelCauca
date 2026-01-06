(function() {
    console.log("Inicializando lógica Modificar Proyecto (Directores + Estudiantes)...");

    /* ==============================================
       LOGICA DE DOCENTES (Directores)
       ============================================== */
    const selectDept = document.getElementById('mod_departamento');
    const selectDirector = document.getElementById('mod_director');
    const selectCodirector = document.getElementById('mod_codirector');
    const selectModalidad = document.getElementById('mod_modalidad');
    const dataScript = document.getElementById('docentes-data-modificar');

    if (selectDept && dataScript) {
        let DOCENTES = [];
        try { DOCENTES = JSON.parse(dataScript.textContent); } catch (e) { console.error(e); }

        const dirInicial = selectDirector.dataset.selected;
        const codirInicial = selectCodirector.dataset.selected;

        function poblarSelects(depto) {
            selectDirector.innerHTML = '<option value="">-- Sin director --</option>';
            selectCodirector.innerHTML = '<option value="">-- Sin codirector --</option>';
            if (!depto) {
                selectDirector.disabled = true; 
                selectCodirector.disabled = true;
                return;
            }
            selectDirector.disabled = false;
            
            const filtrados = DOCENTES.filter(d => d.departamento === depto);
            filtrados.forEach(d => {
                const optD = new Option(d.nombre, d.id);
                if (String(d.id) === String(dirInicial)) optD.selected = true;
                selectDirector.add(optD);

                const optC = new Option(d.nombre, d.id);
                if (String(d.id) === String(codirInicial)) optC.selected = true;
                selectCodirector.add(optC);
            });
        }

        function gestionarCodirector() {
            const modalidad = selectModalidad.value;
            const contenedor = selectCodirector.closest('.col-md-6');
            if (modalidad === 'INVESTIGACION') {
                contenedor.style.display = 'block';
                selectCodirector.disabled = false;
            } else {
                contenedor.style.display = 'none';
                selectCodirector.disabled = true;
                selectCodirector.value = '';
            }
        }

        selectDept.addEventListener('change', function() {
            selectDirector.innerHTML = '<option value="">-- Sin director --</option>';
            selectCodirector.innerHTML = '<option value="">-- Sin codirector --</option>';
            const nuevos = DOCENTES.filter(d => d.departamento === this.value);
            nuevos.forEach(d => {
                selectDirector.add(new Option(d.nombre, d.id));
                selectCodirector.add(new Option(d.nombre, d.id));
            });
            gestionarCodirector();
        });

        selectModalidad.addEventListener('change', gestionarCodirector);
        
        // Init Directores
        poblarSelects(selectDept.value);
        gestionarCodirector();
    }


    /* ==============================================
       LOGICA DE ESTUDIANTES (Search & Tag)
       ============================================== */
    const searchInput = document.getElementById('mod_buscador_estudiantes');
    const resultsList = document.getElementById('mod_lista_resultados');
    const selectedContainer = document.getElementById('mod_contenedor_seleccionados');
    const realSelect = document.getElementById('mod_select_real_estudiantes');
    const msgSinEstudiantes = document.getElementById('mod_msg_sin_estudiantes');
    const currentStudentsScript = document.getElementById('current-students-data');

    if (searchInput && realSelect) {
        let ALL_STUDENTS = [];
        Array.from(realSelect.options).forEach(opt => {
            ALL_STUDENTS.push({
                id: opt.value,
                name: opt.dataset.nombre || opt.text,
                fullText: opt.text.toLowerCase()
            });
        });

        // 1. Marcar iniciales (Pre-selección)
        if (currentStudentsScript) {
            try {
                const currentIDs = JSON.parse(currentStudentsScript.textContent);
                currentIDs.forEach(legajo => {
                    const option = realSelect.querySelector(`option[value="${legajo}"]`);
                    if (option) option.selected = true;
                });
            } catch (e) { console.error("Error cargando estudiantes actuales:", e); }
        }

        // 2. Renderizador de Tags
        function renderSelectedTags() {
            selectedContainer.innerHTML = '';
            let count = 0;
            Array.from(realSelect.options).forEach(opt => {
                if (opt.selected) {
                    count++;
                    const badge = document.createElement('div');
                    badge.className = 'badge bg-primary d-flex align-items-center p-2';
                    badge.innerHTML = `
                        <span class="me-2">${opt.dataset.nombre || opt.text}</span>
                        <i class="btn-close btn-close-white" style="cursor:pointer; font-size: 0.5rem;"></i>
                    `;
                    badge.querySelector('.btn-close').addEventListener('click', () => {
                        opt.selected = false;
                        renderSelectedTags();
                    });
                    selectedContainer.appendChild(badge);
                }
            });
            if (count === 0) selectedContainer.appendChild(msgSinEstudiantes);
        }

        // 3. Buscador
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            resultsList.innerHTML = '';
            if (query.length < 2) {
                resultsList.style.display = 'none';
                return;
            }

            const matches = ALL_STUDENTS.filter(s => {
                const isSelected = realSelect.querySelector(`option[value="${s.id}"]`).selected;
                return !isSelected && s.fullText.includes(query);
            }).slice(0, 8);

            if (matches.length > 0) {
                matches.forEach(s => {
                    const item = document.createElement('button');
                    item.type = 'button';
                    item.className = 'list-group-item list-group-item-action';
                    item.textContent = s.name; 
                    item.addEventListener('click', () => {
                        realSelect.querySelector(`option[value="${s.id}"]`).selected = true;
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

        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !resultsList.contains(e.target)) {
                resultsList.style.display = 'none';
            }
        });

        renderSelectedTags();
    }

})();