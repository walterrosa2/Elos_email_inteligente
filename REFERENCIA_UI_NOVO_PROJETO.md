# Referência de UI e Lógica — Replicar Interface do P1_salva_email

> Documento para o desenvolvedor que vai construir uma **nova aplicação de leitura e download de e-mails** com interface e padrões idênticos aos do `P1_salva_email`.
>
> Caminho-base do projeto de referência:
> `P1_salva_email/`

---

## 1. Visão geral da arquitetura

| Camada | Tecnologia | Pasta |
|---|---|---|
| Backend API | FastAPI + Pydantic v2 | [app/](app/) |
| Frontend SPA | React 19 + Vite + TS strict | [frontend/](frontend/) |
| Estilo | Tailwind CSS v4 (`@tailwindcss/vite`) | [frontend/src/index.css](frontend/src/index.css) |
| Estado global | Zustand | [frontend/src/store/](frontend/src/store/) |
| Server cache | TanStack Query | [frontend/src/lib/api.ts](frontend/src/lib/api.ts) |
| Roteamento | react-router-dom v7 | [frontend/src/App.tsx](frontend/src/App.tsx) |
| Ícones | lucide-react | — |
| Gráficos | recharts | [frontend/src/pages/Reports.tsx](frontend/src/pages/Reports.tsx) |
| Sanitização HTML | dompurify | (preview de e-mail) |
| Empacotamento | Docker multi-stage + Compose | [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml) |

---

## 2. Arquivos do FRONTEND a estudar (ordem recomendada)

### 2.1 Bootstrap e configuração
1. [frontend/package.json](frontend/package.json) — dependências exatas (React 19, Tailwind v4, TanStack Query, Zustand, recharts, lucide-react, dompurify).
2. [frontend/vite.config.ts](frontend/vite.config.ts) — porta fixa (`5177`), plugin Tailwind v4.
3. [frontend/tsconfig.json](frontend/tsconfig.json) + [tsconfig.app.json](frontend/tsconfig.app.json) — **strict mode obrigatório**.
4. [frontend/src/main.tsx](frontend/src/main.tsx) — bootstrap React + QueryClientProvider.
5. [frontend/src/index.css](frontend/src/index.css) — design tokens (`--color-primary-*`), fundo `gray-100`.
6. [frontend/src/App.css](frontend/src/App.css) — estilos globais complementares.

### 2.2 Roteamento e guardas de autenticação
7. [frontend/src/App.tsx](frontend/src/App.tsx) — `BrowserRouter`, `AuthGuard` (token + role admin), rotas aninhadas dentro do `DashboardLayout`.

### 2.3 Camada de API e contratos
8. [frontend/src/lib/api.ts](frontend/src/lib/api.ts) — instância Axios, baseURL via `import.meta.env.VITE_API_URL`, interceptores de token e 401.
9. [frontend/src/types/generated.ts](frontend/src/types/generated.ts) — tipos gerados via `openapi-typescript` a partir de [openapi.json](openapi.json). **Nunca editar à mão.**

### 2.4 Estado global
10. [frontend/src/store/authStore.ts](frontend/src/store/authStore.ts) — Zustand com persistência de `token` e `user`.
11. [frontend/src/hooks/useAuth.ts](frontend/src/hooks/useAuth.ts) — hook de login/logout encapsulando o store.

### 2.5 Layout e navegação
12. [frontend/src/layouts/DashboardLayout.tsx](frontend/src/layouts/DashboardLayout.tsx) — shell com sidebar fixa + `<Outlet />`.
13. [frontend/src/components/Sidebar.tsx](frontend/src/components/Sidebar.tsx) — navegação, ícones lucide, item ativo, badge de role.

### 2.6 Páginas (uma a uma — copiar o padrão visual)
14. [frontend/src/pages/Login.tsx](frontend/src/pages/Login.tsx) — card centralizado, validação inline, tratamento de 401/422.
15. [frontend/src/pages/Dashboard.tsx](frontend/src/pages/Dashboard.tsx) — KPIs em cards, layout grid.
16. [frontend/src/pages/Analysis.tsx](frontend/src/pages/Analysis.tsx) — **principal referência para listagem/preview de e-mails** (tabela + drawer/modal de detalhe).
17. [frontend/src/pages/Reports.tsx](frontend/src/pages/Reports.tsx) — gráficos `recharts`, filtros de período, export.
18. [frontend/src/pages/Schedule.tsx](frontend/src/pages/Schedule.tsx) — agendamento de jobs (polling de status).
19. [frontend/src/pages/Contracts.tsx](frontend/src/pages/Contracts.tsx) — CRUD admin.
20. [frontend/src/pages/Settings.tsx](frontend/src/pages/Settings.tsx) — formulário de configuração SMTP/IMAP + credenciais.

---

## 3. Arquivos do BACKEND a estudar (espelhar o contrato)

### 3.1 Bootstrap
- [app/api/main.py](app/api/main.py) — `FastAPI()`, `CORSMiddleware` lendo origens do `.env`, montagem de `StaticFiles` para servir o build do React e **catch-all SPA** como **último** handler.
- [app/api/security.py](app/api/security.py) — JWT/OAuth2, `get_current_user`, dependência de admin.

