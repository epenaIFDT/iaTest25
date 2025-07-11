# extraccion_componentes_optimizado.py

import json
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict, Counter

# ==========================
# CONFIGURACIÓN DE PATRONES
# ==========================

PATRONES = {
    "tarjeta_video": [
        r'tarjeta\s+de\s+(video|gráfica)[^\n,;]*',
        r'video\s+tarjeta\s+de\s+(video|gráfica)[^\n,;]*',
        r'nvidia\s.*?rtx\s?\d{3,4}[^,;\n]*',
        r'rtx\s\d{3,4}[^,;\n]*',
        r'gtx\s\d{3,4}[^,;\n]*',
        r'rx\s\d{3,4}[^,;\n]*',
        r'geforce\s.*?rtx\s?\d{3,4}[^,;\n]*',
        r'geforce\s.*?gtx\s?\d{3,4}[^,;\n]*',
        r'geforce\s.*?rx\s?\d{3,4}[^,;\n]*',
        r'tarjeta\s+de\s+video\s+rtx\s*\d{3,4}[^,;\n]*',
        r'tarjeta\s+de\s+video\s+rtx\s*\d{3,4}.*?\d{1,2}\s*gb.*?gddr\d.*?ecc'
    ],
    "grafica_integrada": [
        r'gr[áa]ficos\s+(uhd|intel|amd|vega)[^\n,;]*',
        r'video\s+integrado[^\n,;]*',
        r'gr[áa]ficos\s+integrados[^\n,;]*',
        r'integrada|integrados|integrado',
        r'intel\s+uhd\s+graphics\s+7\d{2}',
        r'gr[áa]ficos\s+integrados'
    ],

}

# ==========================
# FUNCIONES DE UTILIDAD
# ==========================

def buscar_patron(texto, patrones):
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None

def cortar_por_claves(texto, claves, offset=0):
    texto = texto.lower()[offset:] if offset else texto.lower()
    posiciones = [re.search(clave, texto).start() for clave in claves if re.search(clave, texto)]
    return texto[:min(posiciones)] if posiciones else texto

def normalizar_espacios_guiones(texto):
    texto = texto.lower()
    texto = re.sub(r'[\s\-]+', ' ', texto)
    return texto.strip()

# ==========================
# FUNCIONES DE EXTRACCIÓN
# ==========================

def extraer_video(texto):
    texto = texto.lower()
    patron_dedicado = buscar_patron(texto, PATRONES["tarjeta_video"])
    patron_integrado = buscar_patron(texto, PATRONES["grafica_integrada"])
    
    if patron_dedicado:
        return True, patron_dedicado, False
    if patron_integrado:
        return True, patron_integrado, True
    return False, None, False

def extraer_gabinete(texto: str):
    texto = normalizar_espacios_guiones(texto)

    patrones_tipo = {
        "Mid Tower": [
            r'\b(mid\s*tower|midtower|medium\s*tower|mediumtower)\b'
        ],
        "Formato reducido": [
            r'\b(formato\s+reducido|small\s+form\s*factor|sff|mini\s*-?\s*itx|micro\s*-?\s*atx|mini\s*-?\s*torre|minitorre|mini\s*torre)\b'
        ],
        "Full Tower": [
            r'\b(full\s*tower|fulltower|full\s*torre|torre\s*(grande)?|tipo\s*torre|gabinete\s+torre|forma\s+torre|torre\s+pr)\b'
        ]
    }

    for tipo in ["Mid Tower", "Formato reducido", "Full Tower"]:
        for patron in patrones_tipo[tipo]:
            if re.search(patron, texto, re.IGNORECASE):
                return True, tipo

    if "gabinete" in texto or "torre" in texto:
        return True, None

    return False, None

def extraer_fuente(texto):
    texto = texto.lower()

    # Palabras clave que indican presencia de fuente
    claves_fuente = [
        r'fuente\s+de\s+poder',
        r'\bfuente\b',
        r'wattaje',
        r'watt\b',
        r'certificación',
        r'certificado',
        r'\bw\b'
    ]

    mencionada = any(re.search(p, texto) for p in claves_fuente)

    # Wattaje (ej. "500W", "750 watts")
    match_watt = re.search(r'(\d{3,4})\s*(w|watts)', texto)
    watt_val = f"{match_watt.group(1)}W" if match_watt else None

    # Certificación 80 Plus
    match_cert = re.search(r'(80\s*plus\s*(gold|silver|bronze|platinum|titanium))|plus\s*(gold|silver|bronze|platinum|titanium)', texto)
    cert_val = None
    if match_cert:
        for g in reversed(match_cert.groups()):
            if g:
                cert_val = g.strip().title() if g.lower().startswith("80") else "Plus " + g.strip().title()
                break

    return mencionada or bool(watt_val or cert_val), watt_val, cert_val


