# Walkthrough - Pipeline V2.1 Implementado

## Visão Geral
Concluímos a refatoração e evolução do sistema para a versão V2.1. O sistema agora opera com uma arquitetura modular, orientada a Jobs, com suporte total a Human-in-the-Loop.

## Módulos Implementados

### 1. Fundação (`app/core`, `app/db`)
- Configuração centralizada com Pydantic (`.env`).
- Logging estruturado (Loguru) salvando em JSON.
- Banco de dados SQLite com modelos `Job` e `User`.

### 2. Ingestão (`app/ingest`, `app/storage`)
- Conector IMAP robusto.
- Armazenamento local com hashing SHA256 (De-duplicação).
- Criação de Jobs idempotentes baseados em `Message-ID` + `Hash Anexo`.

### 3. OCR e Textract (`app/textract`)
- Wrapper para AWS Textract (Síncrono).
- Validação prévia de PDF (senha, corrupção).

### 4. Inteligência (`app/classify`, `app/extract`, `app/contracts`)
- **Contracts Manager**: Carrega schemas JSON dinamicamente.
- **Classificação**: LLM OpenAI identifica o tipo do documento e escolhe o contrato.
- **Extração**: LLM extrai dados seguindo estritamente o schema do contrato.
- **Validação**: Verifica campos obrigatórios e tipos de dados.

### 5. Interface (`app/review`, `streamlit_app.py`)
- **Login**: Autenticação simples (Admin).
- **Dashboard**: Visão geral de Jobs e filtros.
- **Detalhes**: Visualizador de PDF lado a lado com formulário de edição/aprovação.
- **Operação Manual**: Botões para disparar a ingestão e o processamento sob demanda.

### 6. Relatórios e Auditoria (`app/outputs`, `app/observability`)
- Geração de Excel consolidado.
- Gráficos de distribuição de status e volumes (Plotly).

## Como Executar

1. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Inicializar Banco de Dados**:
   ```bash
   python -m app.db.init_db
   ```

3. **Rodar a Aplicação**:
   ```bash
   streamlit run streamlit_app.py
   ```

## Próximos Passos (Sugestões)
- Migrar para Postgres em produção.
- Adicionar suporte a processamento Assíncrono no Textract (para arquivos grandes).
- Implementar triggers automáticos (Schduler) além da execução manual.
