# DevOps & Railway Patterns

## 1. Padrão de Imagens no GHCR
Ao publicar imagens no Github Container Registry (GHCR):
- NUNCA suba variáveis de ambiente, arquivos SQLite (`.db`) ou configs brutas em Repositórios Públicos para evitar exposição da chave Master do Office 365, do Banco ou Chaves Azure. Use sempre **Private Repositories**.
- **MANDATÓRIO para Repositórios Privados:** Sempre gerar um **Personal Access Token (PAT)** no Github (Settings > Developer Settings > Tokens (classic)) marcando permissões específicas de `write:packages` e `delete:packages`.
- Injetar o Token copiado lá no Repositório do Github na aba "Secrets and Variables > Actions" sob o nome obrigatório **`CR_PAT`**.
- O `.github/workflows/publish-ghcr.yml` DEVE usar: `password: ${{ secrets.CR_PAT }}` ao invés de `${{ secrets.GITHUB_TOKEN }}`, evitando assim o erro universal *`denied: permission_denied: write_package`*.
- **Atenção:** Os nomes declarados em `IMAGE_NAME` no arquivo `.yml` do Github Actions devem ser todos forçados a **letra minúscula**.

## 2. Padrão Railway e Deploy de Containers
- Evitar volumes efêmeros para armazenamento de arquivos críticos (Pdfs/Excel/XML). Em containers, prefira instanciar Bind Mounts usando caminhos dinâmicos no Windows (`-v "${PWD}/dados:/app/dados"`). 
- Toda regra de execução WebServer (como APIs e Frontend React) não deve ter portas chumbadas explicitamente para a cloud. Use leitura de portas de ambiente `os.environ.get("PORT", 8080)`.
