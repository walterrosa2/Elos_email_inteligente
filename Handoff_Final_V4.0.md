# Handoff Package — Roteamento Inteligente & Períodos Customizados (V4.0)

Este documento resume as modificações efetuadas na aplicação **Elos Inteligente**, valida os testes e build executados e detalha como rodar e implantar a aplicação, incluindo o esclarecimento sobre volumes no Docker.

---

## 1. Resumo das Alterações Efetuadas

### Backend (Python/FastAPI)
- **Banco de Dados**: Novas colunas de vencimento inseridas na tabela `Job` e `EmailContext` via migrações automáticas seguras em `app/db/database.py`.
- **Roteamento Inteligente (V4.0)**:
  - Implementada lógica de eleição da maior data de vencimento (Anexos vs Corpo do E-mail) no `RoutingService` em `app/routing/service.py`.
  - Fallback automático para a data de recebimento do e-mail quando nenhum vencimento for detectado.
  - Salvamento de metadados da eleição (Origem e Contexto explicativo) no banco de dados para auditoria.
  - Implementada a pasta de quarentena `"Sem Vencimento"` no staging. Jobs sem vencimento detectado têm seus arquivos físicos movidos para essa pasta.
  - Adicionada compatibilidade de fallback em `RoutingService` para ler chaves tradicionais do `extraction_result` (regras baseadas no `doc_type`) se a nova extração direta `original_due_date` estiver vazia (legado/mocks de testes).
- **Destinos Customizados por Período**:
  - Parâmetro `destination_folder` incluído nas configurações dos períodos em `DEFAULT_SETTINGS`.
  - A pasta final respeita o caminho digitado pelo usuário, utilizando a pasta temporal `{ano-mes}/Dia_{payment_day}` apenas em caso de campo nulo ou vazio.

### Frontend (React/TypeScript)
- **Painel de Configurações**: Adicionado o campo de texto "Pasta Destino" para os 3 períodos sob o card de Roteamento de Pagamentos.
- **Tela de Direcionamento (Routing.tsx)**:
  - Reformulada com **Split View**:
    - Esquerda: Visualizador dinâmico de anexos (PDFs/Imagens) via Blob URL autenticado com JWT.
    - Direita (Gaveta de 45%): Desenvolvida com cabeçalho e rodapé fixos. A área central contendo a auditoria do vencimento, o anexo e o corpo do e-mail é rolável de forma independente. O card do corpo do e-mail tem altura confortável travada em `h-96` para rolagem de textos extensos. Os botões de ação ("Aprovar e Rotear" e "Data Manual") ficam fixados de forma estática no rodapé da gaveta, eliminando sobreposições.
  - Filtros rápidos por Vencimento ("Com Vencimento" vs "Sem Vencimento").
  - Múltipla seleção com checkbox para aprovação de direcionamentos em lote.

---

## 2. Dúvida do Cliente: Implantação Docker e Pastas Fora do Container

### Como funciona a montagem do volume no Docker?
Sim, o destino dos arquivos direcionados pode ser qualquer pasta na máquina do cliente (Host), fora do container Docker.

Para isso, usamos a montagem de volumes na inicialização do Docker. Você aponta uma pasta raiz genérica da máquina física para a pasta de pagamentos dentro do container.

### Exemplo prático no `docker-compose.yml`:
```yaml
version: "3.8"
services:
  elos-app:
    image: elos-email-inteligente:latest
    ports:
      - "8000:8000"
    volumes:
      - "C:/Elos_Pagamentos:/app/dados/servidor_pagamentos"
      - "C:/Elos_Staging:/app/dados/staging"
    environment:
      - DATABASE_URL=sqlite:///app/dados/elos.db
```

### O usuário final precisa ajustar as pastas mensalmente. Isso exige reiniciar o Docker?
**Não.** O volume mapeia a pasta raiz (ex: `C:/Elos_Pagamentos` mapeada para `/app/dados/servidor_pagamentos`). 
Quando o usuário acessa as configurações no navegador e digita uma nova pasta (ex: `2026-07/Lote_Primeira_Quinzena`), a aplicação dentro do container criará a pasta `/app/dados/servidor_pagamentos/2026-07/Lote_Primeira_Quinzena` e copiará os arquivos lá.

Como essa pasta está dentro do volume mapeado, ela aparecerá instantaneamente no Windows Server / máquina do cliente em:
`C:\Elos_Pagamentos\2026-07\Lote_Primeira_Quinzena\`

**Conclusão**: A montagem do volume é realizada apenas uma vez na instalação. Os ajustes mensais de pastas feitos pelo usuário nas configurações do sistema funcionam dinamicamente e sem interrupções!

---

## 3. Evidências de Qualidade e Homologação

### 3.1. Testes de Backend (Aprovados)
Todos os testes foram executados com sucesso utilizando o interpretador do ambiente virtual:
```powershell
.venv\Scripts\python test_routing.py
```
**Resultado da Execução**:
```text
--- Testando Parse de Datas ---
OK: Todos os formatos de data parseados corretamente.

--- Testando Calculo de Roteamento ---
OK: NF de emissao 2026-06-06 direcionada corretamente para a pasta: 2026-06/Dia_01
OK: Com prioridade ativa, NF herdou vencimento do Boleto (2026-06-18) e foi para: 2026-06/Dia_10

--- Testando Caminho Customizado (destination_folder) ---
OK: Direcionamento respeitou a pasta customizada do período 2: Junho_2026/Customizado_Lote_2

--- Testando Eleição de Maior Vencimento (V4.0) ---
OK: Maior vencimento (30/06) eleito com sucesso.
OK: Fallback para data de recebimento do e-mail verificado com sucesso.

--- Testando Quarentena Sem Vencimento (V4.0) ---
OK: Arquivo movido com sucesso para a quarentena em: dados/servidor_pagamentos/test_quarentena_staging/Sem Vencimento/documento_sem_venc.pdf

--- Testando Redirecionamento Fisico (Copia) ---
OK: Arquivo copiado com sucesso para: C:\Users\walte\OneDrive\Workspace\IA\ELOS\Projeto - ELOS - Salvamento e tabulação automatica de emails\P1_salva_email\dados\servidor_pagamentos\2026-06\Dia_10\NF_123.pdf

[SUCESSO] TODOS OS TESTES PASSARAM COM SUCESSO!
```

### 3.2. Compilação do Frontend (Aprovada)
O build estático e a análise do compilador TypeScript completaram sem nenhum aviso ou erro:
```powershell
cd frontend
npm run build
```
**Resultado do Build**:
```text
vite v7.3.1 building client environment for production...
transforming...
✓ 1868 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.46 kB │ gzip:   0.29 kB
dist/assets/index-JFQuciM_.css   41.63 kB │ gzip:   7.96 kB
dist/assets/index-mjucO8Rd.js   437.18 kB │ gzip: 133.50 kB
✓ built in 5.82s
```

---

## 4. Instruções de Execução Local

### Iniciando a aplicação (PowerShell no Windows):
```powershell
.\_start.ps1
```
Esse script ativará o ambiente virtual `.venv`, carregará as variáveis do `.env`, subirá o backend FastAPI na porta 8000 e o frontend Vite no servidor de desenvolvimento.

### Acessando a aplicação:
- Abra o navegador em `http://localhost:5173`.
- Vá para a aba de **Roteamento** (ícone de pasta com check `/routing`) para validar a nova interface Split View, aprovação em lote e filtros "Com Vencimento" e "Sem Vencimento".
- Acesse as **Configurações** (ícone de engrenagem `/settings`) para ajustar e testar as pastas customizadas de cada período.
