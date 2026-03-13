# Documentação do Pipeline — Coleta e Extração de Notas Fiscais

Este documento detalha o funcionamento passo a passo da aplicação, desde a captura de e-mails até a geração dos relatórios finais. A rotina foi projetada para ser modular, robusta e auditável.

---

## 1. Visão Geral da Arquitetura

O projeto segue uma estrutura modular em Python, organizada da seguinte forma:

- **`app/core/`**: Configurações globais, conexão com `.env`, modelos de dados e logs centralizados.
- **`app/email_client/`**: Gerenciamento da conexão IMAP e busca de e-mails.
- **`app/ingest/`**: Validação de arquivos, OCR (quando necessário) e classificação do tipo de nota fiscal.
- **`app/extract/`**: Motores de extração de dados (Regex e padrões textuais).
- **`app/outputs/`**: Geração de arquivos Excel e JSON, além da organização de pastas diárias.

---

## 2. Passo a Passo do Pipeline

A execução segue um fluxo linear de 6 etapas principais:

### 📥 Passo 1: Conexão e Busca (IMAP)
O sistema conecta-se ao servidor de e-mail (ex: Outlook/Office365) utilizando as credenciais configuradas.
- **Filtro**: Busca e-mails que contenham palavras-chave no assunto ou corpo (ex: "NFe", "DANFE", "NFSe").
- **Segurança**: As senhas são recuperadas via **Keyring** ou variáveis de ambiente para evitar exposição.

### 📁 Passo 2: Staging (Download e Metadados)
Os anexos PDF dos e-mails identificados são baixados para uma área temporária.
- **Rastreabilidade**: Para cada e-mail, é gerado um registro de "Origem" contendo o remetente, assunto, data do e-mail e identificador único (`Message-ID`).

### 🔍 Passo 3: Validação e OCR
Antes da extração, cada arquivo PDF passa por uma triagem:
- **`PDFCheck`**: Verifica se o arquivo é válido e se possui texto pesquisável.
- **OCR Condicional**: Se o PDF for uma imagem (escaneado), o sistema utiliza a biblioteca `ocrmypdf` para aplicar OCR e torná-lo legível.

### 🏷️ Passo 4: Classificação
O sistema analisa o conteúdo textual para identificar o tipo de nota fiscal:
- **NFe/CT-e**: Identificado pela Chave de Acesso de 44 dígitos.
- **NFSe**: Identificado por termos como "RPS", "Prestador" e "Tomador".

### 📊 Passo 5: Extração de Dados
Nesta etapa, os extratores específicos entram em ação:
- **Cabeçalho**: Extrai Chave, Número, Data de Emissão, CNPJs (Emitente/Destinatário) e Valores Totais.
- **Itens**: Captura a lista de produtos ou serviços contidos na nota.
- **Extra Fields**: Qualquer campo adicional não mapeado é capturado como `EXTRA_` para garantir 100% de cobertura.

### 💾 Passo 6: Persistência e Organização
Os dados extraídos são salvos e os arquivos organizados:
- **Estrutura de Pastas**: Os arquivos são movidos para uma pasta baseada na **data do e-mail** (`AAAA/MM/DD`).
- **Excel Diário**: Uma planilha com 4 abas (**CABECALHO**, **ITENS**, **ERROS**, **ORIGEM**) é atualizada automaticamente.
- **JSON**: Um arquivo JSON por nota é gerado para integrações futuras.

---

## 3. Monitoramento e Logs (Auditabilidade)

Conforme os requisitos de segurança e confiabilidade:
- **Loguru**: Todos os passos são registrados em arquivos de log diários na pasta `dados/logs/`.
- **Níveis de Log**: Informações de erro incluem detalhes técnicos e ações sugeridas para correção.
- **Interface Streamlit**: O usuário pode acompanhar a execução manual e visualizar os logs em tempo real através do painel.

---

## 4. Tecnologias Utilizadas

| Componente | Tecnologia |
| :--- | :--- |
| **Linguagem** | Python 3.11+ |
| **Interface** | Streamlit |
| **OCR** | OCRmyPDF + Tesseract |
| **Extração** | Regex + PDFMiner |
| **Logs** | Loguru |
| **Segurança** | Keyring + Azure OAuth2 (Opcional) |
