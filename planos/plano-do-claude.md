# Plano do Claude: SharkMaps

Análise da ideia e guia passo a passo para programá-la em Python.

> Este plano usa o projeto `sharkmaps.zip` gerado na conversa como ponto de partida. O código foi escrito e a sintaxe conferida, mas **não foi executado** (o ambiente de criação não tinha folium nem PySide6). Rode e teste cada etapa antes de seguir para a próxima.

---

## 1. A ideia em uma frase

Um programa em Python, executável no computador, que une **(a)** um mapa interativo com incidentes com tubarões e postos de salva-vidas, **(b)** uma área educativa com textos, imagens e tabelas e **(c)** um resumo dos dados, para promover educação ambiental e registrar casos para fins acadêmicos no litoral de Pernambuco.

---

## 2. Análise da ideia

### Pontos fortes

- **Lacuna real e bem justificada:** a revisão mostra trabalhos que mapeiam (Kunst et al.) e trabalhos que divulgam (Medeiros et al.), mas nenhum que una os dois em uma ferramenta própria.
- **Escopo viável para um trabalho acadêmico:** folium + PySide6 + pandas são bibliotecas maduras, bem documentadas e adequadas para quem está começando.
- **Arquitetura simples e extensível:** separar interface, lógica do mapa, dados e conteúdo permite evoluir cada parte sem quebrar as outras.
- **Conteúdo editável sem código:** textos em Markdown na pasta `conteudo/` deixam pesquisadores e professores contribuírem sem programar.

### Riscos e pontos fracos (vale tratar no artigo)

| Ponto | Por que importa | O que fazer |
|---|---|---|
| **Qualidade e origem dos dados** | O mapa só é útil se os registros forem confiáveis. Hoje o projeto tem apenas dados de exemplo. | Definir a fonte (ex.: CEMIT, citado na introdução), pedir autorização de uso e registrar a fonte de cada ponto (a coluna `fonte` já existe). |
| **"Precisão geográfica"** | A Tabela 1 promete mapa com precisão geográfica, mas os pontos são aproximados. | Trocar o termo por "localização aproximada" e explicar como as coordenadas são obtidas. |
| **Privacidade e ética** | Incidentes envolvem pessoas. Dados identificáveis sobre vítimas são sensíveis (LGPD). | Registrar só local aproximado, data e espécie. Nunca nomes ou dados pessoais. |
| **Responsabilidade sobre segurança** | O programa não substitui a sinalização oficial nem prevê risco. | Incluir um aviso na interface e no artigo: é ferramenta educativa e de registro, não de alerta oficial. |
| **Dependência de internet** | O artigo diz que o programa independe de plataformas externas, mas o folium carrega mapas (tiles) e o Leaflet pela internet. | Ser preciso no texto: independe de *redes sociais*, mas usa mapas online. Como evolução, cache de tiles ou mapa offline. |
| **Dados só locais (CSV)** | A introdução fala em "banco de dados" e registro eficiente de casos, mas um CSV local não sincroniza entre usuários. | Para a v1, CSV basta. Como proposta futura, SQLite ou um servidor. |
| **Distribuição** | Para quem não programa, "rodar Python" é uma barreira. | Gerar um executável (etapa 12), sabendo que o QtWebEngine dá algum trabalho no empacotamento. |

### Diferenciais que você pode defender na seção "Funcionalidades com inovação"

1. Mapa e conteúdo educativo **no mesmo programa**, sem depender de rede social.
2. **Conteúdo atualizável por arquivos**, sem mexer no código.
3. **Resumo automático** dos registros (pandas) ao lado do material educativo.
4. Cadastro de novos pontos direto na interface, com validação.

---

## 3. Guia passo a passo

Cada etapa termina com um **checkpoint**: um jeito rápido de saber se deu certo antes de continuar.

### Etapa 0: Pré-requisitos

- Python 3.10 ou superior (`python --version`).
- VS Code (ou outra IDE) e Git instalado.
- Conta no GitHub.

**Checkpoint:** `python --version` e `git --version` respondem no terminal.

### Etapa 1: Definir requisitos e escopo

Escreva a lista de requisitos (a mesma da Metodologia) e decida o que fica **fora** da v1 (login, banco de dados, mapa offline).

