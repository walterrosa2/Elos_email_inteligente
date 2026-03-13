# Requisitos Funcionais — Coleta e Extração de Notas Fiscais por E‑mail
**Versão:** 1.0  
**Data:** 10/10/2025  
**Responsável:** Walter (Analista de Negócios)  
**Stack:** Python + OpenAI • Execução via Prompt de Comando • Painel Streamlit

---

## 1. Objetivo
Identificar e-mails com notas fiscais, baixar anexos (PDF), aplicar OCR quando necessário, extrair e tabular *todos os campos* relevantes em Excel, e organizar arquivos em pastas diárias baseadas na **data do e-mail**, com painel de administração e agendamento de execução.

## 2. Escopo e Atores
- **Atores:** Operador (usuário do painel), Serviço de Agendamento, Servidor de E-mail (IMAP/Exchange), Módulo de OCR/Extração.
- **Escopo:** Conexão ao e-mail, identificação de NFs, download de anexos, OCR/extração, tabulação Excel, organização de pastas, histórico e notificações.
- **Fora de escopo (v1):** Validação fiscal contra SEFAZ/Prefeitura, assinatura digital de saídas, integrações externas (ERP).

## 3. Requisitos Funcionais (RF)
**RF-001 – Configuração de e-mail**  

O sistema deve permitir cadastrar servidor, porta, protocolo, usuário/senha, pasta-alvo (ex.: INBOX/NFs) e testar a conexão.

**RF-002 – Seleção de escopo de varredura**  

Permitir definir intervalo (“hoje”, “últimas 24h”, data específica) e/ou processamento incremental desde a última execução.

**RF-003 – Identificação de e-mails com NFs**  

Detectar candidatos por assunto/corpo (palavras-chave como “NFe”, “NF-e”, “DANFE”, “NFSe”), remetentes configuráveis e existência de anexos PDF.

**RF-004 – Download de anexos**  

Baixar todos os PDFs dos e-mails identificados para área temporária, preservando metadados (remetente, assunto, data/hora do e-mail, Message-ID).

**RF-005 – Validação de anexos**  

Validar tipo (PDF), tamanho mínimo e legibilidade básica; anexos inválidos vão para fila de erros com motivo.

**RF-006 – Classificação do tipo de NF**  

Classificar automaticamente **NFe/NFCe/NFSe/CT-e** a partir de elementos visuais/textuais (ex.: “Chave de Acesso”, “RPS”, “ISS”).

**RF-007 – OCR e leitura**  

Aplicar OCR quando o PDF não for pesquisável e extrair texto necessário à extração de campos.

**RF-008 – Extração de campos (Cabeçalho – NFe/NFCe)**  

Extrair: chave de acesso, nº NF, série, data de emissão/saída, **emitente** (CNPJ, razão, IE, endereço), **destinatário** (CNPJ/CPF, razão, IE, endereço), CFOP(s), valor produtos, frete, seguro, descontos, **impostos** (ICMS/BC/valor/aliq., IPI, PIS, COFINS), valor total e forma de pagamento.

**RF-009 – Extração de itens (NFe/NFCe)**  

Extrair por item: nº do item, código, descrição, NCM, CFOP, CST/CSOSN, unidade, quantidade, valor unitário, valor total, impostos por item (ICMS/IPI/PIS/COFINS), descontos e observações.

**RF-010 – Extração de campos (NFSe)**  

Extrair: nº NFSe, RPS, data emissão, **prestador** (CNPJ, razão, inscrição), **tomador** (CNPJ/CPF, razão), código do serviço/LC116, município, base de cálculo, alíquota, ISS, valor serviço, retenções (INSS, IR, CSRF) e discriminação.

**RF-011 – Cobertura de “todos os campos”**  

Qualquer campo legível que não conste no dicionário básico deve ser capturado e exportado com colunas dinâmicas prefixadas por `EXTRA_` (garantindo cobertura total).

**RF-012 – Normalização de dados**  

Normalizar datas (DD/MM/AAAA), CNPJ/CPF (somente dígitos), valores (decimal), remover ruído de OCR e padronizar nomes de colunas.

**RF-013 – Validação de consistência**  

Checar presença de chave (NFe/NFCe), soma de itens vs. total, CNPJ válido e datas coerentes com a data do e-mail. Divergências devem ir para a planilha **ERROS** com motivo.

**RF-014 – De-duplicação**  

Evitar duplicidade por **chave de acesso** e, na ausência, por **hash** do anexo. Registrar ocorrências.

**RF-015 – Organização de pastas por data do e-mail**  

