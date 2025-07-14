import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import io

class TableCombinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Combinador de Tablas para Excel (sin encabezados)")
        self.root.geometry("1200x700")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(3, weight=1)

        self._setup_ui()

    def _setup_ui(self):
        # Etiquetas
        ttk.Label(self.root, text="Tabla 1 (pega desde Excel sin encabezados):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(self.root, text="Tabla 2 (pega desde Excel sin encabezados):").grid(row=0, column=1, sticky="w", padx=10, pady=5)

        # Áreas de texto para entrada
        self.input1 = tk.Text(self.root, height=10, wrap="none")
        self.input1.grid(row=1, column=0, padx=10, sticky="nsew")
        self.input2 = tk.Text(self.root, height=10, wrap="none")
        self.input2.grid(row=1, column=1, padx=10, sticky="nsew")

        # Botones de acción
        frame_btns = tk.Frame(self.root)
        frame_btns.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(frame_btns, text="🔄 Cargar y Mostrar Tablas", command=self.load_tables).pack(side="left", padx=5)
        ttk.Button(frame_btns, text="🧮 Combinar Tablas", command=self.combine_tables).pack(side="left", padx=5)
        ttk.Button(frame_btns, text="📋 Copiar Resultado", command=self.copy_to_clipboard).pack(side="left", padx=5)
        ttk.Button(frame_btns, text="🧹 Limpiar Todo", command=self.clear_all).pack(side="left", padx=5)

        # Visualización de las tablas
        self.tree1 = ttk.Treeview(self.root)
        self.tree2 = ttk.Treeview(self.root)
        self.tree1.grid(row=3, column=0, padx=10, sticky="nsew")
        self.tree2.grid(row=3, column=1, padx=10, sticky="nsew")

        ttk.Label(self.root, text="Resultado combinado:").grid(row=4, column=0, columnspan=2, sticky="w", padx=10)
        self.tree_result = ttk.Treeview(self.root)
        self.tree_result.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.status = ttk.Label(self.root, text="")
        self.status.grid(row=6, column=0, columnspan=2)

    def parse_text_to_df(self, text):
        try:
            # Leer como tabla sin encabezado
            df = pd.read_csv(io.StringIO(text.strip()), sep="\t", header=None)
            df.columns = [f"Col{i+1}" for i in range(df.shape[1])]
            return df
        except Exception as e:
            raise ValueError(f"Error al leer datos: {e}")

    def _display_dataframe(self, tree, df):
        tree.delete(*tree.get_children())
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"

        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

    def load_tables(self):
        try:
            text1 = self.input1.get("1.0", tk.END)
            text2 = self.input2.get("1.0", tk.END)

            self.df1 = self.parse_text_to_df(text1)
            self.df2 = self.parse_text_to_df(text2)

            self._display_dataframe(self.tree1, self.df1)
            self._display_dataframe(self.tree2, self.df2)

            self.status.config(text="✅ Tablas cargadas correctamente", foreground="green")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status.config(text="❌ Error al cargar tablas", foreground="red")

    def combine_tables(self):
        try:
            if self.df1.empty or self.df2.empty:
                raise ValueError("Debe cargar ambas tablas antes de combinar.")

            # Producto cartesiano
            self.combined_df = self.df1.merge(self.df2, how='cross')
            self._display_dataframe(self.tree_result, self.combined_df)

            self.status.config(text="✅ Tablas combinadas exitosamente", foreground="blue")
        except Exception as e:
            messagebox.showerror("Error al combinar", str(e))
            self.status.config(text="❌ Error al combinar", foreground="red")

    def copy_to_clipboard(self):
        try:
            if self.combined_df.empty:
                raise ValueError("No hay datos combinados para copiar.")
            
            output_text = self.combined_df.to_csv(
                sep="\t",
                index=False,
                header=False,
                lineterminator="\n"
            ).strip()

            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            self.root.update()
            self.status.config(text="📋 Resultado copiado al portapapeles (sin encabezado)", foreground="blue")
        except Exception as e:
            messagebox.showerror("Error al copiar", str(e))
            self.status.config(text="❌ Error al copiar", foreground="red")

    def clear_all(self):
        self.input1.delete("1.0", tk.END)
        self.input2.delete("1.0", tk.END)

        for tree in [self.tree1, self.tree2, self.tree_result]:
            tree.delete(*tree.get_children())
            tree["columns"] = []
            tree["show"] = ""

        self.status.config(text="🧹 Datos limpiados", foreground="gray")
        self.df1 = pd.DataFrame()
        self.df2 = pd.DataFrame()
        self.combined_df = pd.DataFrame()

if __name__ == "__main__":
    root = tk.Tk()
    app = TableCombinerApp(root)
    root.mainloop()
