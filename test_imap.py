import os
from dotenv import load_dotenv
from imapclient import IMAPClient

# Force load .env
load_dotenv(override=True)

HOST = os.getenv("EMAIL_HOST")
PORT = int(os.getenv("EMAIL_PORT", 993))
USER = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASSWORD")
SSL = os.getenv("EMAIL_USE_SSL", "true").lower() == "true"

HOSTS_TO_TEST = ["outlook.office365.com", "imap-mail.outlook.com"]

print("--- TESTING IMAP CONNECTION ---")
print(f"USER: {USER}")
print(f"SSL:  {SSL}")
print(f"PASS: {'*' * len(PASSWORD) if PASSWORD else 'NONE'}")

success = False

for host in HOSTS_TO_TEST:
    print(f"\n[TESTING HOST: {host}]")
    try:
        print(f"1. Connecting to {host}...")
        client = IMAPClient(host, port=PORT, ssl=SSL)
        print("   Connection established.")

        print(f"2. Logging in as {USER}...")
        client.login(USER, PASSWORD)
        print("   ✅ LOGIN SUCCESSFUL!")
        
        print("3. Listing folders...")
        folders = client.list_folders()
        print(f"   Found {len(folders)} folders.")
        
        client.logout()
        success = True
        break # Stop if one works

    except Exception as e:
        print(f"   ❌ FAILED: {e}")

if not success:
    print("\n❌ ALL CONNECTION ATTEMPTS FAILED.")
    print("DICAS:")
    print("- Se o erro for 'LOGIN failed' em ambos, a senha esta errada ou a Microsoft bloqueou Basic Auth para esta conta.")
    print("- Voce mencionou OAuth2: Para usar OAuth2 real, o codigo precisaria ser reescrito para usar Tokens, nao senha.")
    print("- A 'Senha de Aplicativo' eh a solucao paliativa. Se ela nao funciona, pode ser necessario migrar para OAuth2.")
