import os
import sqlite3
import shutil
import argparse
from loguru import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "dados", "app_v2.db")
STORAGE_DIR = os.path.join(BASE_DIR, "dados", "storage")

def clean_database(dry_run=False):
    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found at {DB_PATH}")
        return

    logger.info(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Count before
        cursor.execute("SELECT COUNT(*) FROM jobs")
        jobs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_contexts")
        emails_count = cursor.fetchone()[0]
        
        if dry_run:
            logger.info(f"[DRY-RUN] Se executado, apagaria {jobs_count} registros de 'jobs' e {emails_count} registros de 'email_contexts'.")
            return

        logger.info(f"Apagando {jobs_count} registros de 'jobs'...")
        cursor.execute("DELETE FROM jobs")
        
        logger.info(f"Apagando {emails_count} registros de 'email_contexts'...")
        cursor.execute("DELETE FROM email_contexts")

        conn.commit()
        logger.info("Executando VACUUM no banco de dados...")
        conn.execute("VACUUM")
        logger.success("Limpeza de transações na base de dados concluída ✅")

    except Exception as e:
        logger.error(f"Erro ao limpar banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

def clean_storage(dry_run=False):
    if not os.path.exists(STORAGE_DIR):
        logger.info(f"Diretório de storage não encontrado em {STORAGE_DIR}, ignorando.")
        return

    logger.info(f"Analisando diretório de storage: {STORAGE_DIR}")
    
    files_to_delete = []
    dirs_to_delete = []
    
    for item in os.listdir(STORAGE_DIR):
        item_path = os.path.join(STORAGE_DIR, item)
        if item == ".gitkeep":
            continue
            
        if os.path.isfile(item_path) or os.path.islink(item_path):
            files_to_delete.append(item_path)
        elif os.path.isdir(item_path):
            dirs_to_delete.append(item_path)
            
    if dry_run:
        logger.info(f"[DRY-RUN] Se executado, apagaria {len(files_to_delete)} arquivos e {len(dirs_to_delete)} pastas do storage.")
        return

    for item_path in files_to_delete:
        try:
            os.unlink(item_path)
        except Exception as e:
            logger.error(f"Falha ao apagar arquivo {item_path}: {e}")
            
    for item_path in dirs_to_delete:
        try:
            shutil.rmtree(item_path)
        except Exception as e:
            logger.error(f"Falha ao apagar diretório {item_path}: {e}")

    logger.success(f"Storage limpo ({len(files_to_delete)} arquivos, {len(dirs_to_delete)} pastas) ✅")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpa registros transacionais do banco de dados e arquivos processados.")
    parser.add_argument("--force", action="store_true", help="Executa a deleção de fato. Sem essa flag, o script rodará apenas em modo Dry Run.")
    
    args = parser.parse_args()
    
    dry_run = not args.force
    
    if dry_run:
        logger.info("Iniciando MODO DRY RUN (nenhuma alteração será salva). Use --force para executar a deleção.")
    else:
        logger.warning("Iniciando MODO DELEÇÃO.")
        
    clean_database(dry_run)
    clean_storage(dry_run)
