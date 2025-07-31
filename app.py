import streamlit as st
import sys
import os

# Configuración de la página
st.set_page_config(
    page_title="AgroPrint - Calculadora de Huella de Carbono",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar y ejecutar AgroPrint
try:
    # Asegurarse de que el archivo AgroPrint.py esté en el path
    current_dir = os.path.dirname(__file__)
    agroprint_path = os.path.join(current_dir, "AgroPrint.py")
    
    if os.path.exists(agroprint_path):
        # Ejecutar AgroPrint.py con codificación UTF-8
        with open(agroprint_path, 'r', encoding='utf-8') as f:
            exec(f.read())
    else:
        st.error("❌ Error: No se encontró el archivo AgroPrint.py")
        st.info("Por favor, asegúrese de que AgroPrint.py esté en el mismo directorio.")
        
except Exception as e:
    st.error(f"❌ Error al cargar AgroPrint: {str(e)}")
    st.info("Por favor, contacte al administrador para resolver este problema.")
