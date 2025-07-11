from pathlib import Path
import pandas as pd
import streamlit as st

def cargar_datos_empleabilidad():
    if 'df_empleabilidad' not in st.session_state:
        # Ruta basada en el archivo app.py, que es el punto de entrada
        ruta_proyecto = Path(__file__).resolve().parent.parent  # sube dos niveles desde utils/
        ruta_archivo = ruta_proyecto / "data" / "empleabilidad.xlsx"

        if not ruta_archivo.exists():
            st.error(f"No se encontró el archivo: {ruta_archivo}")
            st.stop()

        df = pd.read_excel(ruta_archivo, sheet_name="Limpia")
        st.session_state.df_empleabilidad = df

    return st.session_state.df_empleabilidad

def cargar_datos_titulos():
    if "df_titulos" not in st.session_state:
        ruta_proyecto = Path(__file__).resolve().parent.parent
        ruta_archivo = ruta_proyecto / "data" / "empleabilidad.xlsx"

        if not ruta_archivo.exists():
            st.error(f"No se encontró el archivo: {ruta_archivo}")
            st.stop()

        df = pd.read_excel(ruta_archivo, sheet_name="Titulos")
        st.session_state.df_titulos = df

    return st.session_state.df_titulos
