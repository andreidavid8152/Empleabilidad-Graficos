import streamlit as st

def inicializar_filtros():
    if 'filtros' not in st.session_state:
        st.session_state.filtros = {
            'Nivel': "Todos",
            'Oferta Actual': "Todos",
            'Facultad': "Todas",
            'Carrera': "Todas",
            'Cohorte': "Todos",
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

def aplicar_filtros(df, incluir=None):
    """Aplica solo los filtros especificados en `incluir` (lista de strings)."""
    inicializar_filtros()
    selecciones = {}

    incluir = incluir or ['Nivel', 'Oferta Actual', 'Facultad', 'Carrera', 'Cohorte', 'Trabajo Formal']

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

    if 'Trabajo Formal' in incluir:
        formal_sel = filtro_selectbox("Trabajo Formal", sorted(df['Empleo formal'].dropna().astype(str).unique()), "Trabajo Formal", "Todos")
        df = df if formal_sel == "Todos" else df[df['Empleo formal'].astype(str) == formal_sel]
        selecciones['Trabajo Formal'] = formal_sel

    return df, selecciones
