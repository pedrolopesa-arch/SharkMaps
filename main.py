"""Ponto de entrada principal da aplicação SharkMaps."""

import os
import sys

# Desativa aceleração de hardware por GPU no WebEngine para evitar tela branca no Windows
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtWidgets import QApplication, QStackedWidget
from interface.boas_vindas import TelaBoasVindas
from interface.estilos import TEMA_OCEANICO
from interface.janela import JanelaPrincipal


class SharkMapsApp:
    """Gerenciador de telas e transições entre Boas-Vindas e Janela Principal."""

    def __init__(self):
        self.janela_principal = JanelaPrincipal()
        self.tela_boas_vindas = TelaBoasVindas()

        # Conexões de fluxo da aplicação
        self.tela_boas_vindas.entrar_visitante.connect(self._iniciar_modo_visitante)
        self.tela_boas_vindas.entrar_admin.connect(self._iniciar_modo_admin)
        self.janela_principal.solicitar_troca_modo.connect(self._voltar_boas_vindas)

        # Exibe inicialmente a tela acolhedora de boas-vindas
        self.tela_boas_vindas.resize(750, 600)
        self.tela_boas_vindas.show()

    def _iniciar_modo_visitante(self):
        self.janela_principal.definir_sessao(None)
        self.tela_boas_vindas.hide()
        self.janela_principal.show()

    def _iniciar_modo_admin(self, dados_usuario):
        self.janela_principal.definir_sessao(dados_usuario)
        self.tela_boas_vindas.hide()
        self.janela_principal.show()

    def _voltar_boas_vindas(self):
        self.janela_principal.hide()
        self.tela_boas_vindas.show()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(TEMA_OCEANICO)

    controlador = SharkMapsApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
