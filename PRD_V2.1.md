# PRD - Documentação do Pipeline V2.1
## Coleta, Classificação e Extração de Documentos (Fiscal e Financeiro)

### 1. Visão Geral
Esta versão (V2.1) evolui o MVP anterior para um pipeline robusto, orientado a Jobs, com garantia de idempotência, auditabilidade completa e suporte a "Human-in-the-Loop" para casos de baixa confiança. O objetivo é suportar múltiplos tipos de documentos (NF de produto, CT-e, NFS, Boletos, Faturas) através de um sistema de "contratos" (schemas) configuráveis.

### 2. Arquitetura Modular (V2.1)
A estrutura de diretórios e responsabilidades é organizada para manter a modularidade sem quebrar o legado funcional:

- **`app/core/`**: Configurações globais, variáveis de ambiente (.env), configuração de logs (Loguru) e utilitários base.
- **`app/db/`**: Camada de persistência. SQLite para o MVP+, preparado para migração para Postgres. Responsável por salvar metadados dos jobs.
- **`app/storage/`**: Gerenciamento de arquivos (Local e/ou S3/Blob). Implementa hashing, versionamento e organização de pastas.
- **`app/email_client/`**: Conectores IMAP (e futuramente Graph API). Regras de busca por cliente/caixa.
- **`app/ingest/`**: Staging area. Validações iniciais, deduplicação e normalização de entrada.
- **`app/orchestrator/`**: Gerenciador do ciclo de vida dos Jobs (Fila, Estados, Retries, Paralelismo).
- **`app/textract/`**: (Novo) Wrapper para AWS Textract. Suporte a processamento síncrono e assíncrono com fallback.
- **`app/classify/`**: Motor de classificação híbrida (Regras + LLM). Identifica `doc_type`, confiança e sinais.
- **`app/contracts/`**: (Novo) Gerenciamento de schemas (contratos) JSON para cada tipo de documento.
- **`app/extract/`**: Extração de dados baseada nos contratos. Utiliza Plugins + LLM.
- **`app/validation/`**: Regras de negócio, normalização de dados e validações fiscais/financeiras.
- **`app/review/`**: Interface Streamlit para revisão manual (Human-in-the-Loop).
- **`app/outputs/`**: Geração de arquivos finais (Excel, JSON, Export).
- **`app/auth/`**: (Novo) Controle de acesso (RBAC) e autenticação.
- **`app/observability/`**: (Novo) Métricas, dashboards de auditoria e trilhas de processamento.

### 3. Fluxo do Pipeline (Ciclo de Vida do Job)
Cada anexo de e-mail é tratado como um **Job** único com estados persistidos:
`QUEUED` → `STAGED` → `TEXT_EXTRACTED` → `CLASSIFIED` → `EXTRACTED` → `VALIDATED` → (`APPROVED` | `REVIEW_PENDING`) → `EXPORTED`

#### 3.1. Ingestão (Ingest) & Staging
- **Fonte**: Monitoramento de caixas de e-mail via IMAP.
- **Identificação**: Chave única baseada em `Message-ID` + `Attachment_Hash` (SHA256).
- **Ação**:
    1.  Baixar anexo.
    2.  Salvar binário na camada de Storage.
    3.  Criar registro de Job no DB com metadados iniciais.
- **Deduplicação**: Ignora processamento se o hash já existir e estiver concluído.

#### 3.2. Pré-processamento (Textract)
- **Objetivo**: Converter PDF/Imagem em texto cru (`raw_text`) preservando layout quando possível.
- **Ferramenta**: AWS Textract.
    - **Sync**: Para arquivos pequenos/leves.
    - **Async**: Fallback para arquivos grandes ou complexos.
- **Validação**: `PDFCheck` para detectar arquivos corrompidos ou protegidos por senha antes do envio.
- **Armazenamento de Anexos**:
    - Estrutura hierárquica por data de ingestão: `dados/{ano}/{mes}/{dia}/{nome_arquivo}`.
    - Sanitização de nomes de arquivos para compatibilidade com SO.
    - De-duplicação mantida via Hash (logada, mas arquivo salvo na estrutura de data).
- **Auditoria de Desenvolvimento (DevMode)**:
    - Se `DEV_AUDIT_MODE=True`, salvar arquivos intermediários em `dados/audit/{job_id}/`:
        - OCR raw (JSON).
        - Prompt enviado ao LLM.
        - Resposta bruta do LLM.
- **Logs de Execução**:

#### 3.3. Classificação
- **Entrada**: Texto extraído + Metadados.
- **Mecanismo**: LLM (OpenAI) comparando contra lista de "Contratos" ativos.
- **Saída**: Tipo de Documento (`doc_type`), Grau de Confiança (`confidence`) e Evidências (`signals`).
- **Guardrail**: Se `confidence` < limiar configurado, marca como `REVIEW_PENDING`.

#### 3.4. Gestão de Contratos (Contracts)
Sistema dinâmico onde usuários (Admin) podem cadastrar novos tipos de documentos.
Cada contrato define:
- **Schema JSON**: Campos a serem extraídos.
- **Regras de Validação**: Ex: CNPJ obrigatório, Soma de itens deve bater com total.
- **Prompt Template**: Instruções específicas para o LLM.

#### 3.5. Extração (Extract)
- Executa a extração dos campos definidos no contrato selecionado.
- Utiliza **Plugins** (scripts Python especializados) ou **LLM** genérico instruído pelo contrato.
- Gera JSON estruturado.

#### 3.6. Validação e Normalização
- Aplica máscaras (CPF/CNPJ), converte datas para ISO, normaliza valores monetários.
- Executa regras de negócio (cross-check de valores).
- Se houver erro de validação (ex: CNPJ inválido), o Job vai para revisão.

#### 3.7. Revisão Human-in-the-Loop
- Interface no Streamlit focada em operadores.
- Lista jobs com status `REVIEW_PENDING` ou `FAILED`.
- Permite visualizar o PDF original lado a lado com o formulário de dados extraídos.
- Ações: Corrigir dados e Aprovar, ou Rejeitar (marcar como não suportado).

### 4. Requisitos Não-Funcionais
- **Configuração via .env**: Segredos (API Keys) nunca hardcoded.
- **Logging Auditável**: Uso de `loguru` para rastrear cada passo do Job.
- **Observabilidade**: Painel de auditoria mostrando taxas de sucesso, erros comuns e volumetria.
- **Segurança**: Separação de configurações operacionais (editáveis no front) de segredos de infraestrutura. Autenticação de usuários.

### 5. Saídas (Outputs)
- Manutenção da estrutura de pastas atual (`AAAA/MM/DD`).
- Geração de Excel consolidado (Diário ou por Período).
- Arquivos JSON individuais por documento para integração.
