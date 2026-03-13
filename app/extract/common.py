import re
from typing import Optional
from datetime import datetime
from loguru import logger

class TextNormalizer:
    
    @staticmethod
    def to_float(value: str) -> float:
        """
        Converts BRL currency string (e.g. 1.234,56) to float.
        """
        if not value:
            return 0.0
        
        # Remove potential currency symbol and whitespace
        clean = value.replace("R$", "").replace(" ", "").strip()
        
        try:
            # Case 1: 1.234,56 -> Remove . replace , with .
            if "," in clean and "." in clean:
                clean = clean.replace(".", "").replace(",", ".")
            # Case 2: 1234,56 -> Replace , with .
            elif "," in clean:
                clean = clean.replace(",", ".")
            # Case 3: 1234.56 -> Keep
            
            return float(clean)
        except ValueError:
            logger.debug(f"Could not convert to float: {value}")
            return 0.0

    @staticmethod
    def clean_digits(value: str) -> str:
        """Removes non-digits."""
        if not value: return ""
        return re.sub(r"\D", "", value)

    @staticmethod
    def parse_date(value: str) -> Optional[datetime]:
        """
        Tries to parse Brazil format DD/MM/YYYY.
        """
        if not value: return None
        
        clean = value.strip()
        # Find pattern DD/MM/YYYY
        match = re.search(r"(\d{2})[/.-](\d{2})[/.-](\d{4})", clean)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        return None
        
    @staticmethod
    def extract_key_field(text: str, label_pattern: str, value_pattern: str = r".+") -> Optional[str]:
        """
        Helper for Regex extraction: Look for Label followed by Value
        """
        # simplified regex construction
        # Label separator often : or whitespace
        full_pattern = rf"{label_pattern}[:\s]*({value_pattern})"
        match = re.search(full_pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None
