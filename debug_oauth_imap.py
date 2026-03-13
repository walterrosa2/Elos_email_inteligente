import os
import sys
import base64
import msal
from pathlib import Path
from msal import PublicClientApplication, ConfidentialClientApplication
from imapclient import IMAPClient
from dotenv import load_dotenv

load_dotenv(override=True)

# Azure Configurations
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID", "common") # "common" for multi-tenant/personal
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
EMAIL_USER = os.getenv("EMAIL_USER")

# Microsoft scopes for IMAP
SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]

def generate_auth_string(user, token):
    """Generates the XOAUTH2 authentication string."""
    auth_string = f"user={user}\x01auth=Bearer {token}\x01\x01"
    return base64.b64encode(auth_string.encode()).decode()

def get_token_device_code():
    """Acquires token using Device Code Flow (interactive) and persists cache."""
    print("\n--- INICIANDO DEVICE CODE FLOW ---")
    
    # Persistence setup
    cache_dir = Path("dados")
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / "token_cache.bin"
    cache = msal.SerializableTokenCache()
    
    if cache_path.exists():
        cache.deserialize(cache_path.read_text())
        print(f"Cache carregado de {cache_path}")

    def save_cache():
        if cache.has_state_changed:
            cache_path.write_text(cache.serialize())
            print(f"Cache salvo em {cache_path}")

    # App initialization with cache
    if CLIENT_SECRET:
        print("Usando Client Secret...")
        app = ConfidentialClientApplication(
            CLIENT_ID, 
            client_credential=CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            token_cache=cache
        )
    else:
        app = PublicClientApplication(
            CLIENT_ID, 
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            token_cache=cache
        )
    
    # 1. Try silent first
    # 1. Try silent first
    accounts = app.get_accounts()
    if accounts:
        print(f"Tentando auth silenciosa para {accounts[0]['username']}...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            print("Auth silenciosa bem sucedida!")
            save_cache()
            return result["access_token"]

    # 2. Interactive
    try:
        flow = app.initiate_device_flow(scopes=SCOPES)
    except AttributeError:
         # Fallback logic if needed, but for simplicity let's assume PublicClient works or we fix scopes
         app = PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}", token_cache=cache)
         flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        print(f"Erro ao iniciar flow: {flow.get('error_description')}")
        return None
    
    print(f"\n{flow['message']}")
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        save_cache()
        return result["access_token"]
    else:
        print(f"Erro ao adquirir token: {result.get('error_description')}")
        return None

def get_token_client_secret():
    """Acquires token using Client Secret (non-interactive, needs admin consent for some scopes)."""
    print("\n--- INICIANDO CLIENT SECRET FLOW ---")
    app = ConfidentialClientApplication(
        CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    
    # Note: Client Secret might not work for IMAP.AccessAsUser.All without a user context
    # Usually IMAP OAuth2 requires a user-delegated token.
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" in result:
        print("Token de App adquirido (Graph API). Note: IMAP pode requerer token de USUÁRIO.")
        return result["access_token"]
    else:
        print(f"Erro: {result.get('error_description')}")
        return None

def test_imap_connection(token):
    print("\n--- TESTANDO CONEXÃO IMAP ---")
    host = "outlook.office365.com"
    try:
        print(f"Conectando a {host}...")
        with IMAPClient(host, use_uid=True, ssl=True) as server:
            print("Conectado! Autenticando com XOAUTH2...")
            # imapclient uses oauth2 method for XOAUTH2
            server.oauth2_login(EMAIL_USER, token)
            print("✅ AUTENTICAÇÃO OAUTH2 COM SUCESSO!")
            
            folders = server.list_folders()
            print(f"Encontradas {len(folders)} pastas.")
            
    except Exception as e:
        print(f"❌ ERRO NA CONEXÃO/AUTH: {e}")

if __name__ == "__main__":
    if not CLIENT_ID:
        print("ERRO: AZURE_CLIENT_ID não configurado no .env")
        sys.exit(1)
        
    print("Configuração detectada:")
    print(f"Client ID: {CLIENT_ID}")
    print(f"User: {EMAIL_USER}")
    
    # Priorizar Device Code para debug de conta pessoal/delegada
    token = get_token_device_code()
    
    if token:
        test_imap_connection(token)
    else:
        print("\nFalha ao obter token.")
