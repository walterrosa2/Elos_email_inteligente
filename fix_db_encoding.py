
import sqlite3
import os
import argparse

def fix_encoding_issues(apply_fix=False):
    db_path = "app_v2.db"
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check EmailContext
        # \ufffd is the replacement character
        cursor.execute("SELECT message_id, subject FROM email_contexts WHERE body_text LIKE '%\ufffd%' OR subject LIKE '%\ufffd%'")
        rows = cursor.fetchall()
        
        if not rows:
            print("No emails with encoding issues found.")
            return

        print(f"Found {len(rows)} emails with encoding issues (\ufffd).")
        for row in rows:
            print(f"- ID: {row[0]}")
            print(f"  Subject: {row[1]}")
            
        if apply_fix:
            print("\nApplying fix: Deleting broken EmailContext records...")
            # We only delete from email_contexts. The Job records (attachments) remain, 
            # so they won't be re-processed by Textract, but the metadata will be refreshed if re-ingested.
            # Actually, to refresh Job metadata too, we might want to update them or leave them.
            # If we delete EmailContext, the next ingestion cycle for the same emails will recreate it.
            
            msg_ids = [row[0] for row in rows]
            placeholders = ','.join(['?'] * len(msg_ids))
            
            cursor.execute(f"DELETE FROM email_contexts WHERE message_id IN ({placeholders})", msg_ids)
            conn.commit()
            print(f"Successfully deleted {cursor.rowcount} records. Please re-run ingestion to fix them.")
        else:
            print("\nDry-run: No changes made. Run with --fix to delete these records.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix encoding issues in DB by deleting broken records.")
    parser.add_argument("--fix", action="store_true", help="Apply the fix (delete records)")
    args = parser.parse_args()
    
    fix_encoding_issues(apply_fix=args.fix)
