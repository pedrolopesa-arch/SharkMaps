"""Aba educacional e científica do SharkMaps com renderização de artigos e estatísticas."""

from pathlib import Path
from PySide6.QtCore import QDir, Qt, QUrl
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import config
from mapa.repositorio import carregar_pontos


class AbaInfo(QWidget):
    """Aba informativa: materiais didáticos, dados ecológicos e resumo estatístico."""

    CHAVE_RESUMO = "__resumo__"

    def __init__(self, parent=None):
        super().__init__(parent)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        layout_principal.addWidget(splitter)

        # 1. Painel Esquerdo: Lista de Tópicos
        painel_esquerdo = QWidget()
        layout_esq = QVBoxLayout(painel_esquerdo)
        layout_esq.setContentsMargins(12, 12, 12, 12)
        layout_esq.setSpacing(8)

        lbl_titulos = QLabel("<b>📚 Materiais Educativos:</b>")
        lbl_titulos.setStyleSheet("color: #0a2540; font-size: 14px;")
        layout_esq.addWidget(lbl_titulos)

        self.lista_topicos = QListWidget()
        self.lista_topicos.currentItemChanged.connect(self._ao_selecionar_topico)
        layout_esq.addWidget(self.lista_topicos)

        splitter.addWidget(painel_esquerdo)

        # 2. Painel Direito: Navegador de Texto
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        # Configuração rigorosa dos caminhos de busca para imagens e conteúdo
        caminho_conteudo = str(config.CONTEUDO_DIR.resolve())
        caminho_imagens = str(config.IMAGENS_DIR.resolve())

        QDir.setSearchPaths("imagens", [caminho_imagens])
        QDir.addSearchPath("imagens", caminho_imagens)
        QDir.setSearchPaths("conteudo", [caminho_conteudo])
        QDir.addSearchPath("conteudo", caminho_conteudo)

        self.browser.document().setBaseUrl(QUrl.fromLocalFile(caminho_conteudo + "/"))

        splitter.addWidget(self.browser)
        splitter.setSizes([290, 810])

        self.artigos_md = {}
        self.carregar_conteudos()

    def carregar_conteudos(self):
        """Varre a pasta de conteúdo e popula a lista de tópicos."""
        self.lista_topicos.clear()
        self.artigos_md.clear()

        # Item fixo: Resumo dos Registros
        item_resumo = QListWidgetItem("📊 Resumo Científico dos Registros")
        item_resumo.setData(Qt.UserRole, self.CHAVE_RESUMO)
        self.lista_topicos.addItem(item_resumo)

        # Varre arquivos .md
        if config.CONTEUDO_DIR.is_dir():
            for arquivo in sorted(config.CONTEUDO_DIR.glob("*.md")):
                titulo = self._extrair_titulo_md(arquivo)
                item = QListWidgetItem(f"📖 {titulo}")
                item.setData(Qt.UserRole, str(arquivo))
                self.lista_topicos.addItem(item)
                self.artigos_md[str(arquivo)] = arquivo

        if self.lista_topicos.count() > 0:
            self.lista_topicos.setCurrentRow(0)

    def _extrair_titulo_md(self, caminho_md: Path) -> str:
        try:
            with open(caminho_md, "r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha.startswith("# "):
                        return linha.replace("# ", "").replace("🏖️", "").replace("🦈", "").replace("🌊", "").strip()
        except Exception:
            pass
        return caminho_md.stem.capitalize()

    def _ao_selecionar_topico(self, item_atual: QListWidgetItem, item_anterior=None):
        if not item_atual:
            return

        chave = item_atual.data(Qt.UserRole)
        if chave == self.CHAVE_RESUMO:
            self.exibir_resumo()
        elif chave in self.artigos_md:
            caminho_arquivo = self.artigos_md[chave]
            try:
                with open(caminho_arquivo, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                self.browser.setMarkdown(conteudo)
                self._formatar_elementos_artigo()
            except Exception as e:
                self.browser.setHtml(f"<p style='color:red;'>Erro ao carregar artigo: {e}</p>")

    def _formatar_elementos_artigo(self):
        """Centraliza blocos de imagens e legendas científicas para máxima elegância visual."""
        doc = self.browser.document()
        bloco = doc.begin()
        while bloco.isValid():
            texto = bloco.text()
            # Se o bloco contiver uma imagem (código de objeto \ufffc) ou uma legenda iniciada com Figura/*Figura
            if "\ufffc" in texto or texto.strip().startswith("Figura") or texto.strip().startswith("*Figura"):
                formato = bloco.blockFormat()
                formato.setAlignment(Qt.AlignCenter)
                cursor = self.browser.textCursor()
                cursor.setPosition(bloco.position())
                cursor.setBlockFormat(formato)
            bloco = bloco.next()

    def atualizar_resumo(self):
        item_selecionado = self.lista_topicos.currentItem()
        if item_selecionado and item_selecionado.data(Qt.UserRole) == self.CHAVE_RESUMO:
            self.exibir_resumo()

    def exibir_resumo(self):
        """Gera e renderiza métricas analíticas e consolidação de espécies."""
        df = carregar_pontos(config.PONTOS_CSV, apenas_oficiais=False)

        total_registros = len(df)
        total_oficiais = len(df[df["status"] == "oficial"]) if not df.empty else 0
        total_incidentes = len(df[(df["tipo"] == "incidente") & (df["status"] == "oficial")]) if not df.empty else 0
        total_salvavidas = len(df[df["tipo"] == "posto_salvavidas"]) if not df.empty else 0
        total_pendentes = len(df[df["status"] == "pendente"]) if not df.empty else 0

        html_especies = "<p><i>Nenhum registro de incidente documentado.</i></p>"
        if not df.empty and total_incidentes > 0:
            df_inc = df[(df["tipo"] == "incidente") & (df["status"] == "oficial")].copy()
            df_inc["especie"] = df_inc["especie"].replace("", "Não identificada")
            contagem = df_inc["especie"].value_counts().reset_index()
            contagem.columns = ["Espécie Documentada", "Casos Oficiais"]
            html_especies = contagem.to_html(index=False, classes="tabela-resumo", border=0)

        html_conteudo = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #1e293b;
                    padding: 20px;
                    background-color: #ffffff;
                }}
                h2 {{ color: #0a2540; border-bottom: 2px solid #0077b6; padding-bottom: 8px; }}
                h3 {{ color: #0077b6; margin-top: 24px; }}
                .cards-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 12px;
                    margin: 16px 0;
                }}
                .card {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-left: 5px solid #0077b6;
                    padding: 12px 16px;
                    border-radius: 6px;
                }}
                .card-vermelho {{ border-left-color: #e63946; }}
                .card-amarelo {{ border-left-color: #f59e0b; }}
                .card-verde {{ border-left-color: #10b981; }}
                .card-valor {{ font-size: 22px; font-weight: bold; color: #0a2540; margin-top: 4px; }}
                .card-legenda {{ font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }}
                .tabela-resumo {{
                    width: 100%; border-collapse: collapse; margin-top: 12px;
                }}
                .tabela-resumo th {{
                    background-color: #0a2540; color: #ffffff; padding: 10px; text-align: left; font-size: 13px;
                }}
                .tabela-resumo td {{
                    border-bottom: 1px solid #e2e8f0; padding: 10px; font-size: 13px;
                }}
                .tabela-resumo tr:nth-child(even) {{
                    background-color: #f8fafc;
                }}
                .aviso-rodape {{
                    background-color: #f0fdf4; border: 1px solid #bbf7d0;
                    color: #166534; padding: 14px; border-radius: 6px; margin-top: 28px; font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <h2>📊 Resumo Científico da Base SharkMaps</h2>
            <p>Métricas consolidadas a partir dos registros georreferenciados documentados pelo CEMIT / MONITUBA no litoral de Pernambuco e Fernando de Noronha.</p>

            <div class="cards-grid">
                <div class="card card-vermelho">
                    <div class="card-legenda">Incidentes Oficiais Documentados</div>
                    <div class="card-valor">{total_incidentes}</div>
                </div>
                <div class="card card-verde">
                    <div class="card-legenda">Postos de Guarda-Vidas Mapeados (CBMPE)</div>
                    <div class="card-valor">{total_salvavidas}</div>
                </div>
                <div class="card">
                    <div class="card-legenda">Total de Registros Oficiais no Banco</div>
                    <div class="card-valor">{total_oficiais}</div>
                </div>
                <div class="card card-amarelo">
                    <div class="card-legenda">Relatos Cidadãos Pendentes de Curadoria</div>
                    <div class="card-valor">{total_pendentes}</div>
                </div>
            </div>

            <h3>Distribuição por Espécie (Incidentes Oficiais)</h3>
            {html_especies}

            <div class="aviso-rodape">
                <b>Compromisso Científico e Ético:</b> A plataforma SharkMaps cumpre rigorosamente as diretrizes éticas e de proteção a dados sensíveis (LGPD), não armazenando identidades de vítimas ou dados pessoais. Todos os dados são georreferenciados com base em relatórios públicos de órgãos competentes (CEMIT, SDS-PE, CBMPE e ICMBio).
            </div>
        </body>
        </html>
        """
        self.browser.setHtml(html_conteudo)
