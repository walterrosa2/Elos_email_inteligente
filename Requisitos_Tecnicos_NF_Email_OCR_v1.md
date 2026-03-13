# Requisitos Técnicos — Coleta e Extração de Notas Fiscais por E-mail (v1.0)
**Data:** 10/10/2025 — **Timezone:** America/Sao_Paulo  
**Alinhado a:** Requisitos Funcionais v1.0

> Escopo técnico alinhado ao seu documento de **Requisitos Funcionais v1.0**, mantendo nomes de abas/colunas e regras de pastas. Foco em reduzir retrabalho, garantir rastreabilidade e permitir evolução incremental.

---

## 1) Arquitetura de Solução

- **Camadas**
  - **Ingestão de E-mail** (IMAP/Exchange): busca, filtragem e download de anexos PDF; captura de metadados (Message-ID, remetente, assunto, data/hora).
  - **Staging & Classificação**: verificação do tipo (PDF), legibilidade, **classificação do tipo de NF** (NFe/NFCe/NFSe/CT-e) via padrões textuais/visuais.
  - **OCR & Extração**: OCR somente quando necessário (PDF não pesquisável); extração de campos de **cabeçalho** e **itens**; normalização e validações.
  - **Persistência & Saídas**: Excel diário (abas: CABECALHO, ITENS, ERROS, ORIGEM), JSON por nota e agregado diário; trilha de auditoria.
  - **Orquestração & Agendamento**: serviço de agenda diária + execução manual.
  - **Painel (Streamlit)**: configuração, execução, monitoramento, reprocesso e relatórios.
- **Fluxo (alto nível)**
  1. IMAP/Exchange → filtra e-mails candidatos → baixa anexos PDF.
  2. Staging → valida tipo e legibilidade → classifica tipo de NF.
  3. OCR condicional → extrai campos/itens → normaliza → valida.
  4. De-dupe → Excel/JSON → move arquivos para pastas do **dia do e-mail**.
  5. Log, métricas e notificação opcional ao final.

## 2) Stack Técnica (versões sugeridas)

- **Python** 3.11+  
- **E-mail**: `imapclient` (IMAP) / `mailparser`; opcional Exchange: `exchangelib` (v2).  
- **PDF**: `pypdf` (checagem), `pdfminer.six` (texto).  
- **OCR**: `ocrmypdf` + Tesseract (Idioma pt/eng); fallback: `pytesseract` em imagens extraídas.  
- **Classificação & Extração**: `regex`/`rapidfuzz`, `pandas` (tabulação); opcional: `docling` (v2) p/ layouts difíceis.  
- **Excel**: `pandas` + `openpyxl` (preserva abas, appends idempotentes).  
- **Agendamento**: `APScheduler` (background) e/ou agendador do SO (Task Scheduler/crontab).  
- **Config & Secrets**: `pydantic-settings` (.env), `keyring` (credenciais).  
- **Logs**: `logging` (handler rotativo), **JSONLog** opcional (`python-json-logger`).  
- **Hashing**: `hashlib` (SHA-256).  
- **Web UI**: `streamlit` + `watchdog` (opcional, observar pastas).  
- **Validações**: `pydantic` (schemas de saída); CNPJ/CPF: `validate-docbr`.

## 3) Estrutura de Módulos (pastas/arquivos)

```
app/
  core/
    config.py           # BaseSettings (env, paths, timezone, limites)
    logging_config.py   # Formato, rotação, níveis e correlação
    constants.py        # Palavras-chave, regex, dicionário de colunas
    models.py           # Schemas pydantic (Cabecalho, Item, Erro, Origem)
    utils.py            # Hash, datas, normalização, validadores
  email_client/
    imap_service.py     # Conexão, busca, filtros, download
    classifiers.py      # Heurísticas de e-mail (assunto/corpo/anexo)
  ingest/
    staging.py          # Salvamento inicial, metadados .json, .eml opcional
    pdf_check.py        # Valida PDF, pesquisável vs scaneado
    ocr.py              # OCR condicional (ocrmypdf) com fila
    nf_classifier.py    # NFe/NFCe/NFSe/CT-e (regex/estruturas)
  extract/
    nfe_danfe.py        # Regras de campos/itens NFe/NFCe
    nfse.py             # Regras NFSe (RPS, LC116, ISS, retenções)
    common.py           # Normalização, EXTRA_*, mapeamento de colunas
    validators.py       # Consistência (chave, totais, CNPJ, datas)
    dedupe.py           # Por chave e/ou hash
  outputs/
    excel_writer.py     # Escrita/append idempotente nas 4 abas
    json_writer.py      # JSON por nota e agregado diário
    organizer.py        # Move para /AAAA/MM/DD/ e subpastas
  scheduler/
    jobs.py             # Tarefa diária, reprocesso por dia ou por arquivo
  ui/
    app.py              # Streamlit (páginas: Conexão, Agendamentos, Execução, Layout, Relatórios)
  tests/
    data/               # PDFs de exemplo (pesquisáveis/scaneados)
    test_*.py
```