Criar estrutura `raiz/AAAA/MM/DD/` (com base na **data/hora do e-mail**). Subpastas mínimas: `originais/`, `processados/`, `planilhas/`, `logs/`, `json/`.

**RF-016 – Arquivamento do e-mail (opcional)**  

Salvar `.eml` e/ou metadados do e-mail em JSON para rastreabilidade.

**RF-017 – Planilha Excel diária**  

Gerar/atualizar **arquivo Excel por dia** com abas: **CABECALHO** (1 linha por nota), **ITENS** (1 linha por item), **ERROS**, **ORIGEM**. Se já existir, **anexar sem duplicar**.

**RF-018 – Exportação JSON**  

Salvar JSON por nota e um agregador diário com todos os campos extraídos.

**RF-019 – Painel Streamlit (Dashboard)**  

Exibir última execução, NFs processadas, erros, tempo total e links para pastas/planilhas do dia.

**RF-020 – Painel: Conexão de E-mail**  

CRUD de conexões, teste de conexão, seleção de pasta do servidor e filtros (remetentes, palavras-chave).

**RF-021 – Painel: Agendamentos**  

Cadastrar horário diário (ex.: 07:00), ativar/desativar e **executar agora** manualmente; registrar histórico de execuções.

**RF-022 – Painel: Execução & Logs**  

Mostrar fila, progresso por e-mail/anexo, status de OCR/extração e erros detalhados. Botão **reprocessar** item.

**RF-023 – Painel: Layout/Colunas**  

Exibir/baixar dicionário de dados, colunas dinâmicas criadas e amostra dos registros.

**RF-024 – Notificações**  

Enviar e-mail-resumo ao final (configurável): total processado, sucessos, erros, anexos ignorados e link para pasta do dia.

**RF-025 – Tratamento de anexos não-NF**  

Arquivar em `ignorados/` com razão registrada (boletos, imagens etc.).

**RF-026 – Reprocessamento controlado**  

Permitir reprocessar **um dia** ou **um e-mail/anexo específico**, com trilha de auditoria.

**RF-027 – Parametrizações gerais**  

Configurar fuso horário (padrão America/Sao_Paulo), idioma, padrão monetário, tamanho máximo, timeouts, retenção (dias) e limpeza.

**RF-028 – Segurança de acesso ao painel**  

Proteção por senha (v1) e perfis **Admin/Operador** (v2). Registrar login/logout.

**RF-029 – Relatórios**  

Baixar CSV/Excel filtrado por período, remetente, tipo de NF, CNPJ emitente/destinatário e presença de erros.

**RF-030 – Observabilidade**  

Gerar logs por execução/e-mail/anexo; armazenar em `logs/` do dia e exibir no painel.

**RF-031 – Internacionalização de campos (opcional v2)**  

Mapeamento de rótulos para PT-BR e EN-US nas planilhas.

**RF-032 – Multi-caixa postal (opcional v2)**  

Suportar múltiplas conexões de e-mail com isolamento de pastas de saída.

---

## 4. Layout Excel (referência mínima para implementação)
- **CABECALHO:** `DT_EMAIL | MSG_ID | TIPO_NF | CHAVE | NUMERO | SERIE | EMISSAO | EMITENTE_CNPJ | EMITENTE_RAZAO | DEST_CNPJCPF | DEST_RAZAO | VALOR_PRODUTOS | VALOR_TOTAL | ICMS_BC | ICMS_VALOR | IPI_VALOR | PIS_VALOR | COFINS_VALOR | MUNICIPIO | UF | FORMA_PAGTO | EXTRA_*`
- **ITENS:** `CHAVE | ITEM_N | COD | DESCRICAO | NCM | CFOP | CST | UN | QTDE | VLR_UNIT | VLR_TOTAL | ICMS_ALIQ | ICMS_VALOR | IPI_VALOR | PIS_VALOR | COFINS_VALOR | EXTRA_*`
- **ERROS:** `DT_EMAIL | MSG_ID | ARQUIVO | MOTIVO | DETALHE | ACAO_SUGERIDA`
- **ORIGEM:** `DT_EMAIL | MSG_ID | REMETENTE | ASSUNTO | ARQUIVO | HASH | CAMINHO_ORIGINAL`

## 5. Dependências & Premissas (para referência do time técnico)
- Acesso IMAP/Exchange com permissões de leitura e download.
- PDFs podem ser pesquisáveis ou escaneados (OCR necessário).
- Volume diário variável; execução automática diária às HH:MM (configurável).
- Armazenamento local seguindo a estrutura de pastas por **data do e-mail**.

---

**Observação:** Este documento cobre somente *Requisitos Funcionais*. Requisitos Técnicos, EAP/WBS e estimativas serão tratados nas próximas etapas.