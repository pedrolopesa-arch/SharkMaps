"""Aba do mapa interativo com QWebEngineView, filtros e formulário de cadastro."""

import html
from pathlib import Path
import tempfile
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QCheckBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import config
from mapa.gerador import gerar_mapa
from mapa.repositorio import adicionar_ponto, carregar_pontos


class AbaMapa(QWidget):
    """Aba interativa com visualização do mapa via Folium e cadastro de novos registros."""

    dados_alterados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.arquivo_mapa_temp = Path(tempfile.gettempdir()) / "sharkmaps_mapa.html"

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # Divisor ajustável entre o painel de controles e o mapa
        splitter = QSplitter(Qt.Horizontal)
        layout_principal.addWidget(splitter)

        # 1. Painel Lateral (Filtros e Formulário) com Barra de Rolagem
        painel_lateral = self._criar_painel_lateral()
        splitter.addWidget(painel_lateral)

        # 2. Visualizador Web do Mapa
        self.web_view = QWebEngineView()

        # Configurações de segurança para permitir carregar recursos externos (tiles OSM, Leaflet CDN)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        splitter.addWidget(self.web_view)

        # Proporção inicial: 340px para controles, restante para o mapa
        splitter.setSizes([340, 760])

        # Inicializa o mapa pela primeira vez
        self.atualizar_mapa()

    def _criar_painel_lateral(self) -> QWidget:
        """Cria o painel com filtros de camada e formulário de novo ponto."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(320)
        scroll.setMaximumWidth(400)

        conteudo = QWidget()
        layout = QVBoxLayout(conteudo)
        layout.setSpacing(12)

        # --- Grupo: Filtros de Camadas ---
        grupo_filtros = QGroupBox("Filtros do Mapa")
        layout_filtros = QVBoxLayout(grupo_filtros)

        self.chk_incidentes = QCheckBox("Exibir Incidentes")
        self.chk_incidentes.setChecked(True)
        self.chk_incidentes.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_incidentes)

        self.chk_salvavidas = QCheckBox("Exibir Postos de Salva-vidas")
        self.chk_salvavidas.setChecked(True)
        self.chk_salvavidas.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_salvavidas)

        self.chk_cluster = QCheckBox("Agrupar Marcadores (Cluster)")
        self.chk_cluster.setChecked(True)
        self.chk_cluster.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_cluster)

        self.chk_calor = QCheckBox("Mapa de Calor (Incidentes)")
        self.chk_calor.setChecked(False)
        self.chk_calor.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_calor)

        btn_recarregar = QPushButton("Atualizar Visualização")
        btn_recarregar.clicked.connect(self.atualizar_mapa)
        layout_filtros.addWidget(btn_recarregar)

        layout.addWidget(grupo_filtros)

        # --- Grupo: Cadastro de Novo Ponto ---
        grupo_cadastro = QGroupBox("Cadastrar Novo Ponto")
        layout_form = QFormLayout(grupo_cadastro)
        layout_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["incidente", "posto_salvavidas"])
        layout_form.addRow("Tipo:", self.combo_tipo)

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: Praia de Boa Viagem - Posto 5")
        layout_form.addRow("Local / Nome*:", self.input_nome)

        self.input_lat = QLineEdit()
        self.input_lat.setPlaceholderText("Ex: -8.1256")
        layout_form.addRow("Latitude*:", self.input_lat)

        self.input_lon = QLineEdit()
        self.input_lon.setPlaceholderText("Ex: -34.8998")
        layout_form.addRow("Longitude*:", self.input_lon)

        self.input_data = QLineEdit()
        self.input_data.setPlaceholderText("AAAA-MM-DD")
        layout_form.addRow("Data:", self.input_data)

        self.combo_especie = QComboBox()
        self.combo_especie.setEditable(True)
        self.combo_especie.addItems([
            "Tubarão-tigre",
            "Tubarão-cabeça-chata",
            "Não identificada",
            "N/A"
        ])
        layout_form.addRow("Espécie:", self.combo_especie)

        self.input_desc = QTextEdit()
        self.input_desc.setMaximumHeight(70)
        self.input_desc.setPlaceholderText("Breve descrição do ponto ou ocorrência")
        layout_form.addRow("Descrição:", self.input_desc)

        self.input_fonte = QLineEdit()
        self.input_fonte.setPlaceholderText("Ex: CEMIT, CBMPE")
        layout_form.addRow("Fonte:", self.input_fonte)

        self.btn_salvar = QPushButton("Salvar Registro")
        self.btn_salvar.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 6px;")
        self.btn_salvar.clicked.connect(self.salvar_ponto)
        layout_form.addRow(self.btn_salvar)

        layout.addWidget(grupo_cadastro)
        layout.addStretch()

        scroll.setWidget(conteudo)
        return scroll

    def atualizar_mapa(self):
        """Lê os pontos cadastrados, gera o HTML com Folium e carrega no QWebEngineView."""
        try:
            df = carregar_pontos(config.PONTOS_CSV)
            mapa = gerar_mapa(
                df=df,
                mostrar_incidentes=self.chk_incidentes.isChecked(),
                mostrar_salvavidas=self.chk_salvavidas.isChecked(),
                agrupar=self.chk_cluster.isChecked(),
                mapa_calor=self.chk_calor.isChecked()
            )
            # Salva no arquivo temporário para evitar o limite de 2MB do setHtml
            mapa.save(str(self.arquivo_mapa_temp))

            # Carrega via QUrl limpo a partir do arquivo local (sem query params que quebram no Windows)
            url = QUrl.fromLocalFile(str(self.arquivo_mapa_temp))
            self.web_view.load(url)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Gerar Mapa", f"Ocorreu um erro ao gerar o mapa:\n{e}")

    def salvar_ponto(self):
        """Valida e grava o novo ponto no arquivo CSV."""
        nome = self.input_nome.text().strip()
        lat_txt = self.input_lat.text().strip().replace(",", ".")
        lon_txt = self.input_lon.text().strip().replace(",", ".")

        if not nome:
            QMessageBox.warning(self, "Validação", "Por favor, preencha o campo 'Local / Nome'.")
            self.input_nome.setFocus()
            return

        try:
            lat = float(lat_txt)
            lon = float(lon_txt)
        except ValueError:
            QMessageBox.warning(
                self,
                "Coordenadas Inválidas",
                "Latitude e Longitude devem ser números válidos.\nExemplo: Latitude: -8.1256, Longitude: -34.8998"
            )
            return

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            QMessageBox.warning(
                self,
                "Coordenadas Fora dos Limites",
                "A latitude deve estar entre -90 e 90 e a longitude entre -180 e 180."
            )
            return

        novo_ponto = {
            "tipo": self.combo_tipo.currentText(),
            "nome": nome,
            "lat": lat,
            "lon": lon,
            "data": self.input_data.text().strip(),
            "especie": self.combo_especie.currentText().strip(),
            "descricao": self.input_desc.toPlainText().strip(),
            "fonte": self.input_fonte.text().strip()
        }

        try:
            adicionar_ponto(config.PONTOS_CSV, novo_ponto)
            QMessageBox.information(self, "Sucesso", "Ponto cadastrado com sucesso!")

            # Limpa o formulário
            self.input_nome.clear()
            self.input_lat.clear()
            self.input_lon.clear()
            self.input_data.clear()
            self.input_desc.clear()
            self.input_fonte.clear()

            # Notifica ouvintes e recarrega o mapa
            self.dados_alterados.emit()
            self.atualizar_mapa()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Gravação", f"Não foi possível salvar o ponto:\n{e}")
