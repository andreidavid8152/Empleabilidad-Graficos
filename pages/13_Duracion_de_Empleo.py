import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta

from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

# ------------------------------------------------------------------
# AJUSTES ESTÉTICOS
# ------------------------------------------------------------------
aplicar_tema_plotly()
st.title("⏳ Duración de Empleos de Graduados")

# ------------------------------------------------------------------
# 1. CARGA Y PRE-PROCESAMIENTO
# ------------------------------------------------------------------
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

df_base['FECINGAFI.1'] = pd.to_datetime(df_base['FECINGAFI.1'], errors='coerce')
df_base['Empleo formal'] = (
    df_base['Empleo formal']
    .astype(str)
    .str.strip()
    .str.upper()
)
df_base = df_base.dropna(subset=['FECINGAFI.1', 'IdentificacionBanner.1', 'NOMEMP.1'])

# ------------------------------------------------------------------
# 2. CÁLCULO DE DURACIÓN EN CADA EMPLEO (incluye el último empleo)
# ------------------------------------------------------------------
df_ordenado = df_base.sort_values(
    ['IdentificacionBanner.1', 'NOMEMP.1', 'FECINGAFI.1']
)

empleos = []
for _, grupo in df_ordenado.groupby(['IdentificacionBanner.1', 'NOMEMP.1']):
    fechas = grupo['FECINGAFI.1'].tolist()
    for i in range(len(fechas) - 1):
        inicio, fin = fechas[i], fechas[i + 1]
        delta = relativedelta(fin, inicio)
        duracion_meses = delta.years * 12 + delta.months
        if duracion_meses > 0:
            fila = grupo.iloc[i].to_dict()
            fila['DuracionMeses'] = duracion_meses
            empleos.append(fila)
    
    # ✅ Incluir el último empleo con duración 0
    if len(fechas) > 0:
        fila_final = grupo.iloc[-1].to_dict()
        fila_final['DuracionMeses'] = 0
        empleos.append(fila_final)

df = pd.DataFrame(empleos)

# ------------------------------------------------------------------
# 3. APLICAR FILTROS (incluye Cohorte)
# ------------------------------------------------------------------
df_fil, selecciones = aplicar_filtros(
    df,
    incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte", "Trabajo Formal"]
)

# ------------------------------------------------------------------
# 4. INSIGHT Y VISUALIZACIÓN
# ------------------------------------------------------------------
if df_fil.empty:
    st.warning("No hay datos para esta combinación de filtros.")
else:
    # 4.1 Insight: duración más frecuente
    freq = (
        df_fil['DuracionMeses']
        .value_counts()
        .reset_index(name='Cantidad')
        .rename(columns={'index': 'DuracionMeses'})
    )
    top = freq.sort_values('Cantidad', ascending=False).iloc[0]
    dur_top = int(top['DuracionMeses'])
    dur_text = "Menos de un mes" if dur_top == 0 else f"{dur_top} mes" + ("es" if dur_top != 1 else "")

    fac = selecciones.get("Facultad")
    car = selecciones.get("Carrera")
    if car and car != "Todas":
        sujeto = f"egresados de la carrera {car}"
    elif fac and fac != "Todas":
        sujeto = f"egresados de la facultad {fac}"
    else:
        sujeto = "egresados"

    texto_mensaje = (
        f"El tiempo de permanencia más común en un mismo empleo para {sujeto} es de <strong>{dur_text}</strong>."
    )
    st.markdown(f"""
    <div style="
        background-color: #fdf0f6;
        border-left: 6px solid #d8b4e2;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    ">
        <p style="margin: 0; font-size: 1.05rem;">
            <strong>📊 Insight:</strong><br>{texto_mensaje}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 4.2 Histograma de duración con porcentaje dentro de las barras
    fig = px.histogram(
        df_fil,
        x='DuracionMeses',
        nbins=20,
        histnorm='percent',
        labels={'DuracionMeses': 'Meses'},
        title='Distribución de duración de empleos'
    )
    # Texto dentro de barra con porcentaje
    fig.update_traces(
        texttemplate='%{y:.1f}%',
        textposition='inside',
        hovertemplate=(
            "Meses desde la graduación: <b>%{x}</b><br>"
            "Porcentaje: <b>%{y:.1f}%</b><extra></extra>"
        )
    )
    fig.update_layout(
        yaxis_title='Porcentaje de empleos',
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# 5. NOTA EXPLICATIVA
# ------------------------------------------------------------------
mostrar_tarjeta_nota(
    texto_principal="""
<strong>📌 Nota:</strong><br>
Esta visualización muestra la permanencia (en meses) de los egresados en un mismo empleador.
""",
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
<strong>Relación de Dependencia:</strong> Graduados contratados formalmente por un empleador.<br>
<strong>Afiliado Voluntario:</strong> Autoafiliados al IESS (emprendedores, independientes, etc.).<br>
<strong>Desconocido:</strong> Sin información laboral registrada (sin empleo formal, inactivos, trabajando fuera del país o en sectores no reportados).
"""
)
