import os
import hashlib
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger

class LocalStorageAdapter:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def calculate_hash(self, file_content: bytes) -> str:
        """Calculates SHA256 hash of the file content."""
        return hashlib.sha256(file_content).hexdigest()

    def save_file(self, file_content: bytes, filename: str, date_subfolder: str = None) -> dict:
        """
        Saves the file to local storage.
        Preserves original filename if possible. Handles duplicates by checking hash.
        """
        file_hash = self.calculate_hash(file_content)
        
        if date_subfolder:
            # Use provided date structure: dados/storage/2026/01/20/
            sub_dir = self.base_path / date_subfolder
        else:
            # Fallback to hash prefix: dados/storage/a1/
            sub_dir = self.base_path / file_hash[:2]
            
        sub_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename (redundant check, but safer)
        ext = Path(filename).suffix
        stem = Path(filename).stem
        import re
        clean_ext = re.sub(r'[\<\>\:\"\/\\\|\?\*\x00-\x1f]', '', ext).replace('\r', '').replace('\n', '')
        clean_stem = re.sub(r'[\<\>\:\"\/\\\|\?\*\x00-\x1f]', '', stem).replace('\r', '').replace('\n', '')
        
        # Limit stem length to avoid path limits (Windows ~260 chars max path)
        if len(clean_stem) > 100:
            clean_stem = clean_stem[:100]

        final_filename = f"{clean_stem}{clean_ext}"
        file_path = sub_dir / final_filename
        
        # Collision handling
        if file_path.exists():
            # Check if it is the same file
            existing_bytes = file_path.read_bytes()
            existing_hash = self.calculate_hash(existing_bytes)
            
            if existing_hash != file_hash:
                # Same name, different content: Rename
                final_filename = f"{clean_stem}_{file_hash[:8]}{clean_ext}"
                file_path = sub_dir / final_filename
            else:
                logger.info(f"File already exists (same content): {file_path}")
        
        # Write if new path doesn't exist (or if we just defined a new unique name)
        if not file_path.exists():
             with open(file_path, "wb") as f:
                f.write(file_content)
             logger.info(f"File saved: {file_path}")

        return {
            "attachment_hash": file_hash,
            "storage_uri": str(file_path.absolute()),
            "original_name": filename,
            "size_bytes": len(file_content)
        }



    def resolve_path(self, storage_uri: str) -> Path:
        """Resolves a storage URI to a valid local Path, handling Docker/OS differences."""
        if not storage_uri:
            return None
            
        path = Path(storage_uri)
        if path.exists():
            return path
            
        # Try relative to CWD
        rel_path = Path(os.getcwd()) / storage_uri.lstrip("/\\")
        if rel_path.exists():
            return rel_path
            
        # Handle Docker paths stored in DB (e.g., /app/dados/storage/...)
        if storage_uri.startswith("/app/"):
            # Try to map /app/ to current project root
            relative_from_app = storage_uri.replace("/app/", "", 1)
            mapped_path = Path(os.getcwd()) / relative_from_app.lstrip("/\\")
            if mapped_path.exists():
                return mapped_path

        # Handle mismatch between STORAGE_PATH setting and DB path
        # If DB path contains 'dados/storage', try to find it under CWD
        if 'dados/storage' in storage_uri:
            parts = storage_uri.split('dados/storage')
            if len(parts) > 1:
                sub_path = parts[1].lstrip("/\\")
                # Try Path(os.getcwd()) / 'dados/storage' / sub_path
                final_path = Path(os.getcwd()) / 'dados' / 'storage' / sub_path
                if final_path.exists():
                    return final_path

        return path

    def get_file(self, storage_uri: str) -> bytes:
        """Reads a file from storage."""
        path = self.resolve_path(storage_uri)
        if not path or not path.exists():
            raise FileNotFoundError(f"File not found at {storage_uri} (resolved to {path})")
        return path.read_bytes()

storage = LocalStorageAdapter()

