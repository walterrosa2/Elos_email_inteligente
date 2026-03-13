# PRD V2 - Remodelagem UI (React SPA), Acessos e DB Otimizado

## 1. Objetivo e Escopo
**Objetivo Geral:** Migrar a interface da aplicação para uma Single Page Application (React/Next.js ou Vite), substituindo o Streamlit, para oferecer um visual premium, corporativo e escalável, sem comprometer a integridade da lógica de negócios existente no backend Python.
**Escopo:** 
- Migração de Frontend (Streamlit -> React SPA).
- Implementação de Backend API (FastAPI) com rigorosa validação de contratos (Pydantic).
- Controle de acesso (RBAC - Admin vs Elos).
- Simplificação de Status e automação de agendamentos.
- Manutenção do SQLite como banco transacional, otimizando exportações de log/dados no momento de download.

---

## 2. Estratégia de Arquitetura Proposta (Confirmada)

### 2.1. Frontend: React SPA (Vite/Tailwind) e Backend: FastAPI
* **Desafio de Migração (Regra de Ouro):** Como exigido pelo protocolo "Agentic Enterprise Migration", o backend (Python) será a **única fonte da verdade** para lógica de negócios. O frontend (React) será exclusivamente uma camada de apresentação burra e roteamento de estados visuais.
* **Garantia de Sincronia (Back/Front):** Será obrigatório o uso do Agent "API Contract Architect". A API FastAPI deve gerar documentação OpenAPI (Swagger), que será convertida tipograficamente (TypeScript TypeScript Interfaces) para o React. Nenhuma tela nascerá no front sem um endpoint respectivo mapeado; nenhum endpoint existirá sem estar conectado ao ciclo da tela no front.

### 2.2. Controle de Acesso (RBAC)
* Implementado com base na restrição do payload de autenticação JWT/Session gerado pelo FastAPI.
* **Perfil Admin:** Acesso irrestrito (inclusive Auditoria, setup de Prompt e Extensões).
* **Perfil Elos:** Acesso limitado a: Painel Geral, Análise de Email, Agendamento e Relatórios. Oculte colunas que gerem confusão técnica (ex: score de Confiança IA).

### 2.3. Banco de Dados (SQLite + Exportação Híbrida)
* Manter o SQLite em `app_v2.db` presencial para gerenciar setups, usuários e contratos.
* **Atenção à Performance:** Com as mudanças na interface, verificaremos obrigatoriamente (via testes) se os schemas no SQLAlchemy refletem precisamente os JSONs que o FastAPI cuspirá. Telas como "Exportação Excel" poderão fazer uso temporário de junção Pandas/SQLite para não travar a UI React.

---

## 3. Diretrizes de Faseamento (Isolamento de Contexto)

Para garantir que o agente não sofra "esquecimento" ou alucinações de contexto, a execução será dividida em **Fases Estritas**. O fim de cada fase gerará um Handoff/Review para ser injetado em um NOVO CHAT:

### Fase 1: Análise e Contrato de API (Backend Scaffold)
* Converter o `streamlit_app.py` num mapeamento de Rotas.
* Criar a camada FastAPI (`app/api/main.py`) e expor os Controllers (Auth, Ingestion, OCR, Relatórios).
* Validar todos os schemas de entrada/saída (Pydantic v2).
* Gerar Swagger.
* **Handoff:** Endpoints testáveis via Swagger sem UI.

### Fase 2: Scaffold React e Tipos Mapeados (Frontend Core)
* Inicializar React + Vite + TypeScript.
* Engolir o Swagger da Fase 1 e gerar os Hooks/Tipos (`frontend/src/types/generated.ts`).
* Configurar Tailwind CSS, Zustand/Context para Auth, e Axios/TanStack Query.
* **Handoff:** Aplicação rodando branca, apenas com Login funcionando e Sidebar montada baseada no Role do user logado.

### Fase 3: Migração das Telas (Painel Geral e Configurações)
* Implementar Painel Geral (cards, filtros, novo mapa de 3 status: "Concluído", "Não mapeado", "Erro").
* Implementar a visualização dos Contratos e Configurações (Admin).
* **Handoff:** Telas estáticas alimentadas por API Real com RBAC operacional.

### Fase 4: Migração das Telas Complexas (E-mail e Agendador)
* Implementar tela de E-mails com painel duplo (lado a lado): Lista de e-mails à esquerda e leitor PDF/Imagem + JSON Extraído à direita. (Tratar quebra de UTF8).
* Criar interface de Agendamento paramétrico e disparo manual.
* **Handoff:** Todos os módulos interativos funcionais.

### Fase 5: Relatórios, Otimização DB e QA Final
* Fazer o end-to-end do fluxo de geração de XLSX no fastapi e download como `Blob` no React.
* Auditar testes e remover views de logs cruas do front Elos.
* **Handoff:** Versão de Produção empacotável.

---

## 4. Próximos Passos Imediatos
Sugerimos congelar este PRD. A primeira tarefa de execução é aprovar o `Task.md` novo e entrarmos tecnicamente na **Fase 1**.
