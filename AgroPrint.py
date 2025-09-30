import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Factores de emisión y parámetros configurables (modificar aquí) ---

# --- Potenciales de calentamiento global (GWP) ---
# Unidades: adimensional (relación respecto a CO2)
# Fuente: IPCC AR6 (2021), 100 años
GWP = {
    "CO2": 1,      # IPCC AR6
    "CH4": 27,     # IPCC AR6, metano no fósil
    "N2O": 273     # IPCC AR6
}

# --- Factores IPCC 2006 para emisiones de N2O ---
# Unidades: kg N2O-N / kg N
# Fuente: IPCC 2006 Vol.4 Cap.11 Tabla 11.1. 2019 REFINEMENT
EF1 = 0.01   # Emisión directa de N2O-N por aplicación de N
EF4 = 0.01   # Emisión indirecta de N2O-N por volatilización
EF5 = 0.011 # Emisión indirecta de N2O-N por lixiviación/escurrimiento

# --- Fracciones por defecto (modificables) ---
# Unidades: adimensional
# Fuente: IPCC 2006 Vol.4 Cap.11 Tabla 11.1. Refinement 2019
FRAC_VOLATILIZACION_INORG = 0.11   # Fracción de N volatilizado de fertilizantes inorgánicos (IPCC)
FRAC_VOLATILIZACION_ORG = 0.21     # Fracción de N volatilizado de fertilizantes orgánicos (IPCC 2006 Vol.4 Cap.11 Tabla 11.1, nota: estiércol sólido 0.2, líquido 0.4; se usa 0.2 como valor conservador)
FRAC_LIXIVIACION = 0.24            # Fracción de N lixiviado (aplica a todo N si precipitación > 1,000 mm) (IPCC)
# Nota: El IPCC no diferencia entre inorgánico y orgánico para lixiviación, usa 0.3 para ambos si corresponde.

# --- Factores de emisión para quema de residuos agrícolas ---
# Unidades: kg gas / kg materia seca quemada
# Fuente: IPCC 2006 Vol.4 Cap.2 Tablas 2.5 y 2.6
EF_CH4_QUEMA = 2.7 / 1000   # kg CH4 / kg MS
EF_N2O_QUEMA = 0.07 / 1000  # kg N2O / kg MS
FRACCION_SECA_QUEMA = 0.8   # adimensional, típico IPCC
FRACCION_QUEMADA = 0.9      # adimensional, típico IPCC

# --- Factores sugeridos para fertilizantes orgánicos (estructura eficiente y compacta) ---
# Unidades: fraccion_seca (adimensional), N/P2O5/K2O (% peso fresco)
# Fuente: IPCC 2006 Vol.4 Cap.10, Tablas 10A.2 y 10A.3, literatura FAO y valores de uso común
FACTORES_ORGANICOS = {
    "Tierra de hoja (quillota)": {
        "fraccion_seca": 1.00,  # 100%
        "N": 0.7,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Guano de pavo": {
        "fraccion_seca": 1.00,
        "N": 4.1,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Guano de vacuno": {
        "fraccion_seca": 1.00,
        "N": 3.1,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Guano de cabra": {
        "fraccion_seca": 1.00,
        "N": 2.2,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Guano rojo": {
        "fraccion_seca": 1.00,
        "N": 6.0,
        "P2O5": 9.0,
        "K2O": 1.0,
        "fuente": "https://www.indap.gob.cl/sites/default/files/2022-02/n%C2%BA8-manual-de-produccio%CC%81n-agroecologica.pdf"
    },
    "Harina de sangre": {
        "fraccion_seca": 1.00,
        "N": 13.0,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": "https://www.indap.gob.cl/sites/default/files/2022-02/n%C2%BA8-manual-de-produccio%CC%81n-agroecologica.pdf"
    },
    "Turba de copiapó": {
        "fraccion_seca": 1.00,
        "N": 0.64,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Estiercol de vacuno sólido": {
        "fraccion_seca": 0.215,  # 21,5%
        "N": 0.565,
        "P2O5": 0.17,
        "K2O": 0.475,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Purin de vacuno": {
        "fraccion_seca": 0.075,
        "N": 0.405,
        "P2O5": 0.085,
        "K2O": 0.35,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Estiércol de cerdo sólido": {
        "fraccion_seca": 0.215,
        "N": 0.58,
        "P2O5": 0.355,
        "K2O": 0.33,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Purin de cerdo": {
        "fraccion_seca": 0.0665,
        "N": 0.535,
        "P2O5": 0.145,
        "K2O": 0.305,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Estiércol sólido de ave": {
        "fraccion_seca": 0.475,
        "N": 1.925,
        "P2O5": 1.07,
        "K2O": 1.05,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Purín de ave": {
        "fraccion_seca": 0.1175,
        "N": 0.895,
        "P2O5": 0.33,
        "K2O": 0.555,
        "fuente": "https://biblioteca.inia.cl/server/api/core/bitstreams/102077ad-5b60-46b2-8b35-c0e8250a2965/content"
    },
    "Otros": {  # Entrada genérica para evitar KeyError
        "fraccion_seca": 1.0,
        "N": 0.0,
        "P2O5": 0.0,
        "K2O": 0.0,
        "fuente": ""
    }
}

# --- Factores de emisión genéricos para nutrientes (por producción) ---
# Unidades: kg CO2e/kg nutriente
# Fuente: Ecoinvent, Agri-footprint, literatura LCA
FE_N_GEN = 3.0    # kg CO2e/kg N
FE_P2O5_GEN = 1.5 # kg CO2e/kg P2O5
FE_K2O_GEN = 1.2  # kg CO2e/kg K2O

# --- Valores por defecto y factores de emisión centralizados ---
valores_defecto = {
    "fe_electricidad": 0.2021,        # kg CO2e/kWh (SEN, promedio 2024, Chile)
    "fe_combustible_generico": 3.98648,   # kg CO2e/litro (LUBRICANTE)
    "fe_agua": 0.00015,               # kg CO2e/litro de agua de riego (DEFRA)
    "fe_maquinaria": 2.5,             # kg CO2e/litro (valor genérico maquinaria)
    "fe_transporte": 0.15,            # kg CO2e/km recorrido (valor genérico transporte)
    "fe_agroquimico": 5.0,            # kg CO2e/kg ingrediente activo (valor genérico)
    "rendimiento_motor": 0.25,        # litros/kWh (valor genérico motor diésel/gasolina)
}