## 4) Configuração (.env) — chaves principais

```
APP_TIMEZONE=America/Sao_Paulo
DATA_ROOT=./dados
EMAIL_PROTOCOL=IMAP
EMAIL_HOST=imap.seudominio.com
EMAIL_PORT=993
EMAIL_USER=usuario@dominio.com
EMAIL_FOLDER=INBOX/NFs
EMAIL_USE_SSL=true
EMAIL_SENDER_WHITELIST=fornecedor1.com,fornecedor2.com
EMAIL_SUBJECT_KEYWORDS=NFe;NF-e;DANFE;NFSe;RPS
SCAN_WINDOW=24h                 # ou YYYY-MM-DD
MAX_ATTACHMENT_MB=25
OCR_LANG=por+eng
SCHEDULE_DAILY=07:00
RETENCAO_DIAS=180
```

> Senhas guardadas via **keyring**; .env não deve conter segredos.

## 5) Regras Técnicas de Processamento

- **Chave de correlação**: `MSG_ID` (Message-ID) + `nome_arquivo` + `SHA256` (do anexo).  
- **Classificação de NF** (mínima v1):  
  - **NFe/NFCe**: presença de “Chave de Acesso” (44 dígitos), “DANFE”, campos ICMS/IPI, CFOP, NCM.  
  - **NFSe**: “RPS”, “Código do Serviço/LC116”, “ISS”, “Tomador/Prestador”.  
  - **CT-e** (se aparecer): “Conhecimento de Transporte”, “CT-e”, CFOP 5353/6353 (indicativo).  
- **OCR condicional**: executar **apenas** quando `pdfminer` indicar ausência de texto; usar `ocrmypdf --skip-text --optimize 1`.  
- **Extração**:
  - **Cabeçalho** (NFe/NFCe): chave, número, série, emissor/dest., datas, valores e impostos; **Itens**: nº item, código, descrição, NCM, CFOP, CST/CSOSN, UN, QTDE, unitário, total, impostos por item.  
  - **NFSe**: nº NFSe, RPS, datas, prestador/tomador, base, alíquota/ISS, retenções (INSS/IR/CSRF), código do serviço, município, discriminação.  
  - **Campos extras** não mapeados → colunas dinâmicas `EXTRA_*`.
- **Normalização**: datas `DD/MM/AAAA`, números decimais com ponto interno (para Excel via pandas), CNPJ/CPF só dígitos, UF uppercase.  
- **Validações**:  
  - Chave NFe 44 dígitos válida (módulo verificador).  
  - Soma dos itens ≈ total (tolerância configurável).  
  - CNPJ/CPF válidos.  
  - Data de emissão coerente com **data do e-mail** (alerta se divergente).  
  - Inconsistências → aba **ERROS** (com `MOTIVO` e `ACAO_SUGERIDA`).  
- **De-duplicação**:  
  - Prioridade: **CHAVE**; fallback: **SHA-256** do anexo + `MSG_ID`.  
  - Duplicatas → registradas (contagem/primeira ocorrência preservada).  
- **Organização de Pastas** (com base **na data do e-mail**):  
  ```
  {DATA_ROOT}/{AAAA}/{MM}/{DD}/
      originais/     # anexos brutos
      processados/   # PDFs pós-OCR (se aplicado)
      planilhas/     # Excel diário
      json/          # por-nota + agregado dia
      logs/          # logs da execução
      ignorados/     # anexos não-NF
  ```
- **Excel diário**: arquivo único por dia; **append idempotente** (checar chave/hash antes de inserir).  
- **JSON**: um arquivo por nota (`CHAVE.json`) e um `YYYY-MM-DD_aggregate.json`.

## 6) Painel (Streamlit)

- **Conexão de E-mail**: CRUD de perfis, teste de conexão, pasta do servidor, filtros (remetentes, keywords).  
- **Agendamentos**: horário diário (HH:MM), ativar/desativar, **Executar agora**, histórico de runs.  
- **Execução & Logs**: fila de e-mails/ anexos, status (baixado → OCR → extraído → validado → escrito), botão **Reprocessar**.  
- **Layout/Colunas**: exibe dicionário, colunas `EXTRA_*` geradas, preview de registros.  
- **Relatórios**: filtros por período, tipo NF, CNPJ, remetente; exportar CSV/Excel.  
- **Acesso**: senha simples (v1); perfis Admin/Operador (v2).  
- **UX**: links diretos para pastas/planilha do dia.

## 7) Agendamento & Execução

