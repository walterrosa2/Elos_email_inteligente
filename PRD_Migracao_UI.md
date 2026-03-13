# PRD - Remodelagem UI, Acessos e DB (Projeto ELOS)

## 1. Objetivo e Escopo
**Objetivo Geral:** Remodelar a interface (frontend) e ajustar regras de negócio para tornar a aplicação mais visual, simples, corporativa e fácil de usar para o usuário final.
**Escopo:** Migração/Evolução do frontend atual, implementação de controle de acesso (RBAC), refinamento dos status de execução, automação de agendamentos, melhoria na visualização de e-mails/anexos e reestruturação da exportação de dados.

---

## 2. Estratégia de Arquitetura Proposta (Para Revisão)

Ao analisar a estrutura atual (Streamlit + SQLite + Python), apresento as seguintes sugestões para sua decisão antes de codificarmos:

### 2.1. Estratégia de Frontend
O Streamlit atual é rápido para prototipação, mas de fato possui limitações estéticas ("feio e pouco corporativo") e de layout complexo (ex: visualização de e-mails estilo Outlook).
* **Opção A (Recomendada): Migração para SPA (React/Vite + Tailwind) com FastAPI.**
  * *Por quê?* Permite controle total do design (componentes corporativos, modais, cards bonitos de e-mail, visualização lado a lado de PDF).
  * *Impacto:* Exigirá criar uma camada de API (FastAPI) em cima das funções Python existentes e reescrever a UI em React. Como o app tem poucas telas e baixo volume de CRUD, a migração é viável e trará o aspecto 100% corporativo desejado.
* **Opção B: Streamlit "Premium" (Custom CSS + Componentes React embutidos).**
  * *Por quê?* Mantém a stack 100% Python. Usando injeção avançada de CSS e bibliotecas como `streamlit-elements`, podemos melhorar muito o visual.
  * *Impacto:* Mais rápido de fazer, mas ainda pode esbarrar em algumas limitações de interatividade fina (ex: abrir anexo modal e interagir independentemente).

### 2.2. Estratégia de Controle de Acesso
A aplicação terá 2 perfis usando *Role-Based Access Control* (RBAC) simples.
* **Tabela de Usuários:** Adicionar um campo `role` (`admin` ou `elos`).
* **Perfil Admin:** Acesso irrestrito. Vê todas as abas, incluindo "Auditoria" (logs técnicos e coluna de *confiança* das IAs), "Gestão de Contratos" e "Configurações" (onde editará o prompt da OpenAI).
* **Perfil Elos:** Foco operacional. Terá acesso apenas a:
  - Painel Geral
  - Análise de Email (visualização)
  - Agendamento (Visualização e trigger manual)
  - Emissão de Relatórios (Dados dos E-mails).
  - *Não verá* status de "confiança" das IAs ou opções de configurações globais.

### 2.3. Estratégia de Banco de Dados
A aplicação atual usa SQLite (sqlalchemy).
* **Análise (SQLite vs DuckDB):**
  * O **SQLite** é perfeitamente capaz de lidar com a rotina descrita (poucos usuários, mais leituras visuais, baixo volume de inserções concorrentes).
  * O **DuckDB** brilha enormemente se estivéssemos falando de milhões de linhas ou análises OLAP ultra pesadas.
* **Recomendação:** **Manter o SQLite** como banco de dados transacional principal (para guardar setups, usuários e contratos). Para a **Tela de Exportação e Filtros de E-mails**, podemos usar **Pandas + SQLAlchemy** para gerar o arquivo `.xlsx` ultra formatado, ou, de forma híbrida, conectar o DuckDB diretamente ao arquivo SQLite (`sqlite_scanner`) apenas no momento da exportação, garantindo extrema velocidade sem precisar migrar todo o banco.

---

## 3. Requisitos das Telas Principais

### 3.1. Painel Geral
* **Objetivo:** Controle central de todas as execuções.
* **Filtros:** Status, Remetente, Assunto, Nome do Arquivo.
* **Status Simplificado:**
  1. `Concluído`: Salvo na pasta e processado conforme contrato.
  2. `Não mapeado`: Arquivo sem contrato cadastrado (`unknown`). *Nota: Se for `unknown` com confiança ALTA, exibir apenas `Não mapeado`. Se tiver confiança BAIXA, exibir também `Não mapeado`.*
  3. `Erro`: Falhas técnicas.
* **Acesso Elos/Admin:** Elos não vê o score de confiança (Admin vê em área separada).

### 3.2. Agendamento e Execuções
* **Objetivo:** Parametrizar a busca e processamento.
* **Componentes:**
  * Toggle/Botões para "Ativar Agendamento" e "Execução Manual".
  * **Agendamento:** Parâmetros de recorrência (Diário, Semanal, Quinzenal, Mensal) + Horário (XX:XX). A busca foca sempre no período de tempo "anterior" ao trigger.
  * **Manual:** Datepicker (Range de Datas) para forçar uma busca específica.

### 3.3. Análise de Email
* **Cards Visuais:** Filtrar e exibir e-mails como cards (Data, Criticidade com cor específica, Assunto).
* **Sanitização:** Forçar UTF-8 nos textos do assunto/remetente para evitar poluição visual de caracteres especiais.
* **Visualização Estilo Outlook:** Clicar num card abre o corpo estruturado.
* **Painel de Anexos:**
  * Visualizador PDF/Imagens integrado (Side-by-side ou Modal Fullscreen).
  * Abaço/Lado do anexo: exibir metadados extraídos pela IA do contrato.
* **Configuração Admin:** Na tela de configurações, prover um `textarea` onde o Admin pode editar o Prompt de IA de criticidade.

### 3.4. Dados dos Emails (Relatórios/Exportação)
* **Objetivo:** Tabela analítica com dados raw e extrações IA.
* **Exportação:** Gerar `.xlsx` formatado e visualmente limpo.

### 3.5. Telas de Gestão (Somente Admin)
* **Configurações:** Consolida Prompts, Extensões permitidas para anexos e setups do sistema.
* **Auditoria:** Logs detalhados, confiança de IA.
* **Gestão de Contratos:** Mantém fluxo atual.

---

## 4. Próximos Passos (Ação do Usuário)
Por favor, revise as perguntas abaixo para seguirmos:

1. **Frontend:** Vamos seguir com a reescrita para React (SPA) visando 100% de personalização corporativa ou estilizamos o Streamlit atual?
2. **Banco de Dados:** Posso confirmar a manutenção do SQLite usando rotinas em Pandas/DuckDB apenas nos momentos de exportação pesada?

Após sua validação, adaptarei o plano de arquitetura e iniciaremos a implementação.
