import json
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# ================================
# PATRONES CONFIGURABLES
# ================================

# Cada entrada en este diccionario representa un tipo de información a buscar
# Puedes agregar nuevas entradas o modificar las existentes sin tocar el resto del código
PATRONES = {
    "tarjeta_video": [
        r'tarjeta de (video|gráfica)[^\n,;]*',
        r'video tarjeta de (video|gráfica)[^\n,;]*',
        r'nvidia\s.*?rtx\s?\d{3,4}[^,;\n]*',
        r'rtx\s\d{3,4}[^,;\n]*',
        r'gtx\s\d{3,4}[^,;\n]*',
        r'rx\s\d{3,4}[^,;\n]*',
        r'geforce\s.*?rtx\s?\d{3,4}[^,;\n]*',
        r'geforce\s.*?gtx\s?\d{3,4}[^,;\n]*',
        r'geforce\s.*?rx\s?\d{3,4}[^,;\n]*'
    ],
    "grafica_integrada": [
        r'gr[áa]ficos integrados',
        r'video integrado',
        r'integrada',
        r'integrados',
        r'integrado'
    ],
    "gabinete": [
        r'(case|gabinete)[^\n,;]*',
        r'gabinete[^\n,;]*',
        r'case[^\n,;]*',
        r'mid tower[^.\n]*',
        r'formato reducido[^.\n]*'
    ],
    "fuente_poder": [
        r'fuente de poder[^.\n]*',
        r'fuente[^.\n]*',
        r'wattaje[^.\n]*',
        r'certificación[^.\n]*',
        r'certificado[^.\n]*',
        r'watt[^.\n]*',
        r'w[^.\n]*',
    ]
}

# Función para eliminar todo lo posterior a "memoria ram", para evitar confusión con otras características
def cortar_en_memoria_ram(texto):
    match = re.search(r'memoria ram', texto)
    if match:
        return texto[:match.start()]
    return texto

# Función general para buscar coincidencias con una lista de patrones
def buscar_patron(texto, patrones):
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return match.group(0).strip()
    return None

# Extrae información de tarjeta de video (incluyendo gráficos integrados)
def extraer_video(texto):
    texto_preprocesado = cortar_en_memoria_ram(texto)

    video_info = buscar_patron(texto_preprocesado, PATRONES["tarjeta_video"])
    grafica_integrada = bool(buscar_patron(texto_preprocesado, PATRONES["grafica_integrada"]))

    tarjeta_mencionada = bool(video_info or grafica_integrada)

    if grafica_integrada:
        video_info = "Gráficos integrados"

    return tarjeta_mencionada, video_info, grafica_integrada

# Extrae tipo de gabinete
def extraer_gabinete(texto):
    frase = buscar_patron(texto, PATRONES["gabinete"])
    if frase:
        if "mid tower" in frase:
            return True, "Mid Tower"
        elif "formato reducido" in frase:
            return True, "Formato Reducido"
        else:
            return True, "Otro"
    return False, None

# Extrae información de fuente de poder: wattaje y certificación
# Extrae información de fuente de poder: wattaje y certificación
def extraer_fuente(texto):
    fuente_mencionada = False
    watt = None
    cert = None

    # Expandir reconocimiento para todo el texto, no solo patrones específicos
    texto = texto.lower()

    # Detectar presencia de fuente de poder
    if any(re.search(p, texto) for p in PATRONES["fuente_poder"]):
        fuente_mencionada = True

    # Wattaje - buscar expresiones como "750w", "750 watts", etc.
    watt_match = re.search(r'(\d{3,4})\s*(w|watts)', texto)
    if watt_match:
        watt = watt_match.group(1) + "W"

    # Certificación - capturar variantes de 80 plus
    cert_match = re.search(r'(80\s*plus\s*(gold|silver|bronze|platinum|titanium)?)|plus\s*(gold|silver|bronze|platinum|titanium)', texto)
    if cert_match:
        grupos = cert_match.groups()
        # Selección cuidadosa del nombre detectado
        for g in grupos[::-1]:  # priorizar el último no None
            if g and g.strip():
                cert = "Plus " + g.strip().title() if not g.lower().startswith("80") else g.strip().title()
                break

    if watt or cert:
        fuente_mencionada = True

    return fuente_mencionada, watt, cert


# Función principal de extracción por registro
def procesar_registro(contenido):
    texto = contenido.get("texto extraído y normalizado", "").lower()
    id_extraccion = contenido.get("id_extraccion", "")

    # Extracción por categoría
    tarjeta_mencionada, descripcion_tarjeta, integrada = extraer_video(texto)
    gabinete_mencionado, tipo_gabinete = extraer_gabinete(texto)
    fuente_mencionada, watts, certificacion = extraer_fuente(texto)

    return {
        "id_extraccion": id_extraccion,
        "tarjeta_video_mencionada": tarjeta_mencionada,
        "descripcion_tarjeta_video": descripcion_tarjeta,
        "grafica_integrada": integrada,
        "gabinete_mencionado": gabinete_mencionado,
        "tipo_gabinete": tipo_gabinete,
        "fuente_poder_mencionada": fuente_mencionada,
        "wattaje_fuente": watts,
        "certificacion_fuente": certificacion
    }

# Interfaz gráfica para seleccionar archivo
def seleccionar_archivo():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        title="Selecciona un archivo JSON",
        filetypes=[("Archivos JSON", "*.json")]
    )

# Procesamiento general del archivo
def procesar_archivo_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    resultados = {}
    for nombre_archivo, contenido in data.items():
        resultados[nombre_archivo] = procesar_registro(contenido)

    return resultados

# Guardar archivo JSON en la misma carpeta con prefijo "det_"
def guardar_resultado(original_path, resultados):
    carpeta = os.path.dirname(original_path)
    nombre_original = os.path.basename(original_path)
    nuevo_nombre = "det_" + nombre_original
    ruta_salida = os.path.join(carpeta, nuevo_nombre)

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

    return ruta_salida

# Función principal
def main():
    archivo = seleccionar_archivo()
    if not archivo:
        messagebox.showwarning("Aviso", "No se seleccionó ningún archivo.")
        return

    try:
        resultados = procesar_archivo_json(archivo)
        salida = guardar_resultado(archivo, resultados)
        messagebox.showinfo("Éxito", f"Archivo procesado exitosamente:\n{salida}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

if __name__ == "__main__":
    main()
