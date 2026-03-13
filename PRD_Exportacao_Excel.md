# PRD - Melhorias na Exportação Excel e Preview de Dados

## 1. Avaliação Técnica do Cenário Atual

Após analisar o código do backend (`app/api/v1/endpoints/reports.py`) e do frontend (`frontend/src/pages/Dashboard.tsx`), identificamos as causas raízes dos problemas relatados:

### A. Erro de Corrupção no Excel ("O Excel não pôde abrir o arquivo...")
**Causa:** O erro `Registros Removidos: Fórmula de parte de /xl/worksheets/sheet1.xml` ocorre porque o `pandas.to_excel` está gravando strings que começam com caracteres especiais (`=`, `+`, `-`, `@`). O Excel tenta interpretá-los como o início de uma fórmula, mas, como não são, o conteúdo XML do arquivo corrompe.
**Solução:** Implementar uma sanitização (limpeza de caracteres iniciais) antes da gravação do arquivo Excel.

### B. Falta de Filtros na Exportação
**Causa:** No frontend, o botão "Exportar Relatório" não passa todos os filtros aplicados na tela (`doc_type`, `start_date`, `end_date`, `searchTerm`, `criticalityFilter`, `filenameFilter`). Ele envia apenas o `status_filter`.
**Solução:** Ajustar a função de exportação do frontend para coletar todos os filtros ativos e passá-los para a API do backend de forma correta.

### C. Abas Ausentes e Dados Misturados ("Formatação Crua")
**Causa:** Atualmente, a rota de exportação achata (flatten) todos os JSONs de extração em uma única aba (`Extrações`) e a salva sem formatação. Como resultado:
- Faltam as abas individuais para cada contrato (NFs, faturas, cancelamentos, etc.).
- Falta a aba inicial de "Dados Gerais".
- O Excel gerado é "cru" (sem cabeçalhos travados, tamanhos de coluna dimensionados, negrito, etc.).
**Solução:** Utilizar `openpyxl` ou `xlsxwriter` em conjunto com o Pandas para desenhar várias abas (`Sheets`): 1 aba "Dados Gerais" contendo todas as linhas gerais extraídas (ID, Remetente, Assunto, Anexo, etc.) e 1 aba para cada `Tipo de Contrato` detectado, contendo aquele ID correspondente e os campos das extrações. Aplicar estilos e redimensionamento automático de colunas.

### D. Banco de Dados Ideal vs Atual
**Análise DuckDB vs SQLite:** O banco de dados atual do projeto, `app_v2.db` (SQLite), é robusto e possui suporte nativo à leitura/extração dos campos JSON via SQLAlchemy. Não é necessário implementar o DuckDB (que adicionaria complexidade arquitetural desnecessária para relatórios tabulares de pequeno a médio porte). A solução via SQLite + API para a separação da interface em tabelas será mais rápida de ser posta em prática, performática o suficiente e mantém a simplicidade.
**Recomendação:** Utilizar o próprio ecossistema do FastAPI + SQLite já implantado no projeto.

---

## 2. Requisitos da Solução

### 2.1. Tela Nova/Melhorada: Preview da Exportação ("Relatórios")
De acordo com o relato do usuário: *"ao entrar na tela de apresentação dos dados de contratos, precisamos mostrar uma aba/tela de dados gerais, e outras com os dados extraidos..."*.
Dessa forma:
1. Deve ser criada uma interface de "Preview de Exportação" ou "Relatórios Tabulares" onde o usuário veja:
   - Uma **área superior** de filtros.
   - Uma **região central com Abas (Tabs)** espelhando as abas do Excel: "Dados Gerais", "Contrato A", "Contrato B", etc.
2. Cada Aba funcionará como um Data Grid, apresentando as colunas específicas de sua finalidade com a possibilidade de varrer as informações antes do download final.
3. Botão "Exportar Relatório" garantindo que os filtros exibidos ali correspondam ao arquivo final.

### 2.2. Componentes de Software a Alterar
- Frontend:
  - Adicionar ou migrar a estrutura de relatórios com Tabs.
  - Ajustar chamadas de API (`api.ts`).
- Backend:
  - Modificar `/api/v1/endpoints/reports.py`.
  - Implementar lógica multiplas planilhas (multi-sheet) no Excel via `pd.ExcelWriter`.
  - Sanitizar dados para exportação.
