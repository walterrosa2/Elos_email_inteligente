# Task List - Pipeline V2.1 & V2.2 Refinements

## Fase 1: Fundação e Estrutura (V2.1) - [x] Concluído
- [x] Definição da Estrutura de Diretórios (`app/core`, `app/db`, etc).
- [x] Configuração Centralizada (`config.py`).
- [x] Logging (`logging.py`).
- [x] Banco de Dados (`models.py`, `init_db.py`).

## Fase 2: Ingestão e Staging (V2.1) - [x] Concluído
- [x] Adaptador de Storage Local (Hash-based).
- [x] Serviço IMAP (`imap_service.py`).
- [x] Ingestão de E-mails (`ingest/service.py`).

## Fase 3: OCR e Pré-processamento (V2.1) - [x] Concluído
- [x] Wrapper Textract (`textract/service.py`).
- [x] Validação de PDF (`pdf_validator.py`).

## Fase 4: Inteligência (V2.1) - [x] Concluído
- [x] Gerenciador de Contratos (JSON Schemas).
- [x] Serviço de Classificação (OpenAI).

## Fase 5: Extração e Validação (V2.1) - [x] Concluído
- [x] Serviço de Extração (OpenAI).
- [x] Serviço de Validação.

## Fase 6: Interface e Human-in-the-Loop (V2.1) - [x] Concluído
- [x] Autenticação Simples.
- [x] Dashboard de Jobs.
- [x] Visualização Detalhada (PDF + Form).
- [x] Ações de Aprovação/Rejeição.

## Fase 7: Saídas e Observabilidade (V2.1) - [x] Concluído
- [x] Gerador de Excel.
- [x] Dashboard de Métricas.

## Fase 8: Refinamentos V2.2 (New!)
- [x] **Melhoria no Storage**
    - [x] Refatorar `LocalStorageAdapter` para salvar em `dados/{ano}/{mes}/{dia}`.
    - [x] Atualizar `ingest/service.py` para passar a data correta.
- [x] **Auditoria de Desenvolvimento**
    - [x] Criar variável `DEV_AUDIT_MODE` em `config.py`.
    - [x] Implementar `AuditLogger` para salvar arquivos em `dados/audit`.
    - [x] Integrar `AuditLogger` no `textract`, `classify` e `extract`.
- [x] **Correção de Logs**
    - [x] Garantir criação da pasta `logs/` no startup.
