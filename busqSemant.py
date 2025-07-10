import json
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import re
from tkinter import filedialog
import tkinter as tk

# =====================
# CONFIGURACIÓN INICIAL
# =====================
modelo = SentenceTransformer('all-MiniLM-L6-v2')


def extraer_fuente(texto):
    """Extrae watts y certificaciones de fuente de poder."""
    watts = re.findall(r"\b\d{3,4}\s*W\b", texto, re.IGNORECASE)
    certificaciones = re.findall(r"80\s*\+?\s*\w+", texto, re.IGNORECASE)
    return {
        "watts": watts,
        "certificaciones": certificaciones
    }


def realizar_busqueda(textos, nombres, consulta, top_k=5):
    vectores = modelo.encode(textos)
    index = faiss.IndexFlatL2(vectores[0].shape[0])
    index.add(np.array(vectores))

    vector_q = modelo.encode([consulta])
    _, indices = index.search(np.array(vector_q), top_k)
    return [(nombres[i], textos[i]) for i in indices[0]]


def cargar_json_desde_dialogo():
    """Abre un diálogo de archivos sin usar tkinter GUI principal."""
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    archivo = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
    return archivo


# =====================
# PROCESO PRINCIPAL
# =====================

def main():
    archivo_json = cargar_json_desde_dialogo()

    if not archivo_json:
        print("❌ No se seleccionó ningún archivo.")
        return

    try:
        with open(archivo_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("❌ Error al cargar el archivo:", e)
        return

    textos = []
    nombres = []

    for nombre_archivo, contenido in data.items():
        texto = contenido.get("texto extraído y normalizado", "")
        textos.append(texto)
        nombres.append(nombre_archivo)

    consultas = {
        "Tarjeta de video / Gráfica": "tarjeta de video o tarjeta gráfica",
        "Gabinete / Case": "gabinete o case",
        "Fuente de poder": "fuente de poder con watts y certificación"
    }

    for categoria, consulta in consultas.items():
        print(f"\n🧠 {categoria} — Consulta: \"{consulta}\"")
        print("-" * 100)
        resultados = realizar_busqueda(textos, nombres, consulta)

        for nombre, texto in resultados:
            print(f"📄 Documento: {nombre}")

            if categoria == "Fuente de poder":
                extra = extraer_fuente(texto)
                print(f"   🔌 Watts detectados: {', '.join(extra['watts']) or 'No detectado'}")
                print(f"   🏅 Certificaciones: {', '.join(extra['certificaciones']) or 'No detectado'}")

            print("   📜 Extracto:")
            print(f"   {texto[:500].replace('\n', ' ')}...\n")


if __name__ == "__main__":
    main()
