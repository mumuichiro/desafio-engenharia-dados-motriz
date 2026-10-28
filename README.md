# Desafio Técnico — Engenheiro(a) de Dados Pleno (Motriz)

Este repositório contém a solução completa para o pipeline de integração, higienização, validação e análise de dados de frequência escolar das **Redes Municipais A, B e C**, referente ao período letivo de **03/08/2026 a 30/10/2026**.

---

## 1. Arquitetura da Solução

A solução foi desenvolvida em **Python 3.10+** utilizando uma arquitetura modular baseada em princípios de *Clean Code* e *Design Patterns* (em especial o **Strategy Pattern** para os extratores de dados).

desafio_motriz/
├── dados/                      # Dados brutos das redes A, B e C + Calendário oficial
├── extractors/                 # Estratégias de extração heterogênea (SQL, NDJSON, CSV)
├── transformers/               # Engine de higienização, sanitização e validação (Regras R1-R10)
├── loaders/                    # Carga no Google BigQuery com fallback local
├── utils/                      # Sanitização Unicode/regex e logger estruturado
├── sql/                        # Consultas em BigQuery Standard SQL
├── resultados/                 # Diretório de saída local (Staging em CSV)
├── main.py                     # Orquestrador do pipeline
└── README.md

### Camadas de Dados (Medallion Architecture)

1. **Camada Bruta (Raw):** Extração fidedigna das fontes de dados sem alteração de esquema.
2. **Camada Tratada (Staging / Silver):** 
   - `stg_frequencia_validos`: Registros higienizados que cumprem 100% das regras de negócio.
   - `stg_frequencia_invalidos`: Registros descartados enriquecidos com a coluna `motivo_descarte` para auditoria e relatórios de qualidade.
3. **Camada Analítica (Gold / Marts):** Views e consultas SQL (`sql/`) com agregações por escola, por turma e lista de acompanhamento da busca ativa escolar.

---

## 2. Decisões de Engenharia e Raciocínio Técnico

### A. Extração Modular (Strategy Pattern)
Cada rede utiliza uma tecnologia de persistência distinta:
- **Rede A (PostgreSQL):** Parser dedicado para leitura direta das instruções do dump SQL (`schema educacao`), processando blocos de inserção/cópia com tratamento resiliente de codificação (`UTF-8` e `Latin-1`), sem dependência obrigatória de instância ativa de banco relacional.
- **Rede B (NoSQL / NDJSON):** Leitura iterativa linha a linha de JSONs aninhados, tratando estruturas complexas e datas no formato estendido do MongoDB (`$date`).
- **Rede C (Planilhas CSV):** Varredura dinâmica no diretório `dados/rede_c/*.csv` (12 planilhas referentes a 4 escolas × 3 meses) com detecção automática de codificação e delimitadores, padronizando cabeçalhos heterogêneos.

### B. Sanitização e Identidade do Aluno (Regra R4)
Para consolidar a identidade dos alunos sem duplicar cadastros por variações de grafia, acentuação ou caixa:
- Utilizou-se a decomposição **Unicode NFD** para remover acentos/diacríticos.
- Aplicação de letras minúsculas e limpeza de múltiplos espaços internos via Expressões Regulares (Regex).
- A chave sanitizada (`nome_aluno_sanitizado` + `data_nascimento`) é utilizada para garantir a deduplicação (R5) e a agregação da Busca Ativa (R9), preservando o nome original para exibição nos relatórios.

### C. Qualidade e Gestão de Registros Inválidos (Regra R2)
Registros que violam critérios essenciais (fora do calendário letivo, campos obrigatórios nulos, datas fora da vigência de matrícula ou status de frequência desconhecido) **não são deletados silenciosamente**. Eles são redirecionados para a tabela/arquivo de auditoria `stg_frequencia_invalidos`, viabilizando diagnósticos de qualidade de dados junto às secretarias municipais.

### D. Idempotência e Graceful Degradation
- **Idempotência:** A carga no BigQuery utiliza a disposição `WRITE_TRUNCATE`, garantindo que reexecuções do pipeline não dupliquem registros na camada de staging.
- **Fallback Local (Resiliência):** Caso o ambiente de execução não possua credenciais ativas da Google Cloud Platform (`DefaultCredentialsError`), o pipeline executa uma degradação suave, salvando automaticamente as tabelas tratadas na pasta local `/resultados` em formato CSV seguindo exatamente o layout exigido no enunciado.

---

## 3. Relatório de Qualidade de Dados

