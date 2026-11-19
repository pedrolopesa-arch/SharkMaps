# 🦈 SharkMaps — Monitoramento Costeiro & Educação Ambiental

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Maps](https://img.shields.io/badge/Mapping-Folium%20%7C%20Leaflet-77B800.svg?logo=leaflet&logoColor=white)](https://python-visualization.github.io/folium/)
[![Institution](https://img.shields.io/badge/UFRPE-PISI--1-green.svg)](https://ww3.ufrpe.br/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Sumário

- [Visão Geral](#-visão-geral)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Arquitetura e Estrutura de Diretórios](#-arquitetura-e-estrutura-de-diretórios)
- [Aplicação das Estruturas de Dados (PISI-1)](#-aplicação-das-estruturas-de-dados-pisi-1)
- [Segurança e Autenticação Institucional](#-segurança-e-autenticação-institucional)
- [Pré-requisitos e Instalação](#-pré-requisitos-e-instalação)
- [Como Executar](#-como-executar)
- [Credenciais Padrão de Demonstração](#-credenciais-padrão-de-demonstração)
- [Autores e Agradecimentos](#-autores-e-agradecimentos)

---

## 🌊 Visão Geral

O **SharkMaps** é uma aplicação desktop desenvolvida no âmbito da disciplina de **Princípios de Programação (PISI-1)** do curso de **Sistemas de Informação da Universidade Federal Rural de Pernambuco (UFRPE)**.

A ferramenta foi projetada para enfrentar o desafio histórico dos incidentes com tubarões na costa pernambucana (com foco na Região Metropolitana do Recife e Fernando de Noronha), unindo:
1. **Espacialização e georreferenciamento científico** dos incidentes oficiais registrados por órgãos competentes (como CEMIT/MONITUBA e ICMBio);
2. **Sinalização ativa de postos de salva-vidas** do Corpo de Bombeiros Militar de Pernambuco (CBMPE);
3. **Educação ambiental e prevenção ativa**, oferecendo à população e turistas fichas biológicas das espécies locais (*Carcharhinus leucas*, *Galeocerdo cuvier*), compreensão de fatores de risco marinho e protocolos de primeiros socorros.

---

## 🚀 Principais Funcionalidades

### 1. 🗺️ Mapa Interativo e Camadas Geográficas
- **Integração Desktop + Web**: Renderização em tempo real de mapas baseados em Folium/Leaflet diretamente na janela do PySide6 através de `QWebEngineView`.
- **Camada de Incidentes**: Marcadores com categorização visual por espécie, data, praia e descrição do evento.
- **Agrupamento Dinâmico (*Clustering*)**: Uso de `MarkerCluster` para otimização de desempenho visual em trechos de alta densidade de registros.
- **Mapa de Calor (*HeatMap*)**: Visualização de manchas de incidência térmica para identificar trechos críticos da orla.
- **Polígono da Área de Risco**: Delimitação geométrica das zonas historicamente restritas (Pina, Boa Viagem, Piedade, Paiva).
- **Postos de Salvamento (CBMPE)**: Mapeamento de guaritas e postos fixos de bombeiros militares ao longo da faixa litorânea.

### 2. 📝 Gestão de Registros (CRUD Geográfico com Trava de Integridade)
- **Modo Visitante vs. Modo Institucional**: Visitantes navegam pelas camadas e conteúdos educativos em modo somente leitura; administradores e pesquisadores autenticados podem cadastrar, alterar e remover registros.
- **Trava Geográfica (*Bounding Box Validation*)**: Qualquer nova coordenada informada é verificada automaticamente contra os limites territoriais permitidos:
  - Litoral de Pernambuco: Latitude `[-8.95, -7.50]`, Longitude `[-35.25, -34.75]`
  - Arquipélago de Fernando de Noronha: Latitude `[-3.95, -3.75]`, Longitude `[-32.55, -32.35]`
- **Backups Automáticos & Auditoria**: A cada mutação na base de dados (`dados/pontos.csv`), um snapshot é armazenado em `dados/backups/` e uma linha de auditoria com timestamp e hash de sessão é gravada em `dados/auditoria.log`.

### 3. 🛡️ Segurança e Acesso Institucional
- Senhas armazenadas com **hash criptográfico SHA-256** e **salt exclusivo gerado aleatoriamente** (`secrets.token_hex(16)`).
- Prevenção contra ataques de temporização (*timing attacks*) via `secrets.compare_digest`.
- Validação de formato e restrição a e-mails institucionais de ensino e pesquisa (`@ufrpe.br`, `@ufpe.br`, `@cemit.pe.gov.br`, `@bombeiros.pe.gov.br`, etc.).

### 4. 📚 Educação e Primeiros Socorros Costeiros
- **Catálogo de Espécies**: Informações morfológicas, comportamento, habitat e status na Lista Vermelha da IUCN.
- **Fatores Ambientais de Risco**: Guias sobre a influência das marés de sizígia, turbidez da água em períodos chuvosos e canais submarinos naturais.
- **Protocolos de Emergência**: Acesso direto aos contatos de prontidão (Bombeiros 193, SAMU 192) e fluxograma de resposta a traumas marinhos e estancamento de hemorragias.

---

## 🏗️ Arquitetura e Estrutura de Diretórios

```
projeto-worktree/
├── assets/                       # Recursos visuais e identidade da aplicação
│   └── logo_sharkmaps.svg        # Logotipo vetorial do SharkMaps
├── conteudo/                     # Fichas educativas em Markdown e ativos estáticos
│   ├── especies.md               # Catálogo biológico detalhado de elasmobrânquios
│   ├── fatores_ambientais.md     # Análise de correntes, marés e turbidez
│   ├── prevencao.md              # Diretrizes de segurança e primeiros socorros
│   └── Imagens/                  # Ilustrações e diagramas anatômicos
├── dados/                        # Camada de persistência local
│   ├── admins.json               # Credenciais de administradores (salt + hash)
│   ├── pontos.csv                # Base georreferenciada de incidentes e postos
│   ├── auditoria.log             # Trilha de auditoria das operações do sistema
│   ├── backups/                  # Cópias de segurança automáticas geradas pelo CRUD
│   └── camadas/                  # Arquivos GeoJSON (polígonos de risco)
├── interface/                    # Camada de Apresentação (PySide6 / Qt6)
│   ├── boas_vindas.py            # Splash screen, seleção de perfil e modal de login
│   ├── janela.py                 # Janela principal com controle de abas e sessão
│   ├── aba_mapa.py               # Visualizador do mapa (WebEngine) e painéis de controle
│   ├── aba_info.py               # Visualizador de conteúdo educativo e emergência
│   └── estilos.py                # Folhas de estilo QSS (tema oceânico)
├── mapa/                         # Camada Geoespacial e Negócio
│   ├── gerador.py                # Lógica de renderização de mapas com Folium
│   └── repositorio.py            # Acesso a dados, validações geográficas e backups
├── seguranca/                    # Camada de Criptografia e Autenticação
│   └── auth.py                   # Hashes com salt, verificação e gestão de admins
├── config.py                     # Constantes globais, caminhos e limites geográficos
├── main.py                       # Ponto de entrada e inicialização do SharkMapsApp
├── requirements.txt              # Dependências do ecossistema Python
└── README.md                     # Documentação oficial do projeto
```

---

## 🧠 Aplicação das Estruturas de Dados (PISI-1)

Conforme os princípios lecionados na disciplina, as estruturas de dados nativas do Python foram selecionadas estrategicamente de acordo com suas características de desempenho e semântica:

| Estrutura | Local de Aplicação | Justificativa Técnica |
| :--- | :--- | :--- |
| **Tuplas (`tuple`)** | `config.py`, `mapa/repositorio.py`, `seguranca/auth.py` | Utilizadas para armazenar coordenadas fixas (ex: centro do Recife `(-8.05428, -34.8813)`), intervalos numéricos imutáveis de trava geográfica (`LIMITES_LITORAL_PE`) e retornos duplos de validação de login `(status_booleano, mensagem)`. |
| **Listas (`list`)** | `main.py`, `mapa/repositorio.py`, `mapa/gerador.py`, `interface/aba_info.py` | Empregadas para coleções dinâmicas e ordenadas de elementos, tais como os argumentos do Chromium, ordem das colunas do CSV, vértices do polígono da Área de Perigo e a lista de coordenadas fornecida ao `HeatMap`. |
| **Dicionários (`dict`)** | `mapa/repositorio.py`, `mapa/gerador.py`, `interface/aba_info.py` | Permitem mapeamento semântico chave-valor com busca $O(1)$. Utilizados para empacotar os atributos de cada novo incidente antes da persistência, associar cores às categorias de marcadores e consolidar métricas estatísticas. |
| **Dicionários Aninhados (`dict de dict`)** | `seguranca/auth.py`, `dados/admins.json` | Estruturação de dados hierárquicos indexados por uma chave única (`username`), permitindo resgatar instantaneamente todas as credenciais e metadados (`nome`, `instituicao`, `papel`, `salt`, `hash`, `ativo`) e facilitando a serialização JSON. |

---

## 🔒 Segurança e Autenticação Institucional

O módulo `seguranca/auth.py` implementa boas práticas de autenticação:
1. **Derivação de Hash com Salt Aleatório**:
   $$\text{Hash} = \text{SHA-256}(\text{Salt} + \text{Senha})$$
2. **Resistência a Timing Attacks**:
   As comparações de senhas não usam operadores `==`, mas sim `secrets.compare_digest()`, mantendo o tempo de checagem constante independentemente de quantos caracteres coincidam.
3. **Domínios Autorizados para Pesquisadores**:
   O auto-cadastro ou validação institucional verifica extensões governamentais e acadêmicas:
   - `@ufrpe.br`, `@ufpe.br`, `@upe.br`
   - `@cemit.pe.gov.br`, `@pe.gov.br`, `@bombeiros.pe.gov.br`
   - `@icmbio.gov.br`, `@ibama.gov.br`, `@gov.br`

---

## 💻 Pré-requisitos e Instalação

### Pré-requisitos
- **Python 3.10 ou superior** instalado ([python.org](https://www.python.org/downloads/))
- **Git** instalado no sistema operacional

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/SEU-USUARIO/sharkmaps.git
   cd sharkmaps
   ```

2. **Crie e ative um ambiente virtual (recomendado):**
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🏃 Como Executar

Com o ambiente virtual ativado, execute o ponto de entrada da aplicação:

```bash
python main.py
```

> **Nota técnica (Windows)**: O arquivo `main.py` injeta automaticamente a variável de ambiente `QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu"`, evitando eventuais telas em branco durante a renderização do mapa com aceleração de hardware em placas de vídeo integradas.

---

## 🔑 Credenciais Padrão de Demonstração

Para fins acadêmicos e avaliação de bancas examinadoras, o sistema já é inicializado com as seguintes credenciais pré-configuradas em `dados/admins.json`:

| Usuário | Senha Padrão | Instituição | Perfil |
| :--- | :--- | :--- | :--- |
| `admin` | `SharkUFRPE@2026` | UFRPE / Projeto SharkMaps | Super-Administrador |
| `admin_cemit` | `SharkUFRPE@2026` | CEMIT - Pernambuco | Pesquisador / Analista |

> *A senha pode ser alterada diretamente na interface após o login institucional.*

---

## 👥 Autores e Agradecimentos

- **Desenvolvedor:** Pedro Lopes Arruda ([@pedrolopesa](https://github.com/pedro-lopes-a))
- **Orientador / Docente:** Prof. Me. Cleyton V. C. de Magalhães
- **Unidade Acadêmica:** Departamento de Estatística e Informática (DEINFO)
- **Instituição:** Universidade Federal Rural de Pernambuco (UFRPE)
- **Apoio e Fontes de Dados:**
  - Comitê Estadual de Monitoramento de Incidentes com Tubarões (**CEMIT/PE**)
  - Corpo de Bombeiros Militar de Pernambuco (**CBMPE**)
  - Instituto Chico Mendes de Conservação da Biodiversidade (**ICMBio**)
