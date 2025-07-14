import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import re
import os

CONFIG_FILE = "patrones_config.json"

def cargar_todas_las_configuraciones():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_configuracion_por_nombre(nombre, data):
    todas = cargar_todas_las_configuraciones()
    todas[nombre] = data
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(todas, f, indent=4, ensure_ascii=False)

def extraer_patron_dinamico(texto, patrones_validos, patrones_excluir):
    texto = texto.lower()
    for patron in patrones_validos:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            valor = match.group(0).strip()
            if any(re.search(p, valor, re.IGNORECASE) for p in patrones_excluir):
                continue
            return valor
    return None

def crear_ventana_scrollable(root, titulo="Ventana", ancho=800, alto=500):
    """
    Crea una ventana Toplevel con un área scrollable vertical y devuelve:
    - la ventana
    - el frame interno donde insertar widgets
    """
    ventana = tk.Toplevel(root)
    ventana.title(titulo)
    ventana.geometry(f"{ancho}x{alto}")
    ventana.transient(root)
    ventana.grab_set()

    contenedor = tk.Frame(ventana)
    contenedor.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(contenedor)
    scrollbar = tk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    # Configura el scroll interno
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Scroll con la rueda del mouse
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    return ventana, scrollable_frame


class GestorPatronesApp:
    def __init__(self, root):
        self.todas_configuraciones = cargar_todas_las_configuraciones()
        self.configuracion_actual = tk.StringVar()

        if self.todas_configuraciones:
            primera_config = list(self.todas_configuraciones.keys())[0]
            self.configuracion_actual.set(primera_config)
            self.patrones = self.todas_configuraciones[primera_config]
        else:
            self.configuracion_actual.set("sin_nombre")
            self.patrones = {}

        self.componentes = list(self.patrones.keys()) or ["chipset"]
        self.componente_actual = tk.StringVar(value=self.componentes[0])

        self.root = root
        self.root.title("Gestor Formal de Patrones de Extracción")
        self.root.geometry("950x800")

        self._crear_interfaz()

    def _crear_interfaz(self):
        frame_selector = tk.LabelFrame(self.root, text="Configuración actual", padx=10, pady=5)
        frame_selector.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_selector, text="Seleccionar configuración:").pack(side=tk.LEFT)
        self.dropdown_config = tk.OptionMenu(
            frame_selector,
            self.configuracion_actual,
            *self.todas_configuraciones.keys(),
            command=self._cambiar_configuracion
        )
        self.dropdown_config.pack(side=tk.LEFT, padx=10)
        tk.Button(frame_selector, text="Cargar", command=self._cambiar_configuracion).pack(side=tk.LEFT)

        frame_comp = tk.LabelFrame(self.root, text="Gestión de Componentes", padx=10, pady=5)
        frame_comp.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_comp, text="Componente seleccionado:").pack(side=tk.LEFT)
        self.dropdown = tk.OptionMenu(frame_comp, self.componente_actual, *self.componentes, command=self._actualizar_listas)
        self.dropdown.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_comp, text="Agregar Componente", command=self._agregar_componente).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_comp, text="Eliminar Componente", command=self._eliminar_componente).pack(side=tk.LEFT, padx=5)

        frame_patrones = tk.Frame(self.root)
        frame_patrones.pack(fill="both", expand=True, padx=10, pady=5)

        frame_val = tk.LabelFrame(frame_patrones, text="Patrones Válidos")
        frame_val.pack(fill="both", expand=True, pady=(0, 10))

        frame_val_list = tk.Frame(frame_val)
        frame_val_list.pack(fill="both", expand=True)
        scroll_val = tk.Scrollbar(frame_val_list, orient="vertical")
        self.list_val = tk.Listbox(frame_val_list, yscrollcommand=scroll_val.set, height=4)
        scroll_val.config(command=self.list_val.yview)
        self.list_val.pack(side="left", fill="both", expand=True)
        scroll_val.pack(side="right", fill="y")

        frame_val_buttons = tk.Frame(frame_val)
        frame_val_buttons.pack(anchor="e", pady=5)
        tk.Button(frame_val_buttons, text="Agregar Patrón", command=lambda: self._agregar_patron("validos")).pack(side="left", padx=5)
        tk.Button(frame_val_buttons, text="Eliminar Patrón", command=lambda: self._eliminar_patron("validos")).pack(side="left", padx=5)

        frame_exc = tk.LabelFrame(frame_patrones, text="Patrones de Exclusión")
        frame_exc.pack(fill="both", expand=True)

        frame_exc_list = tk.Frame(frame_exc)
        frame_exc_list.pack(fill="both", expand=True)
        scroll_exc = tk.Scrollbar(frame_exc_list, orient="vertical")
        self.list_exc = tk.Listbox(frame_exc_list, yscrollcommand=scroll_exc.set, height=4)
        scroll_exc.config(command=self.list_exc.yview)
        self.list_exc.pack(side="left", fill="both", expand=True)
        scroll_exc.pack(side="right", fill="y")

        frame_exc_buttons = tk.Frame(frame_exc)
        frame_exc_buttons.pack(anchor="e", pady=5)
        tk.Button(frame_exc_buttons, text="Agregar Patrón", command=lambda: self._agregar_patron("excluir")).pack(side="left", padx=5)
        tk.Button(frame_exc_buttons, text="Eliminar Patrón", command=lambda: self._eliminar_patron("excluir")).pack(side="left", padx=5)

        frame_prueba = tk.LabelFrame(self.root, text="Área de Prueba de Extracción", padx=10, pady=5)
        frame_prueba.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(frame_prueba, text="Texto de prueba:").pack(anchor="w")

        frame_txt_prueba = tk.Frame(frame_prueba)
        frame_txt_prueba.pack(fill="both", expand=False)

        scroll_prueba = tk.Scrollbar(frame_txt_prueba, orient="vertical")
        self.txt_prueba = tk.Text(frame_txt_prueba, height=4, yscrollcommand=scroll_prueba.set)
        scroll_prueba.config(command=self.txt_prueba.yview)

        self.txt_prueba.pack(side="left", fill="both", expand=True)
        scroll_prueba.pack(side="right", fill="y")


        tk.Button(frame_prueba, text="Probar Extracción", command=self._probar_extraccion).pack(pady=5)

        tk.Label(frame_prueba, text="Resultado:", font=("Arial", 10, "bold")).pack(anchor="w")

        frame_txt_resultado = tk.Frame(frame_prueba)
        frame_txt_resultado.pack(fill="both", expand=False)

        scroll_resultado = tk.Scrollbar(frame_txt_resultado, orient="vertical")
        self.txt_resultado = tk.Text(frame_txt_resultado, height=4, state="disabled", bg="#f7f7f7", yscrollcommand=scroll_resultado.set)
        scroll_resultado.config(command=self.txt_resultado.yview)

        self.txt_resultado.pack(side="left", fill="both", expand=True)
        scroll_resultado.pack(side="right", fill="y")


        tk.Button(self.root, text="Guardar Configuración", command=self._guardar).pack(pady=10)
        self._actualizar_listas()

    def _actualizar_listas(self, *_):
        comp = self.componente_actual.get()
        self.list_val.delete(0, tk.END)
        self.list_exc.delete(0, tk.END)
        for p in self.patrones.get(comp, {}).get("validos", []):
            self.list_val.insert(tk.END, p)
        for p in self.patrones.get(comp, {}).get("excluir", []):
            self.list_exc.insert(tk.END, p)

    def _agregar_componente(self):
        nuevo = simpledialog.askstring("Nuevo Componente", "Ingrese nombre del nuevo componente:")
        if nuevo and nuevo not in self.patrones:
            self.patrones[nuevo] = {"validos": [], "excluir": []}
            self.componentes.append(nuevo)
            menu = self.dropdown["menu"]
            menu.add_command(label=nuevo, command=tk._setit(self.componente_actual, nuevo, self._actualizar_listas))
            self.componente_actual.set(nuevo)
            self._actualizar_listas()

    def _eliminar_componente(self):
        comp = self.componente_actual.get()
        if messagebox.askyesno("Confirmación", f"¿Eliminar componente '{comp}'?"):
            del self.patrones[comp]
            self.componentes.remove(comp)
            self.componente_actual.set(self.componentes[0] if self.componentes else "")
            self._actualizar_dropdown_componentes()
            self._actualizar_listas()

    def _agregar_patron(self, tipo):
        def guardar_patron():
            nuevo_patron = entry.get().strip()
            if nuevo_patron:
                componente = self.componente_actual.get()
                self.patrones[componente][tipo].append(nuevo_patron)
                (self.list_val if tipo == "validos" else self.list_exc).insert(tk.END, nuevo_patron)
                ventana.destroy()

        def copiar_patron(event, texto):
            ventana.clipboard_clear()
            ventana.clipboard_append(texto)
            ventana.update()

        ventana, scrollable_frame = crear_ventana_scrollable(
            self.root,
            titulo=f"Agregar patrón de tipo: {tipo.capitalize()}",
            ancho=850,
            alto=700
        )

        tk.Label(scrollable_frame, text="Ingrese el patrón Regex:", font=("Arial", 11, "bold")).pack(pady=(10, 0))
        entry = tk.Entry(scrollable_frame, width=100)
        entry.pack(pady=5, padx=10)

        ejemplos = [
            (r"\d", "Coincide con un dígito numérico (0–9).", "Texto: '650W' → Resultado: '6', '5', '0'"),
            (r"(intel|amd)", "Coincide con 'intel' o 'amd'.", "Texto: 'AMD B550' → Resultado: 'AMD'"),
            (r"\bpf2402\b", "Detecta el código 'pf2402' exacto.", "Texto: 'Modelo: pf2402' → Resultado: 'pf2402'")
        ]

        for simbolo, descripcion, ejemplo in ejemplos:
            marco = tk.Frame(scrollable_frame)
            marco.pack(anchor="w", pady=5, fill="x", padx=5)
            etiqueta_simbolo = tk.Label(marco, text=f"Patrón: {simbolo}", font=("Courier", 11, "bold"), fg="blue", cursor="hand2")
            etiqueta_simbolo.pack(anchor="w")
            etiqueta_simbolo.bind("<Double-1>", lambda e, txt=simbolo: copiar_patron(e, txt))
            tk.Label(marco, text=f"Descripción: {descripcion}", font=("Arial", 10)).pack(anchor="w", padx=20)
            tk.Label(marco, text=ejemplo, font=("Courier", 9), fg="gray").pack(anchor="w", padx=40)

        tk.Button(scrollable_frame, text="Guardar patrón", command=guardar_patron).pack(pady=15)

    def _eliminar_patron(self, tipo):
        lista = self.list_val if tipo == "validos" else self.list_exc
        sel = lista.curselection()
        if sel:
            idx = sel[0]
            comp = self.componente_actual.get()
            del self.patrones[comp][tipo][idx]
            lista.delete(idx)

    def _probar_extraccion(self):
        texto = self.txt_prueba.get("1.0", tk.END).strip().lower()
        resultados = []
        for comp, datos in self.patrones.items():
            valor = extraer_patron_dinamico(texto, datos.get("validos", []), datos.get("excluir", []))
            resultados.append(f"{comp.capitalize()}: {valor if valor else 'no menciona'}")
        self.txt_resultado.config(state="normal")
        self.txt_resultado.delete("1.0", tk.END)
        self.txt_resultado.insert(tk.END, "\n".join(resultados))
        self.txt_resultado.config(state="disabled")

    def _cambiar_configuracion(self, *_):
        seleccion = self.configuracion_actual.get()
        if seleccion in self.todas_configuraciones:
            self.patrones = self.todas_configuraciones[seleccion]
            self.componentes = list(self.patrones.keys())
            if self.componentes:
                self.componente_actual.set(self.componentes[0])
            else:
                self.componente_actual.set("")
            self._actualizar_dropdown_componentes()
            self._actualizar_listas()
        else:
            messagebox.showerror("Error", f"La configuración '{seleccion}' no se encuentra.")

    def _actualizar_dropdown_componentes(self):
        self.dropdown["menu"].delete(0, "end")
        for comp in self.componentes:
            self.dropdown["menu"].add_command(label=comp, command=tk._setit(self.componente_actual, comp, self._actualizar_listas))

    def _guardar(self):
        nombre = simpledialog.askstring("Guardar configuración", "Ingrese nombre para esta configuración:")
        if not nombre:
            return
        self.todas_configuraciones[nombre] = self.patrones
        guardar_configuracion_por_nombre(nombre, self.patrones)
        if nombre not in self.dropdown_config["menu"].entrycget(0, "label"):
            self.dropdown_config["menu"].add_command(
                label=nombre,
                command=tk._setit(self.configuracion_actual, nombre, self._cambiar_configuracion)
            )
        self.configuracion_actual.set(nombre)
        messagebox.showinfo("Guardado", f"La configuración '{nombre}' fue guardada correctamente.")

# Ejecutar aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = GestorPatronesApp(root)
    root.mainloop()
