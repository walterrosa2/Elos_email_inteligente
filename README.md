# Coletor de Notas Fiscais via E-mail (OCR + Extração)

Este projeto automatiza o monitoramento de uma caixa de e-mail, baixa anexos PDF (NFe, NFSe, CTe), aplica OCR se necessário, extrai dados e tabula em Excel.

## Estrutura
- **app/core**: Configurações e Modelos de Dados.
- **app/email_client**: Conexão IMAP.
- **app/ingest**: Download, checagem de PDF e OCR.
- **app/extract**: Extração de dados (Regex).
- **app/outputs**: Geração de Excel e JSON.
- **app/ui**: Interface Web (Streamlit).

## Pré-requisitos
1. Python 3.11+
2. Tesseract OCR instalado (e adicionado ao PATH).
3. `ocrmypdf` instalado (via pip e dependências de sistema).

## Instalação
```bash
pip install -r requirements.txt
```

## Configuração
Crie um arquivo `.env` na raiz com as seguintes variáveis (exemplo):
```env
EMAIL_HOST=imap.gmail.com
EMAIL_USER=seu_email@dominio.com
EMAIL_PASSWORD=sua_senha_app # Opcional se usar Keyring
EMAIL_FOLDER=INBOX
OCR_LANG=por+eng
```

## Como Rodar
### Interface Visual
```bash
streamlit run streamlit_app.py
```

### Linha de Comando (Exemplo customizado)
```python
from app.main import Pipeline
Pipeline().run(days_back=1)
```

## Logs e Dados
Os arquivos são salvos na pasta `./dados/AAAA/MM/DD/`.
Logs ficam em `./dados/logs/`.
