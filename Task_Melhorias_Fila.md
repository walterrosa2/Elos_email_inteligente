# Task: Melhorias na Fila e Ingestão

Checlist de atividades para a revisão da tela de agendamento e lógica de processamento.

## Concluído
- [x] **Backend**: Alterar endpoint `/process` para aceitar `start_date` e `end_date`.
- [x] **Backend**: Atualizar `PipelineOrchestrator.run_pipeline` para aplicar filtros de data.
- [x] **Backend**: Aumentar limite de processamento de 10 para 50 jobs por ciclo.
- [x] **Backend**: Adicionar índice em `received_at` no modelo de Job.
- [x] **Backend**: Refinar mapeamento de `simplified_status` (Concluído, Erro, Não mapeado).
- [x] **Frontend**: Adicionar modal de seleção de período ao botão "Processar Fila" na página `Schedule.tsx`.
- [x] **Frontend**: Ajustar textos e labels para clareza operacional ("Busca" vs "Processamento").

## Próximos Passos
- [ ] Validar o processamento de grandes lotes (acima de 50 e-mails) para garantir estabilidade.
- [ ] Monitorar tempo de resposta do OCR/LLM com o novo limite.