# --- Factores de fertilizantes inorgánicos (puedes modificar aquí) ---
# N_porcentaje: fracción de N en el fertilizante (adimensional)
# Frac_volatilizacion: fracción de N volatilizado (adimensional)
# Frac_lixiviacion: fracción de N lixiviado (adimensional)
# FE_produccion_producto: kg CO2e / kg producto (LCA, Ecoinvent/Agri-footprint)
# FE_produccion_N: kg CO2e / kg N (LCA, Ecoinvent/Agri-footprint)
# Fuente de volatilización/lixiviación: IPCC 2006 Vol.4 Cap.11 Tabla 11.1 y literatura LCA para producción
factores_fertilizantes = {
    "Nitrato de amonio (AN)": [
        {"origen": "Unión Europea", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.112, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Norte América", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.249, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Latino América", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.124, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "China, carbón", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 3.643, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference_values.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.850, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China, gas", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.836, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.335, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.469, "Fuente": ""}
    ],
    "Nitrato de amonio cálcico (CAN)": [
        {"origen": "Unión Europea", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.951, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Norte América", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.870, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Latino América", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.779, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "China, carbón", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 3.023, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.350, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China, gas", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.358, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.27, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.055, "Fuente": ""}
    ],
    "Urea": [
        {"origen": "Unión Europea", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.611, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Norte América", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.739, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Latino América", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.746, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "China, carbón", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 3.002, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.180, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China, gas", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.905, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.46, "Frac_volatilizacion": 0.15, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.864, "Fuente": ""}
    ],
    "Nitrato de Amonio y Urea (UAN)": [
        {"origen": "Unión Europea", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.021, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Norte América", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.571, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Latino América", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.526, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "China, carbón", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.615, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.650, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China, gas", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.896, "Fuente": "https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.30, "Frac_volatilizacion": 0.10, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.713, "Fuente": ""}
    ],
    "Nitrosulfato de amonio (ANS)": [
        {"origen": "Europa", "N_porcentaje": 0.26, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.820, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.26, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.580, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0.26, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.440, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0.26, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.220, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.26, "Frac_volatilizacion": 0.05, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.515, "Fuente": ""}
    ],
    "Nitrato de calcio (CN)": [
        {"origen": "Europa", "N_porcentaje": 0.155, "Frac_volatilizacion": 0.01, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.670, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.155, "Frac_volatilizacion": 0.01, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.030, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0.155, "Frac_volatilizacion": 0.01, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.760, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0.155, "Frac_volatilizacion": 0.01, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 2.200, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.155, "Frac_volatilizacion": 0.01, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.665, "Fuente": ""}
    ],
    "Sulfato de amonio (AS)": [
        {"origen": "Europa", "N_porcentaje": 0.21, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.570, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.21, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.710, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0.21, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.690, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0.21, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.360, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.21, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.833, "Fuente": ""}
    ],
    "Fosfato monoamónico (MAP)": [
        {"origen": "Chile", "N_porcentaje": 0.10, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.380, "Fuente": "https://www.climatiq.io/data/emission-factor/941370dd-318b-46ad-941b-80b9c861cf69"}
    ],
    "Fosfato diamonico (DAP)": [
        {"origen": "Europa", "N_porcentaje": 0.18, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.640, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.18, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.810, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0.18, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.730, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0.18, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.330, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.18, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.878, "Fuente": ""}
    ],
    "Superfosfato triple (TSP)": [
        {"origen": "Europa", "N_porcentaje": 0, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.18, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.25, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.19, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.26, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0, "Frac_volatilizacion": 0.08, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.22, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"}
    ],
    "Cloruro de Potasio (MOP)": [
        {"origen": "Europa", "N_porcentaje": 0, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.23, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.23, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.23, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.23, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.23, "Año": 2011, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"}
    ],
    "Ácido bórico": [
        {"origen": "Promedio", "N_porcentaje": 0.00, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 5.52, "Fuente": "https://www.researchgate.net/publication/351106329_Life_cycle_assessment_on_boron_production_is_boric_acid_extraction_from_salt-lake_brine_environmentally_friendly"}
    ],
    "NPK": [
        {"origen": "Europa", "N_porcentaje": 0.15, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0.730, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Rusia", "N_porcentaje": 0.15, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.400, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Estados Unidos", "N_porcentaje": 0.15, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.270, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "China", "N_porcentaje": 0.15, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.730, "Fuente": "https://www.researchgate.net/profile/Frank-Brentrup-2/publication/312553933_Carbon_footprint_analysis_of_mineral_fertilizer_production_in_Europe_and_other_world_regions/links/5881ec8d4585150dde4012fe/Carbon-footprint-analysis-of-mineral-fertilizer-production-in-Europe-and-other-world-regions.pdf"},
        {"origen": "Promedio", "N_porcentaje": 0.15, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 1.283, "Fuente": ""}
    ],
    "Otros": [
        {"origen": "Otros", "N_porcentaje": 0.15, "Frac_volatilizacion": 0.11, "Frac_lixiviacion": 0.24, "FE_produccion_producto": 0, "Fuente": ""}
    ]
}

# --- Factores de emisión organizados por categoría (actualizado con datos detallados y fuentes) ---
factores_emision = {
    'pesticidas': {
        'Media': 5.1,  # kg CO2e / kg i.a. (https://doi.org/10.1016/j.envint.2004.03.005)
    },
    'fungicidas': {
        'Media': 3.9,  # kg CO2e / kg i.a. (https://doi.org/10.1016/j.envint.2004.03.005)
        'Ferbam': 1.2,  # https://doi.org/10.1016/j.envint.2004.03.028
        'Maneb': 2.0,   # https://doi.org/10.1016/j.envint.2004.03.029
        'Capitan': 2.3, # https://doi.org/10.1016/j.envint.2004.03.030
        'Benomilo': 8.0 # https://doi.org/10.1016/j.envint.2004.03.031
    },
    'insecticidas': {
        'Media': 5.1,  # kg CO2e / kg i.a. (https://doi.org/10.1016/j.envint.2004.03.005)
        'Metil paratión': 3.2,   # https://doi.org/10.1016/j.envint.2004.03.032
        'Forato': 4.2,           # https://doi.org/10.1016/j.envint.2004.03.033
        'Carbofurano': 9.1,      # https://doi.org/10.1016/j.envint.2004.03.034
        'Carbaril': 3.1,         # https://doi.org/10.1016/j.envint.2004.03.035
        'Taxafeno': 1.2,         # https://doi.org/10.1016/j.envint.2004.03.036
        'Cipermetrina': 11.7,    # https://doi.org/10.1016/j.envint.2004.03.037
        'Clorodimeformo': 5.0,   # https://doi.org/10.1016/j.envint.2004.03.038
        'lindano': 1.2,          # https://doi.org/10.1016/j.envint.2004.03.039
        'Malatión': 4.6,         # https://doi.org/10.1016/j.envint.2004.03.040
        'Partión': 2.8,          # https://doi.org/10.1016/j.envint.2004.03.041
        'Metoxicloro': 1.4       # https://doi.org/10.1016/j.envint.2004.03.042
    },
    'herbicidas': {
        'Media': 6.3,        # https://doi.org/10.1016/j.envint.2004.03.005
        '2, 4-D': 1.7,       # https://doi.org/10.1016/j.envint.2004.03.005
        '2, 4, 5-T': 2.7,    # https://doi.org/10.1016/j.envint.2004.03.006
        'Alacloro': 5.6,     # https://doi.org/10.1016/j.envint.2004.03.007
        'Atrazina': 3.8,     # https://doi.org/10.1016/j.envint.2004.03.008
        'Bentazón': 8.7,     # https://doi.org/10.1016/j.envint.2004.03.009
        'Butilato': 2.8,     # https://doi.org/10.1016/j.envint.2004.03.010
        'Cloramben': 3.4,    # https://doi.org/10.1016/j.envint.2004.03.011
        'Clorsulfurón': 7.3, # https://doi.org/10.1016/j.envint.2004.03.012
        'Cianazina': 4.0,    # https://doi.org/10.1016/j.envint.2004.03.013
        'Dicamba': 5.9,      # https://doi.org/10.1016/j.envint.2004.03.014
        'Dinosaurio': 1.6,   # https://doi.org/10.1016/j.envint.2004.03.015
        'Diquat': 8.0,       # https://doi.org/10.1016/j.envint.2004.03.016
        'Diurón': 5.4,       # https://doi.org/10.1016/j.envint.2004.03.017
        'EPTC': 3.2,         # https://doi.org/10.1016/j.envint.2004.03.018
        'Fluazifop-butilo': 10.4, # https://doi.org/10.1016/j.envint.2004.03.019
        'Fluometurón': 7.1,  # https://doi.org/10.1016/j.envint.2004.03.020
        'Glifosato': 9.1,    # https://doi.org/10.1016/j.envint.2004.03.021
        'Linuron': 5.8,      # https://doi.org/10.1016/j.envint.2004.03.022
        'MCPA': 2.6,         # https://doi.org/10.1016/j.envint.2004.03.023
        'Metolaclor': 5.5,   # https://doi.org/10.1016/j.envint.2004.03.024
        'Paraquat': 9.2,     # https://doi.org/10.1016/j.envint.2004.03.025
        'Propaclor': 5.8,    # https://doi.org/10.1016/j.envint.2004.03.026
        'Trifluralina': 3.0  # https://doi.org/10.1016/j.envint.2004.03.027
    },
    'agua': valores_defecto["fe_agua"],                # kg CO2e / litro de agua de riego (LCA)
    'maquinaria': valores_defecto["fe_maquinaria"],    # kg CO2e / litro de combustible (valor genérico, no se usa si tienes factores_combustible)
    'materiales': {
        'PET': 2.1,                # kg CO2e / kg material (LCA)
        'HDPE': 1.9,               # kg CO2e / kg material (LCA)
        'Cartón': 0.7,             # kg CO2e / kg material (LCA)
        'Vidrio': 1.2,             # kg CO2e / kg material (LCA)
        'Otro': 1.0                # kg CO2e / kg material (LCA)
    },
    'transporte': valores_defecto["fe_transporte"]     # kg CO2e / km recorrido (valor genérico, puede variar según tipo de transporte)
}

# --- Factores de emisión para gestión de residuos vegetales (IPCC 2006 Vol.4, Cap.4, Tablas 4.1 y 4.2) ---
factores_residuos = {
    "fraccion_seca": 0.8,  # Fracción seca de biomasa (adimensional, típico 0.8, IPCC)
    "compostaje": {
        "aerobico": {
            "EF_CH4": 0.004,    # kg CH4 / kg materia seca compostada (IPCC 2006 Vol.4 Cap.4 Tabla 4.1)
            "EF_N2O": 0.0003    # kg N2O / kg materia seca compostada (IPCC 2006 Vol.4 Cap.4 Tabla 4.1)
        },
        "anaerobico": {
            "EF_CH4": 0.01,     # kg CH4 / kg materia seca compostada (IPCC 2006 Vol.4 Cap.4 Tabla 4.1)
            "EF_N2O": 0.0006    # kg N2O / kg materia seca compostada (IPCC 2006 Vol.4 Cap.4 Tabla 4.1)
        }
    },
    "incorporacion": {
        "fraccion_C": 0.45,        # Fracción de C en biomasa seca (adimensional, IPCC 2006 Vol.4 Cap.2)
        "fraccion_estabilizada": 0.1  # Fracción de C estabilizada en suelo (adimensional, solo opción avanzada, IPCC)
    }
}

# --- Factores de emisión de combustibles ---
factores_combustible = {
    "Diesel (mezcla promedio biocombustibles)": 2.51279,        # kg CO2e / litro (DEFRA)
    "Diesel (100% mineral)": 2.66155,                           # kg CO2e / litro (DEFRA)
    "Gasolina (mezcla media de biocombustibles)": 2.0844,       # kg CO2e / litro (DEFRA)
    "Gasolina (100% gasolina mineral)": 2.66155,                # kg CO2e / litro (DEFRA)
    "Gas Natural Comprimido": 0.44942,                          # kg CO2e / litro (DEFRA)
    "Gas Natural Licuado": 1.17216,                             # kg CO2e / litro (DEFRA)
    "Gas Licuado de petróleo": 1.55713,                         # kg CO2e / litro (DEFRA)
    "Aceite combustible": 3.17493,                              # kg CO2e / litro (DEFRA)
    "Gasóleo": 2.75541,                                         # kg CO2e / litro (DEFRA) (original:)
    "Lubricante": 2.74934,                                      # kg CO2e / litro (DEFRA) (original:)
    "Nafta": 2.11894,                                           # kg CO2e / litro (DEFRA)
    "Butano": 1.74532,                                          # kg CO2e / litro (DEFRA)
    "Otros gases de petróleo": 0.94441,                         # kg CO2e / litro (DEFRA)
    "Propano": 1.54357,                                         # kg CO2e / litro (DEFRA)
    "Aceite quemado": 2.54015,                                  # kg CO2e / litro (DEFRA)
    "Eléctrico": valores_defecto["fe_electricidad"],            # kg CO2e / kWh (valor genérico)
    "Otro": valores_defecto["fe_combustible_generico"]
}

# --- Rendimientos de maquinaria (litros/hora) ---
rendimientos_maquinaria = {
    "Tractor": 10,         # litros de combustible / hora de uso (valor típico)
    "Cosechadora": 15,     # litros de combustible / hora de uso (valor típico)
    "Camión": 25,          # litros de combustible / hora de uso (valor típico)
    "Pulverizadora": 8,    # litros de combustible / hora de uso (valor típico)
    "Otro": 10             # litros de combustible / hora de uso (valor genérico)
}

# --- Opciones de labores ---
opciones_labores = [
    "Siembra", "Cosecha", "Fertilización", "Aplicación de agroquímicos",
    "Riego", "Poda", "Transporte interno", "Otro"
]

# --- FIN DE BLOQUE DE FACTORES Y UNIDADES ---

# --- GENERADOR DE CLAVES ÚNICAS PARA GRÁFICOS ---
if 'plot_counter' not in st.session_state:
    st.session_state.plot_counter = 0

def get_unique_key():
    st.session_state.plot_counter += 1
    return f"plot_{st.session_state.plot_counter}"

# --- DATOS DE ENTRADA ---
st.set_page_config(layout="wide")
st.title("AgroPrint Calculadora de huella de carbono para productos frutícolas")

st.markdown("""
<div style="border: 2px solid #1976d2; border-radius: 8px; padding: 1.2em; background-color: #f0f7ff;">
<span style="font-size:1.3em; font-weight:bold; text-decoration:underline;">
Bienvenido/a a AgroPrint, la calculadora de huella de carbono para productos frutícolas
</span>
<br><br>
Esta herramienta permite estimar la huella de carbono de sistemas productivos frutícolas bajo el enfoque "cradle-to-farm gate" (de la cuna a la puerta de la granja), siguiendo metodologías reconocidas como PAS 2050 y los lineamientos del IPCC 2006 (y actualización de 2019) para el sector AFOLU.

Seleccione si su cultivo es <b>anual</b> o <b>perenne</b>. Según su elección, la calculadora le guiará a través de distintas etapas y pestañas:

<ul>
<li><b>Cultivo anual:</b>
  <ul>
    <li>Ingrese la información de insumos y actividades para cada ciclo productivo del año agrícola.</li>
    <li>Visualice los resultados globales y desglosados por ciclo y fuente de emisión en la pestaña "Resultados".</li>
  </ul>
</li>
<li><b>Cultivo perenne:</b>
  <ul>
    <li>Complete la información para cada etapa: "Implantación", "Crecimiento sin producción" y "Producción".</li>
    <li>En la pestaña "Resultados" podrá analizar los resultados globales, por etapa y por fuente de emisión.</li>
  </ul>
</li>
</ul>

En cada etapa o ciclo, se le solicitarán datos sobre riego, uso de maquinaria, fertilizantes, agroquímicos, gestión de residuos, materiales y transporte (opcional).<br>
Al finalizar, obtendrá un reporte detallado y visual de la huella de carbono de su sistema productivo.
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Inicialización de estructuras para guardar resultados
# -----------------------------
# Guardar resultados parciales para tablas y gráficos
emisiones_etapas = {}         # Emisiones totales por etapa (kg CO2e/ha)
produccion_etapas = {}        # Producción total por etapa (kg/ha)
emisiones_fuentes = {         # Emisiones acumuladas por fuente (kg CO2e/ha)
    "Fertilizantes": 0,
    "Agroquímicos": 0,
    "Riego": 0,
    "Maquinaria": 0,
    "Transporte": 0,
    "Residuos": 0,
    "Fin de vida": 0
}

# -----------------------------
# Sección 1: Caracterización General
# -----------------------------
st.header("1. Caracterización General")
cultivo = st.text_input("Nombre del cultivo o fruta")
anual = st.radio("¿Es un cultivo anual o perenne?", ["Anual", "Perenne"])

# --- Inicialización de resultados según modo anual/perenne ---
if 'modo_anterior' not in st.session_state or st.session_state['modo_anterior'] != anual:
    emisiones_etapas.clear()
    produccion_etapas.clear()
    for k in emisiones_fuentes:
        emisiones_fuentes[k] = 0
    st.session_state["emisiones_anuales"] = []
    st.session_state["emisiones_ciclos"] = []
    st.session_state['modo_anterior'] = anual
    st.session_state['emisiones_fuente_etapa'] = {}

emisiones_fuente_etapa = st.session_state['emisiones_fuente_etapa']
morfologia = st.selectbox("Morfología", ["Árbol", "Arbusto", "Hierba", "Otro"])
ubicacion = st.text_input("Ubicación geográfica del cultivo (región, país)")
tipo_suelo = st.selectbox("Tipo de suelo", [
    "Franco", "Arenoso", "Arcilloso", "Franco-arenoso", "Franco-arcilloso", "Otro"
])
clima = st.selectbox("Zona agroclimática o clima predominante", [
    "Mediterráneo", "Tropical", "Templado", "Desértico", "Húmedo", "Otro"
])
extra = st.text_area("Información complementaria (opcional)")

# -----------------------------
# Inicialización de estructuras para guardar resultados
# -----------------------------
# Guardar resultados parciales para tablas y gráficos
emisiones_etapas = {}         # Emisiones totales por etapa (kg CO2e/ha)
produccion_etapas = {}        # Producción total por etapa (kg/ha)
emisiones_fuentes = {         # Emisiones acumuladas por fuente (kg CO2e/ha)
    "Fertilizantes": 0,
    "Agroquímicos": 0,
    "Riego": 0,
    "Maquinaria": 0,
    "Transporte": 0,
    "Residuos": 0,
    "Fin de vida": 0
}

# -----------------------------
# Funciones de ingreso y cálculo
# -----------------------------
def ingresar_fertilizantes(etapa, unidad_cantidad="ciclo"):
    st.markdown("##### Fertilizantes")
    tipos_inorg = list(factores_fertilizantes.keys())
    tipos_org = list(FACTORES_ORGANICOS.keys())

    sufijo = "ciclo" if unidad_cantidad == "ciclo" else "año"

    n_fert = st.number_input(
        f"¿Cuántos fertilizantes desea agregar? (orgánicos o inorgánicos)",
        min_value=0, step=1, format="%.6g", key=f"num_fert_total_{etapa}"
    )
    fertilizantes = []

    for i in range(int(n_fert)):
        with st.expander(f"Fertilizante #{i+1}"):
            modo = st.radio(
                "¿Cómo desea ingresar este fertilizante?",
                ["Inorgánico (sintético)", "Orgánico (estiércol, compost, guano, etc.)"],
                key=f"modo_fert_{etapa}_{i}"
            )
            if modo == "Inorgánico (sintético)":
                tipo = st.selectbox("Tipo de fertilizante inorgánico", tipos_inorg, key=f"tipo_inorg_{etapa}_{i}")
                if tipo == "Otros":
                    nombre_otro = st.text_input(
                        "Ingrese un nombre representativo para este fertilizante 'Otro' (ej: Nitrato especial, Compost local, etc.)",
                        key=f"nombre_otro_{etapa}_{i}"
                    )
                    modo_otros = st.radio(
                        "¿Cómo desea ingresar el fertilizante 'Otro'?",
                        ["porcentaje", "nutriente"],
                        key=f"modo_otros_{etapa}_{i}"
                    )
                    if modo_otros == "porcentaje":
                        cantidad = st.number_input(f"Cantidad aplicada (kg/ha·{sufijo})", min_value=0.0, format="%.10g", key=f"cant_otros_{etapa}_{i}")
                        n = st.number_input("Contenido de N (%)", min_value=0.0, max_value=100.0, format="%.10g", key=f"N_otros_{etapa}_{i}")
                        p = st.number_input("Contenido de P₂O₅ (%)", min_value=0.0, max_value=100.0, format="%.10g", key=f"P_otros_{etapa}_{i}")
                        k = st.number_input("Contenido de K₂O (%)", min_value=0.0, max_value=100.0, format="%.10g", key=f"K_otros_{etapa}_{i}")
                        usar_fe_personalizado = st.checkbox("¿Desea ingresar un factor de emisión personalizado para la producción de este fertilizante?", key=f"usar_fe_otros_{etapa}_{i}")
                        if usar_fe_personalizado:
                            fe_personalizado = st.number_input("Factor de emisión personalizado (kg CO₂e/kg producto)", min_value=0.0, step=0.000001, format="%.6g", key=f"fe_personalizado_otros_{etapa}_{i}")
                        else:
                            fe_personalizado = None
                        fertilizantes.append({
                            "tipo": nombre_otro if nombre_otro else "Otros",
                            "cantidad": cantidad,
                            "N": n,
                            "P": p,
                            "K": k,
                            "modo_otros": "porcentaje",
                            "es_organico": False,
                            "fe_personalizado": fe_personalizado
                        })
                    else:  # modo_otros == "nutriente"
                        nutriente = st.selectbox("Nutriente aplicado", ["N", "P", "K"], key=f"nutriente_otros_{etapa}_{i}")
                        cantidad = st.number_input(f"Cantidad de {nutriente} aplicada (kg {nutriente}/ha·{sufijo})", min_value=0.0, format="%.6g", key=f"cant_nutriente_otros_{etapa}_{i}")
                        usar_fe_personalizado = st.checkbox("¿Desea ingresar un factor de emisión personalizado para la producción de este fertilizante?", key=f"usar_fe_otros_nutriente_{etapa}_{i}")
                        if usar_fe_personalizado:
                            fe_personalizado = st.number_input("Factor de emisión personalizado (kg CO₂e/kg producto)", min_value=0.0, step=0.000001, format="%.6g", key=f"fe_personalizado_otros_nutriente_{etapa}_{i}")
                        else:
                            fe_personalizado = None
                        fertilizantes.append({
                            "tipo": nombre_otro if nombre_otro else "Otros",
                            "cantidad": cantidad,
                            "nutriente": nutriente,
                            "modo_otros": "nutriente",
                            "es_organico": False,
                            "fe_personalizado": fe_personalizado
                        })
                else:
                    variantes = factores_fertilizantes[tipo]
                    origenes = [v["origen"] for v in variantes]
                    origen = st.selectbox("Origen del fertilizante", origenes, key=f"origen_inorg_{etapa}_{i}")
                    variante = next((v for v in variantes if v["origen"] == origen), variantes[0])
                    cantidad = st.number_input(f"Cantidad aplicada (kg/ha·{sufijo})", min_value=0.0, format="%.6g", key=f"cant_inorg_{etapa}_{i}")
                    # CORRECCIÓN: fuerza el tipo de value a float para evitar errores de Streamlit
                    n = st.number_input(
                        "Contenido de N (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(variante["N_porcentaje"])*100,
                        format="%.10g",
                        key=f"N_inorg_{etapa}_{i}"
                    )
                    usar_fe_personalizado = st.checkbox("¿Desea ingresar un factor de emisión personalizado para la producción de este fertilizante?", key=f"usar_fe_inorg_{etapa}_{i}")
                    if usar_fe_personalizado:
                        fe_personalizado = st.number_input("Factor de emisión personalizado (kg CO₂e/kg producto)", min_value=0.0, step=0.000001, format="%.6g", key=f"fe_personalizado_inorg_{etapa}_{i}")
                    else:
                        fe_personalizado = None
                    fertilizantes.append({
                        "tipo": tipo,
                        "origen": origen,
                        "cantidad": cantidad,
                        "N": n,
                        "es_organico": False,
                        "fe_personalizado": fe_personalizado
                    })
            else:
                tipo = st.selectbox("Tipo de fertilizante orgánico", tipos_org, key=f"tipo_org_{etapa}_{i}")
                valores = FACTORES_ORGANICOS[tipo]
                if tipo == "Otros":
                    nombre_otro_org = st.text_input(
                        "Ingrese un nombre representativo para este fertilizante orgánico 'Otro' (ej: Compost especial, Guano local, etc.)",
                        key=f"nombre_otro_org_{etapa}_{i}"
                    )
                else:
                    nombre_otro_org = None
                st.warning(
                    f"Valores sugeridos para '{tipo}': "
                    f"N = {valores['N']}%, "
                    f"P₂O₅ = {valores['P2O5']}%, "
                    f"K₂O = {valores['K2O']}%, "
                    f"Fracción seca = {valores['fraccion_seca']*100:.1f}%"
                )
                cantidad = st.number_input(f"Cantidad aplicada (kg/ha·{sufijo}, base húmeda)", min_value=0.0, format="%.6g", key=f"cant_org_{etapa}_{i}")
                n = st.number_input("Contenido de N (%)", min_value=0.0, max_value=100.0, value=float(valores['N']), format="%.6g", key=f"N_org_{etapa}_{i}")
                p = st.number_input("Contenido de P₂O₅ (%)", min_value=0.0, max_value=100.0, value=float(valores['P2O5']), format="%.6g", key=f"P_org_{etapa}_{i}")
                k = st.number_input("Contenido de K₂O (%)", min_value=0.0, max_value=100.0, value=float(valores['K2O']), format="%.6g", key=f"K_org_{etapa}_{i}")
                fraccion_seca_pct = st.number_input("Fracción seca del fertilizante (%)", min_value=0.0, max_value=100.0, value=float(valores['fraccion_seca'])*100, format="%.6g", key=f"fraccion_seca_org_{etapa}_{i}")
                st.info("Para el cálculo de huella de carbono, el contenido de N es el principal responsable de las emisiones de N₂O. Si no dispone de los otros nutrientes, puede dejarlos en cero.")
                fertilizantes.append({
                    "tipo": nombre_otro_org if (tipo == "Otros" and nombre_otro_org) else tipo,
                    "cantidad": cantidad,
                    "N": n,
                    "P": p,
                    "K": k,
                    "fraccion_seca": fraccion_seca_pct / 100,  # Convierte a fracción
                    "es_organico": True
                })

    return {"fertilizantes": fertilizantes}

def calcular_emisiones_n2o_fertilizantes_desglosado(fertilizantes, duracion):
    total_n_aplicado = 0
    total_n_volatilizado = 0
    total_n_lixiviado = 0

    for fert in fertilizantes:
        if fert.get("es_organico", False):
            cantidad = fert.get("cantidad", 0)  # kg/ha
            tipo = fert.get("tipo", "Otros")
            valores = FACTORES_ORGANICOS.get(tipo, FACTORES_ORGANICOS["Otros"])
            fraccion_seca = fert.get("fraccion_seca", valores["fraccion_seca"])
            n = fert.get("N", valores["N"]) / 100  # %
            n_aplicado = cantidad * fraccion_seca * n
            frac_vol = FRAC_VOLATILIZACION_ORG
            frac_lix = FRAC_LIXIVIACION
        elif fert["tipo"] == "Otros":
            if fert.get("modo_otros") == "porcentaje":
                cantidad = fert.get("cantidad", 0)
                n = fert.get("N", 0) / 100
                n_aplicado = cantidad * n
                frac_vol = FRAC_VOLATILIZACION_INORG
                frac_lix = FRAC_LIXIVIACION
            elif fert.get("modo_otros") == "nutriente":
                nutriente = fert.get("nutriente")
                cantidad = fert.get("cantidad", 0)
                n_aplicado = cantidad if nutriente == "N" else 0
                frac_vol = FRAC_VOLATILIZACION_INORG
                frac_lix = FRAC_LIXIVIACION
            else:
                n_aplicado = 0
                frac_vol = 0
                frac_lix = 0
        else:
            tipo = fert["tipo"]
            origen = fert.get("origen", None)
            variantes = factores_fertilizantes.get(tipo, [])
            if isinstance(variantes, list):
                variante = next((v for v in variantes if v["origen"] == origen), variantes[0] if variantes else None)
            else:
                variante = None
            if variante:
                cantidad = fert.get("cantidad", 0)
                n_porcentaje = variante.get("N_porcentaje", 0)
                n_aplicado = cantidad * n_porcentaje
                frac_vol = variante.get("Frac_volatilizacion", FRAC_VOLATILIZACION_INORG)
                frac_lix = variante.get("Frac_lixiviacion", FRAC_LIXIVIACION)
            else:
                n_aplicado = 0
                frac_vol = FRAC_VOLATILIZACION_INORG
                frac_lix = FRAC_LIXIVIACION

        n_volatilizado = n_aplicado * frac_vol
        n_lixiviado = n_aplicado * frac_lix

        total_n_aplicado += n_aplicado * duracion
        total_n_volatilizado += n_volatilizado * duracion
        total_n_lixiviado += n_lixiviado * duracion

    n2o_n_directo = total_n_aplicado * EF1
    n2o_n_ind_vol = total_n_volatilizado * EF4
    n2o_n_ind_lix = total_n_lixiviado * EF5

    n2o_n_indirecto = n2o_n_ind_vol + n2o_n_ind_lix

    n2o_directo = n2o_n_directo * (44/28)
    n2o_indirecto = n2o_n_indirecto * (44/28)
    n2o_total = n2o_directo + n2o_indirecto

    n2o_directo_co2e = n2o_directo * GWP["N2O"]
    n2o_indirecto_co2e = n2o_indirecto * GWP["N2O"]
    emision_n2o_co2e_total = n2o_total * GWP["N2O"]

    return emision_n2o_co2e_total, total_n_aplicado, n2o_directo_co2e, n2o_indirecto_co2e

def calcular_emisiones_fertilizantes(fert_data, duracion):
    fertilizantes = fert_data.get("fertilizantes", [])

    emision_produccion = 0
    n_aplicado_inorg = 0
    n_aplicado_org = 0
    volatilizacion_inorg = 0
    lixiviacion_inorg = 0
    volatilizacion_org = 0
    lixiviacion_org = 0

    desglose = []

    for fert in fertilizantes:
        em_prod = 0
        em_n2o_dir = 0
        em_n2o_ind = 0
        em_n2o_ind_vol = 0
        em_n2o_ind_lix = 0

        tipo_fertilizante = "Orgánico" if fert.get("es_organico", False) else "Inorgánico"

        # --- Cálculo de N aplicado y fracciones ---
        n_aplicado = 0
        frac_vol = 0
        frac_lix = 0

        if fert.get("es_organico", False):
            cantidad = fert.get("cantidad", 0)
            tipo = fert.get("tipo", "Otros")
            valores = FACTORES_ORGANICOS.get(tipo, FACTORES_ORGANICOS["Otros"])
            fraccion_seca = fert.get("fraccion_seca", valores["fraccion_seca"])
            n = fert.get("N", valores["N"]) / 100
            n_aplicado = cantidad * fraccion_seca * n
            n_aplicado_org += n_aplicado
            frac_vol = FRAC_VOLATILIZACION_ORG
            frac_lix = FRAC_LIXIVIACION
            volatilizacion_org += n_aplicado * frac_vol
            lixiviacion_org += n_aplicado * frac_lix

        elif fert.get("tipo", "") == "Otros" or fert.get("modo_otros") in ["porcentaje", "nutriente"]:
            nombre_otro = fert.get("tipo", "Otros")
            if fert.get("modo_otros") == "porcentaje":
                cantidad = fert.get("cantidad", 0)
                n = fert.get("N", 0) / 100
                n_aplicado = cantidad * n
            elif fert.get("modo_otros") == "nutriente":
                nutriente = fert.get("nutriente", "").strip().upper()
                cantidad = fert.get("cantidad", 0)
                n_aplicado = cantidad if nutriente == "N" else 0
            else:
                n_aplicado = 0

            if n_aplicado > 0:
                n_aplicado_inorg += n_aplicado
                frac_vol = FRAC_VOLATILIZACION_INORG
                frac_lix = FRAC_LIXIVIACION
                volatilizacion_inorg += n_aplicado * frac_vol
                lixiviacion_inorg += n_aplicado * frac_lix
            else:
                frac_vol = 0
                frac_lix = 0

            # FE personalizado para "Otros"
            fe = fert.get("fe_personalizado", None)
            if fe is not None and fe > 0:
                em_prod = cantidad * fe * duracion
            else:
                em_prod = 0

        else:
            tipo = fert.get("tipo", "")
            origen = fert.get("origen", None)
            variantes = factores_fertilizantes.get(tipo, [])
            if isinstance(variantes, list):
                variante = next((v for v in variantes if v["origen"] == origen), variantes[0] if variantes else None)
            else:
                variante = None
            if variante:
                cantidad = fert.get("cantidad", 0)
                n_porcentaje = variante.get("N_porcentaje", 0)
                n_aplicado = cantidad * n_porcentaje
                n_aplicado_inorg += n_aplicado
                frac_vol = variante.get("Frac_volatilizacion", FRAC_VOLATILIZACION_INORG)
                frac_lix = variante.get("Frac_lixiviacion", FRAC_LIXIVIACION)
                volatilizacion_inorg += n_aplicado * frac_vol
                lixiviacion_inorg += n_aplicado * frac_lix
                # FE personalizado
                fe = fert.get("fe_personalizado", None)
                if fe is not None and fe > 0:
                    em_prod = cantidad * fe * duracion
                else:
                    fe_default = variante.get("FE_produccion_producto", 0)
                    em_prod = cantidad * fe_default * duracion if fe_default else 0
            else:
                cantidad = 0
                n_aplicado = 0
                frac_vol = FRAC_VOLATILIZACION_INORG
                frac_lix = FRAC_LIXIVIACION

        # --- Emisiones N2O directas e indirectas por fertilizante individual ---
        n_volatilizado = n_aplicado * frac_vol
        n_lixiviado = n_aplicado * frac_lix

        n2o_n_directo = n_aplicado * EF1
        n2o_n_ind_vol = n_volatilizado * EF4
        n2o_n_ind_lix = n_lixiviado * EF5
        n2o_n_indirecto = n2o_n_ind_vol + n2o_n_ind_lix
        n2o_directo = n2o_n_directo * (44/28)
        n2o_ind_vol = n2o_n_ind_vol * (44/28)
        n2o_ind_lix = n2o_n_ind_lix * (44/28)
        n2o_indirecto = n2o_ind_vol + n2o_ind_lix
        em_n2o_dir = n2o_directo * GWP["N2O"]
        em_n2o_ind_vol = n2o_ind_vol * GWP["N2O"]
        em_n2o_ind_lix = n2o_ind_lix * GWP["N2O"]
        em_n2o_ind = em_n2o_ind_vol + em_n2o_ind_lix

        desglose.append({
            "Tipo fertilizante": tipo_fertilizante,
            "tipo": fert.get("tipo", fert.get("nutriente", "")),
            "origen": fert.get("origen", ""),
            "cantidad": fert.get("cantidad", 0),
            "emision_produccion": em_prod,
            "emision_n2o_directa": em_n2o_dir,
            "emision_n2o_indirecta": em_n2o_ind,
            "emision_n2o_ind_volatilizacion": em_n2o_ind_vol,
            "emision_n2o_ind_lixiviacion": em_n2o_ind_lix,
            "total": em_prod + em_n2o_dir + em_n2o_ind
        })

        emision_produccion += em_prod

    # --- EMISIONES N2O DIRECTAS E INDIRECTAS (totales) ---
    total_n_aplicado_inorg = n_aplicado_inorg * duracion
    total_n_volatilizado_inorg = volatilizacion_inorg * duracion
    total_n_lixiviado_inorg = lixiviacion_inorg * duracion
    total_n_aplicado_org = n_aplicado_org * duracion
    total_n_volatilizado_org = volatilizacion_org * duracion
    total_n_lixiviado_org = lixiviacion_org * duracion

    total_n_aplicado = total_n_aplicado_inorg + total_n_aplicado_org
    total_n_volatilizado = total_n_volatilizado_inorg + total_n_volatilizado_org
    total_n_lixiviado = total_n_lixiviado_inorg + total_n_lixiviado_org

    n2o_n_directo = total_n_aplicado * EF1
    n2o_n_ind_vol = total_n_volatilizado * EF4
    n2o_n_ind_lix = total_n_lixiviado * EF5
    n2o_n_indirecto = n2o_n_ind_vol + n2o_n_ind_lix
    n2o_directo = n2o_n_directo * (44/28)
    n2o_ind_vol = n2o_n_ind_vol * (44/28)
    n2o_ind_lix = n2o_n_ind_lix * (44/28)
    n2o_indirecto = n2o_ind_vol + n2o_ind_lix
    n2o_directo_co2e = n2o_directo * GWP["N2O"]
    n2o_indirecto_co2e = n2o_indirecto * GWP["N2O"]
    emision_n2o_co2e_total = n2o_directo_co2e + n2o_indirecto_co2e

    return emision_produccion, n2o_directo_co2e, n2o_indirecto_co2e, desglose

def ingresar_agroquimicos(etapa):
    st.markdown("##### Agroquímicos y pesticidas")
    agroquimicos = []
    categorias = [
        ("Pesticida", "pesticidas"),
        ("Fungicida", "fungicidas"),
        ("Insecticida", "insecticidas"),
        ("Herbicida", "herbicidas")
    ]
    tipos_dict = {
        "pesticidas": list(factores_emision["pesticidas"].keys()),
        "fungicidas": (
            ["Media"] +
            sorted([k for k in factores_emision["fungicidas"].keys() if k != "Media"])
        ),
        "insecticidas": (
            ["Media"] +
            sorted([k for k in factores_emision["insecticidas"].keys() if k != "Media"])
        ),
        "herbicidas": list(factores_emision["herbicidas"].keys())
    }
    n_agro = st.number_input(
        "¿Cuántos agroquímicos y/o pesticidas diferentes desea agregar en el ciclo?",
        min_value=0, step=1, format="%.10g", key=f"num_agroquimicos_{etapa}"
    )
    for i in range(n_agro):
        with st.expander(f"Agroquímico #{i+1}"):
            categoria = st.selectbox(
                "Categoría",
                [nombre for nombre, _ in categorias],
                key=f"cat_agro_{etapa}_{i}"
            )
            clave_categoria = dict(categorias)[categoria]
            tipo = st.selectbox(
                f"Tipo de {categoria.lower()}",
                tipos_dict[clave_categoria],
                key=f"tipo_agro_{etapa}_{i}"
            )
            modo = st.radio(
                "¿Cómo desea ingresar la cantidad?",
                ["Producto comercial (kg/ha·ciclo)", "Ingrediente activo (kg/ha·ciclo)"],
                key=f"modo_agro_{etapa}_{i}"
            )
            if modo == "Producto comercial (kg/ha·ciclo)":
                cantidad = st.number_input(
                    "Cantidad de producto comercial aplicada por hectárea en el ciclo (kg/ha·ciclo)",
                    min_value=0.0, format="%.10g", key=f"cantidad_agro_{etapa}_{i}"
                )
                concentracion = st.number_input(
                    "Concentración de ingrediente activo (%)",
                    min_value=0.0, max_value=100.0, value=100.0, format="%.10g",
                    key=f"concentracion_agro_{etapa}_{i}"
                )
                cantidad_ia = cantidad * (concentracion / 100)
            else:
                cantidad_ia = st.number_input(
                    "Cantidad de ingrediente activo aplicada por hectárea en el ciclo (kg/ha·ciclo)",
                    min_value=0.0, format="%.10g", key=f"cantidad_ia_agro_{etapa}_{i}"
                )
            # Permitir FE personalizado con hasta 6 decimales
            usar_fe_personalizado = st.checkbox(
                "¿Desea ingresar un factor de emisión personalizado para este agroquímico?",
                key=f"usar_fe_agro_{etapa}_{i}"
            )
            if usar_fe_personalizado:
                fe = st.number_input(
                    "Factor de emisión personalizado (kg CO₂e/kg ingrediente activo)",
                    min_value=0.0, step=0.000001, format="%.10g", key=f"fe_personalizado_agro_{etapa}_{i}"
                )
            else:
                fe = factores_emision[clave_categoria].get(tipo, valores_defecto["fe_agroquimico"])
            emisiones = cantidad_ia * fe
            agroquimicos.append({
                "categoria": clave_categoria,
                "tipo": tipo,
                "cantidad_ia": cantidad_ia,
                "fe": fe,
                "emisiones": emisiones
            })
    return agroquimicos

def calcular_emisiones_agroquimicos(agroquimicos, duracion):
    total = 0
    for ag in agroquimicos:
        total += ag["emisiones"] * duracion
    return total

# MAQUINARIA EN PERENNES
def ingresar_maquinaria_perenne(etapa, tipo_etapa):
    st.markdown(f"Labores y maquinaria ({tipo_etapa})")
    if not opciones_labores:
        st.error("No hay labores definidas en la base de datos.")
        return []
    labores = []
    n_labores = st.number_input(
        f"¿Cuántas labores desea agregar en la etapa '{tipo_etapa}'?",
        min_value=0,
        step=1,
        value=0,
        key=f"num_labores_{etapa}_{tipo_etapa}"
    )
    for i in range(n_labores):
        with st.expander(f"Labor #{i+1}"):
            nombre_labor_opcion = st.selectbox(
                "Nombre de la labor",
                opciones_labores,
                key=f"nombre_labor_opcion_{etapa}_{tipo_etapa}_{i}"
            )
            if nombre_labor_opcion == "Otro":
                nombre_labor = st.text_input(
                    "Ingrese el nombre de la labor",
                    key=f"nombre_labor_otro_{etapa}_{tipo_etapa}_{i}"
                )
            else:
                nombre_labor = nombre_labor_opcion

            tipo_labor = st.radio(
                "¿La labor es manual o mecanizada?",
                ["Manual", "Mecanizada"],
                key=f"tipo_labor_{etapa}_{tipo_etapa}_{i}"
            )

            if tipo_labor == "Manual":
                st.info("Labor manual: no se consideran emisiones directas de maquinaria ni combustible.")
                labores.append({
                    "nombre_labor": nombre_labor,
                    "tipo_maquinaria": "Manual",
                    "tipo_combustible": "N/A",
                    "litros": 0,
                    "emisiones": 0,
                    "fe_personalizado": None
                })
            else:
                if not rendimientos_maquinaria:
                    st.error("No hay tipos de maquinaria definidos en la base de datos.")
                    continue
                n_maquinas = st.number_input(
                    f"¿Cuántas maquinarias para esta labor?",
                    min_value=1,
                    step=1,
                    value=1,
                    key=f"num_maquinas_{etapa}_{tipo_etapa}_{i}"
                )
                tipos_maquinaria = list(rendimientos_maquinaria.keys())
                for j in range(n_maquinas):
                    if j > 0:
                        st.markdown("---")
                    st.markdown(f"**Maquinaria #{j+1}**")
                    tipo_maq = st.selectbox(
                        "Tipo de maquinaria",
                        tipos_maquinaria,
                        key=f"tipo_maq_{etapa}_{tipo_etapa}_{i}_{j}"
                    )

                    if tipo_maq == "Otro":
                        nombre_maq = st.text_input(
                            "Ingrese el nombre de la maquinaria",
                            key=f"nombre_maq_otro_{etapa}_{tipo_etapa}_{i}_{j}"
                        )
                        rendimiento_recomendado = float(rendimientos_maquinaria.get("Otro", 10))
                    else:
                        nombre_maq = tipo_maq
                        rendimiento_recomendado = float(rendimientos_maquinaria.get(tipo_maq, 10))

                    if not factores_combustible:
                        st.error("No hay tipos de combustible definidos en la base de datos.")
                        continue
                    tipo_comb = st.selectbox(
                        "Tipo de combustible",
                        list(factores_combustible.keys()),
                        key=f"tipo_comb_{etapa}_{tipo_etapa}_{i}_{j}"
                    )
                    fe_comb_default = factores_combustible.get(tipo_comb, 0)

                    repeticiones = st.number_input(
                        f"Número de pasadas o repeticiones en la etapa '{tipo_etapa}'",
                        min_value=1,
                        step=1,
                        value=1,
                        key=f"reps_{etapa}_{tipo_etapa}_{i}_{j}"
                    )

                    modo = st.radio(
                        "¿Cómo desea ingresar el consumo por pasada?",
                        ["Litros de combustible por pasada", "Horas de uso por pasada"],
                        key=f"modo_lab_{etapa}_{tipo_etapa}_{i}_{j}"
                    )

                    if modo == "Horas de uso por pasada":
                        rendimiento = st.number_input(
                            "Ingrese el rendimiento real de su maquinaria (litros/hora)",
                            min_value=0.0,
                            value=rendimiento_recomendado,
                            step=0.1,
                            format="%.10g",
                            key=f"rendimiento_{etapa}_{tipo_etapa}_{i}_{j}"
                        )
                        horas = st.number_input(
                            "Horas de uso por pasada (h/ha·pasada)",
                            min_value=0.0,
                            value=0.0,
                            step=0.1,
                            format="%.10g",
                            key=f"horas_{etapa}_{tipo_etapa}_{i}_{j}"
                        )
                        litros_por_pasada = horas * rendimiento
                    else:
                        litros_por_pasada = st.number_input(
                            "Litros de combustible por pasada (L/ha·pasada)",
                            min_value=0.0,
                            value=0.0,
                            step=0.1,
                            format="%.10g",
                            key=f"litros_{etapa}_{tipo_etapa}_{i}_{j}"
                        )

                    # Permitir FE personalizado para el combustible
                    usar_fe_personalizado = st.checkbox(
                        "¿Desea ingresar un factor de emisión personalizado para el tipo de combustible?",
                        key=f"usar_fe_maq_{etapa}_{tipo_etapa}_{i}_{j}"
                    )
                    if usar_fe_personalizado:
                        fe_comb = st.number_input(
                            "Factor de emisión personalizado (kg CO₂e/litro)",
                            min_value=0.0,
                            step=0.000001,
                            format="%.10g",
                            key=f"fe_personalizado_maq_{etapa}_{tipo_etapa}_{i}_{j}"
                        )
                    else:
                        fe_comb = fe_comb_default

                    litros_totales = litros_por_pasada * repeticiones
                    emisiones = litros_totales * fe_comb

                    labores.append({
                        "nombre_labor": nombre_labor,
                        "tipo_maquinaria": nombre_maq,
                        "tipo_combustible": tipo_comb,
                        "litros": litros_totales,
                        "emisiones": emisiones,
                        "fe_personalizado": fe_comb if usar_fe_personalizado else None
                    })
    return labores

# ====== MAQUINARIA EN ANUAL ======
def ingresar_maquinaria_ciclo(etapa):
    st.markdown("##### Labores y maquinaria")
    labores = []
    n_labores = st.number_input(f"¿Cuántas labores desea agregar en el ciclo?", min_value=0, step=1, key=f"num_labores_{etapa}")
    for i in range(n_labores):
        with st.expander(f"Labor #{i+1}"):
            nombre_labor_opcion = st.selectbox("Nombre de la labor", opciones_labores, key=f"nombre_labor_opcion_{etapa}_{i}")
            if nombre_labor_opcion == "Otro":
                nombre_labor = st.text_input("Ingrese el nombre de la labor", key=f"nombre_labor_otro_{etapa}_{i}")
            else:
                nombre_labor = nombre_labor_opcion

            tipo_labor = st.radio("¿La labor es manual o mecanizada?", ["Manual", "Mecanizada"], key=f"tipo_labor_{etapa}_{i}")

            if tipo_labor == "Manual":
                st.info("Labor manual: no se consideran emisiones directas de maquinaria ni combustible.")
                labores.append({
                    "nombre_labor": nombre_labor,
                    "tipo_maquinaria": "Manual",
                    "tipo_combustible": "N/A",
                    "litros": 0,
                    "emisiones": 0,
                    "fe_personalizado": None
                })
            else:
                n_maquinas = st.number_input(f"¿Cuántas maquinarias para esta labor?", min_value=1, step=1, key=f"num_maquinas_{etapa}_{i}")
                tipos_maquinaria = list(rendimientos_maquinaria.keys())
                for j in range(n_maquinas):
                    if j > 0:
                        st.markdown("---")
                    st.markdown(f"**Maquinaria #{j+1}**")
                    tipo_maq = st.selectbox("Tipo de maquinaria", tipos_maquinaria, key=f"tipo_maq_{etapa}_{i}_{j}")

                    if tipo_maq == "Otro":
                        nombre_maq = st.text_input("Ingrese el nombre de la maquinaria", key=f"nombre_maq_otro_{etapa}_{i}_{j}")
                        rendimiento_recomendado = float(rendimientos_maquinaria["Otro"])
                    else:
                        nombre_maq = tipo_maq
                        rendimiento_recomendado = float(rendimientos_maquinaria.get(tipo_maq, 10))

                    tipo_comb = st.selectbox("Tipo de combustible", list(factores_combustible.keys()), key=f"tipo_comb_{etapa}_{i}_{j}")
                    fe_comb_default = factores_combustible.get(tipo_comb, 0)

                    repeticiones = st.number_input("Número de pasadas o repeticiones en el ciclo", min_value=1, step=1, key=f"reps_ciclo_{etapa}_{i}_{j}")

                    modo = st.radio(
                        "¿Cómo desea ingresar el consumo por pasada?",
                        ["Litros de combustible por pasada", "Horas de uso por pasada"],
                        key=f"modo_lab_{etapa}_{i}_{j}"
                    )

                    if modo == "Horas de uso por pasada":
                        rendimiento = st.number_input(
                            "Ingrese el rendimiento real de su maquinaria (litros/hora)",
                            min_value=0.0,
                            value=rendimiento_recomendado,
                            step=0.1,
                            format="%.10g",
                            key=f"rendimiento_{etapa}_{i}_{j}"
                        )
                        horas = st.number_input("Horas de uso por pasada (h/ha·pasada)", min_value=0.0, format="%.10g", key=f"horas_{etapa}_{i}_{j}")
                        litros_por_pasada = horas * rendimiento
                    else:
                        litros_por_pasada = st.number_input("Litros de combustible por pasada (L/ha·pasada)", min_value=0.0, format="%.10g", key=f"litros_{etapa}_{i}_{j}")

                    # Permitir FE personalizado para el combustible
                    usar_fe_personalizado = st.checkbox(
                        "¿Desea ingresar un factor de emisión personalizado para el tipo de combustible?",
                        key=f"usar_fe_maq_{etapa}_{i}_{j}"
                    )
                    if usar_fe_personalizado:
                        fe_comb = st.number_input(
                            "Factor de emisión personalizado (kg CO₂e/litro)",
                            min_value=0.0,
                            step=0.000001,
                            format="%.10g",
                            key=f"fe_personalizado_maq_{etapa}_{i}_{j}"
                        )
                    else:
                        fe_comb = fe_comb_default

                    litros_totales = litros_por_pasada * repeticiones
                    emisiones = litros_totales * fe_comb

                    labores.append({
                        "nombre_labor": nombre_labor,
                        "tipo_maquinaria": nombre_maq,
                        "tipo_combustible": tipo_comb,
                        "litros": litros_totales,
                        "emisiones": emisiones,
                        "fe_personalizado": fe_comb if usar_fe_personalizado else None
                    })
    return labores

def calcular_emisiones_maquinaria(labores, duracion):
    """
    Calcula las emisiones de maquinaria usando el FE personalizado si existe,
    o el de la base de datos si no.
    """
    total = 0
    for labor in labores:
        litros = labor.get("litros", 0)
        fe = labor.get("fe_personalizado", None)
        if fe is not None and fe > 0:
            fe_utilizado = fe
        else:
            tipo_comb = labor.get("tipo_combustible")
            fe_utilizado = factores_combustible.get(tipo_comb, 0)
        total += litros * fe_utilizado
    return total * duracion

def ingresar_gestion_residuos(etapa):
    # Detectar si es modo anual o perenne
    modo_perenne = "Implantacion" in etapa or "Crecimiento" in etapa or "Producción" in etapa or "produccion" in etapa.lower() or "perenne" in etapa.lower()
    if modo_perenne:
        st.subheader("Gestión de residuos vegetales")
    else:
        st.markdown("---")
        st.subheader("Gestión de residuos vegetales")
    st.markdown("""
    <div style="background-color:#e3f2fd; padding:0.7em; border-radius:6px;">
    <b>¿Qué es la gestión de residuos vegetales?</b><br>
    Se refiere al manejo de los restos vegetales generados en el campo (ramas, hojas, raíces, frutos no cosechados, etc.) después de la cosecha o durante el manejo del cultivo.<br>
    <ul>
    <li><b>Quema:</b> genera emisiones directas de CH₄ y N₂O (se aplica fracción seca y fracción quemada, IPCC 2006).<br>
    <i>Valores recomendados IPCC: fracción seca = 0,8; fracción quemada = 0,9; EF_CH4 = 2,7 g/kg MS; EF_N2O = 0,07 g/kg MS.</i></li>
    <li><b>Compostaje:</b> genera emisiones de CH₄ y N₂O (se aplica fracción seca, IPCC 2006).<br>
    <i>Puede ser aeróbico o anaeróbico. Valores recomendados IPCC: aeróbico (CH₄: 0,004 kg/kg MS, N₂O: 0,0003 kg/kg MS), anaeróbico (CH₄: 0,01 kg/kg MS, N₂O: 0,0006 kg/kg MS).</i></li>
    <li><b>Incorporación al suelo:</b> no genera emisiones directas (el carbono se recicla en el suelo, IPCC 2006). Puede haber secuestro de carbono en modo avanzado (no implementado).</li>
    <li><b>Retiro del campo:</b> no genera emisiones directas en el predio (la gestión ocurre fuera del límite del sistema).</li>
    </ul>
    <i>La fracción seca (típicamente 0,8) sólo se aplica a quema y compostaje, ya que las emisiones se calculan sobre materia seca.</i>
    </div>
    """, unsafe_allow_html=True)

    activar = st.radio(
        "¿Desea ingresar la gestión de residuos vegetales para este ciclo?",
        ["No", "Sí"],
        key=f"activar_residuos_{etapa}"
    )
    detalle = {}

    if activar == "Sí":
        biomasa = st.number_input(
            "Cantidad total de residuos vegetales generados en este ciclo (kg/ha·ciclo, húmeda)",
            min_value=0.0,
            format="%.10g",
            key=f"biomasa_total_{etapa}"
        )
        modo = st.radio(
            "¿Cómo desea ingresar la gestión de residuos?",
            ["Porcentaje (%)", "Kilogramos (kg)"],
            key=f"modo_residuos_{etapa}"
        )
        opciones = st.multiselect(
            "¿Cómo se gestionan los residuos? (puede seleccionar más de una opción)",
            ["Quema", "Compostaje", "Incorporación al suelo", "Retiro del campo"],
            key=f"opciones_residuos_{etapa}"
        )
        cantidades = {}
        suma = 0

        # --- Ajustes y opciones avanzadas por método ---
        ajustes = {}
        for op in opciones:
            with st.expander(f"Gestión: {op}"):
                if modo == "Porcentaje (%)":
                    valor = st.number_input(
                        f"¿Qué porcentaje de la biomasa va a '{op}'?",
                        min_value=0.0, max_value=100.0,
                        format="%.10g",
                        key=f"porc_{op}_{etapa}"
                    )
                    cantidad = biomasa * (valor / 100)
                else:
                    valor = st.number_input(
                        f"¿Cuántos kg de biomasa van a '{op}'?",
                        min_value=0.0, max_value=biomasa,
                        format="%.10g",
                        key=f"kg_{op}_{etapa}"
                    )
                    cantidad = valor
                cantidades[op] = cantidad
                suma += valor if modo == "Porcentaje (%)" else cantidad

                # --- Ajustes específicos por método ---
                if op == "Quema":
                    st.caption("Se aplicará fracción seca y fracción quemada según IPCC 2006 para el cálculo de emisiones.")
                    fraccion_seca = st.number_input(
                        "Fracción seca de la biomasa (valor recomendado IPCC: 0,8)",
                        min_value=0.0, max_value=1.0, value=factores_residuos["fraccion_seca"],
                        format="%.10g",
                        key=f"fraccion_seca_quema_{etapa}"
                    )
                    fraccion_quemada = st.number_input(
                        "Fracción de biomasa efectivamente quemada (valor recomendado IPCC: 0,9)",
                        min_value=0.0, max_value=1.0, value=FRACCION_QUEMADA,
                        format="%.10g",
                        key=f"fraccion_quemada_{etapa}"
                    )
                    ajustes[op] = {
                        "fraccion_seca": fraccion_seca,
                        "fraccion_quemada": fraccion_quemada,
                    }
                    st.info("Si no conoce estos valores, utilice los recomendados por el IPCC.")
                elif op == "Compostaje":
                    st.caption("Se aplicará fracción seca según IPCC 2006 para el cálculo de emisiones.")
                    tipo_compost = st.radio(
                        "Tipo de compostaje",
                        ["Aeróbico (recomendado IPCC)", "Anaeróbico"],
                        key=f"tipo_compostaje_{etapa}"
                    )
                    tipo_compost_ipcc = "aerobico" if tipo_compost.startswith("Aeróbico") else "anaerobico"
                    fraccion_seca = st.number_input(
                        "Fracción seca de la biomasa (valor recomendado IPCC: 0,8)",
                        min_value=0.0, max_value=1.0, value=factores_residuos["fraccion_seca"],
                        format="%.10g",
                        key=f"fraccion_seca_compost_{etapa}"
                    )
                    ajustes[op] = {
                        "tipo": tipo_compost_ipcc,
                        "fraccion_seca": fraccion_seca
                    }
                    st.info("Si no conoce estos valores, utilice los recomendados por el IPCC.")
                elif op == "Incorporación al suelo":
                    st.caption("No se consideran emisiones directas según IPCC 2006. (Modo avanzado para secuestro de carbono no implementado).")
                elif op == "Retiro del campo":
                    destino = st.text_input("Destino o nota sobre el retiro del residuo (opcional)", key=f"destino_retiro_{etapa}")
                    ajustes[op] = {"destino": destino}

        # Advertencias de suma
        if modo == "Porcentaje (%)":
            faltante = 100.0 - suma
            if faltante > 0:
                st.warning(f"Falta ingresar {faltante:.1f}% para completar el 100% de los residuos.")
            elif faltante < 0:
                st.error(f"Ha ingresado más del 100% ({-faltante:.1f}% excedente).")
        else:
            faltante = biomasa - suma
            if faltante > 0:
                st.warning(f"Falta ingresar {faltante:,.1f} kg para completar el total de residuos.")
            elif faltante < 0:
                st.error(f"Ha ingresado más residuos de los existentes ({-faltante:,.1f} kg excedente).")

        # Guardar detalle para cálculo posterior (NO mostrar tabla aquí)
        for op in opciones:
            detalle[op] = {"biomasa": cantidades[op], "ajustes": ajustes.get(op, {})}

        # Si hay faltante, agregar "Sin gestión"
        if faltante > 0 and len(opciones) > 0:
            if modo == "Porcentaje (%)":
                sin_gestion = biomasa * (faltante / 100)
            else:
                sin_gestion = faltante
            detalle["Sin gestión"] = {"biomasa": sin_gestion, "ajustes": {}}

    # Calcular emisiones y agregar al detalle
    em_residuos, detalle_emisiones = calcular_emisiones_residuos(detalle)
    return em_residuos, detalle_emisiones

def calcular_emisiones_residuos(detalle):
    """
    Calcula las emisiones de GEI por gestión de residuos vegetales según IPCC 2006.
    - detalle: dict con {"vía": {"biomasa": ..., "ajustes": {...}}}
    Devuelve: total_emisiones, detalle_emisiones (dict con emisiones por vía)
    """
    total_emisiones = 0
    detalle_emisiones = {}
    for via, datos in detalle.items():
        biomasa = datos.get("biomasa", 0)
        ajustes = datos.get("ajustes", {})
        emisiones = 0
        if via == "Quema":
            em_ch4, em_n2o = calcular_emisiones_quema_residuos(
                biomasa,
                fraccion_seca=ajustes.get("fraccion_seca"),
                fraccion_quemada=ajustes.get("fraccion_quemada"),
                ef_ch4=ajustes.get("ef_ch4"),
                ef_n2o=ajustes.get("ef_n2o")
            )
            emisiones = em_ch4 + em_n2o
        elif via == "Compostaje":
            em_ch4, em_n2o = calcular_emisiones_compostaje(
                biomasa,
                tipo=ajustes.get("tipo", "aerobico"),
                fraccion_seca=ajustes.get("fraccion_seca")
            )
            emisiones = em_ch4 + em_n2o
        elif via == "Incorporación al suelo":
            emisiones = 0  # No se consideran emisiones directas según IPCC
        elif via == "Retiro del campo":
            emisiones = 0  # No se consideran emisiones dentro del predio
        elif via == "Sin gestión":
            emisiones = 0
        detalle_emisiones[via] = {"biomasa": biomasa, "emisiones": emisiones}
        total_emisiones += emisiones
    return total_emisiones, detalle_emisiones

def calcular_emisiones_quema_residuos(
    biomasa,
    fraccion_seca=None,
    fraccion_quemada=None,
    ef_ch4=None,
    ef_n2o=None
):
    if fraccion_seca is None:
        fraccion_seca = factores_residuos["fraccion_seca"]
    if fraccion_quemada is None:
        fraccion_quemada = FRACCION_QUEMADA
    if ef_ch4 is None:
        ef_ch4 = EF_CH4_QUEMA
    if ef_n2o is None:
        ef_n2o = EF_N2O_QUEMA
    biomasa_seca_quemada = biomasa * fraccion_seca * fraccion_quemada
    emision_CH4 = biomasa_seca_quemada * ef_ch4
    emision_N2O = biomasa_seca_quemada * ef_n2o
    emision_CH4_CO2e = emision_CH4 * GWP["CH4"]
    emision_N2O_CO2e = emision_N2O * GWP["N2O"]
    return emision_CH4_CO2e, emision_N2O_CO2e

def calcular_emisiones_compostaje(
    biomasa,
    tipo="aerobico",
    fraccion_seca=None
):
    if fraccion_seca is None:
        fraccion_seca = factores_residuos["fraccion_seca"]
    ms = biomasa * fraccion_seca  # Materia seca
    ef = factores_residuos["compostaje"][tipo]
    em_ch4 = ms * ef["EF_CH4"]
    em_n2o = ms * ef["EF_N2O"]
    em_ch4_co2e = em_ch4 * GWP["CH4"]
    em_n2o_co2e = em_n2o * GWP["N2O"]
    return em_ch4_co2e, em_n2o_co2e

def calcular_emisiones_incorporacion(biomasa, fraccion_seca=None, modo="simple"):
    """
    Calcula emisiones por incorporación de residuos vegetales al suelo.
    - biomasa: cantidad de biomasa incorporada (kg/ha, húmeda)
    - fraccion_seca: fracción seca de la biomasa (por defecto, valor recomendado)
    - modo: "simple" (emisión nula) o "avanzado" (secuestro de carbono, pendiente)
    """
    if fraccion_seca is None:
        fraccion_seca = factores_residuos["fraccion_seca"]
    if modo == "simple":
        return 0
    elif modo == "avanzado":
        return 0

def ingresar_riego_ciclo(etapa):
    st.markdown("### Riego y energía")
    st.caption("Agregue todas las actividades de riego y energía relevantes. Para cada actividad, ingrese el consumo de agua y energía si corresponde (puede dejar en 0 si no aplica).")

    actividades_base = ["Goteo", "Aspersión", "Surco", "Fertirriego", "Otro"]
    n_actividades = st.number_input(
        "¿Cuántas actividades de riego y energía desea agregar en este ciclo?",
        min_value=0, step=1, format="%.10g", key=f"num_actividades_riego_{etapa}"
    )
    energia_actividades = []
    em_agua_total = 0
    em_energia_total = 0

    for i in range(int(n_actividades)):
        with st.expander(f"Actividad #{i+1}"):
            actividad = st.selectbox(
                "Tipo de actividad",
                actividades_base,
                key=f"actividad_riego_{etapa}_{i}"
            )
            if actividad == "Otro":
                nombre_actividad = st.text_input(
                    "Ingrese el nombre de la actividad",
                    key=f"nombre_actividad_otro_{etapa}_{i}"
                )
            else:
                nombre_actividad = actividad

            # Agua (SIEMPRE)
            agua_total = st.number_input(
                "Cantidad total de agua aplicada (m³/ha·ciclo, puede ser 0 si no corresponde)",
                min_value=0.0,
                format="%.10g",
                key=f"agua_total_{etapa}_{i}"
            )

            st.markdown("---")  # Línea divisoria entre agua y energía

            # Energía (SIEMPRE)
            tipo_energia = st.selectbox(
                "Tipo de energía utilizada (puede dejar en 'Otro' y consumo 0 si no corresponde)",
                list(factores_combustible.keys()),
                key=f"tipo_energia_{etapa}_{i}"
            )
            modo_energia = st.radio(
                "¿Cómo desea ingresar el consumo de energía?",
                ["Consumo total (kWh/litros)", "Potencia × horas de uso"],
                key=f"modo_energia_{etapa}_{i}"
            )
            if tipo_energia == "Eléctrico":
                if modo_energia == "Consumo total (kWh/litros)":
                    consumo = st.number_input(
                        "Consumo total de electricidad (kWh/ha·ciclo)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"consumo_elec_{etapa}_{i}"
                    )
                else:
                    potencia = st.number_input(
                        "Potencia del equipo (kW)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"potencia_elec_{etapa}_{i}"
                    )
                    horas = st.number_input(
                        "Horas de uso (h/ha·ciclo)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"horas_elec_{etapa}_{i}"
                    )
                    consumo = potencia * horas
            else:
                if modo_energia == "Consumo total (kWh/litros)":
                    consumo = st.number_input(
                        f"Consumo total de {tipo_energia} (litros/ha·ciclo)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"consumo_comb_{etapa}_{i}"
                    )
                else:
                    potencia = st.number_input(
                        "Potencia del motor (kW)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"potencia_comb_{etapa}_{i}"
                    )
                    horas = st.number_input(
                        "Horas de uso (h/ha·ciclo)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"horas_comb_{etapa}_{i}"
                    )
                    rendimiento = st.number_input(
                        "Rendimiento del motor (litros/kWh)",
                        min_value=0.0,
                        value=valores_defecto["rendimiento_motor"],
                        format="%.10g",
                        key=f"rendimiento_comb_{etapa}_{i}"
                    )
                    consumo = potencia * horas * rendimiento

            # Factor de emisión (por defecto del diccionario, pero permitir personalizado)
            fe_energia = factores_combustible.get(tipo_energia, valores_defecto["fe_combustible_generico"])
            usar_fe_personalizado = st.checkbox(
                "¿Desea ingresar un factor de emisión personalizado para este tipo de energía?",
                key=f"usar_fe_energia_{etapa}_{i}"
            )
            if usar_fe_personalizado:
                fe_energia = st.number_input(
                    "Factor de emisión personalizado (kg CO₂e/kWh o kg CO₂e/litro)",
                    min_value=0.0,
                    step=0.000001,
                    format="%.10g",
                    key=f"fe_personalizado_energia_{etapa}_{i}"
                )

            emisiones_energia = consumo * fe_energia

            energia_actividades.append({
                "actividad": nombre_actividad,
                "tipo_actividad": actividad,
                "agua_total_m3": agua_total,
                "emisiones_agua": agua_total * 1000 * valores_defecto["fe_agua"],
                "consumo_energia": consumo,
                "tipo_energia": tipo_energia,
                "fe_energia": fe_energia,
                "emisiones_energia": emisiones_energia
            })
            em_agua_total += agua_total * 1000 * valores_defecto["fe_agua"]
            em_energia_total += emisiones_energia

    # Mostrar resultados globales de riego y energía
    st.info(
        f"**Riego y energía del ciclo:**\n"
        f"- Emisiones por agua de riego: {em_agua_total:.2f} kg CO₂e/ha·ciclo\n"
        f"- Emisiones por energía: {em_energia_total:.2f} kg CO₂e/ha·ciclo\n"
        f"- **Total riego y energía:** {em_agua_total + em_energia_total:.2f} kg CO₂e/ha·ciclo"
    )

    st.session_state[f"energia_actividades_{etapa}"] = energia_actividades

    return em_agua_total, em_energia_total, energia_actividades

def ingresar_riego_implantacion(etapa):
    st.markdown("### Riego y energía")
    st.caption("Agregue todas las actividades de riego y energía relevantes. Para cada actividad, ingrese el consumo de agua y energía si corresponde (puede dejar en 0 si no aplica).")

    actividades_base = ["Goteo", "Aspersión", "Surco", "Fertirriego", "Otro"]
    n_actividades = st.number_input(
        "¿Cuántas actividades de riego y energía desea agregar en implantación?",
        min_value=0, step=1, format="%.10g", key=f"num_actividades_riego_implantacion_{etapa}"
    )
    energia_actividades = []
    em_agua_total = 0
    em_energia_total = 0

    for i in range(int(n_actividades)):
        with st.expander(f"Actividad #{i+1}"):
            actividad = st.selectbox(
                "Tipo de actividad",
                actividades_base,
                key=f"actividad_riego_implantacion_{etapa}_{i}"
            )
            if actividad == "Otro":
                nombre_actividad = st.text_input(
                    "Ingrese el nombre de la actividad",
                    key=f"nombre_actividad_otro_implantacion_{etapa}_{i}"
                )
            else:
                nombre_actividad = actividad

            # Agua (SIEMPRE)
            agua_total = st.number_input(
                "Cantidad total de agua aplicada (m³/ha, puede ser 0 si no corresponde)",
                min_value=0.0,
                format="%.10g",
                key=f"agua_total_implantacion_{etapa}_{i}"
            )

            st.markdown("---")  # Línea divisoria entre agua y energía

            # Energía (SIEMPRE)
            tipo_energia = st.selectbox(
                "Tipo de energía utilizada (puede dejar en 'Otro' y consumo 0 si no corresponde)",
                list(factores_combustible.keys()),
                key=f"tipo_energia_implantacion_{etapa}_{i}"
            )
            modo_energia = st.radio(
                "¿Cómo desea ingresar el consumo de energía?",
                ["Consumo total (kWh/litros)", "Potencia × horas de uso"],
                key=f"modo_energia_implantacion_{etapa}_{i}"
            )
            if tipo_energia == "Eléctrico":
                if modo_energia == "Consumo total (kWh/litros)":
                    consumo = st.number_input(
                        "Consumo total de electricidad (kWh/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"consumo_elec_implantacion_{etapa}_{i}"
                    )
                else:
                    potencia = st.number_input(
                        "Potencia del equipo (kW)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"potencia_elec_implantacion_{etapa}_{i}"
                    )
                    horas = st.number_input(
                        "Horas de uso (h/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"horas_elec_implantacion_{etapa}_{i}"
                    )
                    consumo = potencia * horas
            else:
                if modo_energia == "Consumo total (kWh/litros)":
                    consumo = st.number_input(
                        f"Consumo total de {tipo_energia} (litros/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"consumo_comb_implantacion_{etapa}_{i}"
                    )
                else:
                    potencia = st.number_input(
                        "Potencia del motor (kW)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"potencia_comb_implantacion_{etapa}_{i}"
                    )
                    horas = st.number_input(
                        "Horas de uso (h/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"horas_comb_implantacion_{etapa}_{i}"
                    )
                    rendimiento = st.number_input(
                        "Rendimiento del motor (litros/kWh)",
                        min_value=0.0,
                        value=valores_defecto["rendimiento_motor"],
                        format="%.10g",
                        key=f"rendimiento_comb_implantacion_{etapa}_{i}"
                    )
                    consumo = potencia * horas * rendimiento

            fe_energia = factores_combustible.get(tipo_energia, valores_defecto["fe_combustible_generico"])
            usar_fe_personalizado = st.checkbox(
                "¿Desea ingresar un factor de emisión personalizado para este tipo de energía?",
                key=f"usar_fe_energia_implantacion_{etapa}_{i}"
            )
            if usar_fe_personalizado:
                fe_energia = st.number_input(
                    "Factor de emisión personalizado (kg CO₂e/kWh o kg CO₂e/litro)",
                    min_value=0.0,
                    step=0.000001,
                    format="%.10g",
                    key=f"fe_personalizado_energia_implantacion_{etapa}_{i}"
                )

            emisiones_energia = consumo * fe_energia

            energia_actividades.append({
                "actividad": nombre_actividad,
                "tipo_actividad": actividad,
                "agua_total_m3": agua_total,
                "emisiones_agua": agua_total * 1000 * valores_defecto["fe_agua"],
                "consumo_energia": consumo,
                "tipo_energia": tipo_energia,
                "fe_energia": fe_energia,
                "emisiones_energia": emisiones_energia
            })
            em_agua_total += agua_total * 1000 * valores_defecto["fe_agua"]
            em_energia_total += emisiones_energia

    # Mostrar resultados globales de riego y energía
    st.info(
        f"**Riego y energía (Implantación):**\n"
        f"- Emisiones por agua de riego: {em_agua_total:.2f} kg CO₂e\n"
        f"- Emisiones por energía: {em_energia_total:.2f} kg CO₂e\n"
        f"- **Total riego y energía:** {em_agua_total + em_energia_total:.2f} kg CO₂e"
    )

    return em_agua_total, em_energia_total, energia_actividades

def ingresar_riego_operacion_perenne(etapa, anios, sistema_riego_inicial):
    st.markdown("### Riego y energía")
    st.caption("Agregue todas las actividades de riego y energía relevantes. Para cada actividad, ingrese el consumo de agua y energía si corresponde (puede dejar en 0 si no aplica).")

    actividades_base = ["Goteo", "Aspersión", "Surco", "Fertirriego", "Otro"]
    emisiones_totales_agua = 0
    emisiones_totales_energia = 0
    emisiones_por_anio = []
    sistema_riego_actual = sistema_riego_inicial

    for anio in range(1, anios + 1):
        st.markdown(f"###### Año {anio}")
        cambiar = st.radio(
            "¿Desea cambiar el sistema de riego este año?",
            ["No", "Sí"],
            key=f"cambiar_riego_{etapa}_{anio}"
        )
        if cambiar == "Sí":
            sistema_riego_actual = st.selectbox("Nuevo tipo de riego", actividades_base, key=f"tipo_riego_{etapa}_{anio}")
        else:
            st.write(f"Tipo de riego: {sistema_riego_actual}")

        n_actividades = st.number_input(
            f"¿Cuántas actividades de riego y energía desea agregar en el año {anio}?",
            min_value=0, step=1, format="%.10g", key=f"num_actividades_riego_operacion_{etapa}_{anio}"
        )
        energia_actividades = []
        em_agua_total = 0
        em_energia_total = 0

        for i in range(int(n_actividades)):
            with st.expander(f"Actividad año {anio} #{i+1}"):
                actividad = st.selectbox(
                    "Tipo de actividad",
                    actividades_base,
                    key=f"actividad_riego_operacion_{etapa}_{anio}_{i}"
                )
                if actividad == "Otro":
                    nombre_actividad = st.text_input(
                        "Ingrese el nombre de la actividad",
                        key=f"nombre_actividad_otro_operacion_{etapa}_{anio}_{i}"
                    )
                else:
                    nombre_actividad = actividad

                # Agua (SIEMPRE)
                agua_total = st.number_input(
                    "Cantidad total de agua aplicada (m³/ha·año, puede ser 0 si no corresponde)",
                    min_value=0.0,
                    format="%.10g",
                    key=f"agua_total_operacion_{etapa}_{anio}_{i}"
                )

                st.markdown("---")  # Línea divisoria entre agua y energía

                # Energía (SIEMPRE)
                tipo_energia = st.selectbox(
                    "Tipo de energía utilizada (puede dejar en 'Otro' y consumo 0 si no corresponde)",
                    list(factores_combustible.keys()),
                    key=f"tipo_energia_operacion_{etapa}_{anio}_{i}"
                )
                modo_energia = st.radio(
                    "¿Cómo desea ingresar el consumo de energía?",
                    ["Consumo total (kWh/litros)", "Potencia × horas de uso"],
                    key=f"modo_energia_operacion_{etapa}_{anio}_{i}"
                )
                if tipo_energia == "Eléctrico":
                    if modo_energia == "Consumo total (kWh/litros)":
                        consumo = st.number_input(
                            "Consumo total de electricidad (kWh/ha·año)",
                            min_value=0.0,
                            format="%.10g",
                            key=f"consumo_elec_operacion_{etapa}_{anio}_{i}"
                        )
                    else:
                        potencia = st.number_input(
                            "Potencia del equipo (kW)",
                            min_value=0.0,
                            format="%.10g",
                            key=f"potencia_elec_operacion_{etapa}_{anio}_{i}"
                        )
                        horas = st.number_input(
                            "Horas de uso (h/ha·año)",
                            min_value=0.0,
                            format="%.10g",
                            key=f"horas_elec_operacion_{etapa}_{anio}_{i}"
                        )
                        consumo = potencia * horas
                else:
                    if modo_energia == "Consumo total (kWh/litros)":
                        consumo = st.number_input(
                            f"Consumo total de {tipo_energia} (litros/ha·año)",
                            min_value=0.0,
                            format="%.10g",
                            key=f"consumo_comb_operacion_{etapa}_{anio}_{i}"
                        )
                    else:
                        potencia = st.number_input(
                            "Potencia del motor (kW)",
                            min_value=0.0,
                            format="%.10g",
                            key=f"potencia_comb_operacion_{etapa}_{anio}_{i}"
                        )
                        horas = st.number_input(
                            "Horas de uso (h/ha·año)",
                            min_value=0.0,
                            format="%.10g",
                            key=f"horas_comb_operacion_{etapa}_{anio}_{i}"
                        )
                        rendimiento = st.number_input(
                            "Rendimiento del motor (litros/kWh)",
                            min_value=0.0,
                            value=valores_defecto["rendimiento_motor"],
                            format="%.10g",
                            key=f"rendimiento_comb_operacion_{etapa}_{anio}_{i}"
                        )
                        consumo = potencia * horas * rendimiento

                fe_energia = factores_combustible.get(tipo_energia, valores_defecto["fe_combustible_generico"])
                usar_fe_personalizado = st.checkbox(
                    "¿Desea ingresar un factor de emisión personalizado para este tipo de energía?",
                    key=f"usar_fe_energia_operacion_{etapa}_{anio}_{i}"
                )
                if usar_fe_personalizado:
                    fe_energia = st.number_input(
                        "Factor de emisión personalizado (kg CO₂e/kWh o kg CO₂e/litro)",
                        min_value=0.0,
                        step=0.000001,
                        format="%.10g",
                        key=f"fe_personalizado_energia_operacion_{etapa}_{anio}_{i}"
                    )

                emisiones_energia = consumo * fe_energia

                energia_actividades.append({
                    "actividad": nombre_actividad,
                    "tipo_actividad": actividad,
                    "agua_total_m3": agua_total,
                    "emisiones_agua": agua_total * 1000 * valores_defecto["fe_agua"],
                    "consumo_energia": consumo,
                    "tipo_energia": tipo_energia,
                    "fe_energia": fe_energia,
                    "emisiones_energia": emisiones_energia
                })
                em_agua_total += agua_total * 1000 * valores_defecto["fe_agua"]
                em_energia_total += emisiones_energia

        # Mostrar resultados del año
        st.info(
            f"**Año {anio} - Riego y energía:**\n"
            f"- Emisiones por agua de riego: {em_agua_total:.2f} kg CO₂e/ha\n"
            f"- Emisiones por energía: {em_energia_total:.2f} kg CO₂e/ha\n"
            f"- **Total riego y energía año {anio}:** {em_agua_total + em_energia_total:.2f} kg CO₂e/ha"
        )

        emisiones_totales_agua += em_agua_total
        emisiones_totales_energia += em_energia_total
        emisiones_por_anio.append({
            "anio": anio,
            "em_agua": em_agua_total,
            "em_energia": em_energia_total,
            "tipo_riego": sistema_riego_actual,
            "energia_actividades": energia_actividades
        })

    # Mostrar resumen total de la etapa
    st.info(
        f"**Resumen total riego y energía etapa {etapa}:**\n"
        f"- Emisiones totales por agua de riego: {emisiones_totales_agua:.2f} kg CO₂e/ha\n"
        f"- Emisiones totales por energía: {emisiones_totales_energia:.2f} kg CO₂e/ha\n"
        f"- **Total de la etapa:** {emisiones_totales_agua + emisiones_totales_energia:.2f} kg CO₂e/ha"
    )

    return emisiones_totales_agua, emisiones_totales_energia, emisiones_por_anio

def ingresar_riego_crecimiento(etapa, duracion, permitir_cambio_sistema=False):
    st.markdown("### Riego y energía")
    st.caption("Agregue todas las actividades de riego y energía relevantes. Para cada actividad, ingrese el consumo de agua y energía si corresponde (puede dejar en 0 si no aplica).")

    actividades_base = ["Goteo", "Aspersión", "Surco", "Fertirriego", "Otro"]
    n_actividades = st.number_input(
        "¿Cuántas actividades de riego y energía desea agregar?",
        min_value=0, step=1, format="%.10g", key=f"num_actividades_riego_crecimiento_{etapa}"
    )
    energia_actividades = []
    em_agua_total = 0
    em_energia_total = 0
    
    for i in range(int(n_actividades)):
        with st.expander(f"Actividad #{i+1}"):
            actividad = st.selectbox(
                "Tipo de actividad",
                actividades_base,
                key=f"actividad_riego_crecimiento_{etapa}_{i}"
            )
            if actividad == "Otro":
                nombre_actividad = st.text_input(
                    "Ingrese el nombre de la actividad",
                    key=f"nombre_actividad_otro_crecimiento_{etapa}_{i}"
                )
            else:
                nombre_actividad = actividad

            # Agua (SIEMPRE)
            agua_total = st.number_input(
                "Cantidad total de agua aplicada (m³/ha, puede ser 0 si no corresponde)",
                min_value=0.0,
                format="%.10g",
                key=f"agua_total_crecimiento_{etapa}_{i}"
            )

            st.markdown("---")  # Línea divisoria entre agua y energía

            # Energía (SIEMPRE)
            tipo_energia = st.selectbox(
                "Tipo de energía utilizada (puede dejar en 'Otro' y consumo 0 si no corresponde)",
                list(factores_combustible.keys()),
                key=f"tipo_energia_crecimiento_{etapa}_{i}"
            )
            modo_energia = st.radio(
                "¿Cómo desea ingresar el consumo de energía?",
                ["Consumo total (kWh/litros)", "Potencia × horas de uso"],
                key=f"modo_energia_crecimiento_{etapa}_{i}"
            )
            if tipo_energia == "Eléctrico":
                if modo_energia == "Consumo total (kWh/litros)":
                    consumo = st.number_input(
                        "Consumo total de electricidad (kWh/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"consumo_elec_crecimiento_{etapa}_{i}"
                    )
                else:
                    potencia = st.number_input(
                        "Potencia del equipo (kW)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"potencia_elec_crecimiento_{etapa}_{i}"
                    )
                    horas = st.number_input(
                        "Horas de uso (h/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"horas_elec_crecimiento_{etapa}_{i}"
                    )
                    consumo = potencia * horas
            else:
                if modo_energia == "Consumo total (kWh/litros)":
                    consumo = st.number_input(
                        f"Consumo total de {tipo_energia} (litros/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"consumo_comb_crecimiento_{etapa}_{i}"
                    )
                else:
                    potencia = st.number_input(
                        "Potencia del motor (kW)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"potencia_comb_crecimiento_{etapa}_{i}"
                    )
                    horas = st.number_input(
                        "Horas de uso (h/ha)",
                        min_value=0.0,
                        format="%.10g",
                        key=f"horas_comb_crecimiento_{etapa}_{i}"
                    )
                    rendimiento = st.number_input(
                        "Rendimiento del motor (litros/kWh)",
                        min_value=0.0,
                        value=valores_defecto["rendimiento_motor"],
                        format="%.10g",
                        key=f"rendimiento_comb_crecimiento_{etapa}_{i}"
                    )
                    consumo = potencia * horas * rendimiento

            fe_energia = factores_combustible.get(tipo_energia, valores_defecto["fe_combustible_generico"])
            usar_fe_personalizado = st.checkbox(
                "¿Desea ingresar un factor de emisión personalizado para este tipo de energía?",
                key=f"usar_fe_energia_crecimiento_{etapa}_{i}"
            )
            if usar_fe_personalizado:
                fe_energia = st.number_input(
                    "Factor de emisión personalizado (kg CO₂e/kWh o kg CO₂e/litro)",
                    min_value=0.0,
                    step=0.000001,
                    format="%.10g",
                    key=f"fe_personalizado_energia_crecimiento_{etapa}_{i}"
                )

            emisiones_energia = consumo * fe_energia

            energia_actividades.append({
                "actividad": nombre_actividad,
                "tipo_actividad": actividad,
                "agua_total_m3": agua_total,
                "emisiones_agua": agua_total * 1000 * valores_defecto["fe_agua"],
                "consumo_energia": consumo,
                "tipo_energia": tipo_energia,
                "fe_energia": fe_energia,
                "emisiones_energia": emisiones_energia
            })
            em_agua_total += agua_total * 1000 * valores_defecto["fe_agua"]
            em_energia_total += emisiones_energia

    # Mostrar resultados globales de riego y energía (POR AÑO, antes de multiplicar por duración)
    st.info(
        f"**Riego y energía (por año):**\n"
        f"- Emisiones por agua de riego: {em_agua_total:.2f} kg CO₂e/ha·año\n"
        f"- Emisiones por energía: {em_energia_total:.2f} kg CO₂e/ha·año\n"
        f"- **Total riego y energía:** {em_agua_total + em_energia_total:.2f} kg CO₂e/ha·año"
    )

    st.session_state[f"energia_actividades_crecimiento_{etapa}"] = energia_actividades

    # Retornar valores ya multiplicados por la duración para mantener compatibilidad
    return em_agua_total * duracion, em_energia_total * duracion, energia_actividades

def etapa_implantacion():
    st.header("Implantación")
    duracion = st.number_input("Años de duración de la etapa de implantación", min_value=1, step=1, key="duracion_Implantacion")

    # 1. Fertilizantes
    st.markdown("---")
    st.subheader("Fertilizantes utilizados en implantación")
    st.info("Ingrese la cantidad de fertilizantes aplicados por año. El sistema multiplicará por la duración de la etapa.")
    fert = ingresar_fertilizantes("Implantacion", unidad_cantidad="año")
    em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, duracion)
    em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
    st.info(
        f"**Fertilizantes (Implantación):**\n"
        f"- Producción de fertilizantes: {em_fert_prod:.2f} kg CO₂e\n"
        f"- Emisiones directas N₂O: {em_fert_n2o_dir:.2f} kg CO₂e\n"
        f"- Emisiones indirectas N₂O: {em_fert_n2o_ind:.2f} kg CO₂e\n"
        f"- **Total fertilizantes:** {em_fert_total:.2f} kg CO₂e"
    )

    # 2. Agroquímicos
    st.markdown("---")
    st.subheader("Agroquímicos y pesticidas")
    st.info("Ingrese la cantidad de agroquímicos aplicados por año. El sistema multiplicará por la duración de la etapa.")
    agroq = ingresar_agroquimicos("Implantacion")
    em_agroq = calcular_emisiones_agroquimicos(agroq, duracion)
    st.info(
        f"**Agroquímicos (Implantación):**\n"
        f"- **Total agroquímicos:** {em_agroq:.2f} kg CO₂e"
    )

    # 3. Riego (operación y energía para riego)
    st.markdown("---")
    st.subheader("Sistema de riego")
    em_agua, em_energia, energia_actividades = ingresar_riego_implantacion("Implantacion")
    tipo_riego = st.session_state.get("tipo_riego_Implantacion", None)

    # 4. Labores y maquinaria
    st.markdown("---")
    st.subheader("Labores y maquinaria")
    labores = ingresar_maquinaria_perenne("Implantacion", "Implantación")
    em_maq = calcular_emisiones_maquinaria(labores, duracion)
    st.info(
        f"**Maquinaria (Implantación):**\n"
        f"- **Total maquinaria:** {em_maq:.2f} kg CO₂e"
    )

    # 5. Gestión de residuos vegetales
    st.markdown("---")
    st.subheader("Gestión de residuos vegetales")
    em_residuos, detalle_residuos = ingresar_gestion_residuos("Implantacion")
    st.info(
        f"**Gestión de residuos (Implantación):**\n"
        f"- **Total residuos:** {em_residuos:.2f} kg CO₂e"
    )

    total = em_maq + em_agua + em_energia + em_fert_total + em_agroq + em_residuos

    # Guardar resultados por etapa y fuente
    emisiones_etapas["Implantación"] = total
    produccion_etapas["Implantación"] = 0  # No hay producción en implantación

    # ASIGNACIÓN DIRECTA (NO +=)
    emisiones_fuentes["Maquinaria"] = em_maq
    emisiones_fuentes["Riego"] = em_agua + em_energia
    emisiones_fuentes["Fertilizantes"] = em_fert_total
    emisiones_fuentes["Agroquímicos"] = em_agroq
    emisiones_fuentes["Residuos"] = em_residuos

    emisiones_fuente_etapa["Implantación"] = {
        "Fertilizantes": em_fert_total,
        "Agroquímicos": em_agroq,
        "Riego": em_agua + em_energia,
        "Maquinaria": em_maq,
        "Residuos": em_residuos,
        "desglose_fertilizantes": desglose_fert,
        "desglose_agroquimicos": agroq,
        "desglose_maquinaria": labores,
        "desglose_riego": {
            "tipo_riego": tipo_riego,
            "emisiones_agua": em_agua,
            "emisiones_energia": em_energia,
            "energia_actividades": energia_actividades
        },
        "desglose_residuos": detalle_residuos
    }

    st.success(f"Emisiones totales en etapa 'Implantación': {total:.2f} kg CO₂e/ha para {duracion} años")
    return total, 0

def etapa_crecimiento(nombre_etapa, produccion_pregunta=True):
    st.header(nombre_etapa)
    duracion = st.number_input(f"Años de duración de la etapa {nombre_etapa}", min_value=1, step=1, key=f"duracion_{nombre_etapa}")
    segmentar = st.radio(
        "¿Desea ingresar información diferenciada para cada año de la etapa?",
        ["No, ingresaré datos generales para toda la etapa", "Sí, ingresaré datos año por año"],
        key=f"segmentar_{nombre_etapa}"
    )
    if segmentar == "No, ingresaré datos generales para toda la etapa":
        st.info(
            f"""
            Todos los datos que ingrese a continuación se **asumirán iguales para cada año** de la etapa y se multiplicarán por {duracion} años.
            Es decir, el sistema considerará que durante todos los años de esta etapa usted mantiene los mismos consumos, actividades y hábitos de manejo.
            Si existen diferencias importantes entre años (por ejemplo, cambios en fertilización, riego, labores, etc.), le recomendamos ingresar el detalle año por año.
            """
        )
    else:
        st.info(
            "Ingrese los datos correspondientes a cada año de la etapa. El sistema sumará los valores de todos los años."
        )

    produccion_total = 0
    em_total = 0
    resultados_anuales = []

    if segmentar == "Sí, ingresaré datos año por año":
        total_fert = 0
        total_agroq = 0
        total_riego = 0
        total_maq = 0
        total_res = 0
        for anio in range(1, int(duracion) + 1):
            em_anio = 0
            st.markdown(f"#### Año {anio}")
            if produccion_pregunta:
                produccion = st.number_input(f"Producción de fruta en el año {anio} (kg/ha)", min_value=0.0, key=f"prod_{nombre_etapa}_{anio}")
            else:
                produccion = 0

            st.markdown("---")
            st.subheader("Fertilizantes")
            fert = ingresar_fertilizantes(f"{nombre_etapa}_anio{anio}", unidad_cantidad="año")
            em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, 1)
            em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
            st.info(
                f"**Fertilizantes (Año {anio}):**\n"
                f"- Producción de fertilizantes: {em_fert_prod:.2f} kg CO₂e\n"
                f"- Emisiones directas N₂O: {em_fert_n2o_dir:.2f} kg CO₂e\n"
                f"- Emisiones indirectas N₂O: {em_fert_n2o_ind:.2f} kg CO₂e\n"
                f"- **Total fertilizantes:** {em_fert_total:.2f} kg CO₂e"
            )

            st.markdown("---")
            st.subheader("Agroquímicos y pesticidas")
            agroq = ingresar_agroquimicos(f"{nombre_etapa}_anio{anio}")
            em_agroq = calcular_emisiones_agroquimicos(agroq, 1)
            st.info(
                f"**Agroquímicos (Año {anio}):**\n"
                f"- **Total agroquímicos:** {em_agroq:.2f} kg CO₂e"
            )

            st.markdown("---")
            st.subheader("Riego (operación)")
            em_agua, em_energia, energia_actividades = ingresar_riego_crecimiento(f"{nombre_etapa}_anio{anio}", 1, permitir_cambio_sistema=True)
            tipo_riego = st.session_state.get(f"tipo_riego_{nombre_etapa}_anio{anio}", None)

            st.markdown("---")
            st.subheader("Labores y maquinaria")
            labores = ingresar_maquinaria_perenne(f"{nombre_etapa}_anio{anio}", nombre_etapa)
            em_maq = calcular_emisiones_maquinaria(labores, 1)
            st.info(
                f"**Maquinaria (Año {anio}):**\n"
                f"- **Total maquinaria:** {em_maq:.2f} kg CO₂e"
            )

            em_residuos, detalle_residuos = ingresar_gestion_residuos(f"{nombre_etapa}_anio{anio}")
            st.info(
                f"**Gestión de residuos (Año {anio}):**\n"
                f"- **Total residuos:** {em_residuos:.2f} kg CO₂e"
            )

            em_anio = em_fert_total + em_agroq + em_agua + em_energia + em_maq + em_residuos
            em_total += em_anio
            produccion_total += produccion

            total_fert += em_fert_total
            total_agroq += em_agroq
            total_riego += em_agua + em_energia
            total_maq += em_maq
            total_res += em_residuos

            resultados_anuales.append({
                "Año": anio,
                "Emisiones (kg CO₂e/ha·año)": em_anio,
                "Producción (kg/ha·año)": produccion,
                "Fertilizantes": em_fert_total,
                "Agroquímicos": em_agroq,
                "Riego": em_agua + em_energia,
                "Maquinaria": em_maq,
                "Residuos": em_residuos
            })

            emisiones_fuente_etapa[f"{nombre_etapa} - Año {anio}"] = {
                "Fertilizantes": em_fert_total,
                "Agroquímicos": em_agroq,
                "Riego": em_agua + em_energia,
                "Maquinaria": em_maq,
                "Residuos": em_residuos,
                "desglose_fertilizantes": desglose_fert,
                "desglose_agroquimicos": agroq,
                "desglose_maquinaria": labores,
                "desglose_riego": {
                    "tipo_riego": tipo_riego,
                    "emisiones_agua": em_agua,
                    "emisiones_energia": em_energia,
                    "energia_actividades": energia_actividades
                },
                "desglose_residuos": detalle_residuos
            }

            st.info(f"Emisiones en año {anio}: {em_anio:.2f} kg CO₂e/ha")

        emisiones_fuentes["Fertilizantes"] = total_fert
        emisiones_fuentes["Agroquímicos"] = total_agroq
        emisiones_fuentes["Riego"] = total_riego
        emisiones_fuentes["Maquinaria"] = total_maq
        emisiones_fuentes["Residuos"] = total_res

        if resultados_anuales:
            st.markdown("### Emisiones por año en esta etapa")
            df_anual = pd.DataFrame(resultados_anuales)
            df_anual["Emisiones (kg CO₂e/kg fruta·año)"] = df_anual.apply(
                lambda row: row["Emisiones (kg CO₂e/ha·año)"] / row["Producción (kg/ha·año)"] if row["Producción (kg/ha·año)"] > 0 else None,
                axis=1
            )
            st.dataframe(df_anual, hide_index=True)
            st.info(
                "🔎 Las emisiones por año corresponden a cada año de la etapa. "
                "Las emisiones totales de la etapa son la suma de todos los años."
            )

    else:
        if produccion_pregunta:
            produccion = st.number_input(f"Producción de fruta por año en esta etapa (kg/ha·año)", min_value=0.0, key=f"prod_{nombre_etapa}")
        else:
            produccion = 0
        
        st.markdown("---")
        st.subheader("Fertilizantes")
        fert = ingresar_fertilizantes(nombre_etapa, unidad_cantidad="año")
        em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, duracion)
        em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
        st.info(
            f"**Fertilizantes (Etapa completa):**\n"
            f"- Producción de fertilizantes: {em_fert_prod:.2f} kg CO₂e\n"
            f"- Emisiones directas N₂O: {em_fert_n2o_dir:.2f} kg CO₂e\n"
            f"- Emisiones indirectas N₂O: {em_fert_n2o_ind:.2f} kg CO₂e\n"
            f"- **Total fertilizantes:** {em_fert_total:.2f} kg CO₂e"
        )

        st.markdown("---")
        st.subheader("Agroquímicos y pesticidas")
        agroq = ingresar_agroquimicos(nombre_etapa)
        em_agroq = calcular_emisiones_agroquimicos(agroq, duracion)
        st.info(
            f"**Agroquímicos (Etapa completa):**\n"
            f"- **Total agroquímicos:** {em_agroq:.2f} kg CO₂e"
        )

        st.markdown("---")
        st.subheader("Riego (operación)")
        em_agua, em_energia, energia_actividades = ingresar_riego_crecimiento(nombre_etapa, duracion, permitir_cambio_sistema=True)
        tipo_riego = st.session_state.get(f"tipo_riego_{nombre_etapa}", None)

        st.markdown("---")
        st.subheader("Labores y maquinaria")
        labores = ingresar_maquinaria_perenne(nombre_etapa, nombre_etapa)
        em_maq = calcular_emisiones_maquinaria(labores, duracion)
        st.info(
            f"**Maquinaria (Etapa completa):**\n"
            f"- **Total maquinaria:** {em_maq:.2f} kg CO₂e"
        )

        em_residuos, detalle_residuos = ingresar_gestion_residuos(nombre_etapa)
        st.info(
            f"**Gestión de residuos (Etapa completa):**\n"
            f"- **Total residuos:** {em_residuos:.2f} kg CO₂e"
        )

        em_total = em_fert_total + em_agroq + em_agua + em_energia + em_maq + em_residuos
        produccion_total = produccion * duracion

        emisiones_fuentes["Fertilizantes"] = em_fert_total
        emisiones_fuentes["Agroquímicos"] = em_agroq
        emisiones_fuentes["Riego"] = em_agua + em_energia
        emisiones_fuentes["Maquinaria"] = em_maq
        emisiones_fuentes["Residuos"] = em_residuos

        emisiones_fuente_etapa[nombre_etapa] = {
            "Fertilizantes": em_fert_total,
            "Agroquímicos": em_agroq,
            "Riego": em_agua + em_energia,
            "Maquinaria": em_maq,
            "Residuos": em_residuos,
            "desglose_fertilizantes": desglose_fert,
            "desglose_agroquimicos": agroq,
            "desglose_maquinaria": labores,
            "desglose_riego": {
                "tipo_riego": tipo_riego,
                "emisiones_agua": em_agua,
                "emisiones_energia": em_energia,
                "energia_actividades": energia_actividades
            },
            "desglose_residuos": detalle_residuos
        }

        st.info(f"Emisiones totales en la etapa: {em_total:.2f} kg CO₂e/ha para {duracion} años")
        st.info(f"Producción total en la etapa: {produccion_total:.2f} kg/ha")

    emisiones_etapas[nombre_etapa] = em_total
    produccion_etapas[nombre_etapa] = produccion_total

    st.success(f"Emisiones totales en etapa '{nombre_etapa}': {em_total:.2f} kg CO₂e/ha para {duracion} años")
    return em_total, produccion_total

def etapa_produccion_segmentada():
    st.header("Crecimiento con producción")
    st.warning(
        "Puede segmentar esta etapa en sub-etapas (por ejemplo, baja y alta producción). "
        "Si segmenta, para cada sub-etapa se preguntará la producción esperada y duración.\n\n"
        "🔎 **Sugerencia profesional:** Si desea considerar las emisiones asociadas al último año productivo del cultivo (por ejemplo, insumos, riego, energía, labores y actividades relacionadas con el fin de vida del huerto), "
        "le recomendamos crear una sub-etapa llamada **'Fin de vida'** dentro de esta etapa de producción. "
        "En esa sub-etapa podrá ingresar todos los insumos y actividades relevantes para el último año del cultivo, incluyendo la gestión de residuos vegetales generados por la remoción de plantas (árboles, arbustos, etc.).\n\n"
        "**Nota:** Si aún no ha llegado al fin de vida de su huerto, puede estimar estos valores según su experiencia o dejar la sub-etapa vacía. "
        "No cree una sub-etapa de fin de vida si ya incluyó todos los residuos y actividades en las sub-etapas anteriores."
    )
    segmentar = st.radio(
        "¿Desea segmentar esta etapa en sub-etapas?",
        ["No, usar una sola etapa", "Sí, segmentar en sub-etapas"],
        key="segmentar_produccion"
    )
    em_total = 0
    prod_total = 0
    emisiones_anuales = []  # [(año, emisiones, producción, nombre_subetapa)]
    if segmentar == "Sí, segmentar en sub-etapas":
        n_sub = st.number_input("¿Cuántas sub-etapas desea ingresar?", min_value=1, step=1, key="n_subetapas")
        anio_global = 1
        total_fert = 0
        total_agroq = 0
        total_riego = 0
        total_maq = 0
        total_res = 0
        for i in range(int(n_sub)):
            st.markdown(f"### Sub-etapa {i+1}")
            nombre = st.text_input(f"Nombre de la sub-etapa {i+1} (ej: baja producción, alta producción, fin de vida)", key=f"nombre_sub_{i}")
            prod = st.number_input(f"Producción esperada anual en esta sub-etapa (kg/ha/año)", min_value=0.0, key=f"prod_sub_{i}")
            dur = st.number_input(f"Años de duración de la sub-etapa", min_value=1, step=1, key=f"dur_sub_{i}")

            st.markdown(f"#### Datos para sub-etapa {i+1}: {nombre}")
            segmentar_anios = st.radio(
                f"¿Desea ingresar información diferenciada para cada año de la sub-etapa '{nombre}'?",
                ["No, ingresaré datos generales para toda la sub-etapa", "Sí, ingresaré datos año por año"],
                key=f"segmentar_anios_sub_{i}"
            )
            em_sub = 0
            prod_sub_total = 0
            if segmentar_anios == "Sí, ingresaré datos año por año":
                for anio in range(1, int(dur) + 1):
                    st.markdown(f"##### Año {anio}")
                    produccion = st.number_input(f"Producción de fruta en el año {anio} (kg/ha)", min_value=0.0, key=f"prod_{nombre}_{anio}_{i}")
                    
                    st.markdown("---")
                    st.subheader("Fertilizantes")
                    fert = ingresar_fertilizantes(f"{nombre}_anio{anio}_{i}", unidad_cantidad="año")
                    em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, 1)
                    em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
                    # Mostrar resumen de fertilizantes
                    st.info(f"**Fertilizantes (año {anio}):** {em_fert_total:.2f} kg CO₂e/ha")

                    st.markdown("---")
                    st.subheader("Agroquímicos y pesticidas")
                    agroq = ingresar_agroquimicos(f"{nombre}_anio{anio}_{i}")
                    em_agroq = calcular_emisiones_agroquimicos(agroq, 1)
                    # Mostrar resumen de agroquímicos
                    st.info(f"**Agroquímicos (año {anio}):** {em_agroq:.2f} kg CO₂e/ha")

                    st.markdown("---")
                    st.subheader("Riego (operación)")
                    em_agua, em_energia, energia_actividades = ingresar_riego_crecimiento(f"{nombre}_anio{anio}_{i}", 1, permitir_cambio_sistema=True)
                    tipo_riego = st.session_state.get(f"tipo_riego_{nombre}_anio{anio}_{i}", None)

                    st.markdown("---")
                    st.subheader("Labores y maquinaria")
                    labores = ingresar_maquinaria_perenne(f"{nombre}_anio{anio}_{i}", nombre)
                    em_maq = calcular_emisiones_maquinaria(labores, 1)  # Solo por año
                    # Mostrar resumen de maquinaria
                    st.info(f"**Maquinaria (año {anio}):** {em_maq:.2f} kg CO₂e/ha")

                    em_residuos, detalle_residuos = ingresar_gestion_residuos(f"{nombre}_anio{anio}_{i}")
                    # Mostrar resumen de residuos
                    st.info(f"**Gestión de residuos (año {anio}):** {em_residuos:.2f} kg CO₂e/ha")

                    em_anio = em_fert_total + em_agroq + em_agua + em_energia + em_maq + em_residuos
                    em_sub += em_anio
                    prod_sub_total += produccion

                    total_fert += em_fert_total
                    total_agroq += em_agroq
                    total_riego += em_agua + em_energia
                    total_maq += em_maq
                    total_res += em_residuos

                    # Guardar emisiones y producción por año y sub-etapa
                    nombre_etapa = f"{nombre} - Año {anio_global}"
                    emisiones_etapas[nombre_etapa] = em_anio
                    produccion_etapas[nombre_etapa] = produccion
                    emisiones_anuales.append((anio_global, em_anio, produccion, nombre))
                    emisiones_fuente_etapa[nombre_etapa] = {
                        "Fertilizantes": em_fert_total,
                        "Agroquímicos": em_agroq,
                        "Riego": em_agua + em_energia,
                        "Maquinaria": em_maq,
                        "Residuos": em_residuos,
                        "desglose_fertilizantes": desglose_fert,
                        "desglose_agroquimicos": agroq,
                        "desglose_maquinaria": labores,
                        "desglose_riego": {
                            "tipo_riego": tipo_riego,
                            "emisiones_agua": em_agua,
                            "emisiones_energia": em_energia,
                            "energia_actividades": energia_actividades
                        },
                        "desglose_residuos": detalle_residuos
                    }
                    anio_global += 1

            else:
                st.markdown("---")
                st.subheader("Fertilizantes")
                fert = ingresar_fertilizantes(f"{nombre}_general_{i}", unidad_cantidad="año")
                em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, dur)
                em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
                # Mostrar resumen de fertilizantes (por año)
                st.info(f"**Fertilizantes (por año):** {em_fert_total/dur:.2f} kg CO₂e/ha·año → **Total sub-etapa:** {em_fert_total:.2f} kg CO₂e/ha")

                st.markdown("---")
                st.subheader("Agroquímicos y pesticidas")
                agroq = ingresar_agroquimicos(f"{nombre}_general_{i}")
                em_agroq = calcular_emisiones_agroquimicos(agroq, dur)
                # Mostrar resumen de agroquímicos (por año)
                st.info(f"**Agroquímicos (por año):** {em_agroq/dur:.2f} kg CO₂e/ha·año → **Total sub-etapa:** {em_agroq:.2f} kg CO₂e/ha")

                st.markdown("---")
                st.subheader("Riego (operación)")
                em_agua, em_energia, energia_actividades = ingresar_riego_crecimiento(f"{nombre}_general_{i}", dur, permitir_cambio_sistema=True)
                tipo_riego = st.session_state.get(f"tipo_riego_{nombre}_general_{i}", None)

                st.markdown("---")
                st.subheader("Labores y maquinaria")
                labores = ingresar_maquinaria_perenne(f"{nombre}_general_{i}", nombre)
                em_maq = calcular_emisiones_maquinaria(labores, dur)  # Multiplica por duración
                # Mostrar resumen de maquinaria (por año)
                st.info(f"**Maquinaria (por año):** {em_maq/dur:.2f} kg CO₂e/ha·año → **Total sub-etapa:** {em_maq:.2f} kg CO₂e/ha")

                em_residuos, detalle_residuos = ingresar_gestion_residuos(f"{nombre}_general_{i}")
                # Mostrar resumen de residuos (por año)
                st.info(f"**Gestión de residuos (por año):** {em_residuos/dur:.2f} kg CO₂e/ha·año → **Total sub-etapa:** {em_residuos:.2f} kg CO₂e/ha")

                em_sub = em_fert_total + em_agroq + em_agua + em_energia + em_maq + em_residuos
                prod_sub_total = prod * dur

                total_fert += em_fert_total
                total_agroq += em_agroq
                total_riego += em_agua + em_energia
                total_maq += em_maq
                total_res += em_residuos

                nombre_etapa = f"{nombre}"
                emisiones_etapas[nombre_etapa] = em_sub
                produccion_etapas[nombre_etapa] = prod_sub_total
                emisiones_fuente_etapa[nombre_etapa] = {
                    "Fertilizantes": em_fert_total,
                    "Agroquímicos": em_agroq,
                    "Riego": em_agua + em_energia,
                    "Maquinaria": em_maq,
                    "Residuos": em_residuos,
                    "desglose_fertilizantes": desglose_fert,
                    "desglose_agroquimicos": agroq,
                    "desglose_maquinaria": labores,
                    "desglose_riego": {
                        "tipo_riego": tipo_riego,
                        "emisiones_agua": em_agua,
                        "emisiones_energia": em_energia,
                        "energia_actividades": energia_actividades
                    },
                    "desglose_residuos": detalle_residuos
                }
                for k in range(int(dur)):
                    emisiones_anuales.append((anio_global, em_sub/dur, prod, nombre))
                    anio_global += 1

            em_total += em_sub
            prod_total += prod_sub_total
            st.success(f"Emisiones totales en sub-etapa '{nombre}': {em_sub:.2f} kg CO₂e/ha para {dur} años")

        emisiones_fuentes["Fertilizantes"] = total_fert
        emisiones_fuentes["Agroquímicos"] = total_agroq
        emisiones_fuentes["Riego"] = total_riego
        emisiones_fuentes["Maquinaria"] = total_maq
        emisiones_fuentes["Residuos"] = total_res

    else:
        nombre_etapa = st.text_input("Nombre para la etapa de producción (ej: Producción, Producción plena, etc.)", value="Producción", key="nombre_etapa_produccion_unica")
        em, prod = etapa_crecimiento(nombre_etapa, produccion_pregunta=True)
        em_total += em
        prod_total += prod

    st.session_state["emisiones_anuales"] = emisiones_anuales

    return em_total, prod_total

def etapa_anual():
    st.header("Ciclo anual")
    n_ciclos = st.number_input("¿Cuántos ciclos realiza por año?", min_value=1, step=1, key="n_ciclos")
    ciclos_diferentes = st.radio(
        "¿Los ciclos son diferentes entre sí?",
        ["No, todos los ciclos son iguales", "Sí, cada ciclo es diferente"],
        key="ciclos_diferentes"
    )
    if ciclos_diferentes == "No, todos los ciclos son iguales":
        st.info(
            f"""
            Todos los datos que ingrese a continuación se **asumirán iguales para cada ciclo** y se multiplicarán por {n_ciclos} ciclos.
            Es decir, el sistema considerará que en todos los ciclos usted mantiene los mismos consumos, actividades y hábitos de manejo.
            Si existen diferencias importantes entre ciclos, le recomendamos ingresar el detalle ciclo por ciclo.
            """
        )
    else:
        st.info(
            "Ingrese los datos correspondientes a cada ciclo. El sistema sumará los valores de todos los ciclos, permitiendo reflejar cambios o variaciones entre ciclos."
        )

    em_total = 0
    prod_total = 0
    emisiones_ciclos = []
    desglose_fuentes_ciclos = []

    if ciclos_diferentes == "No, todos los ciclos son iguales":
        st.markdown("### Datos para un ciclo típico (se multiplicará por el número de ciclos)")
        produccion = st.number_input("Producción de fruta en el ciclo (kg/ha·ciclo)", min_value=0.0, key="prod_ciclo_tipico")
        
        st.markdown("---")
        st.subheader("Fertilizantes")
        fert = ingresar_fertilizantes("ciclo_tipico", unidad_cantidad="ciclo")
        em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, 1)
        em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
        st.info(
            f"**Fertilizantes (por ciclo):**\n"
            f"- Producción de fertilizantes: {em_fert_prod:.2f} kg CO₂e/ha·ciclo\n"
            f"- Emisiones directas N₂O: {em_fert_n2o_dir:.2f} kg CO₂e/ha·ciclo\n"
            f"- Emisiones indirectas N₂O: {em_fert_n2o_ind:.2f} kg CO₂e/ha·ciclo\n"
            f"- **Total fertilizantes:** {em_fert_total:.2f} kg CO₂e/ha·ciclo"
        )

        st.markdown("---")
        st.subheader("Agroquímicos y pesticidas")
        agroq = ingresar_agroquimicos("ciclo_tipico")
        em_agroq = calcular_emisiones_agroquimicos(agroq, 1)
        st.info(
            f"**Agroquímicos (por ciclo):**\n"
            f"- **Total agroquímicos:** {em_agroq:.2f} kg CO₂e/ha·ciclo"
        )

        st.markdown("---")
        st.subheader("Riego")
        em_agua, em_energia, energia_actividades = ingresar_riego_ciclo("ciclo_tipico")
        tipo_riego = st.session_state.get("tipo_riego_ciclo_tipico", "")

        st.markdown("---")
        st.subheader("Labores y maquinaria")
        labores = ingresar_maquinaria_ciclo("ciclo_tipico")
        em_maq = calcular_emisiones_maquinaria(labores, 1)
        st.info(
            f"**Maquinaria (por ciclo):**\n"
            f"- **Total maquinaria:** {em_maq:.2f} kg CO₂e/ha·ciclo"
        )

        em_residuos, detalle_residuos = ingresar_gestion_residuos("ciclo_tipico")
        st.info(
            f"**Gestión de residuos (por ciclo):**\n"
            f"- **Total gestión de residuos:** {em_residuos:.2f} kg CO₂e/ha·ciclo"
        )

        em_ciclo = em_fert_total + em_agroq + em_agua + em_energia + em_maq + em_residuos
        em_total = em_ciclo * n_ciclos
        prod_total = produccion * n_ciclos
        for ciclo in range(1, int(n_ciclos) + 1):
            desglose_fuentes_ciclos.append({
                "Ciclo": ciclo,
                "Fertilizantes": em_fert_total,
                "Agroquímicos": em_agroq,
                "Riego": em_agua + em_energia,
                "Maquinaria": em_maq,
                "Residuos": em_residuos,
                "desglose_fertilizantes": desglose_fert,
                "desglose_agroquimicos": agroq,
                "desglose_maquinaria": labores,
                "desglose_riego": {
                    "tipo_riego": tipo_riego,
                    "emisiones_agua": em_agua,
                    "emisiones_energia": em_energia,
                    "energia_actividades": energia_actividades
                },
                "desglose_residuos": detalle_residuos
            })
            emisiones_ciclos.append((ciclo, em_ciclo, produccion))

        emisiones_fuentes["Fertilizantes"] = em_fert_total * n_ciclos
        emisiones_fuentes["Agroquímicos"] = em_agroq * n_ciclos
        emisiones_fuentes["Riego"] = (em_agua + em_energia) * n_ciclos
        emisiones_fuentes["Maquinaria"] = em_maq * n_ciclos
        emisiones_fuentes["Residuos"] = em_residuos * n_ciclos

        st.info(f"Emisiones por ciclo típico: {em_ciclo:.2f} kg CO₂e/ha·ciclo")
        st.info(f"Emisiones anuales (todos los ciclos): {em_total:.2f} kg CO₂e/ha·año")

        emisiones_etapas["Anual"] = em_total
        produccion_etapas["Anual"] = prod_total
        emisiones_fuente_etapa["Anual"] = {
            "Fertilizantes": emisiones_fuentes["Fertilizantes"],
            "Agroquímicos": emisiones_fuentes["Agroquímicos"],
            "Riego": emisiones_fuentes["Riego"],
            "Maquinaria": emisiones_fuentes["Maquinaria"],
            "Residuos": emisiones_fuentes["Residuos"]
        }

    else:
        total_fert = 0
        total_agroq = 0
        total_riego = 0
        total_maq = 0
        total_res = 0
        for i in range(int(n_ciclos)):
            st.markdown(f"### Ciclo {i+1}")
            produccion = st.number_input(f"Producción de fruta en el ciclo {i+1} (kg/ha·ciclo)", min_value=0.0, key=f"prod_ciclo_{i+1}")

            st.subheader("Fertilizantes")
            fert = ingresar_fertilizantes(f"ciclo_{i+1}", unidad_cantidad="ciclo")
            em_fert_prod, em_fert_n2o_dir, em_fert_n2o_ind, desglose_fert = calcular_emisiones_fertilizantes(fert, 1)
            em_fert_total = em_fert_prod + em_fert_n2o_dir + em_fert_n2o_ind
            st.info(
                f"**Fertilizantes (Ciclo {i+1}):**\n"
                f"- Producción de fertilizantes: {em_fert_prod:.2f} kg CO₂e/ha\n"
                f"- Emisiones directas N₂O: {em_fert_n2o_dir:.2f} kg CO₂e/ha\n"
                f"- Emisiones indirectas N₂O: {em_fert_n2o_ind:.2f} kg CO₂e/ha\n"
                f"- **Total fertilizantes:** {em_fert_total:.2f} kg CO₂e/ha"
            )

            st.subheader("Agroquímicos y pesticidas")
            agroq = ingresar_agroquimicos(f"ciclo_{i+1}")
            em_agroq = calcular_emisiones_agroquimicos(agroq, 1)
            st.info(
                f"**Agroquímicos (Ciclo {i+1}):**\n"
                f"- **Total agroquímicos:** {em_agroq:.2f} kg CO₂e/ha"
            )

            st.subheader("Riego")
            em_agua, em_energia, energia_actividades = ingresar_riego_ciclo(f"ciclo_{i+1}")
            tipo_riego = st.session_state.get(f"tipo_riego_ciclo_{i+1}", "")

            st.subheader("Labores y maquinaria")
            labores = ingresar_maquinaria_ciclo(f"ciclo_{i+1}")
            em_maq = calcular_emisiones_maquinaria(labores, 1)
            st.info(
                f"**Maquinaria (Ciclo {i+1}):**\n"
                f"- **Total maquinaria:** {em_maq:.2f} kg CO₂e/ha"
            )

            em_residuos, detalle_residuos = ingresar_gestion_residuos(f"ciclo_{i+1}")
            st.info(
                f"**Gestión de residuos (Ciclo {i+1}):**\n"
                f"- **Total gestión de residuos:** {em_residuos:.2f} kg CO₂e/ha"
            )

            em_ciclo = em_fert_total + em_agroq + em_agua + em_energia + em_maq + em_residuos
            em_total += em_ciclo
            prod_total += produccion
            desglose_fuentes_ciclos.append({
                "Ciclo": i+1,
                "Fertilizantes": em_fert_total,
                "Agroquímicos": em_agroq,
                "Riego": em_agua + em_energia,
                "Maquinaria": em_maq,
                "Residuos": em_residuos,
                "desglose_fertilizantes": desglose_fert,
                "desglose_agroquimicos": agroq,
                "desglose_maquinaria": labores,
                "desglose_riego": {
                    "tipo_riego": tipo_riego,
                    "emisiones_agua": em_agua,
                    "emisiones_energia": em_energia,
                    "energia_actividades": energia_actividades
                },
                "desglose_residuos": detalle_residuos
            })
            emisiones_ciclos.append((i+1, em_ciclo, produccion))

            total_fert += em_fert_total
            total_agroq += em_agroq
            total_riego += em_agua + em_energia
            total_maq += em_maq
            total_res += em_residuos

            st.info(f"Emisiones en ciclo {i+1}: {em_ciclo:.2f} kg CO₂e/ha·ciclo")

        if n_ciclos > 1:
            st.markdown("### Comparación de emisiones entre ciclos")
            for ciclo, em, prod in emisiones_ciclos:
                st.write(f"Ciclo {ciclo}: {em:.2f} kg CO₂e/ha·ciclo, Producción: {prod:.2f} kg/ha·ciclo")

        emisiones_fuentes["Fertilizantes"] = total_fert
        emisiones_fuentes["Agroquímicos"] = total_agroq
        emisiones_fuentes["Riego"] = total_riego
        emisiones_fuentes["Maquinaria"] = total_maq
        emisiones_fuentes["Residuos"] = total_res

        emisiones_etapas["Anual"] = em_total
        produccion_etapas["Anual"] = prod_total
        emisiones_fuente_etapa["Anual"] = {
            "Fertilizantes": emisiones_fuentes["Fertilizantes"],
            "Agroquímicos": emisiones_fuentes["Agroquímicos"],
            "Riego": emisiones_fuentes["Riego"],
            "Maquinaria": emisiones_fuentes["Maquinaria"],
            "Residuos": emisiones_fuentes["Residuos"]
        }

    st.session_state["emisiones_ciclos"] = emisiones_ciclos
    st.session_state["desglose_fuentes_ciclos"] = desglose_fuentes_ciclos
    return em_total, prod_total

import locale

# Establecer el locale a español para los formatos numéricos
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES')
    except:
        locale.setlocale(locale.LC_ALL, '')

def format_num(x, decimales=6):
    try:
        if pd.isnull(x):
            return ""
        if isinstance(x, float) or isinstance(x, int):
            # Si es mayor o igual a 10, usa 2 decimales
            if abs(x) >= 10:
                return locale.format_string("%.2f", x, grouping=True)
            # Si es menor a 10, muestra hasta 6 decimales pero sin ceros innecesarios
            # Usar locale.format_string para respetar el separador decimal
            # Elimina ceros innecesarios después de formatear
            s = locale.format_string(f"%.{decimales}f", x, grouping=True)
            if "," in s:
                s = s.rstrip('0').rstrip(',')
            else:
                s = s.rstrip('0').rstrip('.')
            return s
        return x
    except Exception:
        return x

def format_percent(x):
    try:
        if pd.isnull(x):
            return ""
        return locale.format_string("%.1f", x, grouping=True)
    except Exception:
        return x

# -----------------------------
# Resultados Finales
# -----------------------------

def explicacion_fuente(fuente):
    if fuente == "Fertilizantes":
        return "Incluye la producción del fertilizante, emisiones directas de N₂O (por aplicación) y emisiones indirectas de N₂O (por volatilización y lixiviación)."
    elif fuente == "Riego":
        return "Corresponde al uso de agua (energía para extracción y distribución) y al tipo de energía utilizada (diésel, electricidad, etc.)."
    elif fuente == "Maquinaria":
        return "Proviene del consumo de combustibles fósiles (diésel, gasolina, etc.) en las labores agrícolas mecanizadas."
    elif fuente == "Agroquímicos":
        return "Incluye la producción y aplicación de pesticidas, fungicidas y herbicidas."
    elif fuente == "Residuos":
        return "Emisiones por gestión de residuos vegetales: quema, compostaje, incorporación al suelo, etc."
    else:
        return "Desglose no disponible para esta fuente."

import numpy as np

###################################################
# RESULTADOS PARA CULTIVO ANUAL
###################################################

def mostrar_resultados_anual(em_total, prod_total):
    import plotly.express as px
    import plotly.graph_objects as go

    st.header("Resultados Finales")
    st.info(
        "En esta sección se presentan los resultados globales y desglosados del cálculo de huella de carbono para el cultivo anual. "
        "Se muestran los resultados globales del sistema productivo, el detalle por ciclo productivo y por fuente de emisión, "
        "y finalmente el desglose interno de cada fuente. Todas las tablas muestran emisiones en kg CO₂e/ha·año y kg CO₂e/kg fruta. "
        "Todos los gráficos muestran emisiones en kg CO₂e/ha·año."
    )

    # --- RECONSTRUCCIÓN CORRECTA DE TOTALES GLOBALES DESDE EL DESGLOSE ---
    fuentes = ["Fertilizantes", "Agroquímicos", "Riego", "Maquinaria", "Residuos"]
    desglose_fuentes_ciclos = st.session_state.get("desglose_fuentes_ciclos", [])
    emisiones_fuentes_reales = {f: 0 for f in fuentes}
    for ciclo in desglose_fuentes_ciclos:
        for f in fuentes:
            emisiones_fuentes_reales[f] += ciclo.get(f, 0)
    # Actualiza los acumuladores globales
    for f in fuentes:
        emisiones_fuentes[f] = emisiones_fuentes_reales[f]
    em_total = sum(emisiones_fuentes_reales.values())
    # Si hay producción total, recalcúlala desde los ciclos
    emisiones_ciclos = st.session_state.get("emisiones_ciclos", [])
    prod_total = sum([c[2] for c in emisiones_ciclos]) if emisiones_ciclos else prod_total

    # --- Resultados globales ---
    st.markdown("#### Resultados globales")
    st.metric("Total emisiones estimadas", format_num(em_total, 2) + " kg CO₂e/ha·año")
    if prod_total > 0:
        st.metric("Emisiones por kg de fruta", format_num(em_total / prod_total, 3) + " kg CO₂e/kg fruta")
    else:
        st.warning("No se ha ingresado producción total. No es posible calcular emisiones por kg de fruta.")

    # --- Gráficos globales de fuentes ---
    valores_fuentes = [emisiones_fuentes.get(f, 0) for f in fuentes]
    total_fuentes = sum(valores_fuentes)
    st.markdown("#### % de contribución de cada fuente (global, kg CO₂e/ha·año)")
    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(
            x=fuentes,
            y=valores_fuentes,
            labels={"x": "Fuente", "y": "Emisiones (kg CO₂e/ha·año)"},
            color=fuentes,
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Emisiones por fuente en el año",
        )
        y_max = max(valores_fuentes) if valores_fuentes else 1
        textos = [format_num(v) for v in valores_fuentes]
        fig_bar.add_trace(go.Scatter(
            x=fuentes,
            y=valores_fuentes,
            text=textos,
            mode="text",
            textposition="top center",
            showlegend=False
        ))
        fig_bar.update_layout(showlegend=False, height=400)
        fig_bar.update_yaxes(range=[0, y_max * 1.15])
        st.plotly_chart(fig_bar, use_container_width=True, key=get_unique_key())
    with col2:
        if total_fuentes > 0:
            fig_pie = px.pie(
                names=fuentes,
                values=valores_fuentes,
                title="% de contribución de cada fuente",
                color=fuentes,
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.3
            )
            fig_pie.update_traces(textinfo='percent+label')
        else:
            fig_pie = px.pie(names=["Sin datos"], values=[1], color_discrete_sequence=["#cccccc"])
        fig_pie.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_pie, use_container_width=True, key=get_unique_key())

    st.markdown("---")

    # --- Resultados por ciclo ---
    if emisiones_ciclos:
        st.markdown("#### Emisiones por ciclo productivo")
        df_ciclos = pd.DataFrame(emisiones_ciclos, columns=[
            "Ciclo",
            "Emisiones (kg CO₂e/ha·ciclo)",
            "Producción (kg/ha·ciclo)"
        ])
        df_ciclos["Nombre ciclo"] = ["Ciclo " + str(c) for c in df_ciclos["Ciclo"]]
        df_ciclos["Emisiones (kg CO₂e/kg fruta·ciclo)"] = df_ciclos.apply(
            lambda row: row["Emisiones (kg CO₂e/ha·ciclo)"] / row["Producción (kg/ha·ciclo)"] if row["Producción (kg/ha·ciclo)"] > 0 else None,
            axis=1
        )
        total_emisiones_ciclos = df_ciclos["Emisiones (kg CO₂e/ha·ciclo)"].sum()
        if total_emisiones_ciclos > 0:
            df_ciclos["% contribución"] = df_ciclos["Emisiones (kg CO₂e/ha·ciclo)"] / total_emisiones_ciclos * 100
        else:
            df_ciclos["% contribución"] = 0

        st.markdown("**Tabla: Emisiones y producción por ciclo**")
        st.dataframe(
            df_ciclos[[
                "Nombre ciclo",
                "Emisiones (kg CO₂e/ha·ciclo)",
                "Producción (kg/ha·ciclo)",
                "Emisiones (kg CO₂e/kg fruta·ciclo)",
                "% contribución"
            ]].style.format({
                "Emisiones (kg CO₂e/ha·ciclo)": format_num,
                "Producción (kg/ha·ciclo)": format_num,
                "Emisiones (kg CO₂e/kg fruta·ciclo)": lambda x: format_num(x, 3),
                "% contribución": format_percent
            }),
            hide_index=True
        )
        st.caption("Unidades: kg CO₂e/ha·ciclo, kg/ha·ciclo, kg CO₂e/kg fruta·ciclo, % sobre el total anual.")

        # Gráfico de barras por ciclo (kg CO₂e/ha)
        st.markdown("##### Gráfico: Emisiones por ciclo (kg CO₂e/ha·ciclo)")
        y_max_ciclo = df_ciclos["Emisiones (kg CO₂e/ha·ciclo)"].max() if not df_ciclos.empty else 1
        textos_ciclo = [format_num(v) for v in df_ciclos["Emisiones (kg CO₂e/ha·ciclo)"]]
        fig_ciclo = px.bar(
            df_ciclos,
            x="Nombre ciclo",
            y="Emisiones (kg CO₂e/ha·ciclo)",
            color="Nombre ciclo",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={"Emisiones (kg CO₂e/ha·ciclo)": "Emisiones (kg CO₂e/ha·ciclo)"},
            title="Emisiones por ciclo"
        )
        fig_ciclo.add_trace(go.Scatter(
            x=df_ciclos["Nombre ciclo"],
            y=df_ciclos["Emisiones (kg CO₂e/ha·ciclo)"],
            text=textos_ciclo,
            mode="text",
            textposition="top center",
            showlegend=False
        ))
        fig_ciclo.update_layout(showlegend=False, height=400)
        fig_ciclo.update_yaxes(range=[0, y_max_ciclo * 1.15])
        st.plotly_chart(fig_ciclo, use_container_width=True, key=get_unique_key())

    st.markdown("---")

    # --- Resultados por fuente en cada ciclo ---
    desglose_fuentes_ciclos = st.session_state.get("desglose_fuentes_ciclos", [])
    if desglose_fuentes_ciclos:
        st.markdown("#### Emisiones por fuente en cada ciclo")
        fuentes = ["Fertilizantes", "Agroquímicos", "Riego", "Maquinaria", "Residuos"]
        for idx, ciclo in enumerate(desglose_fuentes_ciclos):
            st.markdown(f"##### {'Ciclo ' + str(ciclo['Ciclo']) if 'Ciclo' in ciclo else 'Ciclo típico'}")
            prod = ciclo.get("Producción", None)
            if prod is None:
                prod = None
                for c in emisiones_ciclos:
                    if c[0] == ciclo.get("Ciclo"):
                        prod = c[2]
                        break
            total_fuente = sum([ciclo[f] for f in fuentes])
            df_fuentes_ciclo = pd.DataFrame({
                "Fuente": fuentes,
                "Emisiones (kg CO₂e/ha·ciclo)": [ciclo[f] for f in fuentes]
            })
            if prod and prod > 0:
                df_fuentes_ciclo["Emisiones (kg CO₂e/kg fruta·ciclo)"] = df_fuentes_ciclo["Emisiones (kg CO₂e/ha·ciclo)"] / prod
            else:
                df_fuentes_ciclo["Emisiones (kg CO₂e/kg fruta·ciclo)"] = None
            if total_fuente > 0:
                df_fuentes_ciclo["% contribución"] = df_fuentes_ciclo["Emisiones (kg CO₂e/ha·ciclo)"] / total_fuente * 100
            else:
                df_fuentes_ciclo["% contribución"] = 0

            st.dataframe(df_fuentes_ciclo.style.format({
                "Emisiones (kg CO₂e/ha·ciclo)": format_num,
                "Emisiones (kg CO₂e/kg fruta·ciclo)": lambda x: format_num(x, 3),
                "% contribución": format_percent
            }), hide_index=True)
            st.caption("Unidades: kg CO₂e/ha·ciclo, kg CO₂e/kg fruta·ciclo, % sobre el total del ciclo.")

            # Gráfico de barras por fuente en el ciclo (kg CO₂e/ha)
            st.markdown("##### Gráfico: Emisiones por fuente en el ciclo (kg CO₂e/ha·ciclo)")
            y_max_fuente = df_fuentes_ciclo["Emisiones (kg CO₂e/ha·ciclo)"].max() if not df_fuentes_ciclo.empty else 1
            textos_fuente = [format_num(v) for v in df_fuentes_ciclo["Emisiones (kg CO₂e/ha·ciclo)"]]
            fig_fuente = px.bar(
                df_fuentes_ciclo,
                x="Fuente",
                y="Emisiones (kg CO₂e/ha·ciclo)",
                color="Fuente",
                color_discrete_sequence=px.colors.qualitative.Set2,
                title="Emisiones por fuente en el ciclo"
            )
            fig_fuente.add_trace(go.Scatter(
                x=df_fuentes_ciclo["Fuente"],
                y=df_fuentes_ciclo["Emisiones (kg CO₂e/ha·ciclo)"],
                text=textos_fuente,
                mode="text",
                textposition="top center",
                showlegend=False
            ))
            fig_fuente.update_layout(showlegend=False, height=400)
            fig_fuente.update_yaxes(range=[0, y_max_fuente * 1.15])
            st.plotly_chart(fig_fuente, use_container_width=True, key=get_unique_key())

            # --- Desglose interno de cada fuente ---
            st.markdown("###### Desglose interno de cada fuente")
            fuentes_ordenadas = sorted(
                df_fuentes_ciclo["Fuente"],
                key=lambda f: ciclo.get(f, 0),
                reverse=True
            )
            for fuente in fuentes_ordenadas:
                valor = ciclo[fuente]
                if valor > 0:
                    st.markdown(f"**{fuente}**")
                    st.info(f"Explicación: {explicacion_fuente(fuente)}")
                    # --- FERTILIZANTES ---
                    if fuente == "Fertilizantes" and ciclo.get("desglose_fertilizantes"):
                        df_fert = pd.DataFrame(ciclo["desglose_fertilizantes"])
                        if not df_fert.empty:
                            df_fert["Tipo fertilizante"] = df_fert["tipo"].apply(
                                lambda x: "Orgánico" if "org" in str(x).lower() or "estiércol" in str(x).lower() or "guano" in str(x).lower() else "Inorgánico"
                            )
                            total_fert = df_fert["total"].sum()
                            df_fert["% contribución"] = df_fert["total"] / total_fert * 100
                            if prod and prod > 0:
                                df_fert["Emisiones (kg CO₂e/kg fruta·ciclo)"] = df_fert["total"] / prod
                            else:
                                df_fert["Emisiones (kg CO₂e/kg fruta·ciclo)"] = None
                            st.markdown("**Tabla: Desglose de fertilizantes (orgánicos e inorgánicos)**")
                            st.dataframe(
                                df_fert[[
                                    "Tipo fertilizante", "tipo", "cantidad", "emision_produccion",
                                    "emision_n2o_directa", "emision_n2o_ind_volatilizacion", "emision_n2o_ind_lixiviacion",
                                    "emision_n2o_indirecta", "total", "Emisiones (kg CO₂e/kg fruta·ciclo)", "% contribución"
                                ]].style.format({
                                    "cantidad": format_num,
                                    "emision_produccion": format_num,
                                    "emision_n2o_directa": format_num,
                                    "emision_n2o_ind_volatilizacion": format_num,
                                    "emision_n2o_ind_lixiviacion": format_num,
                                    "emision_n2o_indirecta": format_num,
                                    "total": format_num,
                                    "Emisiones (kg CO₂e/kg fruta·ciclo)": lambda x: format_num(x, 3),
                                    "% contribución": format_percent
                                }),
                                hide_index=True
                            )
                            st.caption("Unidades: cantidad (kg/ha·ciclo), emisiones (kg CO₂e/ha), % sobre el total de fertilizantes. N₂O indirecta se desglosa en volatilización y lixiviación.")
                            # --- Gráficos de barras apiladas por tipo de emisión (orgánico e inorgánico por separado) ---
                            for tipo_cat in ["Orgánico", "Inorgánico"]:
                                df_tipo = df_fert[df_fert["Tipo fertilizante"] == tipo_cat]
                                if not df_tipo.empty:
                                    st.markdown(f"**Gráfico: Emisiones por fertilizante {tipo_cat.lower()} y tipo de emisión (kg CO₂e/ha·ciclo)**")
                                    labels = df_tipo["tipo"]
                                    em_prod = df_tipo["emision_produccion"].values
                                    em_n2o_dir = df_tipo["emision_n2o_directa"].values
                                    em_n2o_ind_vol = df_tipo["emision_n2o_ind_volatilizacion"].values
                                    em_n2o_ind_lix = df_tipo["emision_n2o_ind_lixiviacion"].values
                                    fig_fert = go.Figure()
                                    fig_fert.add_bar(x=labels, y=em_prod, name="Producción")
                                    fig_fert.add_bar(x=labels, y=em_n2o_dir, name="N₂O directa")
                                    fig_fert.add_bar(x=labels, y=em_n2o_ind_vol, name="N₂O indirecta (volatilización)")
                                    fig_fert.add_bar(x=labels, y=em_n2o_ind_lix, name="N₂O indirecta (lixiviación)")
                                    totales = em_prod + em_n2o_dir + em_n2o_ind_vol + em_n2o_ind_lix
                                    textos_tot = [format_num(v) for v in totales]
                                    fig_fert.add_trace(go.Scatter(
                                        x=labels,
                                        y=totales,
                                        text=textos_tot,
                                        mode="text",
                                        textposition="top center",
                                        showlegend=False
                                    ))
                                    fig_fert.update_layout(
                                        barmode='stack',
                                        yaxis_title="Emisiones (kg CO₂e/ha·ciclo)",
                                        title=f"Emisiones por fertilizante {tipo_cat.lower()} y tipo de emisión",
                                        height=400
                                    )
                                    fig_fert.update_yaxes(range=[0, max(totales) * 1.15 if len(totales) > 0 else 1])
                                    st.plotly_chart(fig_fert, use_container_width=True, key=get_unique_key())
                    # --- AGROQUÍMICOS ---
                    elif fuente == "Agroquímicos" and ciclo.get("desglose_agroquimicos"):
                        df_agro = pd.DataFrame(ciclo["desglose_agroquimicos"])
                        if not df_agro.empty:
                            total_agro = df_agro["emisiones"].sum()
                            df_agro["% contribución"] = df_agro["emisiones"] / total_agro * 100
                            if prod and prod > 0:
                                df_agro["Emisiones (kg CO₂e/kg fruta·ciclo)"] = df_agro["emisiones"] / prod
                            else:
                                df_agro["Emisiones (kg CO₂e/kg fruta·ciclo)"] = None
                            st.markdown("**Tabla: Desglose de agroquímicos**")
                            st.dataframe(df_agro[["categoria", "tipo", "cantidad_ia", "emisiones", "Emisiones (kg CO₂e/kg fruta·ciclo)", "% contribución"]].style.format({
                                "cantidad_ia": format_num,
                                "emisiones": format_num,
                                "Emisiones (kg CO₂e/kg fruta·ciclo)": lambda x: format_num(x, 3),
                                "% contribución": format_percent
                            }), hide_index=True)
                            st.caption("Unidades: cantidad ingrediente activo (kg/ha·ciclo), emisiones (kg CO₂e/ha·ciclo y kg CO₂e/kg fruta·ciclo), % sobre el total de agroquímicos.")

                            # --- Gráfico de barras apiladas por categoría y tipo (kg CO₂e/ha) ---
                            st.markdown("**Gráfico: Emisiones de agroquímicos por categoría y tipo (kg CO₂e/ha·ciclo)**")
                            df_group = df_agro.groupby(["categoria", "tipo"]).agg({"emisiones": "sum"}).reset_index()
                            categorias = df_group["categoria"].unique()
                            tipos = df_group["tipo"].unique()
                            fig_agro = go.Figure()
                            for tipo in tipos:
                                vals = []
                                for cat in categorias:
                                    row = df_group[(df_group["categoria"] == cat) & (df_group["tipo"] == tipo)]
                                    vals.append(row["emisiones"].values[0] if not row.empty else 0)
                                fig_agro.add_bar(x=categorias, y=vals, name=tipo)
                            totales = df_group.groupby("categoria")["emisiones"].sum().reindex(categorias).values
                            textos_tot = [format_num(v) for v in totales]
                            fig_agro.add_trace(go.Scatter(
                                x=categorias,
                                y=totales,
                                text=textos_tot,
                                mode="text",
                                textposition="top center",
                                showlegend=False
                            ))
                            fig_agro.update_layout(
                                barmode='stack',
                                yaxis_title="Emisiones (kg CO₂e/ha·ciclo)",
                                title="Emisiones de agroquímicos por categoría y tipo",
                                height=400
                            )
                            y_max_agro = max(totales) if len(totales) > 0 else 1
                            fig_agro.update_yaxes(range=[0, y_max_agro * 1.15])
                            st.plotly_chart(fig_agro, use_container_width=True, key=get_unique_key())

                            # --- Gráfico de torta por categoría (kg CO₂e/ha) ---
                            st.markdown("**Gráfico: % de contribución de cada categoría de agroquímico (kg CO₂e/ha·ciclo)**")
                            df_cat = df_agro.groupby("categoria").agg({"emisiones": "sum"}).reset_index()
                            fig_pie_agro = px.pie(
                                df_cat,
                                names="categoria",
                                values="emisiones",
                                title="Contribución de cada categoría de agroquímico",
                                color_discrete_sequence=px.colors.qualitative.Set2,
                                hole=0.3
                            )
                            fig_pie_agro.update_traces(textinfo='percent+label')
                            fig_pie_agro.update_layout(showlegend=True, height=400)
                            st.plotly_chart(fig_pie_agro, use_container_width=True, key=get_unique_key())
                    # --- MAQUINARIA ---
                    elif fuente == "Maquinaria" and ciclo.get("desglose_maquinaria"):
                        df_maq = pd.DataFrame(ciclo["desglose_maquinaria"])
                        if not df_maq.empty:
                            total_maq = df_maq["emisiones"].sum()
                            df_maq["% contribución"] = df_maq["emisiones"] / total_maq * 100
                            if prod and prod > 0:
                                df_maq["Emisiones (kg CO₂e/kg fruta·ciclo)"] = df_maq["emisiones"] / prod
                            else:
                                df_maq["Emisiones (kg CO₂e/kg fruta·ciclo)"] = None
                            st.markdown("**Tabla: Desglose de maquinaria**")
                            st.dataframe(df_maq[["nombre_labor", "tipo_maquinaria", "tipo_combustible", "litros", "emisiones", "Emisiones (kg CO₂e/kg fruta·ciclo)", "% contribución"]].style.format({
                                "litros": format_num,
                                "emisiones": format_num,
                                "Emisiones (kg CO₂e/kg fruta·ciclo)": lambda x: format_num(x, 3),
                                "% contribución": format_percent
                            }), hide_index=True)
                            st.caption("Unidades: litros (L/ha·ciclo), emisiones (kg CO₂e/ha·ciclo y kg CO₂e/kg fruta·ciclo), % sobre el total de maquinaria.")

                            # --- Gráfico de torta: emisiones por labor (kg CO₂e/ha) ---
                            st.markdown("**Gráfico: % de contribución de cada labor (torta, kg CO₂e/ha·ciclo)**")
                            df_labor = df_maq.groupby("nombre_labor")["emisiones"].sum().reset_index()
                            fig_pie_labor = px.pie(
                                df_labor,
                                names="nombre_labor",
                                values="emisiones",
                                title="Contribución de cada labor al total de emisiones de maquinaria",
                                color_discrete_sequence=px.colors.qualitative.Set2,
                                hole=0.3
                            )
                            fig_pie_labor.update_traces(textinfo='percent+label')
                            fig_pie_labor.update_layout(showlegend=True, height=400)
                            st.plotly_chart(fig_pie_labor, use_container_width=True, key=get_unique_key())

                            # --- Gráfico de torta: emisiones por maquinaria dentro de cada labor (kg CO₂e/ha) ---
                            labores_unicas = df_maq["nombre_labor"].unique()
                            for labor in labores_unicas:
                                df_labor_maq = df_maq[df_maq["nombre_labor"] == labor]
                                if len(df_labor_maq) > 1:
                                    st.markdown(f"**Gráfico: % de contribución de cada maquinaria en la labor '{labor}' (torta, kg CO₂e/ha·ciclo)**")
                                    fig_pie_maq = px.pie(
                                        df_labor_maq,
                                        names="tipo_maquinaria",
                                        values="emisiones",
                                        title=f"Contribución de cada maquinaria en la labor '{labor}'",
                                        color_discrete_sequence=px.colors.qualitative.Pastel,
                                        hole=0.3
                                    )
                                    fig_pie_maq.update_traces(textinfo='percent+label')
                                    fig_pie_maq.update_layout(showlegend=True, height=400)
                                    st.plotly_chart(fig_pie_maq, use_container_width=True, key=get_unique_key())

                            # --- Gráfico de barras apiladas: labor (X), emisiones (Y), apilado por maquinaria (kg CO₂e/ha) ---
                            st.markdown("**Gráfico: Emisiones por labor y tipo de maquinaria (barras apiladas, kg CO₂e/ha·ciclo)**")
                            df_maq_grouped = df_maq.groupby(["nombre_labor", "tipo_maquinaria"]).agg({"emisiones": "sum"}).reset_index()
                            labores = df_maq_grouped["nombre_labor"].unique()
                            tipos_maq = df_maq_grouped["tipo_maquinaria"].unique()
                            fig_maq = go.Figure()
                            for maq in tipos_maq:
                                vals = []
                                for l in labores:
                                    row = df_maq_grouped[(df_maq_grouped["nombre_labor"] == l) & (df_maq_grouped["tipo_maquinaria"] == maq)]
                                    vals.append(row["emisiones"].values[0] if not row.empty else 0)
                                fig_maq.add_bar(
                                    x=labores,
                                    y=vals,
                                    name=maq
                                )
                            totales = df_maq_grouped.groupby("nombre_labor")["emisiones"].sum().reindex(labores).values
                            textos_tot = [format_num(v) for v in totales]
                            fig_maq.add_trace(go.Scatter(
                                x=labores,
                                y=totales,
                                text=textos_tot,
                                mode="text",
                                textposition="top center",
                                showlegend=False
                            ))
                            y_max_maq = max(totales) if len(totales) > 0 else 1
                            fig_maq.update_layout(
                                barmode='stack',
                                yaxis_title="Emisiones (kg CO₂e/ha·ciclo)",
                                title="Emisiones por labor y tipo de maquinaria",
                                height=400
                            )
                            fig_maq.update_yaxes(range=[0, y_max_maq * 1.15])
                            st.plotly_chart(fig_maq, use_container_width=True, key=get_unique_key())
                    # --- RIEGO ---
                    elif fuente == "Riego" and ciclo.get("desglose_riego"):
                        dr = ciclo["desglose_riego"]
                        energia_actividades = dr.get("energia_actividades", [])
                        actividades = []
                        for ea in energia_actividades:
                            actividades.append({
                                "Actividad": ea.get("actividad", ""),
                                "Tipo actividad": ea.get("tipo_actividad", ""),
                                "Consumo agua (m³)": ea.get("agua_total_m3", 0),
                                "Emisiones agua (kg CO₂e)": ea.get("emisiones_agua", 0),
                                "Consumo energía": ea.get("consumo_energia", 0),
                                "Tipo energía": ea.get("tipo_energia", ""),
                                "Emisiones energía (kg CO₂e)": ea.get("emisiones_energia", 0),
                            })
                        if actividades:
                            df_riego = pd.DataFrame(actividades)
                            df_riego["Emisiones totales (kg CO₂e)"] = df_riego["Emisiones agua (kg CO₂e)"] + df_riego["Emisiones energía (kg CO₂e)"]
                            if prod and prod > 0:
                                df_riego["Emisiones totales (kg CO₂e/kg fruta)"] = df_riego["Emisiones totales (kg CO₂e)"] / prod
                            else:
                                df_riego["Emisiones totales (kg CO₂e/kg fruta)"] = None
                            total_riego = df_riego["Emisiones totales (kg CO₂e)"].sum()
                            if total_riego > 0:
                                df_riego["% contribución"] = df_riego["Emisiones totales (kg CO₂e)"] / total_riego * 100
                            else:
                                df_riego["% contribución"] = 0
                            st.markdown("**Tabla: Desglose de riego por actividad (agua y energía apilados)**")
                            st.dataframe(df_riego[[
                                "Actividad", "Tipo actividad", "Consumo agua (m³)", "Emisiones agua (kg CO₂e)",
                                "Consumo energía", "Tipo energía", "Emisiones energía (kg CO₂e)",
                                "Emisiones totales (kg CO₂e)", "Emisiones totales (kg CO₂e/kg fruta)", "% contribución"
                            ]].style.format({
                                "Consumo agua (m³)": format_num,
                                "Emisiones agua (kg CO₂e)": format_num,
                                "Consumo energía": format_num,
                                "Emisiones energía (kg CO₂e)": format_num,
                                "Emisiones totales (kg CO₂e)": format_num,
                                "Emisiones totales (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
                                "% contribución": format_percent
                            }), hide_index=True)
                            st.caption("Unidades: agua (m³/ha), energía (kWh o litros/ha), emisiones (kg CO₂e/ha y kg CO₂e/kg fruta), % sobre el total de riego.")
                            # Gráfico de barras apiladas por actividad (agua + energía)
                            st.markdown("**Gráfico: Emisiones de riego por actividad (barras apiladas agua + energía, kg CO₂e/ha·ciclo)**")
                            fig_riego = go.Figure()
                            fig_riego.add_bar(
                                x=df_riego["Actividad"],
                                y=df_riego["Emisiones agua (kg CO₂e)"],
                                name="Agua",
                                marker_color="#4fc3f7"
                            )
                            fig_riego.add_bar(
                                x=df_riego["Actividad"],
                                y=df_riego["Emisiones energía (kg CO₂e)"],
                                name="Energía",
                                marker_color="#0288d1"
                            )
                            totales = df_riego["Emisiones totales (kg CO₂e)"].values
                            textos_tot = [format_num(v) for v in totales]
                            fig_riego.add_trace(go.Scatter(
                                x=df_riego["Actividad"],
                                y=totales,
                                text=textos_tot,
                                mode="text",
                                textposition="top center",
                                showlegend=False
                            ))
                            y_max_riego = max(totales) if len(totales) > 0 else 1
                            fig_riego.update_layout(
                                barmode='stack',
                                yaxis_title="Emisiones (kg CO₂e/ha)",
                                title="Emisiones de riego por actividad (agua + energía)",
                                height=400
                            )
                            fig_riego.update_yaxes(range=[0, y_max_riego * 1.15])
                            st.plotly_chart(fig_riego, use_container_width=True, key=get_unique_key())
                        else:
                            st.info("No se ingresaron actividades de riego para este ciclo.")
                    # --- RESIDUOS ---
                    elif fuente == "Residuos" and ciclo.get("desglose_residuos"):
                        dr = ciclo["desglose_residuos"]
                        if isinstance(dr, dict) and dr:
                            df_res = pd.DataFrame([
                                {
                                    "Gestión": k,
                                    "Biomasa (kg/ha·ciclo)": v.get("biomasa", 0),
                                    "Emisiones (kg CO₂e/ha·ciclo)": v.get("emisiones", 0),
                                    "Emisiones (kg CO₂e/kg fruta·ciclo)": v.get("emisiones", 0) / prod if prod and prod > 0 else None
                                }
                                for k, v in dr.items()
                            ])
                            total_res = df_res["Emisiones (kg CO₂e/ha·ciclo)"].sum()
                            df_res["% contribución"] = df_res["Emisiones (kg CO₂e/ha·ciclo)"] / total_res * 100
                            st.markdown("**Tabla: Desglose de gestión de residuos vegetales**")
                            st.dataframe(df_res[[
                                "Gestión", "Biomasa (kg/ha·ciclo)", "Emisiones (kg CO₂e/ha·ciclo)", "Emisiones (kg CO₂e/kg fruta·ciclo)", "% contribución"
                            ]].style.format({
                                "Biomasa (kg/ha·ciclo)": format_num,
                                "Emisiones (kg CO₂e/ha·ciclo)": format_num,
                                "Emisiones (kg CO₂e/kg fruta·ciclo)": lambda x: format_num(x, 3),
                                "% contribución": format_percent
                            }), hide_index=True)
                            st.caption("Unidades: biomasa (kg/ha·ciclo), emisiones (kg CO₂e/ha·ciclo y kg CO₂e/kg fruta·ciclo), % sobre el total de residuos.")
                            textos_res = [format_num(v) for v in df_res["Emisiones (kg CO₂e/ha·ciclo)"]]
                            fig_res = px.bar(
                                df_res,
                                x="Gestión",
                                y="Emisiones (kg CO₂e/ha·ciclo)",
                                color="Gestión",
                                color_discrete_sequence=px.colors.qualitative.Pastel,
                                title="Emisiones por gestión de residuos"
                            )
                            fig_res.add_trace(go.Scatter(
                                x=df_res["Gestión"],
                                y=df_res["Emisiones (kg CO₂e/ha·ciclo)"],
                                text=textos_res,
                                mode="text",
                                textposition="top center",
                                showlegend=False
                            ))
                            fig_res.update_layout(showlegend=False, height=400)
                            fig_res.update_yaxes(range=[0, max(df_res["Emisiones (kg CO₂e/ha·ciclo)"]) * 1.15 if not df_res.empty else 1])
                            st.plotly_chart(fig_res, use_container_width=True, key=get_unique_key())
            st.markdown("---")

    # --- Resumen ejecutivo ---
    st.markdown("#### Resumen ejecutivo")
    st.success(
        "📝 **Resumen ejecutivo:**\n\n"
        "El resumen ejecutivo presenta los resultados clave del cálculo de huella de carbono, útiles para reportes, certificaciones o toma de decisiones.\n\n"
        "Las emisiones totales estimadas para el sistema productivo corresponden a la suma de todas las fuentes y ciclos considerados, expresadas en **kg CO₂e/ha·año**. "
        "Este valor representa las emisiones acumuladas a lo largo de todos los ciclos productivos del año agrícola.\n\n"
        f"**Total emisiones estimadas:** {format_num(em_total, 2)} kg CO₂e/ha·año"
        + (
            f"\n\n**Emisiones por kg de fruta:** {format_num(em_total/prod_total, 3)} kg CO₂e/kg fruta. "
            "Este indicador permite comparar la huella de carbono entre diferentes sistemas o productos, ya que relaciona las emisiones totales con la producción obtenida en el año."
            if prod_total > 0 else "\n\nNo se ha ingresado producción total. No es posible calcular emisiones por kg de fruta."
        )
    )

    st.markdown("---")
    st.markdown("#### Parámetros de cálculo")
    st.write(f"Potenciales de calentamiento global (GWP) usados: {GWP}")
    st.write("Factores de emisión y fórmulas según IPCC 2006 y valores configurables al inicio del código.")

    # Guardar resultados globales y desgloses en session_state para exportación futura
    st.session_state["resultados_globales"] = {
        "tipo": "anual",
        "em_total": em_total,
        "prod_total": prod_total,
        "emisiones_ciclos": st.session_state.get("emisiones_ciclos", []),
        "desglose_fuentes_ciclos": st.session_state.get("desglose_fuentes_ciclos", []),
        "detalle_residuos": st.session_state.get("detalle_residuos", []),
        "emisiones_fuentes": emisiones_fuentes.copy(),
        "emisiones_etapas": emisiones_etapas.copy(),
        "produccion_etapas": produccion_etapas.copy(),
        "emisiones_fuente_etapa": emisiones_fuente_etapa.copy()
    }

###################################################
# RESULTADOS PARA CULTIVO PERENNE
###################################################

def mostrar_resultados_perenne(em_total, prod_total):
    import plotly.express as px
    import plotly.graph_objects as go

    st.header("Resultados Finales")
    st.info(
        "En esta sección se presentan los resultados globales y desglosados del cálculo de huella de carbono para el cultivo perenne. "
        "Se muestran los resultados globales del sistema productivo, el detalle por etapa y por fuente de emisión, "
        "y finalmente el desglose interno de cada fuente. Todas las tablas muestran emisiones en kg CO₂e/ha y kg CO₂e/kg fruta. "
        "Todos los gráficos muestran emisiones en kg CO₂e/ha."
    )

    def limpiar_nombre(etapa):
        return etapa.replace("3.1 ", "").replace("3.2 ", "").replace("3.3 ", "").replace("3. ", "").strip()

    # --- RECONSTRUCCIÓN CORRECTA DE TOTALES GLOBALES DESDE EL DESGLOSE ---
    fuentes = ["Fertilizantes", "Agroquímicos", "Riego", "Maquinaria", "Residuos"]
    etapas_ordenadas = []
    for clave in emisiones_etapas:
        if clave.lower().startswith("implantación"):
            etapas_ordenadas.append(clave)
    for clave in emisiones_etapas:
        if "crecimiento sin producción" in clave.lower():
            etapas_ordenadas.append(clave)
    for clave in emisiones_etapas:
        if clave not in etapas_ordenadas:
            etapas_ordenadas.append(clave)

    # Sumar emisiones por fuente a partir de los desgloses de cada etapa
    emisiones_fuentes_reales = {f: 0 for f in fuentes}
    for etapa in etapas_ordenadas:
        fuente_etapa = emisiones_fuente_etapa.get(etapa, {})
        for f in fuentes:
            emisiones_fuentes_reales[f] += fuente_etapa.get(f, 0)
    # Actualiza los acumuladores globales
    for f in fuentes:
        emisiones_fuentes[f] = emisiones_fuentes_reales[f]
    em_total = sum(emisiones_fuentes_reales.values())
    prod_total = sum([produccion_etapas.get(et, 0) for et in etapas_ordenadas])

    # --- Resultados globales ---
    st.markdown("#### Resultados globales")
    st.metric("Total emisiones estimadas", format_num(em_total, 2) + " kg CO₂e/ha")
    if prod_total > 0:
        st.metric("Emisiones por kg de fruta", format_num(em_total / prod_total, 3) + " kg CO₂e/kg fruta")
    else:
        st.warning("No se ha ingresado producción total. No es posible calcular emisiones por kg de fruta.")
    
    st.markdown("---")

    # --- Gráfico de evolución temporal de emisiones año a año ---
    emisiones_anuales = st.session_state.get("emisiones_anuales", [])
    if emisiones_anuales:
        st.markdown("#### Evolución temporal de emisiones año a año")
        df_evol = pd.DataFrame(emisiones_anuales, columns=["Año", "Emisiones (kg CO₂e/ha)", "Producción (kg/ha)", "Etapa"])
        df_evol["Emisiones_texto"] = df_evol["Emisiones (kg CO₂e/ha)"].apply(format_num)
        fig_evol = px.bar(
            df_evol,
            x="Año",
            y="Emisiones (kg CO₂e/ha)",
            color="Etapa",
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Evolución de emisiones año a año"
        )
        fig_evol.add_trace(go.Scatter(
            x=df_evol["Año"],
            y=df_evol["Emisiones (kg CO₂e/ha)"],
            text=df_evol["Emisiones_texto"],
            mode="text",
            textposition="top center",
            showlegend=False
        ))
        fig_evol.update_layout(showlegend=True, height=400)
        st.plotly_chart(fig_evol, use_container_width=True, key=get_unique_key())

    st.markdown("---")

    # --- Resultados por etapa ---
    if emisiones_etapas:
        st.markdown("#### Emisiones por etapa")
        df_etapas = pd.DataFrame({
            "Etapa": [limpiar_nombre(et) for et in etapas_ordenadas],
            "Clave": etapas_ordenadas,
            "Emisiones (kg CO₂e/ha)": [emisiones_etapas[et] for et in etapas_ordenadas],
            "Producción (kg/ha)": [produccion_etapas.get(et, 0) for et in etapas_ordenadas]
        })
        df_etapas["Emisiones (kg CO₂e/kg fruta)"] = df_etapas.apply(
            lambda row: row["Emisiones (kg CO₂e/ha)"] / row["Producción (kg/ha)"] if row["Producción (kg/ha)"] > 0 else None,
            axis=1
        )
        total_emisiones_etapas = df_etapas["Emisiones (kg CO₂e/ha)"].sum()
        if total_emisiones_etapas > 0:
            df_etapas["% contribución"] = df_etapas["Emisiones (kg CO₂e/ha)"] / total_emisiones_etapas * 100
        else:
            df_etapas["% contribución"] = 0

        st.markdown("**Tabla: Emisiones y producción por etapa**")
        st.dataframe(df_etapas[["Etapa", "Emisiones (kg CO₂e/ha)", "Producción (kg/ha)", "Emisiones (kg CO₂e/kg fruta)", "% contribución"]].style.format({
            "Emisiones (kg CO₂e/ha)": format_num,
            "Producción (kg/ha)": format_num,
            "Emisiones (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
            "% contribución": format_percent
        }), hide_index=True)

        # Gráfico de barras por etapa (texto sólo en el total)
        st.markdown("##### Gráfico: Emisiones por etapa (kg CO₂e/ha)")
        y_max_etapa = df_etapas["Emisiones (kg CO₂e/ha)"].max() if not df_etapas.empty else 1
        textos_etapa = [format_num(v) for v in df_etapas["Emisiones (kg CO₂e/ha)"]]
        fig_etapa = px.bar(
            df_etapas,
            x="Etapa",
            y="Emisiones (kg CO₂e/ha)",
            color="Etapa",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="Emisiones por etapa"
        )
        fig_etapa.add_trace(go.Scatter(
            x=df_etapas["Etapa"],
            y=df_etapas["Emisiones (kg CO₂e/ha)"],
            text=textos_etapa,
            mode="text",
            textposition="top center",
            showlegend=False
        ))
        fig_etapa.update_layout(showlegend=False, height=400)
        fig_etapa.update_yaxes(range=[0, y_max_etapa * 1.15])
        st.plotly_chart(fig_etapa, use_container_width=True, key=get_unique_key())

    st.markdown("---")

    # --- Emisiones por fuente y etapa (tabla y barras apiladas) ---
    if emisiones_etapas and emisiones_fuentes and emisiones_fuente_etapa:
        st.markdown("#### Emisiones por fuente y etapa (tabla y barras apiladas)")
        fuentes = [f for f in emisiones_fuentes.keys() if f != "Transporte"]
        etapas = df_etapas["Clave"].tolist()
        data_fuente_etapa = {fuente: [emisiones_fuente_etapa.get(etapa, {}).get(fuente, 0) for etapa in etapas] for fuente in fuentes}
        df_fuente_etapa = pd.DataFrame(data_fuente_etapa, index=[limpiar_nombre(e) for e in etapas])
        df_fuente_etapa.insert(0, "Etapa", [limpiar_nombre(e) for e in etapas])
        df_fuente_etapa_kg = df_fuente_etapa.copy()
        for i, etapa in enumerate(etapas):
            prod = produccion_etapas.get(etapa, 0)
            if prod > 0:
                df_fuente_etapa_kg.iloc[i, 1:] = df_fuente_etapa.iloc[i, 1:] / prod
            else:
                df_fuente_etapa_kg.iloc[i, 1:] = None
        st.markdown("**Tabla: Emisiones por fuente y etapa (kg CO₂e/ha)**")
        st.dataframe(df_fuente_etapa.style.format(format_num), hide_index=True)
        st.markdown("**Tabla: Emisiones por fuente y etapa (kg CO₂e/kg fruta)**")
        st.dataframe(df_fuente_etapa_kg.style.format(lambda x: format_num(x, 3)), hide_index=True)

        # Gráfico de barras apiladas por fuente y etapa (kg CO₂e/ha) - texto sólo en el total
        st.markdown("##### Gráfico: Emisiones por fuente y etapa (barras apiladas, kg CO₂e/ha)")
        fig_fuente_etapa = go.Figure()
        for fuente in fuentes:
            fig_fuente_etapa.add_bar(
                x=df_fuente_etapa["Etapa"],
                y=df_fuente_etapa[fuente],
                name=fuente
            )
        totales = df_fuente_etapa.iloc[:, 1:].sum(axis=1).values
        textos_tot = [format_num(v) for v in totales]
        fig_fuente_etapa.add_trace(go.Scatter(
            x=df_fuente_etapa["Etapa"],
            y=totales,
            text=textos_tot,
            mode="text",
            textposition="top center",
            showlegend=False
        ))
        y_max_fte = max(totales) if len(totales) > 0 else 1
        fig_fuente_etapa.update_layout(
            barmode='stack',
            yaxis_title="Emisiones (kg CO₂e/ha)",
            title="Emisiones por fuente y etapa (barras apiladas)",
            height=400
        )
        fig_fuente_etapa.update_yaxes(range=[0, y_max_fte * 1.15])
        st.plotly_chart(fig_fuente_etapa, use_container_width=True, key=get_unique_key())

    st.markdown("---")

    # --- Desglose interno de cada fuente por etapa ---
    st.markdown("#### Desglose interno de cada fuente por etapa")
    etapas = df_etapas["Clave"].tolist()
    orden_fuentes = [f for f in emisiones_fuentes.keys() if f != "Transporte"]
    for idx, etapa in enumerate(etapas):
        nombre_etapa_limpio = limpiar_nombre(etapa)
        st.markdown(f"### Etapa: {nombre_etapa_limpio}")
        prod = produccion_etapas.get(etapa, 0)
        # ORDENAR fuentes de mayor a menor emisión en esta etapa
        fuentes_etapa = [f for f in orden_fuentes if f in emisiones_fuente_etapa.get(etapa, {})]
        fuentes_ordenadas = sorted(
            fuentes_etapa,
            key=lambda f: emisiones_fuente_etapa.get(etapa, {}).get(f, 0),
            reverse=True
        )
        for fuente in fuentes_ordenadas:
            valor = emisiones_fuente_etapa.get(etapa, {}).get(fuente, 0)
            if valor > 0:
                st.markdown(f"**{fuente}**")
                st.info(f"Explicación: {explicacion_fuente(fuente)}")
                # --- FERTILIZANTES ---
                if fuente == "Fertilizantes" and emisiones_fuente_etapa[etapa].get("desglose_fertilizantes"):
                    df_fert = pd.DataFrame(emisiones_fuente_etapa[etapa]["desglose_fertilizantes"])
                    if not df_fert.empty:
                        df_fert["Tipo fertilizante"] = df_fert["tipo"].apply(
                            lambda x: "Orgánico" if "org" in str(x).lower() or "estiércol" in str(x).lower() or "guano" in str(x).lower() else "Inorgánico"
                        )
                        total_fert = df_fert["total"].sum()
                        df_fert["% contribución"] = df_fert["total"] / total_fert * 100
                        if prod and prod > 0:
                            df_fert["Emisiones (kg CO₂e/kg fruta)"] = df_fert["total"] / prod
                        else:
                            df_fert["Emisiones (kg CO₂e/kg fruta)"] = None
                        st.markdown("**Tabla: Desglose de fertilizantes (orgánicos e inorgánicos)**")
                        st.dataframe(
                            df_fert[[
                                "Tipo fertilizante", "tipo", "cantidad", "emision_produccion",
                                "emision_n2o_directa", "emision_n2o_ind_volatilizacion", "emision_n2o_ind_lixiviacion",
                                "emision_n2o_indirecta", "total", "Emisiones (kg CO₂e/kg fruta)", "% contribución"
                            ]].style.format({
                                "cantidad": format_num,
                                "emision_produccion": format_num,
                                "emision_n2o_directa": format_num,
                                "emision_n2o_ind_volatilizacion": format_num,
                                "emision_n2o_ind_lixiviacion": format_num,
                                "emision_n2o_indirecta": format_num,
                                "total": format_num,
                                "Emisiones (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
                                "% contribución": format_percent
                            }),
                            hide_index=True
                        )
                        # Gráficos de barras apiladas por tipo de emisión (orgánico e inorgánico por separado)
                        for tipo_cat in ["Orgánico", "Inorgánico"]:
                            df_tipo = df_fert[df_fert["Tipo fertilizante"] == tipo_cat]
                            if not df_tipo.empty:
                                st.markdown(f"**Gráfico: Emisiones por fertilizante {tipo_cat.lower()} y tipo de emisión (kg CO₂e/ha)**")
                                labels = df_tipo["tipo"]
                                em_prod = df_tipo["emision_produccion"].values
                                em_n2o_dir = df_tipo["emision_n2o_directa"].values
                                em_n2o_ind_vol = df_tipo["emision_n2o_ind_volatilizacion"].values
                                em_n2o_ind_lix = df_tipo["emision_n2o_ind_lixiviacion"].values
                                fig_fert = go.Figure()
                                fig_fert.add_bar(x=labels, y=em_prod, name="Producción")
                                fig_fert.add_bar(x=labels, y=em_n2o_dir, name="N₂O directa")
                                fig_fert.add_bar(x=labels, y=em_n2o_ind_vol, name="N₂O indirecta (volatilización)")
                                fig_fert.add_bar(x=labels, y=em_n2o_ind_lix, name="N₂O indirecta (lixiviación)")
                                totales = em_prod + em_n2o_dir + em_n2o_ind_vol + em_n2o_ind_lix
                                textos_tot = [format_num(v) for v in totales]
                                fig_fert.add_trace(go.Scatter(
                                    x=labels,
                                    y=totales,
                                    text=textos_tot,
                                    mode="text",
                                    textposition="top center",
                                    showlegend=False
                                ))
                                fig_fert.update_layout(
                                    barmode='stack',
                                    yaxis_title="Emisiones (kg CO₂e/ha)",
                                    title=f"Emisiones por fertilizante {tipo_cat.lower()} y tipo de emisión",
                                    height=400
                                )
                                fig_fert.update_yaxes(range=[0, max(totales) * 1.15 if len(totales) > 0 else 1])
                                st.plotly_chart(fig_fert, use_container_width=True, key=get_unique_key())
                # --- AGROQUÍMICOS ---
                elif fuente == "Agroquímicos" and emisiones_fuente_etapa[etapa].get("desglose_agroquimicos"):
                    df_agro = pd.DataFrame(emisiones_fuente_etapa[etapa]["desglose_agroquimicos"])
                    if not df_agro.empty:
                        total_agro = df_agro["emisiones"].sum()
                        df_agro["% contribución"] = df_agro["emisiones"] / total_agro * 100
                        if prod and prod > 0:
                            df_agro["Emisiones (kg CO₂e/kg fruta)"] = df_agro["emisiones"] / prod
                        else:
                            df_agro["Emisiones (kg CO₂e/kg fruta)"] = None
                        st.markdown("**Tabla: Desglose de agroquímicos**")
                        st.dataframe(df_agro[["categoria", "tipo", "cantidad_ia", "emisiones", "Emisiones (kg CO₂e/kg fruta)", "% contribución"]].style.format({
                            "cantidad_ia": format_num,
                            "emisiones": format_num,
                            "Emisiones (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
                            "% contribución": format_percent
                        }), hide_index=True)
                        # Gráfico de barras apiladas por categoría y tipo (kg CO₂e/ha)
                        st.markdown("**Gráfico: Emisiones de agroquímicos por categoría y tipo (kg CO₂e/ha)**")
                        df_group = df_agro.groupby(["categoria", "tipo"]).agg({"emisiones": "sum"}).reset_index()
                        categorias = df_group["categoria"].unique()
                        tipos = df_group["tipo"].unique()
                        fig_agro = go.Figure()
                        for tipo in tipos:
                            vals = []
                            for cat in categorias:
                                row = df_group[(df_group["categoria"] == cat) & (df_group["tipo"] == tipo)]
                                vals.append(row["emisiones"].values[0] if not row.empty else 0)
                            fig_agro.add_bar(x=categorias, y=vals, name=tipo)
                        totales = df_group.groupby("categoria")["emisiones"].sum().reindex(categorias).values
                        textos_tot = [format_num(v) for v in totales]
                        fig_agro.add_trace(go.Scatter(
                            x=categorias,
                            y=totales,
                            text=textos_tot,
                            mode="text",
                            textposition="top center",
                            showlegend=False
                        ))
                        fig_agro.update_layout(
                            barmode='stack',
                            yaxis_title="Emisiones (kg CO₂e/ha)",
                            title="Emisiones de agroquímicos por categoría y tipo",
                            height=400
                        )
                        y_max_agro = max(totales) if len(totales) > 0 else 1
                        fig_agro.update_yaxes(range=[0, y_max_agro * 1.15])
                        st.plotly_chart(fig_agro, use_container_width=True, key=get_unique_key())
                        # Gráfico de torta por categoría (kg CO₂e/ha)
                        st.markdown("**Gráfico: % de contribución de cada categoría de agroquímico (kg CO₂e/ha)**")
                        df_cat = df_agro.groupby("categoria").agg({"emisiones": "sum"}).reset_index()
                        fig_pie_agro = px.pie(
                            df_cat,
                            names="categoria",
                            values="emisiones",
                            title="Contribución de cada categoría de agroquímico",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            hole=0.3
                        )
                        fig_pie_agro.update_traces(textinfo='percent+label')
                        fig_pie_agro.update_layout(showlegend=True, height=400)
                        st.plotly_chart(fig_pie_agro, use_container_width=True, key=get_unique_key())
                # --- MAQUINARIA ---
                elif fuente == "Maquinaria" and emisiones_fuente_etapa[etapa].get("desglose_maquinaria"):
                    df_maq = pd.DataFrame(emisiones_fuente_etapa[etapa]["desglose_maquinaria"])
                    if not df_maq.empty:
                        total_maq = df_maq["emisiones"].sum()
                        df_maq["% contribución"] = df_maq["emisiones"] / total_maq * 100
                        if prod and prod > 0:
                            df_maq["Emisiones (kg CO₂e/kg fruta)"] = df_maq["emisiones"] / prod
                        else:
                            df_maq["Emisiones (kg CO₂e/kg fruta)"] = None
                        st.markdown("**Tabla: Desglose de maquinaria**")
                        st.dataframe(df_maq[["nombre_labor", "tipo_maquinaria", "tipo_combustible", "litros", "emisiones", "Emisiones (kg CO₂e/kg fruta)", "% contribución"]].style.format({
                            "litros": format_num,
                            "emisiones": format_num,
                            "Emisiones (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
                            "% contribución": format_percent
                        }), hide_index=True)
                        # Gráfico de torta: emisiones por labor (kg CO₂e/ha)
                        st.markdown("**Gráfico: % de contribución de cada labor (torta, kg CO₂e/ha)**")
                        df_labor = df_maq.groupby("nombre_labor")["emisiones"].sum().reset_index()
                        fig_pie_labor = px.pie(
                            df_labor,
                            names="nombre_labor",
                            values="emisiones",
                            title="Contribución de cada labor al total de emisiones de maquinaria",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            hole=0.3
                        )
                        fig_pie_labor.update_traces(textinfo='percent+label')
                        fig_pie_labor.update_layout(showlegend=True, height=400)
                        st.plotly_chart(fig_pie_labor, use_container_width=True, key=get_unique_key())
                        # Gráfico de torta: emisiones por maquinaria dentro de cada labor (kg CO₂e/ha)
                        labores_unicas = df_maq["nombre_labor"].unique()
                        for labor in labores_unicas:
                            df_labor_maq = df_maq[df_maq["nombre_labor"] == labor]
                            if len(df_labor_maq) > 1:
                                st.markdown(f"**Gráfico: % de contribución de cada maquinaria en la labor '{labor}' (torta, kg CO₂e/ha)**")
                                fig_pie_maq = px.pie(
                                    df_labor_maq,
                                    names="tipo_maquinaria",
                                    values="emisiones",
                                    title=f"Contribución de cada maquinaria en la labor '{labor}'",
                                    color_discrete_sequence=px.colors.qualitative.Pastel,
                                    hole=0.3
                                )
                                fig_pie_maq.update_traces(textinfo='percent+label')
                                fig_pie_maq.update_layout(showlegend=True, height=400)
                                st.plotly_chart(fig_pie_maq, use_container_width=True, key=get_unique_key())
                        # Gráfico de barras apiladas: labor (X), emisiones (Y), apilado por maquinaria (kg CO₂e/ha)
                        st.markdown("**Gráfico: Emisiones por labor y tipo de maquinaria (barras apiladas, kg CO₂e/ha)**")
                        df_maq_grouped = df_maq.groupby(["nombre_labor", "tipo_maquinaria"]).agg({"emisiones": "sum"}).reset_index()
                        labores = df_maq_grouped["nombre_labor"].unique()
                        tipos_maq = df_maq_grouped["tipo_maquinaria"].unique()
                        fig_maq = go.Figure()
                        for maq in tipos_maq:
                            vals = []
                            for l in labores:
                                row = df_maq_grouped[(df_maq_grouped["nombre_labor"] == l) & (df_maq_grouped["tipo_maquinaria"] == maq)]
                                vals.append(row["emisiones"].values[0] if not row.empty else 0)
                            fig_maq.add_bar(
                                x=labores,
                                y=vals,
                                name=maq
                            )
                        totales = df_maq_grouped.groupby("nombre_labor")["emisiones"].sum().reindex(labores).values
                        textos_tot = [format_num(v) for v in totales]
                        fig_maq.add_trace(go.Scatter(
                            x=labores,
                            y=totales,
                            text=textos_tot,
                            mode="text",
                            textposition="top center",
                            showlegend=False
                        ))
                        y_max_maq = max(totales) if len(totales) > 0 else 1
                        fig_maq.update_layout(
                            barmode='stack',
                            yaxis_title="Emisiones (kg CO₂e/ha)",
                            title="Emisiones por labor y tipo de maquinaria",
                            height=400
                        )
                        fig_maq.update_yaxes(range=[0, y_max_maq * 1.15])
                        st.plotly_chart(fig_maq, use_container_width=True, key=get_unique_key())
                # --- RIEGO ---
                elif fuente == "Riego" and emisiones_fuente_etapa[etapa].get("desglose_riego"):
                    dr = emisiones_fuente_etapa[etapa]["desglose_riego"]
                    energia_actividades = dr.get("energia_actividades", [])
                    actividades = []
                    for ea in energia_actividades:
                        actividades.append({
                            "Actividad": ea.get("actividad", ""),
                            "Tipo actividad": ea.get("tipo_actividad", ""),
                            "Consumo agua (m³)": ea.get("agua_total_m3", 0),
                            "Emisiones agua (kg CO₂e)": ea.get("emisiones_agua", 0),
                            "Consumo energía": ea.get("consumo_energia", 0),
                            "Tipo energía": ea.get("tipo_energia", ""),
                            "Emisiones energía (kg CO₂e)": ea.get("emisiones_energia", 0),
                        })
                    if actividades:
                        df_riego = pd.DataFrame(actividades)
                        df_riego["Emisiones totales (kg CO₂e)"] = df_riego["Emisiones agua (kg CO₂e)"] + df_riego["Emisiones energía (kg CO₂e)"]
                        if prod and prod > 0:
                            df_riego["Emisiones totales (kg CO₂e/kg fruta)"] = df_riego["Emisiones totales (kg CO₂e)"] / prod
                        else:
                            df_riego["Emisiones totales (kg CO₂e/kg fruta)"] = None
                        total_riego = df_riego["Emisiones totales (kg CO₂e)"].sum()
                        if total_riego > 0:
                            df_riego["% contribución"] = df_riego["Emisiones totales (kg CO₂e)"] / total_riego * 100
                        else:
                            df_riego["% contribución"] = 0
                        st.markdown("**Tabla: Desglose de riego por actividad (agua y energía apilados)**")
                        st.dataframe(df_riego[[
                            "Actividad", "Tipo actividad", "Consumo agua (m³)", "Emisiones agua (kg CO₂e)",
                            "Consumo energía", "Tipo energía", "Emisiones energía (kg CO₂e)",
                            "Emisiones totales (kg CO₂e)", "Emisiones totales (kg CO₂e/kg fruta)", "% contribución"
                        ]].style.format({
                            "Consumo agua (m³)": format_num,
                            "Emisiones agua (kg CO₂e)": format_num,
                            "Consumo energía": format_num,
                            "Emisiones energía (kg CO₂e)": format_num,
                            "Emisiones totales (kg CO₂e)": format_num,
                            "Emisiones totales (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
                            "% contribución": format_percent
                        }), hide_index=True)
                        # Gráfico de barras apiladas por actividad (agua + energía) - texto sólo en el total
                        fig_riego = go.Figure()
                        fig_riego.add_bar(
                            x=df_riego["Actividad"],
                            y=df_riego["Emisiones agua (kg CO₂e)"],
                            name="Agua"
                        )
                        fig_riego.add_bar(
                            x=df_riego["Actividad"],
                            y=df_riego["Emisiones energía (kg CO₂e)"],
                            name="Energía"
                        )
                        totales = df_riego["Emisiones totales (kg CO₂e)"].values
                        textos_tot = [format_num(v) for v in totales]
                        fig_riego.add_trace(go.Scatter(
                            x=df_riego["Actividad"],
                            y=totales,
                            text=textos_tot,
                            mode="text",
                            textposition="top center",
                            showlegend=False
                        ))
                        y_max_riego = max(totales) if len(totales) > 0 else 1
                        fig_riego.update_layout(
                            barmode='stack',
                            yaxis_title="Emisiones (kg CO₂e/ha)",
                            title="Emisiones de riego por actividad (agua + energía)",
                            height=400
                        )
                        fig_riego.update_yaxes(range=[0, y_max_riego * 1.15])
                        st.plotly_chart(fig_riego, use_container_width=True, key=get_unique_key())
                    else:
                        st.info("No se ingresaron actividades de riego para esta etapa.")
                # --- RESIDUOS ---
                elif fuente == "Residuos" and emisiones_fuente_etapa[etapa].get("desglose_residuos"):
                    dr = emisiones_fuente_etapa[etapa]["desglose_residuos"]
                    if isinstance(dr, dict) and dr:
                        df_res = pd.DataFrame([
                            {
                                "Gestión": k,
                                "Biomasa (kg/ha)": v.get("biomasa", 0),
                                "Emisiones (kg CO₂e/ha)": v.get("emisiones", 0),
                                "Emisiones (kg CO₂e/kg fruta)": v.get("emisiones", 0) / prod if prod and prod > 0 else None
                            }
                            for k, v in dr.items()
                        ])
                        total_res = df_res["Emisiones (kg CO₂e/ha)"].sum()
                        df_res["% contribución"] = df_res["Emisiones (kg CO₂e/ha)"] / total_res * 100
                        textos_res = [format_num(v) for v in df_res["Emisiones (kg CO₂e/ha)"]]
                        st.markdown("**Tabla: Desglose de gestión de residuos vegetales**")
                        st.dataframe(df_res[[
                            "Gestión", "Biomasa (kg/ha)", "Emisiones (kg CO₂e/ha)", "Emisiones (kg CO₂e/kg fruta)", "% contribución"
                        ]].style.format({
                            "Biomasa (kg/ha)": format_num,
                            "Emisiones (kg CO₂e/ha)": format_num,
                            "Emisiones (kg CO₂e/kg fruta)": lambda x: format_num(x, 3),
                            "% contribución": format_percent
                        }), hide_index=True)
                        # Gráfico de barras por gestión de residuos
                        fig_res = px.bar(
                            df_res,
                            x="Gestión",
                            y="Emisiones (kg CO₂e/ha)",
                            color="Gestión",
                            color_discrete_sequence=px.colors.qualitative.Pastel,
                            title="Emisiones por gestión de residuos"
                        )
                        fig_res.add_trace(go.Scatter(
                            x=df_res["Gestión"],
                            y=df_res["Emisiones (kg CO₂e/ha)"],
                            text=textos_res,
                            mode="text",
                            textposition="top center",
                            showlegend=False
                        ))
                        fig_res.update_layout(showlegend=False, height=400)
                        fig_res.update_yaxes(range=[0, max(df_res["Emisiones (kg CO₂e/ha)"]) * 1.15 if not df_res.empty else 1])
                        st.plotly_chart(fig_res, use_container_width=True, key=get_unique_key())

    st.markdown("---")

    # --- Resumen ejecutivo ---
    st.markdown("#### Resumen ejecutivo")
    st.success(
        "📝 **Resumen ejecutivo:**\n\n"
        "El resumen ejecutivo presenta los resultados clave del cálculo de huella de carbono, útiles para reportes, certificaciones o toma de decisiones.\n\n"
        "Las emisiones totales estimadas para el sistema productivo corresponden a la suma de todas las fuentes y etapas consideradas, expresadas en **kg CO₂e/ha**. "
        "Este valor representa las emisiones acumuladas a lo largo de todo el ciclo de vida del cultivo, desde la implantación hasta la última etapa productiva, según el límite 'cradle-to-farm gate'.\n\n"
        f"**Total emisiones estimadas:** {format_num(em_total, 2)} kg CO₂e/ha"
        + (
            f"\n\n**Emisiones por kg de fruta:** {format_num(em_total/prod_total, 3)} kg CO₂e/kg fruta. "
            "Este indicador permite comparar la huella de carbono entre diferentes sistemas o productos, ya que relaciona las emisiones totales con la producción obtenida."
            if prod_total > 0 else "\n\nNo se ha ingresado producción total. No es posible calcular emisiones por kg de fruta."
        )
    )

    st.markdown("---")
    st.markdown("#### Parámetros de cálculo")
    st.write(f"Potenciales de calentamiento global (GWP) usados: {GWP}")
    st.write("Factores de emisión y fórmulas según IPCC 2006 y valores configurables al inicio del código.")

    # Guardar resultados globales y desgloses en session_state para exportación futura
    st.session_state["resultados_globales"] = {
        "tipo": "perenne",
        "em_total": em_total,
        "prod_total": prod_total,
        "emisiones_etapas": emisiones_etapas.copy(),
        "produccion_etapas": produccion_etapas.copy(),
        "emisiones_fuentes": emisiones_fuentes.copy(),
        "emisiones_fuente_etapa": emisiones_fuente_etapa.copy(),
        "detalle_residuos": st.session_state.get("detalle_residuos", []),
        "emisiones_anuales": st.session_state.get("emisiones_anuales", [])
    }

# -----------------------------
# Interfaz principal
# -----------------------------
em_total = 0
prod_total = 0

if anual.strip().lower() == "perenne":
    tabs = st.tabs(["Implantación", "Crecimiento sin producción", "Producción", "Resultados"])
    with tabs[0]:
        em_imp, prod_imp = etapa_implantacion()
        st.session_state["em_imp"] = em_imp
        st.session_state["prod_imp"] = prod_imp
    with tabs[1]:
        em_csp, prod_csp = etapa_crecimiento("Crecimiento sin producción", produccion_pregunta=False)
        st.session_state["em_csp"] = em_csp
        st.session_state["prod_csp"] = prod_csp
    with tabs[2]:
        em_pc, prod_pc = etapa_produccion_segmentada()
        st.session_state["em_pc"] = em_pc
        st.session_state["prod_pc"] = prod_pc
    with tabs[3]:
        # Calcular los totales SOLO al mostrar resultados
        em_total = (
            st.session_state.get("em_imp", 0)
            + st.session_state.get("em_csp", 0)
            + st.session_state.get("em_pc", 0)
        )
        prod_total = st.session_state.get("prod_pc", 0)
        mostrar_resultados_perenne(em_total, prod_total)

elif anual.strip().lower() == "anual":
    tabs = st.tabs(["Ingreso de información", "Resultados"])
    with tabs[0]:
        em_anual, prod_anual = etapa_anual()
        st.session_state["em_anual"] = em_anual
        st.session_state["prod_anual"] = prod_anual
    with tabs[1]:
        # Calcular los totales SOLO al mostrar resultados
        em_total = st.session_state.get("em_anual", 0)
        prod_total = st.session_state.get("prod_anual", 0)
        mostrar_resultados_anual(em_total, prod_total)
else:
    st.warning("Debe seleccionar si el cultivo es anual o perenne para continuar.")