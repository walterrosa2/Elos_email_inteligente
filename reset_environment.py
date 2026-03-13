import os
import shutil

DB_FILE = "app_v2.db"
STORAGE_DIR = "dados/storage"
LOG_DIR = "logs"

def reset_env():
    print("⚠️  ATENÇÃO: ESTA AÇÃO IRÁ APAGAR TODOS OS DADOS!")
    print(f"1. Banco de dados: {DB_FILE}")
    print(f"2. Arquivos baixados: {STORAGE_DIR}")
    print(f"3. Logs: {LOG_DIR}")
    
    confirm = input("\nTem certeza que deseja continuar? (digite 'sim' para confirmar): ")
    
    if confirm.lower() != "sim":
        print("Operação cancelada.")
        return

    # Delete DB
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"✅ Banco de dados removido: {DB_FILE}")
        except Exception as e:
            print(f"❌ Erro ao remover banco: {e}")
    else:
        print(f"ℹ️ Banco de dados não encontrado: {DB_FILE}")

    # Delete Storage Content
    if os.path.exists(STORAGE_DIR):
        try:
            shutil.rmtree(STORAGE_DIR)
            os.makedirs(STORAGE_DIR) # Recreate empty
            print(f"✅ Pasta de armazenamento limpa: {STORAGE_DIR}")
        except Exception as e:
            print(f"❌ Erro ao limpar storage: {e}")
    
    # Delete Logs (Optional)
    if os.path.exists(LOG_DIR):
         try:
            # removing individual files instead of rmtree to keep folder
            for f in os.listdir(LOG_DIR):
                os.remove(os.path.join(LOG_DIR, f))
            print(f"✅ Logs limpos: {LOG_DIR}")
         except Exception as e:
            print(f"⚠️ Erro parcial ao limpar logs: {e}")

    print("\n🚀 Ambiente resetado com sucesso! Você pode iniciar novos testes.")

if __name__ == "__main__":
    reset_env()
