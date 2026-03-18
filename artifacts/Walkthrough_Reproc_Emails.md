# Walkthrough: Reprocessar Emails Não Mapeados

## O que foi feito
Foi implementada uma funcionalidade ponta a ponta (Backend e Frontend) para permitir o reprocessamento manual (re-classificação e re-extração via IA) de e-mails cujos tipos de anexo não haviam sido previamente mapeados pela aba "Gestão de Contratos".

## Onde no código

### Backend
- **Arquivo**: `app/api/v1/endpoints/jobs.py`
  - Foi criada a rota síncrona `POST /api/v1/jobs/{job_id}/reprocess`.
  - Esta rota verifica se há texto previamente extraído (poupando chamadas ao serviço AWS Textract/OCR).
  - Executa as rotinas de `classification_service` e `extraction_service` consecutivamente, simulando o pipeline assíncrono.
  - Atualiza o registro no banco em tempo real, gerando novos valores de `doc_type`, `extraction_result`, `confidence` e `status`.

### Frontend
- **Arquivo**: `frontend/src/pages/Analysis.tsx`
  - Criada a `reprocessMutation` utilizando `api.post(...)` com o React Query.
  - Adicionado o botão "Reprocessar IA" (ícone circular) ao lado de "Salvar Validação".
  - Lógica implementada para que o botão só apareça caso o `simplified_status` seja equivalente a `"Não mapeado"`.
  - Exibição de confirm dialog e carregamento (spinner) para UX fluida e segura.
  - Invalidação local das queries para atualizar tanto a listagem lateral de jobs quanto a visão de detalhe ativo imediatamente após a operação.

## Como testar e validar
1. Certifique-se de que os backend e frontend estão em execução (utilize os scripts `_start.ps1` e similares).
2. Na interface, cadastre ou altere um Contrato na aba **Gestão de Contratos**, para incluir palavras-chaves que você sabe que existem num e-mail que caiu como "Não mapeado".
3. Navegue até a tela **Análise (Dashboard de jobs)**.
4. Filtre por "Status: Não Mapeados" ou encontre um e-mail com a tag amarela alertando que está não mapeado.
5. Selecione-o. No cabeçalho (lado direito), clique no novo botão **Reprocessar IA**.
6. Aceite o prompt de confirmação.
7. Aguarde o spinner (isso levará alguns segundos enquanto os prompts são enviados à OpenAI).
8. Observe o alert de sucesso e a tela se atualizar automaticamente, preenchendo as chaves extraídas (aba Dados Extraídos) e atualizando o status para "Concluído" (ou pendente de revisão se faltar algo).

## Riscos Considerados
- **Custo e Limites de API**: O reprocessamento consome tokens da OpenAI cada vez que o botão é apertado. O *Textract* da AWS **não** é chamado de novo, preservando em grande parte o custo principal e a latência, dado que o texto já extraído é reciclado.
- **Falha de Timeout**: Documentos gigantes podem demorar um pouco mais e gerar timeout da requisição HTTP (embora para este caso costuma resolver dentro de ~15 segundos, o FastAPI não corta). Em ambientes sem proxies pesados não haverá problema.

## Próximos Passos (Evoluções Possíveis)
1. Permitir selecionar múltiplos e-mails "Não mapeados" e aplicar a função de "Reprocessamento em Massa".
2. Criar cron-jobs opcionais para quando o usuário atualizar a Gestão de Contratos, varrer e reprocessar todos os "Não Mapeados" do último mês (em background task para não onerar o UI).