def extraer_chipset(texto):
    texto = texto.lower()

    # Patrones válidos
    patrones_validos = [
        r'chipset\s*:\s*(intel|amd)?\s*[a-z]*\d{3,4}',
        r'(intel|amd)\s*[a-z]{1,4}\d{3,4}',
        r'\b[a-z]{1,2}\d{3,4}\b(?=\s+armada|\s+serie)?',
        r'chipset\s+integrado',
        r'chipset\s+serie\s+[a-z0-9]+',
        r'mainboard\s+chipset\s+serie\s+[a-z0-9]+',
        r'intel\s+serie\s+[a-z0-9]+',
        r'amd\s+serie\s+[a-z0-9]+',
        r'chipset\s*(trx50|z79\s*0|z790)',
        r'(intel|amd)\s*(trx50|z79\s*0|z790)'
    ]

    # Patrones que NO deben considerarse chipset (negativos)
    patrones_excluir = [
        r'\ba5000\b',
        r'\ba6000\b',
        r'\bpf2402\b',
        r'\bpf2702\b',
        r'\brs232\b',
        r'\brx7600\b'  # Evita confundir con GPU Radeon RX
    ]

    # Buscar patrones válidos
    for patron in patrones_validos:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            valor = match.group(0).strip()

            # Validar contra patrones excluidos
            if any(re.search(p, valor) for p in patrones_excluir):
                continue

            return valor[0].upper() + valor[1:]

    return None





# ==========================
# PROCESAMIENTO DE REGISTROS
# ==========================

def procesar_registro(contenido):
    texto = contenido.get("texto extraído y normalizado", "").lower()
    id_extraccion = contenido.get("id_extraccion", "")
    
    tarjeta_mencionada, descripcion_tarjeta, integrada = extraer_video(texto)
    gabinete_mencionado, tipo_gabinete = extraer_gabinete(texto)
    fuente_mencionada, watts, certificacion = extraer_fuente(texto)
    chipset = extraer_chipset(texto)

    return {
        "id_extraccion": id_extraccion,
        "tarjeta_video_mencionada": tarjeta_mencionada,
        "descripcion_tarjeta_video": descripcion_tarjeta,
        "grafica_integrada": integrada,
        "gabinete_mencionado": gabinete_mencionado,
        "tipo_gabinete": tipo_gabinete,
        "fuente_poder_mencionada": fuente_mencionada,
        "wattaje_fuente": watts,
        "certificacion_fuente": certificacion,
        "chipset": chipset
    }

def revisar_y_limpiar_video(data, resultados):
    for archivo, contenido in data.items():
        texto = contenido.get("texto extraído y normalizado", "").lower()
        tarjeta_mencionada, descripcion, integrada = extraer_video(texto)
        resultados[archivo]["tarjeta_video_mencionada"] = tarjeta_mencionada
        resultados[archivo]["descripcion_tarjeta_video"] = descripcion
        resultados[archivo]["grafica_integrada"] = integrada

# ==========================
# INTERFAZ Y ARCHIVOS
# ==========================

def seleccionar_archivo():
    tk.Tk().withdraw()
    return filedialog.askopenfilename(
        title="Selecciona un archivo JSON",
        filetypes=[("Archivos JSON", "*.json")]
    )

def procesar_archivo_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {nombre: procesar_registro(contenido) for nombre, contenido in data.items()}, data

def guardar_resultado(original_path, resultados):
    carpeta = os.path.dirname(original_path)
    nombre_original = os.path.basename(original_path)
    ruta_salida = os.path.join(carpeta, "det_" + nombre_original)

    claves_corte = [
        "memoria ram", "interfaces", "memoria:", "4xdisplayport", "w6d",
        "wotw", "w6t", "pantalla lcd", "chipset", "microsoft office", "p rometheus"
    ]

    for info in resultados.values():
        desc = info.get("descripcion_tarjeta_video")
        if desc and isinstance(desc, str):
            info["descripcion_tarjeta_video"] = cortar_por_claves(desc, claves_corte).strip()

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)
    return ruta_salida

def generar_log(resultados, ruta_original):
    carpeta = os.path.dirname(ruta_original)
    nombre_log = "log_" + os.path.splitext(os.path.basename(ruta_original))[0] + ".txt"
    ruta_log = os.path.join(carpeta, nombre_log)

    booleanas = ["tarjeta_video_mencionada", "grafica_integrada", "gabinete_mencionado", "fuente_poder_mencionada"]
    textuales = ["descripcion_tarjeta_video", "tipo_gabinete", "wattaje_fuente", "certificacion_fuente", "chipset"]

    resumen = defaultdict(Counter)
    con_falsos = [n for n, d in resultados.items() if sum(1 for k in booleanas if not d.get(k)) > 1]

    for n, info in resultados.items():
        for k in textuales:
            val = info.get(k)
            if isinstance(val, str) and val.strip():
                resumen[k][val.strip()] += 1

    with open(ruta_log, 'w', encoding='utf-8') as f:
        f.write("ARCHIVOS CON MÁS DE UNA CARACTERÍSTICA FALSE:\n")
        for n in con_falsos:
            f.write(f"- {n}\n")
        f.write("\nRESUMEN DE VALORES EXTRAÍDOS AGRUPADOS POR CATEGORÍA:\n")
        for cat, conteo in sorted(resumen.items()):
            total = sum(conteo.values())
            f.write(f"\n[{cat.upper()}] (Total: {total})\n")
            for val, cant in sorted(conteo.items()):
                f.write(f'"{val}" - ({cant} veces)\n')
    return ruta_log

# ==========================
# FUNCIÓN PRINCIPAL
# ==========================

def main():
    archivo = seleccionar_archivo()
    if not archivo:
        messagebox.showwarning("Aviso", "No se seleccionó ningún archivo.")
        return
    try:
        resultados, data = procesar_archivo_json(archivo)
        revisar_y_limpiar_video(data, resultados)
        salida = guardar_resultado(archivo, resultados)
        ruta_log = generar_log(resultados, archivo)
        messagebox.showinfo("Éxito", f"Archivo procesado exitosamente:\n{salida}\n\nResumen generado en:\n{ruta_log}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

if __name__ == "__main__":
    main()
