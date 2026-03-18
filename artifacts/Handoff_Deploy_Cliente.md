# Handoff: Deploy no Cliente (Docker Desktop)

Como o nosso repositório no GitHub Container Registry (GHCR) é **Privado** (por questões de segurança para proteger a chave do Office 365 e banco de dados), o Docker Desktop na máquina do cliente precisa de uma permissão especial para conseguir fazer o download (`pull`) da imagem.

Aqui está o guia passo a passo definitivo sobre como instalar na máquina nova.

---

## 🔑 Passo 1: O Token de Leitura (PAT)
O Docker no cliente precisará de um "Personal Access Token" (PAT) idêntico ao que você criou, mas com permissão APENAS de **leitura** (para não correr risco de alguém apagar sua imagem sem querer).

**Você (Walter) deve fazer isso na sua conta do GitHub:**
1. Vá em [Developer Settings > Personal Access Tokens (Classic)](https://github.com/settings/tokens).
2. Clique em **Generate new token (classic)**.
3. Nome: `Deploy_Cliente_Leitura`
4. Expiração: `No expiration`
5. Marque APENAS as caixas:
   - `read:packages` (Permite baixar pacotes Docker)
   - `repo` (Necessário pois o repositório é privado)
6. Gerar e **copiar o código**. Você enviará este código para o cliente (ou usará na máquina dele).

---

## 🛠️ Passo 2: Os Arquivos Necessários
Crie uma pasta vazia na máquina do cliente (Ex: `C:\ELOS_Producao`). 
Coloque apenas **2 arquivos** e **1 pasta** dentro dela:

1. **O arquivo `.env`** (com as credenciais de produção)
2. **O arquivo `docker-compose.yml`** (Pode usar o modelo abaixo)
3. **Pasta `dados/`** (vazia, será populada pelo sistema)

**Modelo do `docker-compose.yml` para o Cliente:**
```yaml
version: '3.8'

services:
  elos_app:
    image: ghcr.io/walterrosa2/elos_email_inteligente:v2.2.3
    container_name: elos_producao
    ports:
      - "8000:8000"
    volumes:
      - ./dados:/app/dados
      - ./.env:/app/.env
    restart: unless-stopped
```

---

## 🚀 Passo 3: Comandos de Deploy no Cliente

Com o Docker Desktop aberto e rodando no cliente, abra o **PowerShell** ou Terminal dentro da pasta `C:\ELOS_Producao` e execute:

**1. Fazer Login no GitHub:**
Ao rodar este comando, ele vai pedir um "Username" (digite `walterrosa2`) e um "Password" (Cole o **Token PAT de Leitura** que você gerou no Passo 1).
```powershell
docker login ghcr.io -u walterrosa2
```

**2. Baixar a Imagem Segura:**
```powershell
docker pull ghcr.io/walterrosa2/elos_email_inteligente:v2.2.3
```

**3. Ligar o Sistema:**
```powershell
docker compose up -d
```

Pronto! A nova versão otimizada com React SPA e FastAPI estará 100% isolada e ativa no endereço `http://localhost:8000` na máquina do cliente, salvando os arquivos e PDFs dentro da pasta `dados/` exatamente onde o docker-compose estiver localizado.