- Funcionais: mapa com marcadores, popups, área educativa, carga de dados por tabela.
- Não funcionais: rodar em Python, interface simples, conteúdo editável sem código.

**Checkpoint:** uma lista curta e numerada (RF01, RF02, RNF01...) que você consegue citar no artigo.

### Etapa 2: Ambiente e versionamento

```bash
mkdir sharkmaps && cd sharkmaps
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install folium pandas PySide6
pip freeze > requirements.txt
git init
```

Crie um `.gitignore` com `.venv/` e `__pycache__/`, faça o primeiro commit e publique no GitHub.

**Checkpoint:** `python -c "import folium, pandas, PySide6"` não dá erro.

### Etapa 3: Criar a estrutura de pastas

```
sharkmaps/
├── main.py
├── config.py
├── interface/   (janela.py, aba_mapa.py, aba_info.py)
├── mapa/        (gerador.py, repositorio.py)
├── dados/       (pontos.csv)
└── conteudo/    (*.md, imagens/)
```

Regra de ouro: `interface/` pode importar `mapa/`, mas `mapa/` **nunca** importa o PySide6. Assim a lógica do mapa pode ser testada sem abrir janela.

**Checkpoint:** a árvore existe e cada pasta de código tem um `__init__.py` vazio.

### Etapa 4: Camada de dados (`mapa/repositorio.py`)

Implemente duas funções:

- `carregar_pontos(caminho)`: lê o CSV com pandas, converte lat/lon para número e descarta linhas inválidas.
- `adicionar_ponto(caminho, ponto)`: acrescenta um registro ao CSV.

Colunas do CSV: `tipo, nome, lat, lon, data, especie, descricao, fonte`.

**Checkpoint:** em um terminal Python, `carregar_pontos(Path("dados/pontos.csv"))` devolve um DataFrame com as linhas esperadas.

### Etapa 5: Gerador do mapa (`mapa/gerador.py`)

Implemente `gerar_mapa(df, ...)`, que devolve um `folium.Map` com:

- marcadores por tipo (cores e ícones diferentes);
- popups com os detalhes (escape o texto com `html.escape`, porque ele vem de arquivo);
- opções de agrupamento (`MarkerCluster`) e mapa de calor (`HeatMap`);
- enquadramento automático com `fit_bounds`.

**Checkpoint:** sem nenhuma interface, rode um script que faz `gerar_mapa(df).save("teste.html")` e abra o HTML no navegador. Os marcadores devem aparecer no litoral do Recife.

### Etapa 6: Esqueleto da interface (`interface/janela.py` e `main.py`)

Crie a `JanelaPrincipal` com um `QTabWidget` vazio (duas abas de texto "Mapa" e "Informações") e o `main.py` que a abre.

**Checkpoint:** `python main.py` abre uma janela com duas abas.

### Etapa 7: Aba do mapa (`interface/aba_mapa.py`)

1. Coloque um `QWebEngineView` ocupando a aba.
2. Gere o mapa, salve em arquivo temporário e carregue com `view.load(QUrl.fromLocalFile(...))` (evita o limite de ~2 MB do `setHtml`).
3. Adicione os filtros de camada (checkboxes) ligados a `atualizar_mapa()`.
4. Adicione o formulário de novo registro, com validação de coordenadas e nome, gravando via `adicionar_ponto`.

**Checkpoint:** o mapa aparece dentro da janela, os checkboxes escondem e mostram as camadas, e um registro novo surge no mapa e no CSV.

### Etapa 8: Aba educacional (`interface/aba_info.py`)

1. Divida a aba em lista (esquerda) e `QTextBrowser` (direita).
2. Leia os `.md` de `conteudo/`, use o primeiro `# Título` como nome na lista e exiba com `setMarkdown`.
3. Configure `setSearchPaths` para as imagens relativas funcionarem.
4. Gere o item "Resumo dos registros" com pandas (`groupby` por espécie, `to_html`).

**Checkpoint:** ao criar um novo arquivo `.md` em `conteudo/` e reabrir o programa, ele aparece na lista, com imagem e tabela renderizadas.

### Etapa 9: Integração

Conecte o sinal `dados_alterados` da aba do mapa ao `atualizar_resumo` da aba de informações, para o resumo mudar quando um registro é adicionado.

**Checkpoint:** adicionar um incidente na aba Mapa altera os números do "Resumo dos registros".

