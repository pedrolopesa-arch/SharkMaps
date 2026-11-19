"""Ponto de entrada da aplicação SharkMaps."""

import os
import sys

# Desativa aceleração de hardware por GPU no WebEngine para evitar tela branca no Windows
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtWidgets import QApplication
from interface.janela import JanelaPrincipal


def main():
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
