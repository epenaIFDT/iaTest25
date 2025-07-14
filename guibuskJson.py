# interfaz_configurable_patrones.py

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import json
import re
import os

# ======================
# CARGA Y GUARDADO JSON
# ======================

CONFIG_FILE = "patrones_config.json"

def cargar_patrones():
    if not os.path.exists(CONFIG_FILE):
        return {
            "chipset": {
                "validos": [],
                "excluir": []
            }
        }
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_patrones(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ======================
# FUNCIÓN DE EXTRACCIÓN
# ======================

def extraer_chipset_dinamico(texto, patrones_validos, patrones_excluir):
    texto = texto.lower()

    for patron in patrones_validos:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            valor = match.group(0).strip()
            if any(re.search(p, valor, re.IGNORECASE) for p in patrones_excluir):
                continue
            return valor[0].upper() + valor[1:]
    return None

# ======================
# INTERFAZ GRÁFICA
# ======================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Patrones de Extracción")

        self.patrones = cargar_patrones()
        self.componentes = list(self.patrones.keys())
        self.componente_actual = tk.StringVar(value=self.componentes[0])

        self._crear_widgets()
        self._cargar_listas()

    def _crear_widgets(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        tk.Label(frame_top, text="Componente:").pack(side=tk.LEFT)
        self.dropdown = tk.OptionMenu(frame_top, self.componente_actual, *self.componentes, command=self._cambiar_componente)
        self.dropdown.pack(side=tk.LEFT)

        self.btn_nuevo = tk.Button(frame_top, text="Agregar componente", command=self._agregar_componente)
        self.btn_nuevo.pack(side=tk.LEFT, padx=10)

        # Lista de patrones válidos
        frame_validos = tk.LabelFrame(self.root, text="Patrones Válidos")
        frame_validos.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.list_validos = tk.Listbox(frame_validos)
        self.list_validos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._agregar_botones_patrones(frame_validos, self.list_validos, "validos")

        # Lista de patrones de exclusión
        frame_excluir = tk.LabelFrame(self.root, text="Patrones de Exclusión")
        frame_excluir.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.list_excluir = tk.Listbox(frame_excluir)
        self.list_excluir.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._agregar_botones_patrones(frame_excluir, self.list_excluir, "excluir")

        # Área de prueba
        frame_test = tk.LabelFrame(self.root, text="Texto de Prueba")
        frame_test.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.texto_prueba = tk.Text(frame_test, height=6)
        self.texto_prueba.pack(fill=tk.BOTH, expand=True)

        self.resultado = tk.Label(self.root, text="", fg="blue")
        self.resultado.pack()

        btn_test = tk.Button(self.root, text="Probar Extracción", command=self._probar_extraccion)
        btn_test.pack(pady=10)

        btn_guardar = tk.Button(self.root, text="Guardar Configuración", command=self._guardar_config)
        btn_guardar.pack(pady=5)

    def _agregar_botones_patrones(self, parent, listbox, tipo):
        frame_btns = tk.Frame(parent)
        frame_btns.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Button(frame_btns, text="Agregar", command=lambda: self._agregar_patron(listbox, tipo)).pack(fill=tk.X)
        tk.Button(frame_btns, text="Eliminar", command=lambda: self._eliminar_patron(listbox, tipo)).pack(fill=tk.X)

    def _agregar_patron(self, listbox, tipo):
        def guardar_patron():
            nuevo_patron = entry.get().strip()
            if nuevo_patron:
                componente = self.componente_actual.get()
                self.patrones[componente][tipo].append(nuevo_patron)
                listbox.insert(tk.END, nuevo_patron)
                ventana.destroy()

        def copiar_a_portapapeles(event, texto):
            ventana.clipboard_clear()
            ventana.clipboard_append(texto)
            ventana.update()

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Nuevo patrón {tipo}")
        ventana.geometry("750x700")
        ventana.transient(self.root)
        ventana.grab_set()

        tk.Label(ventana, text="Escribe el patrón Regex:", font=("Arial", 11, "bold")).pack(pady=5)
        entry = tk.Entry(ventana, width=100)
        entry.pack(pady=5)

        # Marco principal con scroll
        frame_scroll = tk.LabelFrame(ventana, text="Guía Detallada de Comodines y Patrones")
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(frame_scroll)
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        contenido = tk.Frame(canvas)

        contenido.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=contenido, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ejemplos = [
            {
                "simbolo": r"\d",
                "descripcion": "Coincide con un dígito (0-9). Se usa cuando esperas números.",
                "detalle": "Ejemplo: \\d{4} → Coincide con '2024', '1234'. Útil para años, wattaje, modelos."
            },
            {
                "simbolo": r"\w",
                "descripcion": "Carácter alfanumérico (a-z, A-Z, 0-9, _). Útil para nombres, etiquetas técnicas.",
                "detalle": "Ejemplo: \\w+ → Coincide con 'intel', 'abc_123', 'Z590'."
            },
            {
                "simbolo": r"\s",
                "descripcion": "Coincide con cualquier espacio, tabulación o salto de línea.",
                "detalle": "Ejemplo: palabra\\sotra → 'palabra otra' (con un espacio entre palabras)."
            },
            {
                "simbolo": r".",
                "descripcion": "Coincide con cualquier carácter excepto salto de línea.",
                "detalle": "Ejemplo: a.b → 'a1b', 'a*b', 'axb'. No coincide con 'ab'."
            },
            {
                "simbolo": r"[^a-z]",
                "descripcion": "Coincide con cualquier carácter que no sea minúscula (de 'a' a 'z').",
                "detalle": "Ejemplo: [^a-z]{2} → '12', '$A'. Útil para evitar letras específicas."
            },
            {
                "simbolo": r"(intel|amd)",
                "descripcion": "Coincide con 'intel' o 'amd'. Agrupación con alternativas.",
                "detalle": "Ejemplo: (intel|amd) → Coincide con 'intel i5' o 'amd ryzen'."
            },
            {
                "simbolo": r"[a-z]*\d{3,4}",
                "descripcion": "Letras opcionales seguidas de 3 o 4 dígitos. Ideal para chipsets.",
                "detalle": "Ejemplo: 'z790', 'b550', 'x670e'."
            },
            {
                "simbolo": r"chipset\s*:\s*(intel|amd)?\s*[a-z]*\d{3,4}",
                "descripcion": "Busca 'chipset:' seguido de fabricante opcional y código técnico.",
                "detalle": "Ejemplo: 'chipset: intel z790', 'chipset: b550'. Maneja espacios opcionales."
            },
            {
                "simbolo": r"chipset\s*(trx50|z79\s*0|z790)",
                "descripcion": "Detecta palabras 'chipset' seguidas de modelos específicos.",
                "detalle": "Ejemplo: 'chipset TRX50', 'chipset z790'. Coincide si hay espacios intermedios ('z79 0')."
            },
            {
                "simbolo": r"(intel|amd)\s*(trx50|z79\s*0|z790)",
                "descripcion": "Coincide con fabricante seguido del modelo de chipset.",
                "detalle": "Ejemplo: 'Intel Z790', 'AMD TRX50'. Permite variaciones con espacio entre letras y dígitos."
            },
            {
                "simbolo": r"\bpf2402\b",
                "descripcion": "Busca exactamente la palabra 'pf2402'. Rodeado por delimitadores.",
                "detalle": "Ejemplo: 'Modelo: PF2402'. No coincide si está pegado a otros caracteres sin separación."
            },
            {
                "simbolo": r"\bpf2702\b",
                "descripcion": "Igual al anterior, para otra versión/modelo: 'pf2702'.",
                "detalle": "Ejemplo: 'Código PF2702', pero no 'XPF2702Y'."
            },
            {
                "simbolo": r"\brs232\b",
                "descripcion": "Detecta el estándar RS232 como palabra completa.",
                "detalle": "Ejemplo: 'Conector RS232'. Coincide solo si está separado como palabra, no dentro de otra."
            },
            {
                "simbolo": r"\b(full\s*tower|fulltower|full\s*torre|torre\s*(grande)?|tipo\s*torre|gabinete\s+torre|forma\s+torre|torre\s+pr)\b",
                "descripcion": "Coincide con múltiples formas de referirse a gabinetes grandes (Full Tower).",
                "detalle": "Ejemplo: 'gabinete torre', 'torre grande', 'full tower', 'forma torre'. Detecta muchas formas comunes."
            },
            {
                "simbolo": r"\b(formato\s+reducido|small\s+form\s*factor|sff|mini\s*-?\s*itx|micro\s*-?\s*atx|mini\s*-?\s*torre|minitorre|mini\s*torre)\b",
                "descripcion": "Identifica descripciones de gabinetes compactos o mini torres.",
                "detalle": "Ejemplo: 'Mini-ITX', 'formato reducido', 'SFF', 'minitorre'. Maneja variantes con y sin guiones."
            },
            {
                "simbolo": r"\b(mid\s*tower|midtower|medium\s*tower|mediumtower)\b",
                "descripcion": "Detecta gabinetes tipo Mid Tower en diferentes formas escritas.",
                "detalle": "Ejemplo: 'Mid Tower', 'midtower', 'mediumtower'. Ideal para categorizar chasis medianos."
            }
        ]

        for ej in ejemplos:
            marco = tk.Frame(contenido)
            marco.pack(anchor="w", pady=5, fill=tk.X, padx=10)

            simbolo_label = tk.Label(marco, text=ej["simbolo"], font=("Courier", 11, "bold"), fg="blue", cursor="hand2")
            simbolo_label.pack(anchor="w")
            simbolo_label.bind("<Double-1>", lambda e, txt=ej["simbolo"]: copiar_a_portapapeles(e, txt))

            desc_label = tk.Label(marco, text="➤ " + ej["descripcion"], font=("Arial", 10, "italic"))
            desc_label.pack(anchor="w", padx=15)

            detalle_label = tk.Label(marco, text=ej["detalle"], font=("Arial", 9), fg="gray")
            detalle_label.pack(anchor="w", padx=30)

        tk.Button(ventana, text="Guardar patrón", command=guardar_patron).pack(pady=15)





    def _eliminar_patron(self, listbox, tipo):
        seleccion = listbox.curselection()
        if seleccion:
            index = seleccion[0]
            componente = self.componente_actual.get()
            del self.patrones[componente][tipo][index]
            listbox.delete(index)

    def _cambiar_componente(self, value):
        self._cargar_listas()

    def _cargar_listas(self):
        componente = self.componente_actual.get()
        self.list_validos.delete(0, tk.END)
        self.list_excluir.delete(0, tk.END)

        for p in self.patrones[componente]["validos"]:
            self.list_validos.insert(tk.END, p)
        for p in self.patrones[componente]["excluir"]:
            self.list_excluir.insert(tk.END, p)

    def _probar_extraccion(self):
        texto = self.texto_prueba.get("1.0", tk.END).strip()
        componente = self.componente_actual.get()
        patrones_val = self.patrones[componente]["validos"]
        patrones_exc = self.patrones[componente]["excluir"]

        resultado = extraer_chipset_dinamico(texto, patrones_val, patrones_exc)
        self.resultado.config(text=f"Resultado: {resultado if resultado else 'No encontrado'}")

    def _guardar_config(self):
        guardar_patrones(self.patrones)
        messagebox.showinfo("Guardado", "La configuración fue guardada exitosamente.")

    def _agregar_componente(self):
        nuevo = simpledialog.askstring("Nuevo componente", "Nombre del nuevo componente:")
        if nuevo and nuevo not in self.patrones:
            self.patrones[nuevo] = {"validos": [], "excluir": []}
            self.componentes.append(nuevo)
            menu = self.dropdown["menu"]
            menu.add_command(label=nuevo, command=tk._setit(self.componente_actual, nuevo, self._cambiar_componente))
            self.componente_actual.set(nuevo)
            self._cargar_listas()

# ======================
# EJECUCIÓN PRINCIPAL
# ======================

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
