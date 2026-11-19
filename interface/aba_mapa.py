"""Aba do mapa interativo com QWebEngineView, SOS, filtros, curadoria e auditoria."""

from pathlib import Path
import tempfile
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import config
from mapa.gerador import gerar_mapa
from mapa.repositorio import (
    adicionar_ponto,
    aprovar_ponto,
    carregar_pontos,
    excluir_ponto,
    exportar_csv,
    validar_coordenadas,
)
from seguranca.auth import (
    alternar_status_usuario,
    cadastrar_pesquisador,
    listar_usuarios,
    trocar_senha,
)


class DialogoTrocarSenha(QDialog):
    """Diálogo para alteração de senha institucional."""

    def __init__(self, usuario: str, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("Alterar Senha Institucional")
        self.setFixedSize(380, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_atual = QLineEdit()
        self.input_atual.setEchoMode(QLineEdit.Password)
        form.addRow("Senha Atual:", self.input_atual)

        self.input_nova = QLineEdit()
        self.input_nova.setEchoMode(QLineEdit.Password)
        form.addRow("Nova Senha (mín. 8):", self.input_nova)

        self.input_confirma = QLineEdit()
        self.input_confirma.setEchoMode(QLineEdit.Password)
        form.addRow("Confirmar Nova Senha:", self.input_confirma)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_secundario")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Salvar Nova Senha")
        btn_salvar.clicked.connect(self._salvar)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_salvar)
        layout.addLayout(btn_box)

    def _salvar(self):
        atual = self.input_atual.text()
        nova = self.input_nova.text()
        confirma = self.input_confirma.text()

        if nova != confirma:
            QMessageBox.warning(self, "Aviso", "A confirmação da senha não confere.")
            return

        sucesso, msg = trocar_senha(self.usuario, atual, nova)
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class AbaMapa(QWidget):
    """Aba do mapa com diferenciação entre Modo Visitante e Modo Administrador."""

    dados_alterados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.arquivo_mapa_temp = Path(tempfile.gettempdir()) / "sharkmaps_mapa.html"
        self.usuario_atual: Optional[Dict[str, Any]] = None

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        layout_principal.addWidget(splitter)

        # 1. Painel Lateral (Filtros, SOS e Formulários)
        self.painel_lateral = self._criar_painel_lateral()
        splitter.addWidget(self.painel_lateral)

        # 2. Visualizador Web do Mapa
        self.web_view = QWebEngineView()
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        splitter.addWidget(self.web_view)

        splitter.setSizes([380, 770])
        self.atualizar_mapa()

    def definir_usuario(self, usuario: Optional[Dict[str, Any]]):
        """Alterna a interface entre Modo Visitante e Modo Administrador."""
        self.usuario_atual = usuario
        eh_admin = usuario is not None

        # Exibição de cabeçalho de sessão
        if eh_admin:
            self.lbl_sessao.setText(f"👤 {usuario['nome']} ({usuario.get('papel', '').upper()})")
            self.card_sessao.setVisible(True)
            self.chk_pendentes_mapa.setVisible(True)
            self.tabs_admin.setVisible(True)
            self.box_visitante.setVisible(False)
            self._atualizar_tabela_curadoria()
            if usuario.get("papel") == "superadmin":
                self.box_superadmin.setVisible(True)
                self._atualizar_tabela_pesquisadores()
            else:
                self.box_superadmin.setVisible(False)
        else:
            self.card_sessao.setVisible(False)
            self.chk_pendentes_mapa.setVisible(False)
            self.chk_pendentes_mapa.setChecked(False)
            self.tabs_admin.setVisible(False)
            self.box_visitante.setVisible(True)
            self.box_superadmin.setVisible(False)

        self.atualizar_mapa()

    def _criar_painel_lateral(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(350)
        scroll.setMaximumWidth(440)

        conteudo = QWidget()
        layout = QVBoxLayout(conteudo)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- PAINEL FIXO SOS (REF005) ---
        card_sos = QFrame()
        card_sos.setStyleSheet("""
            QFrame {
                background-color: #fef2f2;
                border: 2px solid #ef4444;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout_sos = QVBoxLayout(card_sos)
        layout_sos.setSpacing(4)
        lbl_sos_titulo = QLabel("🚨 EMERGÊNCIA AQUÁTICA (SOS)")
        lbl_sos_titulo.setStyleSheet("font-weight: 900; color: #b91c1c; font-size: 13px;")
        layout_sos.addWidget(lbl_sos_titulo)

        lbl_sos_telefones = QLabel("📞 <b>193</b> Bombeiros (Guarda-Vidas)  |  📞 <b>192</b> SAMU")
        lbl_sos_telefones.setStyleSheet("color: #7f1d1d; font-size: 12px;")
        layout_sos.addWidget(lbl_sos_telefones)

        lbl_sos_dica = QLabel("Em caso de acidente: retire a vítima da água e estanque a hemorragia com pressão direta contínua.")
        lbl_sos_dica.setStyleSheet("color: #991b1b; font-size: 11px;")
        lbl_sos_dica.setWordWrap(True)
        layout_sos.addWidget(lbl_sos_dica)
        layout.addWidget(card_sos)

        # --- CARD DE SESSÃO ADMIN (Oculto para visitante) ---
        self.card_sessao = QFrame()
        self.card_sessao.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout_sessao = QHBoxLayout(self.card_sessao)
        self.lbl_sessao = QLabel("")
        self.lbl_sessao.setStyleSheet("font-weight: bold; color: #166534; font-size: 12px;")
        btn_trocar_senha = QPushButton("🔑 Senha")
        btn_trocar_senha.setObjectName("btn_secundario")
        btn_trocar_senha.setFixedHeight(26)
        btn_trocar_senha.clicked.connect(self._abrir_troca_senha)

        layout_sessao.addWidget(self.lbl_sessao)
        layout_sessao.addStretch()
        layout_sessao.addWidget(btn_trocar_senha)
        self.card_sessao.setVisible(False)
        layout.addWidget(self.card_sessao)

        # --- GRUPO: FILTROS DE CAMADAS ---
        grupo_filtros = QGroupBox("Camadas do Mapa")
        layout_filtros = QVBoxLayout(grupo_filtros)

        self.chk_incidentes = QCheckBox("Incidentes Oficiais (CEMIT)")
        self.chk_incidentes.setChecked(True)
        self.chk_incidentes.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_incidentes)

        self.chk_salvavidas = QCheckBox("Postos de Guarda-Vidas (CBMPE)")
        self.chk_salvavidas.setChecked(True)
        self.chk_salvavidas.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_salvavidas)

        self.chk_perigo = QCheckBox("Área de Atenção Máxima (Canal Submarino)")
        self.chk_perigo.setChecked(True)
        self.chk_perigo.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_perigo)

        self.chk_cluster = QCheckBox("Agrupar Marcadores (Cluster)")
        self.chk_cluster.setChecked(True)
        self.chk_cluster.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_cluster)

        self.chk_calor = QCheckBox("Mapa de Calor (Densidade)")
        self.chk_calor.setChecked(False)
        self.chk_calor.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_calor)

        self.chk_pendentes_mapa = QCheckBox("Exibir Relatos Pendentes no Mapa (Amarelo)")
        self.chk_pendentes_mapa.setChecked(True)
        self.chk_pendentes_mapa.setVisible(False)
        self.chk_pendentes_mapa.toggled.connect(self.atualizar_mapa)
        layout_filtros.addWidget(self.chk_pendentes_mapa)

        btn_atualizar = QPushButton("Atualizar Mapa")
        btn_atualizar.setObjectName("btn_secundario")
        btn_atualizar.clicked.connect(self.atualizar_mapa)
        layout_filtros.addWidget(btn_atualizar)

        layout.addWidget(grupo_filtros)

        # --- SEÇÃO VISITANTE: RELATO DE AVISTAMENTO (STATUS PENDENTE) ---
        self.box_visitante = QGroupBox("Enviar Relato de Avistamento (Cidadão)")
        layout_vis = QVBoxLayout(self.box_visitante)

        lbl_vis_info = QLabel("Viu um tubarão ou registrou uma ocorrência? Seu relato será avaliado pelo CEMIT antes de entrar no mapa público.")
        lbl_vis_info.setStyleSheet("color: #475569; font-size: 11px;")
        lbl_vis_info.setWordWrap(True)
        layout_vis.addWidget(lbl_vis_info)

        form_vis = QFormLayout()
        self.vis_nome = QLineEdit()
        self.vis_nome.setPlaceholderText("Ex: Praia de Boa Viagem - Posto 8")
        form_vis.addRow("Local:", self.vis_nome)

        self.vis_lat = QLineEdit()
        self.vis_lat.setPlaceholderText("Ex: -8.1256 (Litoral PE / Noronha)")
        form_vis.addRow("Latitude:", self.vis_lat)

        self.vis_lon = QLineEdit()
        self.vis_lon.setPlaceholderText("Ex: -34.8998")
        form_vis.addRow("Longitude:", self.vis_lon)

        self.vis_data = QLineEdit()
        self.vis_data.setPlaceholderText("AAAA-MM-DD")
        form_vis.addRow("Data:", self.vis_data)

        self.vis_especie = QComboBox()
        self.vis_especie.setEditable(True)
        self.vis_especie.addItems(["Não identificada", "Tubarão-cabeça-chata", "Tubarão-tigre", "Tubarão-lixa"])
        form_vis.addRow("Espécie:", self.vis_especie)

        self.vis_desc = QTextEdit()
        self.vis_desc.setMaximumHeight(65)
        self.vis_desc.setPlaceholderText("Descreva o que presenciou, maré e condições da água")
        form_vis.addRow("Relato:", self.vis_desc)

        self.vis_contato = QLineEdit()
        self.vis_contato.setPlaceholderText("Seu nome / e-mail ou telefone para contato")
        form_vis.addRow("Contato:", self.vis_contato)

        layout_vis.addLayout(form_vis)

        btn_enviar_relato = QPushButton("📨 Enviar Relato para Curadoria")
        btn_enviar_relato.clicked.connect(self._salvar_relato_visitante)
        layout_vis.addWidget(btn_enviar_relato)

        layout.addWidget(self.box_visitante)

        # --- SEÇÃO ADMINISTRADOR: ABAS DE GESTÃO, CADASTRO E CURADORIA ---
        self.tabs_admin = QTabWidget()
        self.tabs_admin.setVisible(False)

        # Sub-aba Admin 1: Cadastrar Oficial
        tab_cad_admin = QWidget()
        lay_cad = QVBoxLayout(tab_cad_admin)
        form_adm = QFormLayout()

        self.adm_tipo = QComboBox()
        self.adm_tipo.addItems(["incidente", "posto_salvavidas"])
        form_adm.addRow("Tipo:", self.adm_tipo)

        self.adm_nome = QLineEdit()
        form_adm.addRow("Local / Nome*:", self.adm_nome)

        self.adm_lat = QLineEdit()
        form_adm.addRow("Latitude*:", self.adm_lat)

        self.adm_lon = QLineEdit()
        form_adm.addRow("Longitude*:", self.adm_lon)

        self.adm_data = QLineEdit()
        self.adm_data.setPlaceholderText("AAAA-MM-DD")
        form_adm.addRow("Data:", self.adm_data)

        self.adm_especie = QComboBox()
        self.adm_especie.setEditable(True)
        self.adm_especie.addItems(["Tubarão-cabeça-chata", "Tubarão-tigre", "Tubarão-limão", "Não identificada", "N/A"])
        form_adm.addRow("Espécie:", self.adm_especie)

        self.adm_desc = QTextEdit()
        self.adm_desc.setMaximumHeight(65)
        form_adm.addRow("Descrição:", self.adm_desc)

        self.adm_fonte = QLineEdit()
        self.adm_fonte.setText("CEMIT / MONITUBA")
        form_adm.addRow("Fonte:", self.adm_fonte)

        lay_cad.addLayout(form_adm)

        btn_salvar_adm = QPushButton("💾 Cadastrar Incidente Oficial")
        btn_salvar_adm.clicked.connect(self._salvar_ponto_admin)
        lay_cad.addWidget(btn_salvar_adm)

        self.tabs_admin.addTab(tab_cad_admin, "Novo Registro")

        # Sub-aba Admin 2: Curadoria de Relatos Pendentes
        tab_curadoria = QWidget()
        lay_cur = QVBoxLayout(tab_curadoria)

        lbl_cur_info = QLabel("Relatos de cidadãos aguardando validação científica:")
        lbl_cur_info.setStyleSheet("font-size: 11px; color: #475569;")
        lay_cur.addWidget(lbl_cur_info)

        self.tabela_curadoria = QTableWidget(0, 4)
        self.tabela_curadoria.setHorizontalHeaderLabels(["ID", "Local", "Data", "Espécie"])
        self.tabela_curadoria.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_curadoria.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_curadoria.setMinimumHeight(120)
        lay_cur.addWidget(self.tabela_curadoria)

        box_botoes_cur = QHBoxLayout()
        btn_aprovar = QPushButton("✅ Aprovar")
        btn_aprovar.setStyleSheet("background-color: #2a9d8f;")
        btn_aprovar.clicked.connect(self._aprovar_relato_selecionado)

        btn_rejeitar = QPushButton("❌ Excluir")
        btn_rejeitar.setObjectName("btn_perigo")
        btn_rejeitar.clicked.connect(self._excluir_registro_selecionado)

        box_botoes_cur.addWidget(btn_aprovar)
        box_botoes_cur.addWidget(btn_rejeitar)
        lay_cur.addLayout(box_botoes_cur)

        btn_exportar = QPushButton("📥 Exportar Base CSV com Auditoria")
        btn_exportar.setObjectName("btn_secundario")
        btn_exportar.clicked.connect(self._exportar_csv_dialogo)
        lay_cur.addWidget(btn_exportar)

        self.tabs_admin.addTab(tab_curadoria, "Curadoria Pendente")

        layout.addWidget(self.tabs_admin)

        # --- SEÇÃO SUPER-ADMIN: GESTÃO DE PESQUISADORES CREDENCIADOS ---
        self.box_superadmin = QGroupBox("Gestão de Pesquisadores (Super-Admin)")
        self.box_superadmin.setVisible(False)
        lay_super = QVBoxLayout(self.box_superadmin)

        form_pesq = QFormLayout()
        self.sup_user = QLineEdit()
        self.sup_user.setPlaceholderText("identificador (ex: jcosta)")
        form_pesq.addRow("Usuário:", self.sup_user)

        self.sup_nome = QLineEdit()
        self.sup_nome.setPlaceholderText("Nome completo do pesquisador")
        form_pesq.addRow("Nome:", self.sup_nome)

        self.sup_inst = QLineEdit()
        self.sup_inst.setPlaceholderText("UFRPE / Matrícula 123456")
        form_pesq.addRow("Instituição:", self.sup_inst)

        self.sup_email = QLineEdit()
        self.sup_email.setPlaceholderText("email@ufrpe.br ou @ufpe.br")
        form_pesq.addRow("E-mail Oficial:", self.sup_email)

        self.sup_senha = QLineEdit()
        self.sup_senha.setEchoMode(QLineEdit.Password)
        self.sup_senha.setPlaceholderText("Senha inicial (mínimo 8 dígitos)")
        form_pesq.addRow("Senha:", self.sup_senha)

        lay_super.addLayout(form_pesq)

        btn_cadastrar_pesq = QPushButton("➕ Credenciar Novo Pesquisador")
        btn_cadastrar_pesq.clicked.connect(self._cadastrar_novo_pesquisador)
        lay_super.addWidget(btn_cadastrar_pesq)

        self.tabela_pesquisadores = QTableWidget(0, 3)
        self.tabela_pesquisadores.setHorizontalHeaderLabels(["Usuário", "E-mail", "Status"])
        self.tabela_pesquisadores.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_pesquisadores.setMinimumHeight(100)
        lay_super.addWidget(self.tabela_pesquisadores)

        btn_alternar_status = QPushButton("Alternar Status (Ativar / Desativar)")
        btn_alternar_status.setObjectName("btn_secundario")
        btn_alternar_status.clicked.connect(self._alternar_status_pesquisador)
        lay_super.addWidget(btn_alternar_status)

        layout.addWidget(self.box_superadmin)

        layout.addStretch()
        scroll.setWidget(conteudo)
        return scroll

    def atualizar_mapa(self):
        """Regenera o mapa Folium e o carrega no QWebEngineView."""
        try:
            df = carregar_pontos(config.PONTOS_CSV, apenas_oficiais=False)
            eh_admin = self.usuario_atual is not None
            mostrar_pendentes = eh_admin and self.chk_pendentes_mapa.isChecked()

            mapa = gerar_mapa(
                df=df,
                mostrar_incidentes=self.chk_incidentes.isChecked(),
                mostrar_salvavidas=self.chk_salvavidas.isChecked(),
                agrupar=self.chk_cluster.isChecked(),
                mapa_calor=self.chk_calor.isChecked(),
                mostrar_areas_perigo=self.chk_perigo.isChecked(),
                apenas_oficiais=not eh_admin,
                mostrar_pendentes=mostrar_pendentes,
            )

            mapa.save(str(self.arquivo_mapa_temp))
            self.web_view.load(QUrl.fromLocalFile(str(self.arquivo_mapa_temp)))
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Gerar Mapa", f"Ocorreu um erro ao gerar o mapa:\n{e}")

    def _salvar_relato_visitante(self):
        nome = self.vis_nome.text().strip()
        lat_txt = self.vis_lat.text().strip().replace(",", ".")
        lon_txt = self.vis_lon.text().strip().replace(",", ".")

        if not nome or not lat_txt or not lon_txt:
            QMessageBox.warning(self, "Aviso", "Preencha pelo menos Local, Latitude e Longitude.")
            return

        try:
            lat = float(lat_txt)
            lon = float(lon_txt)
        except ValueError:
            QMessageBox.warning(self, "Coordenadas Inválidas", "Latitude e Longitude devem ser números válidos.")
            return

        valido, msg_geo = validar_coordenadas(lat, lon)
        if not valido:
            QMessageBox.critical(self, "Trava Geográfica", msg_geo)
            return

        novo_relato = {
            "tipo": "incidente",
            "nome": nome,
            "lat": lat,
            "lon": lon,
            "data": self.vis_data.text().strip(),
            "especie": self.vis_especie.currentText().strip(),
            "descricao": self.vis_desc.toPlainText().strip(),
            "fonte": f"Cidadão ({self.vis_contato.text().strip() or 'Anônimo'})",
            "status": "pendente",
        }

        sucesso, msg = adicionar_ponto(config.PONTOS_CSV, novo_relato, usuario=None)
        if sucesso:
            QMessageBox.information(
                self,
                "Relato Enviado com Sucesso!",
                "Muito obrigado pela sua contribuição à ciência cidadã!\n\n"
                "Seu relato foi recebido e registrado com status PENDENTE. Ele será analisado "
                "pela equipe de curadoria do CEMIT/UFRPE antes de ser incorporado ao mapa oficial."
            )
            self.vis_nome.clear()
            self.vis_lat.clear()
            self.vis_lon.clear()
            self.vis_data.clear()
            self.vis_desc.clear()
            self.vis_contato.clear()
            self.dados_alterados.emit()
            self.atualizar_mapa()
        else:
            QMessageBox.warning(self, "Não foi possível registrar", msg)

    def _salvar_ponto_admin(self):
        if not self.usuario_atual:
            return

        nome = self.adm_nome.text().strip()
        lat_txt = self.adm_lat.text().strip().replace(",", ".")
        lon_txt = self.adm_lon.text().strip().replace(",", ".")

        if not nome or not lat_txt or not lon_txt:
            QMessageBox.warning(self, "Aviso", "Preencha os campos obrigatórios.")
            return

        try:
            lat = float(lat_txt)
            lon = float(lon_txt)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Coordenadas numéricas inválidas.")
            return

        valido, msg_geo = validar_coordenadas(lat, lon)
        if not valido:
            QMessageBox.critical(self, "Trava Geográfica", msg_geo)
            return

        ponto = {
            "tipo": self.adm_tipo.currentText(),
            "nome": nome,
            "lat": lat,
            "lon": lon,
            "data": self.adm_data.text().strip(),
            "especie": self.adm_especie.currentText().strip(),
            "descricao": self.adm_desc.toPlainText().strip(),
            "fonte": self.adm_fonte.text().strip(),
            "status": "oficial",
        }

        sucesso, msg = adicionar_ponto(config.PONTOS_CSV, ponto, usuario=self.usuario_atual["usuario"])
        if sucesso:
            QMessageBox.information(self, "Sucesso", "Registro oficial cadastrado com backup e auditoria!")
            self.adm_nome.clear()
            self.adm_lat.clear()
            self.adm_lon.clear()
            self.adm_data.clear()
            self.adm_desc.clear()
            self.dados_alterados.emit()
            self.atualizar_mapa()
            self._atualizar_tabela_curadoria()
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def _atualizar_tabela_curadoria(self):
        df = carregar_pontos(config.PONTOS_CSV, apenas_oficiais=False)
        pendentes = df[df["status"] == "pendente"] if not df.empty else pd.DataFrame()

        self.tabela_curadoria.setRowCount(len(pendentes))
        for row_idx, (_, r) in enumerate(pendentes.iterrows()):
            self.tabela_curadoria.setItem(row_idx, 0, QTableWidgetItem(str(r.get("id", ""))))
            self.tabela_curadoria.setItem(row_idx, 1, QTableWidgetItem(str(r.get("nome", ""))))
            self.tabela_curadoria.setItem(row_idx, 2, QTableWidgetItem(str(r.get("data", ""))))
            self.tabela_curadoria.setItem(row_idx, 3, QTableWidgetItem(str(r.get("especie", ""))))

    def _aprovar_relato_selecionado(self):
        linha = self.tabela_curadoria.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um relato pendente na tabela para aprovar.")
            return

        reg_id = self.tabela_curadoria.item(linha, 0).text()
        sucesso = aprovar_ponto(config.PONTOS_CSV, reg_id, self.usuario_atual["usuario"])
        if sucesso:
            QMessageBox.information(self, "Aprovado", f"O registro #{reg_id} agora é OFICIAL e visível publicamente.")
            self.dados_alterados.emit()
            self.atualizar_mapa()
            self._atualizar_tabela_curadoria()

    def _excluir_registro_selecionado(self):
        linha = self.tabela_curadoria.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um registro na tabela para excluir.")
            return

        reg_id = self.tabela_curadoria.item(linha, 0).text()
        resp = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente remover permanentemente o registro #{reg_id}?\nUm backup automático será gerado.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            excluir_ponto(config.PONTOS_CSV, reg_id, self.usuario_atual["usuario"])
            QMessageBox.information(self, "Removido", "Registro removido com sucesso e log registrado.")
            self.dados_alterados.emit()
            self.atualizar_mapa()
            self._atualizar_tabela_curadoria()

    def _exportar_csv_dialogo(self):
        destino, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Base SharkMaps para CSV",
            "sharkmaps_dados_exportados.csv",
            "Arquivos CSV (*.csv)"
        )
        if destino:
            if exportar_csv(config.PONTOS_CSV, destino, self.usuario_atual["usuario"]):
                QMessageBox.information(self, "Exportação Concluída", f"Arquivo salvo com sucesso em:\n{destino}")

    def _atualizar_tabela_pesquisadores(self):
        if not self.usuario_atual or self.usuario_atual.get("papel") != "superadmin":
            return

        usuarios = listar_usuarios(self.usuario_atual["usuario"])
        self.tabela_pesquisadores.setRowCount(len(usuarios))
        for row_idx, u in enumerate(usuarios):
            self.tabela_pesquisadores.setItem(row_idx, 0, QTableWidgetItem(u["usuario"]))
            self.tabela_pesquisadores.setItem(row_idx, 1, QTableWidgetItem(u["email"]))
            status_txt = "Ativo" if u["ativo"] else "Inativo"
            self.tabela_pesquisadores.setItem(row_idx, 2, QTableWidgetItem(status_txt))

    def _cadastrar_novo_pesquisador(self):
        if not self.usuario_atual:
            return

        sucesso, msg = cadastrar_pesquisador(
            solicitante=self.usuario_atual["usuario"],
            novo_usuario=self.sup_user.text().strip(),
            senha_inicial=self.sup_senha.text().strip(),
            nome=self.sup_nome.text().strip(),
            instituicao_matricula=self.sup_inst.text().strip(),
            email=self.sup_email.text().strip(),
        )
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.sup_user.clear()
            self.sup_nome.clear()
            self.sup_inst.clear()
            self.sup_email.clear()
            self.sup_senha.clear()
            self._atualizar_tabela_pesquisadores()
        else:
            QMessageBox.warning(self, "Erro de Validação", msg)

    def _alternar_status_pesquisador(self):
        linha = self.tabela_pesquisadores.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um pesquisador na tabela.")
            return

        usuario_alvo = self.tabela_pesquisadores.item(linha, 0).text()
        status_atual = self.tabela_pesquisadores.item(linha, 2).text()
        novo_status = False if status_atual == "Ativo" else True

        sucesso, msg = alternar_status_usuario(self.usuario_atual["usuario"], usuario_alvo, novo_status)
        if sucesso:
            QMessageBox.information(self, "Status Atualizado", msg)
            self._atualizar_tabela_pesquisadores()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def _abrir_troca_senha(self):
        if self.usuario_atual:
            dlg = DialogoTrocarSenha(self.usuario_atual["usuario"], self)
            dlg.exec()
