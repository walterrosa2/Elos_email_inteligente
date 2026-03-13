# Walkthrough - Correção do Visualizador PDF (Analysis.tsx)

## Análise do Erro Relatado
O problema, visualizado através do botão "Abrir" junto a um ID (`eb6c3475...`) no lugar do documento, ocorre devido a bloqueios de segurança nativos do navegador aplicados a URLs do tipo `blob:` injetadas num `<iframe>`.

1. **Falha na Geração do Blob**: A chamada `axios.get` anterior utilizava `responseType: 'blob'`. Sob certas configurações de rede ou servidor local, isso corrompe os *magic bytes* de arquivos binários pesados como PDFs, fazendo com que o navegador não os reconheça como conteúdo renderizável.
2. **Bloqueio do IFrame (Chrome/Edge)**: Navegadores modernos frequentemente previnem a engine nativa de PDF de exibir conteúdo "inline" quando provém de uma fonte `blob:` embutida num `<iframe>` sem as diretivas exatas de header, substituindo-o por um aviso de fallback ou um prompt de download ("Abrir").

## Solução Implementada

Foi modificado o arquivo `frontend/src/pages/Analysis.tsx` (linhas ~106-123 e ~298-310).

1. **Alteração do `responseType`**:
   Substituímos `'blob'` por `'arraybuffer'`. Ao receber os bytes brutos (`arraybuffer`), construímos o `Blob` manualmente e garantimos que o navegador receba o MIME Type `application/pdf` puro, evitando qualquer corrupção de cabeçalhos por parte do Axios.

2. **Substituição de `<iframe>` por `<object>`**:
   A tag `<object>` é o padrão correto da web para invocação de plugins de visualização (como a engine PDF). Ela possui um suporte melhor com instâncias `URL.createObjectURL` e renderiza nativamente sem disparar o prompt de download interceptado na maioria dos casos.

3. **Fallback Embutido Sensato (UI/UX)**:
   Adicionamos um box de erro elegante **dentro** da tag `<object>`. Se por algum motivo adverso o motor PDF continuar não embutindo o arquivo, o utilizador verá a "Pré-visualização Nativamente Bloqueada" de forma clara e terá um botão "Baixar para Visualizar" destacado, sem aquele design estranho e indefinido.

## Como Validar / Deploy

A versão corrigida já foi incorporada e o build de produção do React via Vite (`npm run build`) foi executado na pasta `frontend/`.

Para testar localmente:
1. Feche as instâncias rodando atualmente e abra usando o script `_start.bat` ou `_start.ps1`.
2. Acesse a tela de análise.

Para **Deploy** ("facilitar a correção" em produção), execute os comandos abaixo para forçar o empacotamento:

```bash
git add frontend/src/pages/Analysis.tsx
git add frontend/dist
git commit -m "fix(ui): resolve bug de bloqueio de renderizacao de pdf em iframe substituindo por object arraybuffer"
git push origin main
```
Conforme as regras do repositório, o envio para a branch default acionará seu fluxo de deploy / GHCR caso configurado.
