# Walkthrough: Filtros de Data e Performance na Fila

Este documento descreve as alterações realizadas para permitir o processamento seletivo por período e aumentar a vazão do pipeline.

## O que foi feito

### 1. Backend: Suporte a Período no Processamento
- Criado o modelo `ProcessRequest` no endpoint de pipeline.
- O endpoint `POST /api/v1/pipeline/process` agora aceita `start_date` e `end_date`.
- O `PipelineOrchestrator` foi atualizado para receber estas datas e aplicá-las em cada etapa do pipeline (OCR, Classificação, Extração).

### 2. Performance: Aumento do Limite por Ciclo
- O limite de jobs processados por passo (Textract, Classify, Extract) foi aumentado de **10 para 50**.
- Isso resolve a lentidão relatada onde muitos jobs ficavam "presos" em processamento por falta de vazão no orquestrador.

### 3. Banco de Dados: Otimização
- Adicionado um índice na coluna `received_at` da tabela `jobs`.
- Isso garante que as filtragens por data disparadas pelo usuário sejam rápidas, mesmo com milhares de registros.

### 4. UI: Novo Modal em Agendamento
- A página `Schedule.tsx` agora exibe um modal de confirmação ao clicar em "Processar Fila".
- O usuário pode especificar o período desejado (ex: processar apenas os e-mails de ontem).

### 5. Status: Refinamento de Lógica
- A lógica de `simplified_status` foi ajustada para categorizar melhor:
    - **Concluído**: Jobs `APPROVED` ou validados com tipo de documento conhecido.
    - **Não mapeado**: Jobs com erro de tipo de contrato desconhecido ou flag explicitamente "unknown".
    - **Erro**: Falhas técnicas (`FAILED`/`ERROR`).

## Como Validar
1.  Vá para a tela de **Agendamento Ingestão**.
2.  Clique em **Processar Fila**.
3.  Preencha uma data de início do dia anterior.
4.  Confirme e verifique nos logs (ou na tela de Análise) que os jobs desse período estão sendo processados.
5.  Observe que agora o sistema processa até 50 jobs por vez, reduzindo o backlog acumulado.
