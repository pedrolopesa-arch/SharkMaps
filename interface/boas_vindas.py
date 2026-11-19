"""Tela de Boas-Vindas e Diálogo de Autenticação Institucional do SharkMaps."""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config
from seguranca.auth import inicializar_admins_se_necessario, verificar_credenciais


class DialogoLogin(QDialog):
    """Diálogo modal para autenticação de pesquisadores e administradores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acesso Restrito - Pesquisador / Administrador")
        self.setFixedSize(420, 260)
        self.setModal(True)
        self.dados_usuario = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("🔐 Autenticação Institucional")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #0a2540;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Área restrita a pesquisadores credenciados do CEMIT/UFRPE.")
        subtitulo.setStyleSheet("color: #64748b; font-size: 12px;")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        form = QFormLayout()
        form.setSpacing(10)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ex: admin ou seu usuário institucional")
        form.addRow("Usuário:", self.input_usuario)

        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha.setPlaceholderText("Senha com hash SHA-256")
        form.addRow("Senha:", self.input_senha)

        layout.addLayout(form)

        layout_botoes = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_secundario")
        btn_cancelar.clicked.connect(self.reject)

        self.btn_entrar = QPushButton("Entrar no Sistema")
        self.btn_entrar.clicked.connect(self._tentar_login)

        layout_botoes.addWidget(btn_cancelar)
        layout_botoes.addWidget(self.btn_entrar)
        layout.addLayout(layout_botoes)

    def _tentar_login(self):
        usuario = self.input_usuario.text().strip()
        senha = self.input_senha.text().strip()

        if not usuario or not senha:
            QMessageBox.warning(self, "Campos Obrigatórios", "Por favor, preencha o usuário e a senha.")
            return

        usuario_autenticado = verificar_credenciais(usuario, senha)
        if usuario_autenticado:
            self.dados_usuario = usuario_autenticado
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Acesso Negado",
                "Credenciais inválidas ou conta inativa.\n\n"
                "Verifique seu identificador e senha. O acesso institucional opera por convite restrito."
            )


class TelaBoasVindas(QWidget):
    """Tela inicial acolhedora com logotipo, apresentação da missão e escolha de modo."""

    entrar_visitante = Signal()
    entrar_admin = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        inicializar_admins_se_necessario()

        layout_externo = QVBoxLayout(self)
        layout_externo.setAlignment(Qt.AlignCenter)
        layout_externo.setContentsMargins(40, 30, 40, 30)

        # Card Central
        card = QFrame()
        card.setMaximumWidth(700)
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 14px;
                border: 1px solid #cbd5e1;
            }
        """)
        layout_card = QVBoxLayout(card)
        layout_card.setContentsMargins(36, 32, 36, 32)
        layout_card.setSpacing(18)
        layout_card.setAlignment(Qt.AlignCenter)

        # 1. Logotipo SVG Centralizado
        if config.LOGO_SVG.is_file():
            logo_widget = QSvgWidget(str(config.LOGO_SVG))
            logo_widget.setFixedSize(140, 140)
            layout_card.addWidget(logo_widget, alignment=Qt.AlignCenter)

        # 2. Título e Missão
        lbl_titulo = QLabel("SHARKMAPS PERNAMBUCO")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0a2540; letter-spacing: 2px;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_titulo)

        lbl_subtitulo = QLabel("Educação Ambiental, Rigor Científico e Segurança Costeira")
        lbl_subtitulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #0077b6;")
        lbl_subtitulo.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_subtitulo)

        lbl_missao = QLabel(
            "Bem-vindo ao SharkMaps! Uma plataforma pública e acadêmica criada para desmistificar "
            "o papel ecológico dos tubarões no litoral de Pernambuco, registrar dados georreferenciados "
            "com integridade científica e disseminar recomendações práticas para a convivência segura na praia."
        )
        lbl_missao.setStyleSheet("font-size: 13px; color: #475569; line-height: 1.5;")
        lbl_missao.setWordWrap(True)
        lbl_missao.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_missao)

        # Linha Divisória
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setStyleSheet("color: #e2e8f0; margin: 8px 0;")
        layout_card.addWidget(linha)

        # 3. Ações de Entrada
        lbl_escolha = QLabel("Como você deseja acessar a plataforma?")
        lbl_escolha.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 13px;")
        lbl_escolha.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_escolha)

        # Botão 1: Visitante / Banhista (Destaque Principal)
        btn_visitante = QPushButton("🌊  Entrar como Visitante / Banhista")
        btn_visitante.setMinimumHeight(48)
        btn_visitante.setStyleSheet("""
            QPushButton {
                background-color: #0077b6;
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0096c7;
            }
        """)
        btn_visitante.clicked.connect(self._ao_entrar_visitante)
        layout_card.addWidget(btn_visitante)

        # Botão 2: Pesquisador / Administrador
        btn_admin = QPushButton("🔐  Acesso Pesquisador / Administrador (CEMIT / UFRPE)")
        btn_admin.setObjectName("btn_secundario")
        btn_admin.setMinimumHeight(40)
        btn_admin.clicked.connect(self._ao_abrir_login)
        layout_card.addWidget(btn_admin)

        # Rodapé Institucional
        lbl_rodape = QLabel("Apoio e Referências: CEMIT • UFRPE • UFPE • Corpo de Bombeiros Militar de PE (193)")
        lbl_rodape.setStyleSheet("color: #94a3b8; font-size: 11px; margin-top: 10px;")
        lbl_rodape.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_rodape)

        layout_externo.addWidget(card)

    def _ao_entrar_visitante(self):
        self.entrar_visitante.emit()

    def _ao_abrir_login(self):
        dialogo = DialogoLogin(self)
        if dialogo.exec() == QDialog.Accepted and dialogo.dados_usuario:
            self.entrar_admin.emit(dialogo.dados_usuario)
