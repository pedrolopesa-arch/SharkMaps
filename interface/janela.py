"""Janela principal da aplicação SharkMaps (PySide6)."""

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)

from interface.aba_info import AbaInfo
from interface.aba_mapa import AbaMapa


class JanelaPrincipal(QMainWindow):
    """Janela principal que integra a aba do mapa interativo e a aba informativa/resumo."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SharkMaps - Monitoramento e Educação Ambiental (Pernambuco)")
        self.resize(1150, 780)

        # Widget central de abas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Instanciação das abas
        self.aba_mapa = AbaMapa()
        self.aba_info = AbaInfo()

        # Integração entre as abas: quando um ponto é cadastrado no mapa, atualiza o resumo estatístico
        self.aba_mapa.dados_alterados.connect(self.aba_info.atualizar_resumo)

        # Adiciona ao QTabWidget
        self.tabs.addTab(self.aba_mapa, "🗺️ Mapa Interativo")
        self.tabs.addTab(self.aba_info, "📚 Informações e Resumo")
