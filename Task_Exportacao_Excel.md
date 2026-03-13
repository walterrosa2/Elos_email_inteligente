# Task - Melhorias Exportação Excel e Preview Tabular

Status: Em Planejamento

## Objetivo
Resolver corrompimento de Excel, aplicar filtros dinâmicos na exportação, formatar a saída com múltiplas abas (Dados Gerais e Contratos Específicos) e criar uma interface interativa de Preview Tabular dos dados antes da exportação.

---

## 🛠️ Checklist de Execução

### 1. Backend: Refatoração da Exportação Excel (app/api/v1/endpoints/reports.py)
Ajustar o backend para gerar arquivos limpos, sem injeção de fórmulas e separados por contrato.

- [x] **Módulo `reports.py`**: Atualizar o endpoint `/export` para receber novos QueryParameters (`searchTerm`, `filenameFilter`, `criticalityFilter`, etc.).
- [x] **Lógica de Sanitização**: Criar função `sanitize_excel_value(value)` que verifique se a string começa com `=`, `+`, `-`, ou `@` e adicione um prefixo limpo (ex: um espaço ou apóstrofo) para impedir que o Excel a interprete como fórmula.
- [x] **Separação de Dados (Multi-Sheet)**: 
  - Mapear a base de dados (`Job`) da query filtrada.
  - Criar um DataFrame contendo apenas "Dados Gerais".
  - Fazer iteração sobre os diferentes `doc_type` retornados na busca. Para cada um, criar um DataFrame específico contendo os campos extraídos daquele tipo. (Utilize o `job.id` em comum para referência de índice).
- [x] **Formatação OpenPyXL**: Utilizar `pd.ExcelWriter(engine='openpyxl')` para:
  - Salvar as N abas criadas (Mínimo: "Dados Gerais"; Máximo: Todas as encontradas).
  - Congelar a painel superior (linha 1 de cabeçalho).
  - Aplicar `Font(bold=True)` e formatação básica para destacar as colunas ativas na linha 1.
  - Ajustar visualmente e dinamicamente a largura das colunas (auto-fit).

### 2. Frontend: Rota Analítica de Preview (Preview de Dados)
Criar ou adaptar uma tela/view capaz de mostrar as tabelas antes da tomada de decisão.

- [x] **Novo Componente Tabular (Ex: ExportPreview.tsx)**: Em vez de misturar com o *Dashboard* existente, criar aba ou sub-página chamada "Relatórios".
- [x] **Layout com Tabs**: Ao lado de "Visão Geral", implantar a nova tela com as Tabs:
  - Tab Padrão: `<Dados Gerais>`
  - Gerar Tabs Extras (ex: `<Contrato X>`) iterando os tipos baseados no dataset filtrado ou na base do sistema.
- [x] **Integração do Endpoint List**: Fazer o fetch do endpoint `/api/v1/jobs` passando os filtros aplicados.
  - Montar tabelas dinâmicas de acordo com a aba selecionada (mapeando a interface e quebrando as chaves do `extraction_result` do JSON nas colunas).
- [x] **Integração com Exportação Excel**: Refatorar o botão `handleExport` que deve disparar o *Get* em `/api/v1/reports/export` com *todos* os filtros preenchidos pelo usuário (Datas, Status, Tipo, Criticidade, Busca, etc).

### 3. Garantias Finais (Quality)
- [x] **Smoke Test Excel**: Gerar um Excel local executando um fluxo e verificar se abre corretamente sem o modal de corrupção. As abas estão criadas precisamente como planejadas.
- [x] **Validação dos Filtros**: Verificar se a filtragem de Data (Start > End) na request garante o respeito de timezones locais, assegurando que nenhum documento do próprio dia escape do filtro.
- [x] Atualizar o PRD.md e Task.md marcando o que foi feito.

---

## Orientações Técnicas Extras (Guia do Desenvolvedor)

1. **Evitar Bibliotecas Pesadas de Grid no Front se Desnecessário**: Use uma solução tabular nativa baseada na atual tabela do `Dashboard.tsx` para listar as Extrações, a fim de não aumentar o bundle.
2. **Lidando com JSON Flatten**: Como os JSONs das faturas variam muito, aplique a técnica de *flatten* segura no Frontend para mostrar na tela:
   ```javascript
   // Pseudocódigo (redução para exibição em tabela)
   const extraKeys = Array.from(new Set(jobs.flatMap(j => Object.keys(j.extraction_result || {}))));
   // Renderizar as colunas usando o array extraKeys
   ```
3. **Download Nativo Blob**: Ao testar o download refeito no frontend, confirme o cabeçalho `content-disposition` devolvido na Response para capturar corretamente o "filename" proposto.
