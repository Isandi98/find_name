import os
import pandas as pd
from fuzzywuzzy import fuzz
import phonetics
import jellyfish
import openpyxl  # Asegúrate de tener openpyxl instalado
import Levenshtein
import random
import nltk
from nltk.corpus import words  # Importar el corpus de palabras
import streamlit as st

# Descargar el corpus de palabras si no se ha hecho
nltk.download('words')

# Lista de terminaciones comunes en nombres farmacéuticos
terminaciones_farmaceuticas = [
    "cillin", "mycin", "olol", "pril", "statin", "sartan", "vir", "zole", "dine", "ine", 
    "mab", "cept", "nib", "ase", "xime", "bactam", "fen", "sol", "cap", "dex", "ril",
    "thromycin", "floxacin", "sulfanil", "prazole", "cort", "dronate", "gliptin", "mide",
    "sartan", "tropin", "zole", "ciclovir", "parin", "bicin", "dazole", "cetam", "fentanil",
    "pyridine", "pyridone", "pyrrolidine", "dine", "zine", "cillin", "dronate", "mab", "tinib"
]

# Raíces farmacéuticas comunes
raices_farmaceuticas = [
    "anti", "bio", "cyto", "neuro", "cardio", "gastro", "hemo", "immuno", "endo", "hormo",
    "anti", "thera", "pharma", "pheno", "met", "pro", "quin", "sulfa", "traz", "val"
]

# Obtener una lista de palabras del corpus y filtrar por longitud
diccionario_palabras = [word for word in words.words() if 3 <= len(word) <= 5]

# Conjunto para almacenar nombres generados y evitar repeticiones
nombres_generados = set()

# Funciones de similitud
def soundex_similarity(name1, name2):
    return fuzz.ratio(jellyfish.soundex(name1.lower()), jellyfish.soundex(name2.lower()))

def phonex_similarity(name1, name2):
    return fuzz.ratio(jellyfish.nysiis(name1.lower()), jellyfish.nysiis(name2.lower()))

def levenshtein_similarity(name1, name2):
    return Levenshtein.distance(name1.lower(), name2.lower())

def ngram_similarity(s1, s2, n=2):
    s1, s2 = s1.lower().replace(" ", ""), s2.lower().replace(" ", "")
    def get_ngrams(string, n):
        return {string[i:i+n]: 1 for i in range(len(string) - n + 1)}
    ngrams1 = get_ngrams(s1, n)
    ngrams2 = get_ngrams(s2, n)
    common_ngrams = set(ngrams1.keys()) & set(ngrams2.keys())
    similarity = 2 * len(common_ngrams) / (len(ngrams1) + len(ngrams2)) if ngrams1 or ngrams2 else 0.0
    len_diff = abs(len(s1) - len(s2)) / max(len(s1), len(s2)) if max(len(s1), len(s2)) > 0 else 0
    adjusted_similarity = similarity * (1 - len_diff)
    return adjusted_similarity * 100

def phonetic_combined_similarity(name1, name2):
    phonetic_similarity = fuzz.ratio(phonetics.metaphone(name1.lower()), phonetics.metaphone(name2.lower()))
    soundex_sim = soundex_similarity(name1, name2)
    phonex_sim = phonex_similarity(name1, name2)
    return (phonetic_similarity + soundex_sim + phonex_sim) / 3

def orthographic_combined_similarity(name1, name2):
    ortho_similarity = levenshtein_similarity(name1, name2)
    ngram_sim = ngram_similarity(name1, name2)
    return (ortho_similarity + ngram_sim) / 2

def average_similarity(name1, name2):
    phonetic_avg = phonetic_combined_similarity(name1, name2)
    orthographic_avg = orthographic_combined_similarity(name1, name2)
    return (phonetic_avg + orthographic_avg) / 2

def leer_nombres_excel(ruta_archivo):
    try:
        df = pd.read_excel(ruta_archivo)
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
    nombre_palabra = random.choice(diccionario_palabras)  # Elegir una palabra del diccionario
    terminacion = random.choice(terminaciones_farmaceuticas)  # Elegir una terminación farmacéutica
    # Crear un nombre más atractivo
    vocales = 'aeiou'
    nombre = "Aba" + nombre_palabra.capitalize() + terminacion  # Combinar con "Aba"
    
    # Mejorar la pronunciabilidad
    nombre_mejorado = ""
    for char in nombre:
        if char in vocales and random.random() < 0.5:  # Alternar vocales
            nombre_mejorado += random.choice(vocales)
        else:
            nombre_mejorado += char

    return nombre_mejorado

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
        if max_sim < 55:
            return nombre_modificado, max_sim, max_sim_nombre

def main():
    st.title("Generador de Nombres Farmacéuticos")

    # Cargar el archivo Excel
    ruta_archivo = st.file_uploader("Sube tu archivo EMA.xlsx", type=["xlsx"])
    
    if ruta_archivo is not None:
        nombres_ema = leer_nombres_excel(ruta_archivo)
        if nombres_ema:
            if st.button("Generar Nombres"):
                for _ in range(5):  # Generar 5 nombres farmacéuticos
                    resultado = encontrar_nombre_unico(nombres_ema)
                    if resultado:
                        nombre_modificado, max_sim, max_sim_nombre = resultado
                        st.write(f"Nombre único encontrado: {nombre_modificado}")
                        st.write(f"Similitud más alta: {max_sim:.2f}% con el nombre: '{max_sim_nombre}'")
                    else:
                        st.write("No se encontraron nombres únicos.")
        else:
            st.error("No se pudieron leer los nombres del archivo.")

if __name__ == "__main__":
    main()