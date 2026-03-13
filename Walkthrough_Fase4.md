# Walkthrough - Migração UI Phase 4 (Análise Dinâmica e Agendador)

Nesta fase, implementamos as funcionalidades mais complexas da interface, permitindo a validação humana dos dados extraídos pela IA e a configuração do agendamento de ingestão.

## O que foi feito

### 1. Backend: Endpoints de Suporte à Análise
- **Endpoint de Arquivos**: Adicionado `GET /api/v1/jobs/{job_id}/file` para servir PDFs e Imagens diretamente do storage local para a UI.
- **Edição de Extração**: Adicionado `PATCH /api/v1/jobs/{job_id}/extraction` permitindo que o usuário salve correções manuais nos campos extraídos pela IA. O status do job muda para `VALIDATED`.
- **Configuração de Agendamento**: Criados endpoints `GET/POST /api/v1/jobs/schedule/config` para persistir os parâmetros do agendador no banco de dados (`system_settings`).

### 2. Frontend: Tela de Análise e Extração (Outlook Style)
- **Layout de Painel Duplo**: Implementada uma lista de e-mails à esquerda com busca em tempo real e badges de status.
- **Visualizador Multinível**:
    - **Aba Documento**: Renderiza o PDF original em um `iframe` ou exibe a imagem do anexo.
    - **Aba Extração**: Gera dinamicamente um formulário baseado nos campos JSON retornados pela IA, permitindo edição e salvamento.
    - **Aba E-mail**: Exibe o corpo do e-mail original para contexto adicional.

### 3. Frontend: Tela de Agendamento
- **Interface Paramétrica**: Permite ativar/desativar a busca automática, definir o intervalo (15m, 1h, etc.) e selecionar os dias da semana e janelas de horário.
- **Disparo Manual**: Botão "Disparar Agora" integrado ao endpoint de ingestão para execução imediata fora do cronograma.

## Como Validar

1.  **Acesse "Análise e Extração"**:
    - Selecione um e-mail na lista à esquerda.
    - Verifique se o PDF/Imagem carrega no centro.
    - Vá na aba "Extração", altere um valor e clique em "Salvar Validação".
    - Verifique se o badge na esquerda muda ou se o status no Dashboard reflete a mudança.
2.  **Acesse "Agendamento"**:
    - Altere o intervalo ou os dias da semana.
    - Clique em "Salvar Alterações" e verifique a confirmação.
    - Teste o botão de "Disparo Manual".

## Notas Técnicas
- **Tipagem**: Todos os novos endpoints foram refletidos em `src/types/generated.ts` via `openapi-typescript`.
- **Segurança**: O endpoint de arquivos valida a existência física e o acesso via JWT.
- **Design**: Mantido o padrão `Tailwind v4` com foco em UX corporativa e clean.
