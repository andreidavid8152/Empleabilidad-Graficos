import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Ranking de Carreras por Empleabilidad")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()

def asignar_quimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Quimestre'] = df['Mes.1'].apply(asignar_quimestre)
df = df[df['Quimestre'].notnull()]
df['Periodo'] = df['Anio.1'].astype(str) + ' ' + df['Quimestre']


# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte_multi", "Trabajo Formal"])

periodos = sorted(df_fil['Periodo'].dropna().unique())
periodo_sel = st.selectbox("Filtrar por Periodo", ["Todos"] + periodos)
df_fil = df_fil if periodo_sel == "Todos" else df_fil[df_fil['Periodo'] == periodo_sel]

# Obtener cohortes seleccionadas del filtro
cohortes_seleccionadas = selecciones.get('Cohorte_multi', [])
if isinstance(cohortes_seleccionadas, list):
    cohortes_seleccionadas = [c for c in cohortes_seleccionadas if c is not None]
else:
    cohortes_seleccionadas = []

# --------------------------
# CÁLCULO DE RANKING POR CARRERA Y COHORTE
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    if 1 < len(cohortes_seleccionadas) <= 3:
        # Asegurarnos de que ambos sean del mismo tipo (int)
        try:
            cohortes_seleccionadas = [int(c) for c in cohortes_seleccionadas]
        except Exception:
            pass  # Si ya son int
        # Filtrar el DataFrame primero
        df_fil_coh = df_fil[df_fil['AnioGraduacion.1'].isin(cohortes_seleccionadas)]
        if df_fil_coh.empty:
            st.warning("No hay datos disponibles para las cohortes seleccionadas.")
        else:
            resumen = df_fil_coh.groupby(['CarreraHomologada.1', 'AnioGraduacion.1']).agg(
                empleados=('Esta_empleado', 'sum'),
                total=('IdentificacionBanner.1', 'nunique')
            ).reset_index()
            resumen = resumen[resumen['total'] > 0]
            resumen['TasaEmpleabilidad'] = resumen['empleados'] / resumen['total']
            if resumen.empty:
                st.warning("No hay datos disponibles para las cohortes seleccionadas.")
            else:
                fig = px.bar(
                    resumen,
                    x='TasaEmpleabilidad',
                    y='CarreraHomologada.1',
                    color='AnioGraduacion.1',
                    orientation='h',
                    barmode='group',
                    title='Ranking de Carreras por Empleabilidad (Comparación de Cohortes)',
                    labels={'CarreraHomologada.1': 'Carrera', 'TasaEmpleabilidad': 'Tasa de empleo', 'AnioGraduacion.1': 'Cohorte'},
                    color_discrete_sequence=px.colors.qualitative.Set2,  # Paleta amigable
                    hover_data={
                        'CarreraHomologada.1': True,
                        'AnioGraduacion.1': True,
                        'TasaEmpleabilidad': ':.2%',
                        'empleados': True,
                        'total': True
                    },
                    text_auto=False  # No mostrar valores sobre las barras
                )
                fig.update_layout(
                    yaxis_title='Carrera',
                    xaxis_title='Tasa de empleo',
                    legend_title_text='Cohorte (Año Graduación)',
                    legend=dict(
                        orientation='h',          # leyenda horizontal
                        yanchor='bottom',
                        y=1.02,                   # justo arriba de la gráfica
                        xanchor='center',
                        x=0.5,                    # centrada horizontalmente
                        title_font_size=12,       # tamaño de fuente título
                        font=dict(size=11)        # tamaño de fuente etiquetas
                    ),
                    margin=dict(t=100, r=20),     # margen superior más grande para la leyenda
                )
                fig.update_yaxes(automargin=True)
                st.plotly_chart(fig, use_container_width=True)



    else:
        # Si solo hay una cohorte, o ninguna, mostrar ranking promedio como antes
        resumen = df_fil.groupby(['CarreraHomologada.1', 'Periodo']).agg(
            empleados=('Esta_empleado', 'sum'),
            total=('IdentificacionBanner.1', 'nunique')
        ).reset_index()
        resumen = resumen[resumen['total'] > 0]
        resumen['TasaQuimestral'] = resumen['empleados'] / resumen['total']
        ranking = resumen.groupby('CarreraHomologada.1')['TasaQuimestral'].mean().reset_index()
        ranking = ranking.sort_values('TasaQuimestral', ascending=False)
        fig = px.bar(
            ranking,
            x='CarreraHomologada.1',
            y='TasaQuimestral',
            title='Ranking de Carreras por Empleabilidad',
            labels={'CarreraHomologada.1': 'Carrera', 'TasaQuimestral': 'Tasa promedio'},
            color='TasaQuimestral'
        )
        fig.update_layout(xaxis_tickangle=-45, yaxis_title='Tasa promedio')
        
        st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra el orden de carreras según su tasa de empleabilidad promedio.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
