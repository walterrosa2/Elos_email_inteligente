# 📘 Manual do Usuário - Sistema de Coleta e Tabulação (V2.1)

Este manual descreve como utilizar o **Leitor Inteligente de E-mails**, um sistema de automação fiscal e financeira que utiliza Inteligência Artificial para extrair dados de documentos (NF-e, CT-e, NFS-e, Boletos) e gerar planilhas consolidadas.

---

## 1. Acesso ao Sistema
1.  Abra a aplicação em seu navegador (geralmente via Streamlit).
2.  Faça o login com seu usuário e senha.
3.  Confirme seu nome no menu lateral 👤 para garantir que está no perfil correto.

---

## 2. Visão Geral (Dashboard)
Ao entrar, você verá o painel de métricas:
*   **Total de Documentos**: Quantidade total processada pelo sistema.
*   **Pendentes de Revisão**: Documentos que a IA não teve 100% de certeza ou que precisam de ajuste manual.
*   **Finalizados / Exportados**: Documentos prontos para o fechamento.

### Legenda de Status
*   **🔵 Concluído**: O processamento foi finalizado com sucesso.
*   **🟡 Não mapeado**: O texto foi lido, mas o modelo do documento não foi reconhecido. Requer verificação ou criação de um novo "Contrato".
*   **🔴 Erro**: Falha técnica durante o download ou leitura (ex: arquivo corrompido).

---

## 3. Fluxo de Operação Diária

### Passo 1: Ingestão (Coleta de E-mails)
Acesse o menu **Execução Manual**:
1.  No campo **"1. Ingestão (E-mail)"**, selecione o período de datas desejado.
2.  Clique em `📥 Buscar E-mails`. O sistema irá conectar ao servidor de e-mail e baixar todos os anexos novos com segurança.

### Passo 2: Processamento (Extração via IA)
Ainda no menu **Execução Manual**:
1.  No campo **"2. Processamento (Extrator)"**, clique em `🚀 Rodar Pipeline`.
2.  O sistema realizará as seguintes etapas automaticamente:
    *   **OCR**: Converte a imagem/PDF em texto.
    *   **Classificação**: Identifica o tipo do documento.
    *   **Extração**: Captura dados como CNPJ, Valor e Chave de Acesso.

---

## 4. Revisão e Pesquisa
No **Dashboard**, você pode gerenciar os documentos processados:
*   **Filtros**: Pesquise por remetente, assunto, ID ou tipo de documento.
*   **Seleção em Massa**: Selecione várias linhas na tabela e use o botão `✅ Aprovar Selecionados` para validá-los de uma só vez.
*   **Detalhes Individuais**: Clique em uma linha e use o botão `👁️ Ver Detalhes` para conferir cada campo extraído lado a lado com o arquivo original.
*   **Arquivos**: Use os botões `📂 Abrir Arquivo` ou `📁 Abrir Pasta` para acessar rapidamente os originais salvos localmente.

---

## 5. Geração de Relatórios (Exportação)
Acesse o menu **Relatórios** para extrair os dados para o Excel:
1.  Selecione a **Data Início** e **Data Fim**.
2.  Clique em `Gerar Excel`.
3.  Após o processamento, clique em `📥 Baixar Excel (.xlsx)` para salvar o arquivo final em seu computador.

---

## 6. Configurações Adicionais
*   **Gestão de Contratos**: Utilize este menu para cadastrar novos tipos de documentos ou ajustar quais campos a IA deve extrair em cada modelo.
*   **Auditoria**: Visualize métricas de performance e saúde do sistema para entender o volume de processamento mensal.

---

## 🛠️ Suporte e Troubleshoot
*   **Documento não reconhecido?** Verifique se o remetente está correto ou se o documento é um modelo novo ainda não cadastrado nos "Contratos".
*   **Lentidão no Processamento?** Documentos muito grandes podem levar mais tempo no OCR. Aguarde a mensagem de finalização antes de iniciar um novo ciclo.
*   **Logs**: Em caso de erros persistentes, consulte a pasta `./logs/` ou informe o ID do documento ao suporte técnico.

---
*Atualizado em: 08 de Abril de 2026*
