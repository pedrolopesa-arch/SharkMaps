"""Tema visual global do SharkMaps com paleta oceânica moderna e amigável (QSS)."""

TEMA_OCEANICO = """
/* Reset e Configurações Gerais */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #1e293b;
    background-color: #f8fafc;
}

/* Janela Principal */
QMainWindow {
    background-color: #f1f5f9;
}

/* Abas (QTabWidget) */
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 8px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0077b6;
    border-top: 3px solid #0077b6;
    border-left: 1px solid #cbd5e1;
    border-right: 1px solid #cbd5e1;
}

QTabBar::tab:hover:!selected {
    background-color: #cbd5e1;
    color: #0a2540;
}

/* Grupos (QGroupBox) */
QGroupBox {
    font-weight: bold;
    color: #0a2540;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 16px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #ffffff;
}

/* Botões */
QPushButton {
    background-color: #0077b6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #0096c7;
}

QPushButton:pressed {
    background-color: #023e8a;
}

QPushButton:disabled {
    background-color: #94a3b8;
    color: #f1f5f9;
}

/* Botões Secundários e de Alerta */
QPushButton#btn_secundario {
    background-color: #ffffff;
    color: #0077b6;
    border: 1.5px solid #0077b6;
}

QPushButton#btn_secundario:hover {
    background-color: #e0f2fe;
}

QPushButton#btn_perigo {
    background-color: #e63946;
    color: #ffffff;
}

QPushButton#btn_perigo:hover {
    background-color: #d62828;
}

/* Campos de Entrada (QLineEdit, QComboBox, QTextEdit) */
QLineEdit, QTextEdit, QComboBox {
    background-color: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #00b4d8;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1.5px solid #0077b6;
    background-color: #ffffff;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    font-size: 13px;
    color: #334155;
    background-color: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #94a3b8;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0077b6;
    border-color: #0077b6;
    image: none;
}

/* Listas (QListWidget) */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    padding: 10px 12px;
    border-radius: 6px;
    margin-bottom: 2px;
}

QListWidget::item:hover {
    background-color: #f0fdf4;
    color: #0f766e;
}

QListWidget::item:selected {
    background-color: #e0f2fe;
    color: #0369a1;
    font-weight: bold;
}

/* Barra de Rolagem (QScrollBar) */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tabelas (QTableWidget) */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    gridline-color: #f1f5f9;
}

QHeaderView::section {
    background-color: #0a2540;
    color: #ffffff;
    padding: 6px;
    font-weight: bold;
    border: none;
}
"""