- **APScheduler** (BackgroundScheduler) com job diário na hora configurada; **jitter** (±2 min) para evitar colisões.  
- **Modo CLI**: `python -m app.cli run --date 2025-10-10` (reprocesso por dia) e `--file caminho.pdf` (item específico).  
- **Reprocesso**: consulta índice local (`processed_index.jsonl` ou SQLite) para evitar duplicidade; opção `--force`.

## 8) Segurança, LGPD e Compliance

- **Credenciais** fora do repositório (keyring/secret store).  
- **Trilha de auditoria**: salvar `.eml` e `origem.json` (remetente, assunto, data/hora, hash, caminhos).  
- **Sanitização**: logs não devem conter dados sensíveis (CNPJ/CPF só últimos 4 dígitos quando necessário).  
- **Retenção**: política configurável (ex.: 180 dias) com rotina de limpeza.  
- **Hardening**: validação estrita de anexos (MIME e assinatura mágica), limite de tamanho e timeouts.

## 9) Observabilidade & Métricas

- **Logs**: por execução/e-mail/anexo; inclusão de `run_id` e `msg_id`.  
- **Métricas**: total de e-mails, anexos baixados/ignorados, % OCR, tempo médio por anexo, taxa de erro, duplicatas.  
- **Notificação** (opcional): resumo por e-mail com indicadores e link para pasta do dia.

## 10) Desempenho e Confiabilidade

- **Paralelismo controlado**: pool de threads p/ OCR/extrator (tamanho configurável).  
- **Backoff** exponencial em falhas IMAP/OCR.  
- **Tolerância** a PDFs corrompidos (quarentena em `ignorados/` com motivo).

## 11) Testes (DoR → DoD)

- **Unit**: normalização, validadores, regex principais, cálculo de totais.  
- **Integração**: IMAP falso, PDFs de exemplo (pesquisáveis e scaneados), OCR offline.  
- **E2E**: cenário diário completo (entrada → planilha), asserts por abas e contagens.  
- **Conjuntos de teste**: NFe, NFCe, NFSe, anexos não-NF, PDFs vazios/corrompidos.  
- **Critérios de aceite**:  
  - Geração de Excel com 4 abas e dtypes corretos.  
  - De-dupe por CHAVE funcionando.  
  - 100% das notas legíveis com campos mínimos; ilegíveis em **ERROS** com ação sugerida.  
  - Estrutura de pastas por **data do e-mail** preenchida.

## 12) Modelo de Dados (tipos principais)

- **CABECALHO**: strings normalizadas (CHAVE, CNPJs, UF), datas `datetime64[ns]` (EMISSAO, DT_EMAIL), numéricos `float64` (VALOR_*, IMPOSTOS_*).  
- **ITENS**: códigos/textos (`str`), quantidades/valores `float64`; manter `ITEM_N` como `Int64` (aceita NA).  
- **ERROS**: `DT_EMAIL: datetime`, `MOTIVO/DETALHE/ACAO_SUGERIDA: str`.  
- **ORIGEM**: remetente/assunto (str), `HASH: str`, caminhos (str).  
- **EXTRA_***: `object` (mapeado a `str`) — não quebrar o schema principal.

## 13) Matriz de Rastreabilidade (amostra)

- **RF-003 (Identificação)** → `email_client/classifiers.py`, filtros configuráveis.  
- **RF-004/005 (Download/Validação)** → `email_client/imap_service.py`, `ingest/pdf_check.py`.  
- **RF-007/008/009/010** → `ingest/ocr.py`, `extract/nfe_danfe.py`, `extract/nfse.py`.  
- **RF-012/013** → `extract/common.py`, `extract/validators.py`.  
- **RF-014** → `extract/dedupe.py` (CHAVE → hash fallback).  
- **RF-015/017/018** → `outputs/organizer.py`, `excel_writer.py`, `json_writer.py`.  
- **RF-019…023** → `ui/app.py`.  
- **RF-026 (Reprocesso)** → `scheduler/jobs.py` + `cli`.

## 14) Riscos & Mitigações

- **Layouts muito variados (NFSe)** → versão v2 com parsers específicos por município + fallback `EXTRA_*`.  
- **OCR pesado** → fila + cache de OCR (não repetir para o mesmo hash).  
- **Anexos não-NF** → regras de descarte claras + pasta `ignorados/` com motivo.  
- **Planilha bloqueada por uso** → retry com lock de arquivo (ex.: `portalocker`) e escrita transacional (temp → swap).

---

### Próximos Passos
1) Confirmar **.env** e credenciais (sem segredos em texto-plano).  
2) Gerar **EAP/WBS** e cronograma de entrega.  
3) Montar **dataset de teste** (5 PDFs de cada tipo + casos de erro).  
4) Iniciar **MVP** com caminho feliz NFe e expandir para NFSe.