### Etapa 10: Testes

Instale `pytest` e teste a lógica que não depende de janela:

```python
# tests/test_repositorio.py
from mapa.repositorio import carregar_pontos, adicionar_ponto

def test_ignora_coordenadas_invalidas(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text("tipo,nome,lat,lon\nincidente,A,abc,-34.9\nincidente,B,-8.1,-34.9\n", encoding="utf-8")
    df = carregar_pontos(csv)
    assert len(df) == 1 and df.iloc[0]["nome"] == "B"

def test_adicionar_ponto(tmp_path):
    csv = tmp_path / "p.csv"
    adicionar_ponto(csv, {"tipo": "incidente", "nome": "X", "lat": -8.1, "lon": -34.9})
    assert len(carregar_pontos(csv)) == 1
```

Faça também um teste manual da interface: coordenadas com vírgula, campo vazio, CSV aberto no Excel (erro de gravação), pasta `conteudo/` vazia.

**Checkpoint:** `pytest` passa e os casos de erro mostram mensagens claras, sem fechar o programa.

### Etapa 11: Dados e conteúdo reais

1. Substitua `dados/pontos.csv` por dados reais, com a fonte registrada em cada linha.
2. Reescreva os textos de `conteudo/` com referências (as do próprio artigo servem de base).
3. Revise o conteúdo de segurança com as orientações oficiais.
4. Adicione imagens em `conteudo/imagens/` (verifique a licença de cada uma).

**Checkpoint:** o resumo não mostra mais o aviso de "dados de exemplo".

### Etapa 12: Distribuição (opcional)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name SharkMaps main.py
```

Cuidados: copie as pastas `dados/` e `conteudo/` para junto do executável. O `config.py` atual usa o caminho do arquivo, e dentro de um executável isso muda, então será preciso ajustar para gravar o CSV numa pasta do usuário. O empacotamento com QtWebEngine costuma exigir testes.

**Checkpoint:** o executável abre em outro computador sem Python instalado.

### Etapa 13: Material para o artigo

Vá guardando durante o desenvolvimento:

- **Fluxograma(s)** do fluxo principal: dados (CSV) → pandas → folium → HTML → `QWebEngineView`, e do cadastro de novo registro.
- **Trechos de código** das funcionalidades inovadoras: carga com validação, geração do mapa, leitura dos `.md`, resumo com pandas.
- **Capturas de tela** das duas abas.
- Registro de **desafios** (limite do `setHtml`, cache do mapa, CSV em uso).

### Etapa 14: Propostas futuras (para o artigo)

- Banco de dados (SQLite) e sincronização entre usuários.
- Camadas de polígonos com GeoPandas (áreas de perigo, correntes de retorno).
- Clique no marcador abrir o texto educativo correspondente.
- Filtros por período e por espécie.
- Mapa offline e versão web/mobile.
- Importação de dados do CEMIT e exportação de relatórios.

---

## 4. Ordem recomendada e armadilhas

**Ordem:** dados (4) → mapa sem interface (5) → janela vazia (6) → aba do mapa (7) → aba educacional (8) → integração (9) → testes (10). Construir assim deixa cada parte verificável sozinha.

**Armadilhas comuns:**

- Mapa no lugar errado: confira se latitude e longitude não estão trocadas e se o sistema de coordenadas é EPSG:4326.
- Imagem que não aparece no texto: quase sempre é caminho relativo errado.
- Mapa que não atualiza: o navegador embutido pode reusar cache; o projeto já evita isso com um parâmetro de versão na URL.
- Mapa em branco sem internet: tiles e Leaflet vêm da rede.
- Registro que não grava: o CSV pode estar aberto no Excel.

---

## 5. Checklist final

- [ ] Requisitos escritos e numerados
- [ ] Repositório no GitHub com commits por etapa
- [ ] Mapa abre dentro da janela, com filtros e popups
- [ ] Cadastro de registros validado e gravado
- [ ] Aba educacional com texto, imagem e tabela
- [ ] Resumo com pandas atualizando
- [ ] Dados reais com fonte; textos com referências
- [ ] Aviso de que a ferramenta não substitui a sinalização oficial
- [ ] Testes passando
- [ ] Fluxogramas, trechos de código e capturas de tela para o artigo
