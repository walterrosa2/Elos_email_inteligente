# PRD: Melhorias de Fluxo e Vazão - Fila de Processamento

## 1. Objetivo
Melhorar a experiência do usuário na gestão da fila de processamento, permitindo maior controle sobre o período de execução e garantindo que o backlog de e-mails seja resolvido de forma eficiente.

## 2. Requisitos Operacionais
- **Filtragem por Período**: O usuário deve poder disparar o processamento de OCR e IA apenas para e-mails recebidos em uma janela de tempo específica.
- **Aumento de Vazão**: O sistema deve processar lotes maiores (50+) em vez do limite restritivo de 10 por ciclo.
- **Simplificação de Status**: Os status exibidos devem ser intuitivos: Erro, Não mapeado, Concluído.

## 3. Limitações e Regras
- O filtro de data é opcional (se vazio, processa tudo o que for possível respeitando o limite).
- O limite de 50 é um compromisso entre performance e consumo de recursos (AWS Textract e Contexto LLM).

## 4. Dados Sensíveis
- Nenhuma mudança na persistência de dados sensíveis; continua seguindo os padrões de criptografia e armazenamento local seguro.
