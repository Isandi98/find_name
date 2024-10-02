import os
import pandas as pd
import phonetics
import jellyfish
import openpyxl  # Asegúrate de tener openpyxl instalado
import Levenshtein
import random
import nltk
from nltk.corpus import words  # Importar el corpus de palabras
import streamlit as st
from difflib import SequenceMatcher

# Descargar el corpus de palabras si no se ha hecho
nltk.download('words')

# Lista de nombres de medicamentos
nombres_medicamentos = [
    "Aspirina", "Ibuprofeno", "Paracetamol", "Amoxicilina", "Ciprofloxacino",
    "Metformina", "Simvastatina", "Lisinopril", "Omeprazol", "Atorvastatina",
    "Clopidogrel", "Losartán", "Sertralina", "Fluoxetina", "Dexametasona",
    "Ranitidina", "Cetirizina", "Alprazolam", "Diazepam", "Levotiroxina"
]

# Lista de términos farmacéuticos
terminos_farmaceuticos = [
    "antibiótico", "analgésico", "antiinflamatorio", "antidepresivo", "antihistamínico",
    "antipirético", "antihipertensivo", "anticoagulante", "antiviral", "hormona",
    "inmunosupresor", "esteroide", "vasodilatador", "diurético", "antipsicótico",
    "anticonvulsivo", "antifúngico", "antiparasitario", "quimioterapia", "vacuna"
]

# Asegúrate de definir la lista 'terminaciones_farmaceuticas' antes de usarla
terminaciones_farmaceuticas = ["ina", "ona", "ida"]  # Ejemplo de terminaciones

# Obtener una lista de palabras del corpus y filtrar por longitud
diccionario_palabras = [word for word in words.words() if 3 <= len(word) <= 5]

# Conjunto para almacenar nombres generados y evitar repeticiones
nombres_generados = set()

# Funciones de similitud
def levenshtein_similarity(name1, name2):
    return 1 - (Levenshtein.distance(name1, name2) / max(len(name1), len(name2)))

def sequence_matcher_similarity(name1, name2):
    return SequenceMatcher(None, name1, name2).ratio()

def phonetic_similarity(name1, name2):
    return 1 - (phonetics.dmetaphone(name1) != phonetics.dmetaphone(name2))

def average_similarity(name1, name2):
    name1 = name1.lower()
    name2 = name2.lower()
    lev_sim = levenshtein_similarity(name1, name2)
    seq_sim = sequence_matcher_similarity(name1, name2)
    phon_sim = phonetic_similarity(name1, name2)
    return (lev_sim + seq_sim + phon_sim) / 3

def leer_nombres_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        return df['Nombre'].tolist()
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        return []

def modificar_nombre(nombre):
    # Cambia una letra aleatoria en el nombre para reducir la similitud
    if len(nombre) > 3:  # Asegurarse de que el nombre sea lo suficientemente largo
        index = random.randint(3, len(nombre) - 1)  # Cambiar solo después de "Aba"
        letra_nueva = random.choice('aeiou') if nombre[index] not in 'aeiou' else random.choice('bcdfghjklmnpqrstvwxyz')
        nombre_modificado = nombre[:index] + letra_nueva + nombre[index + 1:]
        return nombre_modificado
    return nombre

def generar_nombre_farmaceutico():
    # Genera un nombre farmacéutico que comienza con "Aba"
    nombre_medicamento = random.choice(nombres_medicamentos)  # Elegir un nombre de medicamento
    terminacion = random.choice(terminaciones_farmaceuticas)  # Elegir una terminación farmacéutica
    nombre = f"Aba{nombre_medicamento[:3]}{terminacion}"  # Combinar y limitar a 3 letras del nombre
    return nombre

def encontrar_nombre_unico(nombres_ema):
    while True:
        nombre_aleatorio = generar_nombre_farmaceutico()
        
        # Modificar el nombre para reducir la similitud
        nombre_modificado = modificar_nombre(nombre_aleatorio)
        
        # Asegurarse de que el nombre no se haya generado antes y no sea compuesto
        if nombre_modificado in nombres_generados or ' ' in nombre_modificado:
            continue
        
        similitudes = [average_similarity(nombre_modificado, nombre) for nombre in nombres_ema]
        max_sim = max(similitudes)
        max_sim_nombre = nombres_ema[similitudes.index(max_sim)]

        # Solo imprimir si la similitud media más alta es inferior al 55%
        if max_sim < 0.55:  # Cambiado a 0.55 para reflejar el rango de 0 a 1
            return nombre_modificado, max_sim * 100, max_sim_nombre  # Multiplicamos por 100 para mostrar en porcentaje

def main():
    st.title("Generador de Nombres Farmacéuticos")

    # Cargar el archivo Excel
    uploaded_file = st.file_uploader("Sube tu archivo EMA.xlsx", type=["xlsx"])

    if uploaded_file is not None:
        nombres_ema = leer_nombres_excel(uploaded_file)
        if nombres_ema:
            if st.button("Generar Nombres"):
                for _ in range(5):  # Generar 5 nombres farmacéuticos
                    resultado = encontrar_nombre_unico(nombres_ema)
                    if resultado:
                        nombre_modificado, max_sim, max_sim_nombre = resultado
                        st.markdown(f"**Nombre único encontrado:** {nombre_modificado}")
                        st.write(f"Similitud más alta: {max_sim:.2f}% con el nombre: '{max_sim_nombre}'")
                    else:
                        st.write("No se encontraron nombres únicos.")
        else:
            st.error("No se pudieron leer los nombres del archivo.")

if __name__ == "__main__":
    main()