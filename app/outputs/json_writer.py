import json
from pathlib import Path
from typing import List
from loguru import logger
from app.core.models import Cabecalho, Item

class JSONWriter:
    """
    Saves individual JSON files for each invoice.
    """
    
    def save_invoice(self, cabecalho: Cabecalho, items: List[Item], output_path: Path):
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = cabecalho.model_dump()
            data['items'] = [i.model_dump() for i in items]
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
                
            logger.debug(f"JSON saved: {output_path.name}")
            
        except Exception as e:
            logger.error(f"Error writing JSON {output_path}: {e}")