Após a execução do pipeline nas três bases de dados, obteve-se o seguinte balanço consolidado:

| Métrica / Etapa | Registros / Ocorrências |
| :--- | :--- |
| **Registros Lidos — Rede A** | 26.177 |
| **Registros Lidos — Rede B** | 19.680 |
| **Registros Lidos — Rede C** | 22.623 |
| **Total de Registros Brutos Processados** | **68.480** |
| **Registros Duplicados Removidos (Regra R5)** | 520 |
| **Registros Válidos (`stg_frequencia_validos`)** | **42.505** |
| **Registros Inválidos / Auditados (`stg_frequencia_invalidos`)** | **25.455** |

### Principais Motivos de Descarte
1. **Fora do Calendário Letivo (R1):** Ocorrências registradas em fins de semana, feriados ou datas fora do período de 03/08/2026 a 30/10/2026.
2. **Fora da Vigência da Matrícula (R6):** Chamadas efetuadas em datas anteriores ao início ou posteriores ao fim da matrícula do aluno.
3. **Status de Frequência Inválido/Ausente (R3):** Registros sem informação de chamada (nulos) ou com valores não mapeados.

---

## 4. Como Executar o Projeto

### Pré-requisitos
- Python 3.10 ou superior instalado.
- Terminal PowerShell (Windows) ou Bash (Linux/Mac).

### Passo a Passo

1. **Ativar o ambiente virtual (venv):**
   - Windows (PowerShell): `.\venv\Scripts\Activate.ps1`

2. **Instalar dependências:**
   - Comando: `py -m pip install -r requirements.txt`

3. **Disposição dos arquivos de dados:**
   Garanta que a pasta `dados/` contenha os arquivos de entrada:
   - `dados/calendario_letivo_2026.csv`
   - `dados/rede_a/rede_a_dump.sql`
   - `dados/rede_b/alunos_rede_b.ndjson`
   - `dados/rede_c/*.csv` (12 arquivos de planilhas)

4. **Executar o orquestrador do pipeline:**
   - Comando: `py main.py`

5. **Resultados Gerados:**
   - Se autenticado na GCP: As tabelas `stg_frequencia_validos` e `stg_frequencia_invalidos` serão atualizadas no BigQuery.
   - Sem autenticação GCP: Os arquivos `stg_frequencia_validos.csv` e `stg_frequencia_invalidos.csv` estarão disponíveis no diretório `/resultados`.

---

## 5. Modelagem e Consultas SQL (BigQuery)

As consultas analíticas estão armazenadas na pasta `sql/`:

1. **`sql/01_frequencia_escola_mes.sql`**: Agrega o percentual de frequência ponderado por escola e mês (Presenças ÷ Válidos × 100).
2. **`sql/02_frequencia_turma_mes.sql`**: Agrega o percentual de frequência por turma e mês.
3. **`sql/03_alunos_busca_ativa.sql`**: Lista alunos com frequência acumulada estritamente inferior a **75,00%** em todo o período, consolidando o histórico do aluno na rede em caso de transferências entre turmas/escolas.

---

## 6. Governança, Proteção de Dados (LGPD) e Uso de IA

### A. Conformidade com a LGPD
- **Minimização e Propósito:** Dados pessoais de estudantes (nome e data de nascimento) são processados exclusivamente para consolidação do histórico de frequência e controle da Busca Ativa Escolar.
- **Sanitização Segura:** O processo de limpeza transforma os nomes em chaves padronizadas (`nome_aluno_sanitizado`), evitando inconsistências cadastrais e garantindo integridade no tratamento.
- **Segurança e Auditoria:** Registros inconsistentes são isolados no ambiente de staging/auditoria (`stg_frequencia_invalidos`), impedindo vazamento de inconsistências e permitindo governança adequada dos dados.

### B. Transparência no Uso de Ferramentas de IA
Conforme orientação do desafio técnico, declara-se que modelos de Linguagem/IA (Gemini) foram utilizados como ferramenta de apoio no desenvolvimento do projeto, atuando em:
- **Refatoração e Validação de Código:** Suporte na estruturação do padrão *Strategy* para os extratores e otimização das expressões regulares de sanitização Unicode.
- **Formatação de Documentação:** Apoio na revisão da documentação técnica e estruturação do relatório consolidado de métricas de qualidade.
- *Nota:* Todas as soluções, arquitetura, regras de negócio e consultas SQL foram revisadas, testadas e validadas pelo candidato, garantindo total domínio sobre o código entregue.