### 3.2 Endpoints (v1)
- [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py) — `/login`, `/me`.
- [app/api/v1/endpoints/jobs.py](app/api/v1/endpoints/jobs.py) — disparo e status de jobs de leitura de e-mail.
- [app/api/v1/endpoints/pipeline.py](app/api/v1/endpoints/pipeline.py) — orquestração de download/processamento.
- [app/api/v1/endpoints/reports.py](app/api/v1/endpoints/reports.py) — agregações para o dashboard e exportações.
- [app/api/v1/endpoints/contracts.py](app/api/v1/endpoints/contracts.py) — CRUD admin.
- [app/api/v1/endpoints/settings.py](app/api/v1/endpoints/settings.py) — credenciais/SMTP/IMAP.

### 3.3 Domínio (relevante para a nova app de leitura/download)
- [app/email_client/](app/email_client/) — cliente IMAP/Microsoft Graph, OAuth, paginação, filtros.
- [app/ingest/](app/ingest/) — pipeline de ingestão de mensagens e anexos.
- [app/storage/](app/storage/) — persistência de arquivos baixados.
- [app/scheduler/](app/scheduler/) — APScheduler/cron para coletas recorrentes.
- [app/api/schemas/schemas.py](app/api/schemas/schemas.py) — **modelos Pydantic v2** (fonte de verdade do contrato).
- [app/observability/](app/observability/) — Loguru + audit JSONL (ver `python_audit_core`).

### 3.4 Operação
- [_start.ps1](_start.ps1) / [_start.bat](_start.bat) — bootstrap Windows com `uvicorn --reload`.
- [Dockerfile](Dockerfile) — multi-stage (build do frontend + runtime Python).
- [docker-compose.yml](docker-compose.yml) — serviço único + volumes.
- [openapi.json](openapi.json) — contrato fonte para regenerar `types/generated.ts`.

---

## 4. Padrões visuais que DEVEM ser replicados

- **Tema claro**: fundo `#f3f4f6` (gray-100), cards brancos com `shadow-sm rounded-lg`.
- **Primária**: azul `#3b82f6 → #1d4ed8` (`--color-primary-500/600/700`).
- **Tipografia**: sans-serif do sistema; títulos `text-2xl font-semibold text-gray-900`.
- **Layout**: shell `flex` com **sidebar fixa esquerda** (≈240px) + área de conteúdo com `p-8 max-w-7xl`.
- **Ícones**: exclusivamente `lucide-react` para consistência.
- **Feedback**: skeleton/spinner enquanto `isLoading` do TanStack Query; toasts para sucesso/erro.
- **Tabelas**: cabeçalho `bg-gray-50 text-xs uppercase tracking-wide text-gray-500`, linhas com `hover:bg-gray-50`.
- **Estados**: badges coloridas (verde=success, âmbar=pending, vermelho=error) com fundo `*-100` e texto `*-800`.

---

## 5. Convenções de código (não negociáveis)

1. **Contratos**: nada de `Dict[str, Any]` em rota FastAPI — sempre Pydantic. Ao mudar um schema, regenerar `frontend/src/types/generated.ts` no MESMO commit.
   ```bash
   # na raiz do backend
   python dump_openapi.py
   # no frontend
   npx openapi-typescript ../openapi.json -o src/types/generated.ts
   ```
2. **URLs**: nunca hardcoded no React. Usar `import.meta.env.VITE_API_URL`.
3. **CORS**: origens vindas do `.env`, nunca `*` em produção.
4. **Erros HTTP**: backend usa `HTTPException`; frontend mapeia 401→logout, 422→erro de formulário, 5xx→toast.
5. **Estado**: Zustand só para estado de UI persistente (auth, preferências). Dados do servidor → TanStack Query.
6. **Strict TypeScript**: zero `any`, zero `@ts-ignore`.
7. **Imports absolutos no backend**: garantir `__init__.py` em cada pasta de módulo; `PYTHONPATH=.` nos scripts de start.

---

## 6. Roteiro sugerido para o novo projeto

1. Copiar a estrutura de pastas do `frontend/` e do `app/` como esqueleto.
2. Manter inalterados: `package.json` (versões), `vite.config.ts`, `tsconfig*`, `index.css`, `App.tsx` (substituindo páginas), `DashboardLayout.tsx`, `Sidebar.tsx`, `lib/api.ts`, `store/authStore.ts`, `hooks/useAuth.ts`.
3. Reaproveitar como template: `Login.tsx`, `Dashboard.tsx` e principalmente `Analysis.tsx` (que tem o padrão de listar + visualizar e-mail).
4. No backend, reaproveitar `app/api/main.py`, `security.py`, `email_client/`, `ingest/`, `storage/`, `observability/`, `scheduler/` — ajustar apenas os endpoints específicos do novo domínio.
5. Regenerar `openapi.json` e `types/generated.ts` assim que os schemas estabilizarem.
6. Validar paridade visual abrindo as duas apps lado a lado em `http://localhost:5177` (P1) e a porta nova.

---

## 7. Checklist de paridade (antes de considerar "pronto")

- [ ] Sidebar idêntica (ícones, ordem, espaçamentos, estado ativo).
- [ ] Card de login centralizado com mesmas dimensões e mensagens.
- [ ] Dashboard com KPIs em grid 4 colunas (responsivo).
- [ ] Listagem de e-mails com colunas, filtros e paginação no mesmo padrão do `Analysis.tsx`.
- [ ] Preview de e-mail sanitizado com `dompurify`.
- [ ] Toasts e estados de loading consistentes.
- [ ] Build Docker multi-stage funcionando e SPA servida pelo FastAPI.
- [ ] Loguru com `audit.jsonl` ativo.
- [ ] `.env.example` completo; nenhum segredo no repo.
