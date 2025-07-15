import sys
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QStyleFactory, QCheckBox, QDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from itertools import product


# ──────────────────────────────
# UTILIDADES
# ──────────────────────────────

def wrap_text(text: str, max_len: int = 15) -> str:
    """Divide texto largo por palabras respetando longitud máxima por línea."""
    if len(text) <= max_len:
        return text
    parts = text.split(" ")
    lines, current = [], ""
    for word in parts:
        if len(current + " " + word) > max_len:
            lines.append(current.strip())
            current = word
        else:
            current += " " + word
    lines.append(current.strip())
    return "\n".join(lines)


def enable_dark_mode(widget):
    widget.setStyleSheet("""
        QWidget { background-color: #2b2b2b; color: #ffffff; }
        QHeaderView::section { background-color: #3c3c3c; color: #ffffff; }
        QTableWidget { gridline-color: #555; alternate-background-color: #444; }
    """)


# ──────────────────────────────
# VENTANA DE PREVISUALIZACIÓN
# ──────────────────────────────

class PreviewDialog(QDialog):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Previsualización de la Exportación")
        self.resize(1400, 700)

        table = QTableWidget(len(df), len(df.columns))
        table.setHorizontalHeaderLabels(df.columns)
        table.setAlternatingRowColors(True)
        table.setFont(QFont("Arial", 10))

        for r in range(len(df)):
            for c in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[r, c]))
                item.setFlags(Qt.ItemIsEnabled)
                table.setItem(r, c, item)

        table.resizeColumnsToContents()

        layout = QVBoxLayout()
        layout.addWidget(table)
        self.setLayout(layout)


# ──────────────────────────────
# DIÁLOGO DE AGRUPACIÓN DE COLUMNAS
# ──────────────────────────────

from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QLineEdit, QGroupBox, QScrollArea

class GroupSelectionDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agrupar columnas por componente")
        self.resize(950, 600)
        self.columns = columns
        self.groups = []

        self.available_list = QListWidget()
        self.available_list.addItems(columns)
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        self.available_list.itemSelectionChanged.connect(self.update_preview)

        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(100)

        self.groups_container = QListWidget()
        self.groups_container.setDragDropMode(QListWidget.InternalMove)
        self.groups_container.setSelectionMode(QListWidget.NoSelection)

        self.add_group_btn = QPushButton("➕ Agregar Grupo")
        self.add_group_btn.clicked.connect(self.add_group)

        self.accept_btn = QPushButton("✅ Confirmar Grupos")
        self.accept_btn.clicked.connect(self.accept_groups)

        # Layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Lista de Componentes"))
        left_layout.addWidget(self.available_list)
        left_layout.addWidget(QLabel("Valores únicos del componente seleccionado"))
        left_layout.addWidget(self.preview_list)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Grupos Definidos (elige eje Y)"))
        right_layout.addWidget(self.groups_container)

        layout = QHBoxLayout()
        layout.addLayout(left_layout, 40)
        layout.addLayout(right_layout, 60)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self.add_group_btn)
        footer.addWidget(self.accept_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(footer)
        self.setLayout(main_layout)

    def update_preview(self):
        self.preview_list.clear()
        selected_items = self.available_list.selectedItems()
        if not selected_items or not hasattr(self.parent(), 'df'):
            return

        df = self.parent().df
        selected_column = selected_items[0].text()
        if selected_column in df.columns:
            values = df[selected_column].dropna().astype(str).unique().tolist()
            self.preview_list.addItems(values[:100])

    def add_group(self):
        selected_items = self.available_list.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.warning(self, "Mínimo 2 columnas", "Debe seleccionar al menos dos columnas.")
            return

        selected_columns = [item.text() for item in selected_items]

        # Crear interfaz de grupo
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        name_input = QLineEdit()
        name_input.setText("Grupo")
        name_input.setPlaceholderText("Nombre del grupo")
        layout.addWidget(name_input)

        layout.addWidget(QLabel("Seleccionar columna para eje Y (filas):"))
        y_selector = QListWidget()
        y_selector.setMaximumHeight(50)
        y_selector.setSelectionMode(QListWidget.SingleSelection)
        y_selector.addItems(selected_columns)
        layout.addWidget(y_selector)

        layout.addWidget(QLabel("Columnas incluidas:"))
        for col in selected_columns:
            layout.addWidget(QLabel(f" - {col}"))

        remove_btn = QPushButton("❌ Eliminar Grupo")
        remove_btn.clicked.connect(lambda _, w=container: self.remove_group_widget(w))
        layout.addWidget(remove_btn)

        container.setLayout(layout)

        item = QListWidgetItem()
        item.setSizeHint(container.sizeHint())
        self.groups_container.addItem(item)
        self.groups_container.setItemWidget(item, container)

    def remove_group_widget(self, widget):
        for i in range(self.groups_container.count()):
            item = self.groups_container.item(i)
            if self.groups_container.itemWidget(item) == widget:
                self.groups_container.takeItem(i)
                widget.setParent(None)
                break

    def accept_groups(self):
        self.groups = []
        for i in range(self.groups_container.count()):
            item = self.groups_container.item(i)
            widget = self.groups_container.itemWidget(item)

            # Extraer columnas
            labels = [w.text() for w in widget.findChildren(QLabel) if w.text().startswith(" - ")]
            columns = [text[3:] for text in labels]

            # Eje Y
            y_selector = widget.findChild(QListWidget)
            if not y_selector or y_selector.selectedItems() == []:
                QMessageBox.warning(self, "Eje Y no definido", "Seleccione una columna para el eje Y en cada grupo.")
                return
            eje_y = y_selector.selectedItems()[0].text()

            # Nombre personalizado
            name_input = widget.findChild(QLineEdit)
            nombre = name_input.text().strip()

            self.groups.append({
                "columns": columns,
                "eje_y": eje_y,
                "nombre": nombre
            })

        if not self.groups:
            QMessageBox.warning(self, "Sin grupos", "Debe definir al menos un grupo.")
            return
        self.accept()






# ──────────────────────────────
# VENTANA PRINCIPAL
# ──────────────────────────────

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Validador de Configuraciones y Componentes")
        self.resize(1600, 900)
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        enable_dark_mode(self)

        # Datos
        self.df = None
        self.config_col = None
        self.validation = {}
        self.tabs = QTabWidget()

        # Interfaz
        self._setup_ui()

    def _setup_ui(self):
        self.title = QLabel("Seleccione qué combinaciones son válidas")
        self.title.setFont(QFont("Arial", 14, QFont.Bold))

        self.load_btn = QPushButton("📂 Cargar CSV")
        self.preview_btn = QPushButton("👁️ Previsualizar")
        self.export_btn = QPushButton("💾 Exportar CSV filtrado")
        self.stats_label = QLabel("Estadísticas: -")
        self.theme_toggle = QCheckBox("Modo claro / oscuro")
        self.theme_toggle.setChecked(True)

        self.load_btn.clicked.connect(self.load_csv)
        self.preview_btn.clicked.connect(self.preview_data)
        self.export_btn.clicked.connect(self.export_csv)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)

        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.theme_toggle)
        button_layout.addStretch()
        button_layout.addWidget(self.stats_label)

        self.tabs.currentChanged.connect(self.update_stats)
        self.manage_groups_btn = QPushButton("🛠️ Administrar Grupos")
        self.manage_groups_btn.clicked.connect(self.manage_groups)
        button_layout.addWidget(self.manage_groups_btn)


        main_layout = QVBoxLayout()
        main_layout.addWidget(self.title)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def toggle_theme(self, state):
        if state == Qt.Checked:
            enable_dark_mode(self)
        else:
            self.setStyleSheet("")

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo CSV", "", "CSV files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
            try:
                self.df = pd.read_csv(file_path, encoding='utf-8', sep=delimiter)
            except UnicodeDecodeError:
                self.df = pd.read_csv(file_path, encoding='utf-16', sep=delimiter)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        if self.df.shape[1] < 2:
            QMessageBox.warning(self, "Archivo inválido", "Debe contener al menos dos columnas.")
            return

        self.config_col = self.df.columns[0]

        dlg = GroupSelectionDialog(self.df.columns[1:], self)
        if dlg.exec_() != QDialog.Accepted:
            return

        self.grouped_columns = dlg.groups
        self.validation.clear()
        self.build_tabs()
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)





    def build_tabs(self):
        self.tabs.clear()

        for idx, group in enumerate(self.grouped_columns):
            columns = group["columns"]
            eje_y = group["eje_y"]
            nombre = group["nombre"] or f"Grupo {idx+1}"

            cols_x = [col for col in columns if col != eje_y]
            if not cols_x:
                continue

            values_y = sorted(self.df[eje_y].dropna().astype(str).str.strip().unique())
            unique_values_x = []
            for col in cols_x:
                unique_values_x.append(sorted(self.df[col].dropna().astype(str).str.strip().unique()))

            combinaciones_x = list(product(*unique_values_x))

            table = QTableWidget(len(values_y), len(combinaciones_x))
            table.setVerticalHeaderLabels([wrap_text(y) for y in values_y])
            headers = [
                wrap_text(" / ".join([f"{c}: {v}" for c, v in zip(cols_x, combo)]))
                for combo in combinaciones_x
            ]
            table.setHorizontalHeaderLabels(headers)

            for r, y in enumerate(values_y):
                for c, x_combo in enumerate(combinaciones_x):
                    item = QTableWidgetItem()
                    item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Checked)
                    table.setItem(r, c, item)
                    self.validation[(idx, y) + x_combo] = "valid"

            table.itemChanged.connect(self.on_checkbox_change)
            table.horizontalHeader().sectionDoubleClicked.connect(
                lambda col, t=table: self.toggle_column_check_state(t, col)
            )
            table.verticalHeader().sectionDoubleClicked.connect(
                lambda row, t=table: self.toggle_row_check_state(t, row)
            )

            table.setAlternatingRowColors(True)
            table.setFont(QFont("Arial", 10))
            table.horizontalHeader().setFont(QFont("Arial", 10, QFont.Bold))
            table.verticalHeader().setFont(QFont("Arial", 10, QFont.Bold))
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            eje_x_texto = "+".join(cols_x) if len(cols_x) > 1 else cols_x[0]
            tab_title = f"{nombre}:\n{eje_y}\n<->\n{eje_x_texto}"
            self.tabs.addTab(table, tab_title)

        self.update_stats()
        # Ajustar altura de las pestañas
        tab_bar = self.tabs.tabBar()
        tab_bar.setStyleSheet("""
            QTabBar::tab {
                height: 90px;  /* Aumentar la altura de cada pestaña */
                padding: 6px;
                margin: 2px;
                font-size: 6pt;
                font-weight: bold;
                white-space: pre-wrap;
            }
        """)

    

    def toggle_column_check_state(self, table, column):
        state = None
        for row in range(table.rowCount()):
            item = table.item(row, column)
            if state is None:
                state = item.checkState()
            item.setCheckState(Qt.Unchecked if state == Qt.Checked else Qt.Checked)

    def toggle_row_check_state(self, table, row):
        state = None
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if state is None:
                state = item.checkState()
            item.setCheckState(Qt.Unchecked if state == Qt.Checked else Qt.Checked)




    def on_checkbox_change(self, item: QTableWidgetItem):
        table = item.tableWidget()
        group_index = self.tabs.indexOf(table)

        val_y = table.verticalHeaderItem(item.row()).text().replace("\n", " ")
        header_x = table.horizontalHeaderItem(item.column()).text().replace("\n", " ")

        # Extraer valores del encabezado
        combo_parts = header_x.split(" / ")
        combo_x = tuple(seg.split(": ", 1)[1] for seg in combo_parts)
        key = (group_index, val_y) + combo_x

        self.validation[key] = "valid" if item.checkState() == Qt.Checked else "invalid"
        self.update_stats()




    def update_stats(self):
        index = self.tabs.currentIndex()
        if index < 0:
            self.stats_label.setText("Estadísticas: -")
            return
        table = self.tabs.widget(index)
        total = table.rowCount() * table.columnCount()
        valid = sum(
            1 for r in range(table.rowCount()) for c in range(table.columnCount())
            if table.item(r, c).checkState() == Qt.Checked
        )
        categoria = self.tabs.tabText(index).replace("\n", " ")
        self.stats_label.setText(f"🗂 {categoria}: {valid}/{total} válidos")

    def filter_rows(self) -> pd.DataFrame:
        if self.df is None:
            return pd.DataFrame()

        valid_rows = []

        for _, row in self.df.iterrows():
            row_is_valid = True
            for group_index, group_columns in enumerate(self.grouped_columns):
                if len(group_columns) < 2:
                    continue
                val_y = str(row[group_columns[0]]).strip()
                combo_x = tuple(str(row[col]).strip() for col in group_columns[1:])
                key = (group_index, val_y) + combo_x
                if self.validation.get(key, "invalid") != "valid":
                    row_is_valid = False
                    break
            if row_is_valid:
                valid_rows.append(row)

        return pd.DataFrame(valid_rows)




    def preview_data(self):
        df = self.filter_rows()
        if df.empty:
            QMessageBox.information(self, "Previsualización vacía", "No hay filas válidas seleccionadas.")
            return
        dlg = PreviewDialog(df, self)
        dlg.exec_()

    def export_csv(self):
        df = self.filter_rows()
        if df.empty:
            QMessageBox.information(self, "Nada para exportar", "No hay combinaciones válidas seleccionadas.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo CSV", "", "CSV files (*.csv)")
        if path:
            df.to_csv(path, index=False)
            QMessageBox.information(self, "Exportado", f"Archivo guardado:\n{Path(path).name}")

    def manage_groups(self):
        if self.df is None:
            QMessageBox.warning(self, "Sin datos", "Primero debe cargar un archivo CSV.")
            return

        dlg = GroupSelectionDialog(self.df.columns[1:], self)
        # Pasar los grupos actuales como "estado"
        for g in self.grouped_columns:
            item = QListWidgetItem()
            dlg.groups_container.addItem(item)

            container = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)

            name_input = QLineEdit(g["nombre"])
            layout.addWidget(name_input)

            layout.addWidget(QLabel("Seleccionar columna para eje Y (filas):"))
            y_selector = QListWidget()
            y_selector.setMaximumHeight(50)
            y_selector.setSelectionMode(QListWidget.SingleSelection)
            y_selector.addItems(g["columns"])
            y_selector.setCurrentRow(g["columns"].index(g["eje_y"]))
            layout.addWidget(y_selector)

            layout.addWidget(QLabel("Columnas incluidas:"))
            for col in g["columns"]:
                layout.addWidget(QLabel(f" - {col}"))

            remove_btn = QPushButton("❌ Eliminar Grupo")
            remove_btn.clicked.connect(lambda _, w=container: dlg.remove_group_widget(w))
            layout.addWidget(remove_btn)

            container.setLayout(layout)
            item.setSizeHint(container.sizeHint())
            dlg.groups_container.setItemWidget(item, container)

        if dlg.exec_() == QDialog.Accepted:
            self.grouped_columns = dlg.groups
            self.validation.clear()
            self.build_tabs()




# ──────────────────────────────
# EJECUCIÓN
# ──────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
