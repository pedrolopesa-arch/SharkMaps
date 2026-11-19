"""Aba educacional com visualização de artigos em Markdown e resumo estatístico via pandas."""

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
    """Aba educacional: exibe materiais informativos em Markdown e métricas dos registros."""

    CHAVE_RESUMO = "__resumo__"

    def __init__(self, parent=None):
        super().__init__(parent)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        layout_principal.addWidget(splitter)

        # 1. Painel Esquerdo: Lista de Tópicos e Artigos
        painel_esquerdo = QWidget()
        layout_esq = QVBoxLayout(painel_esquerdo)
        layout_esq.setContentsMargins(8, 8, 8, 8)

        lbl_titulos = QLabel("<b>Materiais e Relatórios:</b>")
        layout_esq.addWidget(lbl_titulos)

        self.lista_topicos = QListWidget()
        self.lista_topicos.currentItemChanged.connect(self._ao_selecionar_topico)
        layout_esq.addWidget(self.lista_topicos)

        splitter.addWidget(painel_esquerdo)

        # 2. Painel Direito: Navegador de Texto Rico (Markdown / HTML)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        # Configura caminho base para busca de imagens relativas
        caminho_conteudo = str(config.CONTEUDO_DIR.resolve())
        QDir.addSearchPath("conteudo", caminho_conteudo)
        self.browser.document().setBaseUrl(QUrl.fromLocalFile(caminho_conteudo + "/"))

        splitter.addWidget(self.browser)

        # Proporção inicial: 280px para lista, restante para leitura
        splitter.setSizes([280, 820])

        # Mapeamento interno: item_id -> caminho do arquivo .md
        self.artigos_md = {}

        self.carregar_conteudos()

    def carregar_conteudos(self):
        """Varre a pasta de conteúdo e popula a lista de tópicos."""
        self.lista_topicos.clear()
        self.artigos_md.clear()

        # Item fixo: Resumo dos Registros
        item_resumo = QListWidgetItem("📊 Resumo dos Registros")
        item_resumo.setData(Qt.UserRole, self.CHAVE_RESUMO)
        self.lista_topicos.addItem(item_resumo)

        # Procura por arquivos Markdown na pasta conteudo/
        if config.CONTEUDO_DIR.is_dir():
            for arquivo in sorted(config.CONTEUDO_DIR.glob("*.md")):
                titulo = self._extrair_titulo_md(arquivo)
                item = QListWidgetItem(f"📄 {titulo}")
                item.setData(Qt.UserRole, str(arquivo))
                self.lista_topicos.addItem(item)
                self.artigos_md[str(arquivo)] = arquivo

        # Seleciona o primeiro tópico por padrão
        if self.lista_topicos.count() > 0:
            self.lista_topicos.setCurrentRow(0)

    def _extrair_titulo_md(self, caminho_md: Path) -> str:
        """Extrai o primeiro título (# Título) do arquivo Markdown, ou retorna o nome do arquivo."""
        try:
            with open(caminho_md, "r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha.startswith("# "):
                        return linha.replace("# ", "").strip()
        except Exception:
            pass
        return caminho_md.stem.capitalize()

    def _ao_selecionar_topico(self, item_atual: QListWidgetItem, item_anterior=None):
        """Carrega e exibe o conteúdo do tópico selecionado."""
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
            except Exception as e:
                self.browser.setHtml(f"<p style='color:red;'>Erro ao carregar artigo: {e}</p>")

    def atualizar_resumo(self):
        """Atualiza a visualização do resumo caso esteja selecionado no momento."""
        item_selecionado = self.lista_topicos.currentItem()
        if item_selecionado and item_selecionado.data(Qt.UserRole) == self.CHAVE_RESUMO:
            self.exibir_resumo()

    def exibir_resumo(self):
        """Gera e exibe estatísticas consolidadas dos pontos usando pandas."""
        df = carregar_pontos(config.PONTOS_CSV)

        total_registros = len(df)
        total_incidentes = len(df[df["tipo"] == "incidente"]) if not df.empty else 0
        total_postos = len(df[df["tipo"] == "posto_salvavidas"]) if not df.empty else 0

        # Tabela por espécies (apenas incidentes)
        html_tabela_especies = "<p><i>Nenhum registro de incidente disponível.</i></p>"
        if not df.empty and total_incidentes > 0:
            df_incidentes = df[df["tipo"] == "incidente"].copy()
            df_incidentes["especie"] = df_incidentes["especie"].replace("", "Não identificada")
            contagem = df_incidentes["especie"].value_counts().reset_index()
            contagem.columns = ["Espécie Registrada", "Total de Casos"]
            html_tabela_especies = contagem.to_html(index=False, classes="tabela-resumo", border=0)

        html_conteudo = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #2c3e50; padding: 15px; }}
                h2 {{ color: #2980b9; border-bottom: 2px solid #3498db; padding-bottom: 6px; }}
                h3 {{ color: #16a085; margin-top: 20px; }}
                .cards {{ display: flex; gap: 15px; margin: 20px 0; }}
                .card {{
                    background: #f8f9fa; border-left: 4px solid #3498db;
                    padding: 12px 18px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    margin-bottom: 10px;
                }}
                .card-alerta {{ border-left-color: #e74c3c; }}
                .card-info {{ border-left-color: #27ae60; }}
                .tabela-resumo {{
                    width: 100%; border-collapse: collapse; margin-top: 10px;
                }}
                .tabela-resumo th {{
                    background-color: #f2f2f2; border: 1px solid #ddd; padding: 8px; text-align: left;
                }}
                .tabela-resumo td {{
                    border: 1px solid #ddd; padding: 8px;
                }}
                .aviso-oficial {{
                    background-color: #fff3cd; border: 1px solid #ffeeba;
                    color: #856404; padding: 12px; border-radius: 4px; margin-top: 25px;
                }}
            </style>
        </head>
        <body>
            <h2>📊 Resumo Geral dos Registros</h2>
            <p>Estatísticas compiladas em tempo real a partir da base de dados local de Pernambuco.</p>

            <div class="card card-alerta">
                <b>Total de Incidentes Registrados:</b> {total_incidentes}
            </div>
            <div class="card card-info">
                <b>Postos de Salva-vidas Mapeados:</b> {total_postos}
            </div>
            <div class="card">
                <b>Total de Pontos no Sistema:</b> {total_registros}
            </div>

            <h3>Distribuição por Espécie (Incidentes)</h3>
            {html_tabela_especies}

            <div class="aviso-oficial">
                <b>Aviso Importante:</b> Este compilado tem finalidade estritamente acadêmica e educativa.
                Os registros não substituem relatórios oficiais do CEMIT nem o acompanhamento de risco em tempo real.
            </div>
        </body>
        </html>
        """
        self.browser.setHtml(html_conteudo)
