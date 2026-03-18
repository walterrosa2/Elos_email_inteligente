# Handoff Package: Limpeza de Base de Dados & Setup de Deploy

## 1. O que foi feito
Atingimos as etapas descritas no workflow de **Versionamento** e o plano de ação:
- **Limpeza de Dados Transacionais:**
  - Foi criado o script `scripts/clean_transactions.py` testado com sucesso. Ele foi executado, removendo os 639 `jobs` e 364 `email_contexts` existentes no banco.
  - O diretório `dados/storage` também foi zerado de arquivos não necessários de execução anterior.
  - **Preservado:** Os usuários, 16 contratos, 109 campos e as 4 configurações da tabela `system_settings` (**incluindo token e conexões Office 365 e Agendamentos**) continuam ativas!
- **Quality Gates:** 
  - `ruff` executado, corrigimos cerca de 74 erros sintáticos primários do código.
  - Arquivo `.gitignore` configurado adequadamente, garantindo que logs e anexos futuros não atrapalhem. IMPORTANTE: o arquivo da base de dados com as configurações (`dados/app_v2.db`) está em versionamento ativamente para servir de configuração-base no deploy.
- **Preparação GHCR e GitHub:** 
  - O repositório Git foi finalmente iniciado.
  - Foi criado a pipeline em `.github/workflows/publish-ghcr.yml`. Sempre que uma Tag Semver for enviada ao GitHub, uma nova imagem Docker será gerada automaticamente.

## 2. Ações Pendentes / Bloqueadas (Atenção do Usuário)
A **Fase 3 (Build Local e Smoke Test Docker)** não pôde ser completada pois o daemon do **Docker Desktop** na sua máquina não está rodando no momento. 

> [!WARNING]
> Como o banco `dados/app_v2.db` (contendo todas as credenciais Office365 e prompts de IA) está configurado para acompanhamento de controle de versão (Git), você precisa garantir que repositório cadastrado no GitHub será estritamente **PRIVADO**.

## 3. Próximos Passos & Como Validar

### Início Submissão (Commit e Push para GitHub)
1. Crie o repositório privado no GitHub em sua conta/empresa.
2. Adicione e envie as alterações do seu Git Local usando o terminal:
```bash
git remote add origin https://github.com/[sua-org]/[seu-projeto].git
git commit -m "chore: setup de deploy via GHCR e limpeza de transacoes de devs passados"
git push -u origin master
```

### Criar a imagem Docker em Produção (GHCR)
1. Gere e envie uma tag Semver para que as Actions construam a sua Imagem.
```bash
git tag v2.2.0
git push origin v2.2.0
```
2. Após o fluxo na aba *Actions* do GitHub finalizar, a imagem ficará acessível no servidor da empresa cliente por meio de: `docker run --env-file .env -p 8501:8501 ghcr.io/[sua-org]/[seu-projeto]:v2.2.0`
