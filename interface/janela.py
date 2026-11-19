"""Janela principal da aplicação SharkMaps com cabeçalho de sessão e controle de abas."""

from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import config
from interface.aba_info import AbaInfo
from interface.aba_mapa import AbaMapa


class JanelaPrincipal(QMainWindow):
    """Janela principal que integra Mapa, Conteúdos, Resumo e Gestão de Sessão."""

    solicitar_troca_modo = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SharkMaps - Educação Ambiental e Monitoramento Científico (Pernambuco)")
        self.resize(1200, 800)
        self.usuario_atual: Optional[Dict[str, Any]] = None

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_central = QVBoxLayout(widget_central)
        layout_central.setContentsMargins(8, 8, 8, 8)
        layout_central.setSpacing(6)

        # 1. Barra Superior Institucional
        self.barra_superior = self._criar_barra_superior()
        layout_central.addWidget(self.barra_superior)

        # 2. Abas do Sistema
        self.tabs = QTabWidget()
        layout_central.addWidget(self.tabs)

        self.aba_mapa = AbaMapa()
        self.aba_info = AbaInfo()

        # Integração: novos dados no mapa atualizam o resumo na aba informativa
        self.aba_mapa.dados_alterados.connect(self.aba_info.atualizar_resumo)

        self.tabs.addTab(self.aba_mapa, "🗺️ Mapa Interativo & Monitoramento")
        self.tabs.addTab(self.aba_info, "📚 Conscientização & Rigor Científico")

    def _criar_barra_superior(self) -> QWidget:
        barra = QFrame()
        barra.setStyleSheet("""
            QFrame {
                background-color: #0a2540;
                border-radius: 6px;
                padding: 4px 12px;
            }
        """)
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(6, 4, 6, 4)

        if config.LOGO_SVG.is_file():
            logo_pequeno = QSvgWidget(str(config.LOGO_SVG))
            logo_pequeno.setFixedSize(32, 32)
            layout.addWidget(logo_pequeno)

        lbl_titulo = QLabel("SHARKMAPS")
        lbl_titulo.setStyleSheet("font-weight: 900; font-size: 15px; color: #ffffff; letter-spacing: 1px;")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("• Litoral de Pernambuco")
        lbl_sub.setStyleSheet("font-size: 12px; color: #00b4d8; font-weight: 600;")
        layout.addWidget(lbl_sub)

        layout.addStretch()

        self.lbl_modo = QLabel("Modo Visitante / Banhista")
        self.lbl_modo.setStyleSheet("font-size: 12px; color: #e2e8f0; margin-right: 12px;")
        layout.addWidget(self.lbl_modo)

        self.btn_alternar_modo = QPushButton("Alternar Modo / Login")
        self.btn_alternar_modo.setFixedHeight(28)
        self.btn_alternar_modo.setStyleSheet("""
            QPushButton {
                background-color: #0077b6;
                color: #ffffff;
                font-size: 12px;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0096c7;
            }
        """)
        self.btn_alternar_modo.clicked.connect(self._ao_solicitar_troca)
        layout.addWidget(self.btn_alternar_modo)

        return barra

    def definir_sessao(self, usuario: Optional[Dict[str, Any]]):
        """Configura a janela para o perfil de acesso correspondente."""
        self.usuario_atual = usuario
        self.aba_mapa.definir_usuario(usuario)

        if usuario:
            self.lbl_modo.setText(f"🔐 Pesquisador: <b>{usuario['nome']}</b>")
            self.btn_alternar_modo.setText("Encerrar Sessão")
            self.btn_alternar_modo.setStyleSheet("""
                QPushButton {
                    background-color: #e63946;
                    color: #ffffff;
                    font-size: 12px;
                    padding: 4px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self.lbl_modo.setText("Modo Visitante / Banhista")
            self.btn_alternar_modo.setText("Acesso Restrito / Login")
            self.btn_alternar_modo.setStyleSheet("""
                QPushButton {
                    background-color: #0077b6;
                    color: #ffffff;
                    font-size: 12px;
                    padding: 4px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #0096c7;
                }
            """)

    def _ao_solicitar_troca(self):
        self.solicitar_troca_modo.emit()
