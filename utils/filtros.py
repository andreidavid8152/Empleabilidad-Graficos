import streamlit as st

def inicializar_filtros():
    if 'filtros' not in st.session_state:
        st.session_state.filtros = {
            'Nivel': "Todos",
            'Oferta Actual': "Todos",
            'Facultad': "Todas",
            'Carrera': "Todas",
            'Cohorte': "Todos",
            'Cohorte_multi': [],
            'Trabajo Formal': "Todos"
        }

def filtro_selectbox(label, opciones, clave, todas_label="Todos"):
    opciones_full = [todas_label] + opciones
    valor_inicial = st.session_state.filtros.get(clave, todas_label)
    if valor_inicial not in opciones_full:
        valor_inicial = todas_label
    seleccion = st.selectbox(label, opciones_full,
                             index=opciones_full.index(valor_inicial),
                             key=f"filtro_{clave}")
    st.session_state.filtros[clave] = seleccion
    return seleccion

def filtro_multiselect(label, opciones, clave, max_selecciones=3, min_selecciones=1):
    """Filtro multiselect con validaciones de máximo y mínimo de selecciones."""
    # Obtener las opciones disponibles como strings
    opciones = sorted([str(opcion) for opcion in opciones])
    
    # Limitar los años disponibles a 2022-2024
    años_disponibles = ['2022', '2023', '2024']
    opciones = [año for año in opciones if año in años_disponibles]
    
    # Si es la primera vez que se inicializa, usar los años por defecto
    if f"{clave}_multi" not in st.session_state:
        # Usar los años por defecto (2023 y 2024) si están disponibles
        años_defecto = ['2023', '2024']
        valor_inicial = [año for año in años_defecto if año in opciones]
        
        # Si no están disponibles los años por defecto, usar los últimos años disponibles
        if not valor_inicial:
            valor_inicial = opciones[-min_selecciones:] if len(opciones) >= min_selecciones else opciones
    else:
        # Obtener el valor actual de la sesión
        valor_inicial = st.session_state.filtros[f"{clave}_multi"]
        
        # Validar que las selecciones existentes siguen siendo válidas
        valor_inicial = [año for año in valor_inicial if año in opciones]
        
        # Si no quedan selecciones válidas, usar los últimos años disponibles
        if not valor_inicial:
            valor_inicial = opciones[-min_selecciones:] if len(opciones) >= min_selecciones else opciones
    
    # Validar que no se exceda el máximo de selecciones
    if len(valor_inicial) > max_selecciones:
        valor_inicial = valor_inicial[:max_selecciones]
    
    seleccion = st.multiselect(
        label,
        opciones,
        default=valor_inicial,
        key=f"filtro_{clave}_multi",
        max_selections=max_selecciones
    )
    
    # Asegurar que siempre haya al menos una selección
    if not seleccion:
        seleccion = opciones[-min_selecciones:] if len(opciones) >= min_selecciones else opciones
    
    # Guardar en la sesión
    st.session_state.filtros[f"{clave}_multi"] = seleccion
    return seleccion

def aplicar_filtros(df, incluir=None):
    """Aplica solo los filtros especificados en `incluir` (lista de strings)."""
    inicializar_filtros()
    selecciones = {}

    incluir = incluir or ['Nivel', 'Oferta Actual', 'Facultad', 'Carrera', 'Cohorte', 'Cohorte_multi', 'Trabajo Formal']

    if 'Nivel' in incluir:
        nivel_sel = filtro_selectbox("Nivel", sorted(df['regimen.1'].dropna().unique()), "Nivel", "Todos")
        df = df if nivel_sel == "Todos" else df[df['regimen.1'] == nivel_sel]
        selecciones['Nivel'] = nivel_sel

    if 'Oferta Actual' in incluir:
        oferta_sel = filtro_selectbox("Oferta Actual", sorted(df['Oferta actual'].dropna().unique()), "Oferta Actual", "Todos")
        df = df if oferta_sel == "Todos" else df[df['Oferta actual'] == oferta_sel]
        selecciones['Oferta Actual'] = oferta_sel

    if 'Facultad' in incluir:
        facultad_sel = filtro_selectbox("Facultad", sorted(df['FACULTAD'].dropna().unique()), "Facultad", "Todas")
        df = df if facultad_sel == "Todas" else df[df['FACULTAD'] == facultad_sel]
        selecciones['Facultad'] = facultad_sel

    if 'Carrera' in incluir:
        carrera_sel = filtro_selectbox("Carrera", sorted(df['CarreraHomologada.1'].dropna().unique()), "Carrera", "Todas")
        df = df if carrera_sel == "Todas" else df[df['CarreraHomologada.1'] == carrera_sel]
        selecciones['Carrera'] = carrera_sel

    if 'Cohorte' in incluir:
        cohorte_sel = filtro_selectbox("Cohorte (Año Graduación)", sorted(df['AnioGraduacion.1'].dropna().unique()), "Cohorte", "Todos")
        df = df if cohorte_sel == "Todos" else df[df['AnioGraduacion.1'] == cohorte_sel]
        selecciones['Cohorte'] = cohorte_sel

    if 'Cohorte_multi' in incluir:
        cohorte_multi_sel = filtro_multiselect(
            "Cohorte (Año Graduación) - Múltiples",
            sorted(df['AnioGraduacion.1'].dropna().unique()),
            "Cohorte_multi",
            max_selecciones=3,
            min_selecciones=1
        )
        if cohorte_multi_sel:  # Solo filtrar si hay selección
            df = df[df['AnioGraduacion.1'].astype(str).isin(cohorte_multi_sel)]
            selecciones['Cohorte_multi'] = cohorte_multi_sel

    if 'Trabajo Formal' in incluir:
        formal_sel = filtro_selectbox("Trabajo Formal", sorted(df['Empleo formal'].dropna().astype(str).unique()), "Trabajo Formal", "Todos")
        df = df if formal_sel == "Todos" else df[df['Empleo formal'].astype(str) == formal_sel]
        selecciones['Trabajo Formal'] = formal_sel

    return df, selecciones
