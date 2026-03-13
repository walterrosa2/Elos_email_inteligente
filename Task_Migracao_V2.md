# Task List - Migração UI V2 (React SPA)

## Fase 1: Análise e Contrato de API (Backend Scaffold) - [x] Concluído
- [x] Mapear rotas do Streamlit para FastAPI.
- [x] Criar estrutura FastAPI (`app/api/main.py`).
- [x] Implementar Schemas Pydantic v2.
- [x] Expor Swagger (`/api/docs`).

## Fase 2: Scaffold React e Tipos Mapeados (Frontend Core) - [x] Concluído
- [x] Inicializar React + Vite + TypeScript.
- [x] Gerar tipos TypeScript a partir do OpenAPI (`src/types/generated.ts`).
- [x] Configurar TanStack Query + Zustand + Axios.
- [x] Implementar Fluxo de Login e AuthGuard (RBAC).

## Fase 3: Migração das Telas (Painel Geral e Configurações) - [x] Concluído
- [x] Criar endpoints de filtros complexos no `jobs.py`.
- [x] Criar endpoints de CRUD de Contratos (`contracts.py`).
- [x] Criar endpoints de Configurações de Sistema (`settings.py`).
- [x] Implementar View React: **Painel Geral** (Dashboard).
- [x] Implementar View React: **Configurações** (Prompt IA Admin).
- [x] Implementar View React: **Gestão de Contratos**.

## Fase 4: Migração das Telas Complexas (E-mail e Agendador) - [x] Concluído
- [x] Implementar layout View-Outlook (Lista + Detalhe).
- [x] Sanitizar UTF-8 no React para exibição de corpos de e-mail.
- [x] Construir leitor Side-by-side (PDF/Imagem + JSON Extraído).
- [x] Criar endpoint `/api/v1/jobs/schedule`.
- [x] Criar interface de Agendamento Diário/Semanal.

## Fase 5: Relatórios, QA e Deploy Local - [x] Concluído
- [x] Endpoint `/api/v1/reports/export` para Excel (.xlsx).
- [x] Botão de Download na UI do React.
- [x] Revisão geral SQLite vs React (integridade de dados).
- [x] Atualizar scripts de boot (`_start.bat`/`_start.ps1`) para rodar Uvicorn + Vite.
- [x] Finalizar Documentação e Handoff Final.
