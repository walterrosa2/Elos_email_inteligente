# Handoff Package - Resolução de Problema de Extração de Dados

## O que foi alterado
- **`app/orchestrator/pipeline.py`**: A lógica do pipeline foi modificada para interceptar documentos que são classificados como `unknown` (ou não mapeados) e garantir extração IA dinâmica. Anteriormente, na ausência de contrato, o pipeline pulava o OCR estruturado e deixava `extraction_result` como nulo. Agora, o pipeline gera um pseudocontrato base `"GENERIC_FALLBACK"` (usando o _openai_prompt_padrao_ em configurações, se disponível).
- **`app/extract/service.py`**: O LLM agora recebe explicitamente o comando para "extrair quaisquer pares de chave-valor (party, datas, montantes, etc)" se o array de `contract.fields` estiver vazio. Isso permite uma extração aberta "schema-less".

## Onde no código
- Em `app/orchestrator/pipeline.py`: A adição de checagem do `contract` e geração do dicionário fake Pydantic para `GENERIC_FALLBACK`.
- Em `app/extract/service.py`: Condicionamento de `schema_desc` dinâmico quando a lista de campos nativa for vazia. 

## Como Validar
1. Acesse o Streamlit/React no Frontend e vá na aba "Análise" / "Extração".
2. Selecione qualquer e-mail que contenha uma nota fiscal de serviço ou documento classificado como `unknown` ou "Não Mapeado" (Ex: `Nota Fiscal ref. Contrato de Suporte (atualização)`).
3. Após disparar o processamento de fila / extração, valide se a IA obteve dados no formulário React, substituindo o recado de `Nenhum dado extraído disponível`. Os itens aparecem sob "Campos Reconhecidos", todos gerados pelo entendimento dinâmico do GPT (ex: `recipient_cnpj`, `payment_terms`, etc).

## Próximos Passos (Recomendação)
- Como muitas notas já haviam sido presas na tela por serem puladas iterativamente (`extraction_result = None`, status `"STAGED"` ou `"REVIEW_PENDING"`), recomenda-se que selecione tais faturas no UI e lance pelo botão de `Processar Fila` ou as edite com novos metadados. Devido às centenas de documentos `STAGED` no banco de teste, a leitura demorará na cronjob assíncrona até alcançar.
