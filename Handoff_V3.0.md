# Handoff Package - ELOS V3.0 (Agrupamento e Direcionamento Financeiro)

Este pacote de entrega resume as modificações efetuadas e orientações para testes e colocação em produção.

---

## 📋 Resumo das Mudanças
Implementamos as duas grandes melhorias aprovadas:
1.  **Agrupamento e Consolidação de E-mails**:
    - O frontend agora consome o novo endpoint agrupado `/api/v1/jobs/grouped`, exibindo cada e-mail apenas uma vez.
    - Se houver múltiplos anexos para o mesmo e-mail, um seletor visual na direita permite alternar de forma transparente entre eles.
    - A ingestão descarta de forma inteligente assinaturas e imagens inline menores que 15 KB.
2.  **Roteamento Financeiro Automatizado**:
    - Novo serviço `RoutingService` que lê parâmetros de faixas de datas cadastrados nas Configurações.
    - Roteia os arquivos copiando-os fisicamente para a pasta `{SERVIDOR}/{ANO}-{MES}/Dia_{PAGAMENTO_CALCULADO}/`.
    - Lógica integrada de precedência de Boleto sobre a Nota Fiscal no mesmo e-mail.
    - Nova tela de gerenciamento de direcionamento (`/routing`) com resumos e direcionamento manual ou em lote.

---

## 🛠️ Como Executar e Validar

### 1. Testes Automatizados (Backend)
Na raiz do projeto, execute o script de testes:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\python.exe test_routing.py
```
*Deve finalizar indicando que todos os testes unitários passaram.*

### 2. Rodar a Aplicação
Inicie a aplicação localmente:
```powershell
./_start.ps1
```
Acesse o navegador na porta do frontend (geralmente `http://localhost:5173`) e teste:
- A tela **Análise e Extração** (agrupada com sub-seletores).
- A tela **Configurações Base** (onde as faixas e o diretório de destino do servidor podem ser editados).
- A tela **Direcionamento** (onde você pode listar jobs pendentes/enviados e direcioná-los manualmente ou em lote).

---

## ⚠️ Riscos e Mitigações
1.  **Caminho do Servidor Inexistente**: Caso o caminho do servidor configurado não seja acessível pela máquina do usuário, o envio falhará.
    - *Mitigação*: O sistema captura a exceção, loga no Loguru, marca o status do job como `FAILED` no direcionamento e exibe o erro visualmente na tela de controle de direcionamento para que o usuário saiba que houve problema de rede ou permissão.
2.  **Datas de Documentos Inválidas**: Se a IA não conseguir extrair datas válidas e não houver data customizada, o direcionamento não poderá ser realizado.
    - *Mitigação*: O usuário pode informar uma data customizada diretamente pelo botão "Data Custom" antes de acionar o envio manual.

---

## 🚀 Próximos Passos
- Validar o direcionamento em ambiente de testes conectando a uma pasta de rede real.
- Analisar logs na pasta `dados/logs/` para observar o descarte inteligente de imagens de assinaturas no dia a dia.
- Prosseguir com a integração final no pipeline automatizado.
