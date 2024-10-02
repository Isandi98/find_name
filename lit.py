import os
import fuzzywuzzy
import pandas as pd
import fuzzywuzzy
from fuzzywuzzy import fuzz
import phonetics
import jellyfish
import openpyxl  # Asegúrate de tener openpyxl instalado
import random
import Levenshtein
import streamlit as st

# Sílabas comunes en nombres de medicamentos
silabas_inicio = ["Apo", "Cef", "Dex", "Flu", "Glu", "Hydro", "Ibu", "Keto", "Lora", "Meto", "Napro", "Oxy", "Penta", "Queti", "Rami", "Sero", "Tami", "Uro", "Vita", "Xylo"]
silabas_medio = ["bi", "ce", "di", "fi", "gi", "li", "mi", "ni", "pi", "ri", "si", "ti", "vi", "xi", "zi"]
silabas_final = ["cin", "dine", "fen", "line", "mine", "nate", "pine", "quine", "rine", "sone", "tine", "vir", "zole"]

# Funciones de similitud
# Funciones de similitud
def soundex_similarity(name1, name2):
    return fuzz.ratio(jellyfish.soundex(name1.lower()), jellyfish.soundex(name2.lower()))

def phonex_similarity(name1, name2):
    return fuzz.ratio(jellyfish.nysiis(name1.lower()), jellyfish.nysiis(name2.lower()))

def levenshtein_similarity(name1, name2):
    return fuzz.ratio(name1.lower(), name2.lower())

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

def detailed_similarity(name1, name2):
    ortho_similarity = levenshtein_similarity(name1, name2)
    phonetic_similarity = fuzz.ratio(phonetics.metaphone(name1.lower()), phonetics.metaphone(name2.lower()))
    soundex_sim = soundex_similarity(name1, name2)
    phonex_sim = phonex_similarity(name1, name2)
    ngram_sim = ngram_similarity(name1, name2)
    combined_phonetic = phonetic_combined_similarity(name1, name2)
    combined_orthographic = orthographic_combined_similarity(name1, name2)
    avg_similarity = (combined_phonetic + combined_orthographic) / 2
    justificacion = justificar_similitud(name1, name2)
    return {
        "ortho_similarity": ortho_similarity,
        "phonetic_similarity": phonetic_similarity,
        "soundex_sim": soundex_sim,
        "phonex_sim": phonex_sim,
        "ngram_sim": ngram_sim,
        "combined_phonetic": combined_phonetic,
        "combined_orthographic": combined_orthographic,
        "avg_similarity": avg_similarity,
        "justificacion": justificacion
    }

def justificar_similitud(name1, name2):
    ops = Levenshtein.editops(name1.lower(), name2.lower())
    justificacion = []
    for op in ops:
        if op[0] == 'replace':
            justificacion.append(f"Sustituir '{name1[op[1]]}' por '{name2[op[2]]}'")
        elif op[0] == 'insert':
            justificacion.append(f"Insertar '{name2[op[2]]}' en la posición {op[1]}")
        elif op[0] == 'delete':
            justificacion.append(f"Eliminar '{name1[op[1]]}' de la posición {op[1]}")
    return justificacion

def generar_nombre_inventado():
    inicio = random.choice(silabas_inicio)  # Elegir sílaba de inicio aleatoria
    medio = random.choice(silabas_medio)  # Elegir sílaba del medio aleatoria
    final = random.choice(silabas_final)  # Elegir sílaba final aleatoria
    nombre = inicio + medio + final
    return nombre

def modificar_nombre(nombre):
    nombre_lista = list(nombre)
    indice = random.randint(0, len(nombre_lista) - 1)
    nombre_lista[indice] = chr(random.randint(97, 122))  # Cambia una letra aleatoriamente
    return ''.join(nombre_lista)

def encontrar_nombre_diferente(nombres_ema, umbral_similitud=50):  # Cambiado a 50%
    nombres_generados = {}
    while True:
        print("Buscando... 🔍")  # Mensaje de búsqueda con emoji
        nombre_candidato = generar_nombre_inventado()
        similitudes = [average_similarity(nombre_candidato, nombre_ema) for nombre_ema in nombres_ema]
        similitud_media = sum(similitudes) / len(similitudes) if similitudes else 0
        
        if similitud_media < umbral_similitud:  # Verificar similitud media
            # Almacenar el nombre si cumple con la condición
            nombres_generados[nombre_candidato] = {
                "nombre": nombre_candidato,
                "similitud_media": similitud_media
            }
            print(f"Nombre generado: {nombre_candidato}, Similitud media: {similitud_media}")
            guardar_nombre_en_excel(nombre_candidato)
            return nombre_candidato, nombres_generados

def guardar_nombre_en_excel(nombre):
    try:
        # Cargar el archivo existente
        df = pd.read_excel('C:/Users/isaac/Documents/Cursor/EMA/Nueva/EMA.xlsx')
        # Añadir el nuevo nombre
        df = df.append({'Nombre': nombre}, ignore_index=True)
        # Guardar el archivo actualizado
        df.to_excel('C:/Users/isaac/Documents/Cursor/EMA/Nueva/EMA.xlsx', index=False)
        print(f"Nombre '{nombre}' guardado en el archivo Excel.")
    except Exception as e:
        print(f"Error al guardar el nombre en el archivo Excel: {e}")

def cargar_nombres_ema():
    try:
        print("Leyendo el archivo EMA.xlsx...")
        nombres_ema = pd.read_excel('C:/Users/isaac/Documents/Cursor/EMA/Nueva/EMA.xlsx')['Nombre'].tolist()
        print("Archivo leído correctamente.")
        return nombres_ema
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return []

def buscar_nombres(nombres, nombre_buscado):
    resultados = []
    for nombre in nombres:
        similitud = average_similarity(nombre, nombre_buscado)  # Cambiado a average_similarity
        if similitud < 50:  # Limitar resultados a similitud inferior al 50%
            resultados.append(nombre)
    return resultados

def exportar_resultados(nombres):
    # ... implementación de la función ...
    pass  # Reemplaza esto con el código real

def main():
    st.title("Buscador de Nombres Alternativos")
    # Cargar nombres desde el archivo
    nombres_ema = cargar_nombres_ema()  # Cargar nombres automáticamente
    
    if nombres_ema:  # Verificar si se cargaron nombres
        if st.button("Generar otro nombre"):  # Botón para generar otro nombre
            nombre_inventado, nombres_generados = encontrar_nombre_diferente(nombres_ema)
            similitud_media = nombres_generados[nombre_inventado]["similitud_media"]  # Obtener la similitud media
            
            # Mostrar el nombre y la similitud media en verde
            st.markdown(f"<h3 style='color: green;'>Nombre inventado encontrado: {nombre_inventado}</h3>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='color: green;'>Similitud media con nombres de EMA: {similitud_media:.2f}%</h4>", unsafe_allow_html=True)
    else:
        st.write("No se encontraron nombres en el archivo.")

if __name__ == "__main__":
    main()