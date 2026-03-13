from typing import Dict, Any
from app.contracts.manager import Contract
from app.core.logging import logger

class ValidationService:
    @staticmethod
    def validate(data: Dict[str, Any], contract: Contract) -> Dict[str, Any]:
        """
        Validates the extracted data against the contract rules.
        Returns a dict with 'is_valid' (bool) and 'errors' (list).
        """
        errors = []
        
        for field in contract.fields:
            value = data.get(field.name)
            
            # 1. Required Check
            if field.required and (value is None or value == ""):
                errors.append(f"Missing required field: {field.name}")
                continue
                
            if value is None:
                continue
                
            # 2. Type Check (Basic)
            try:
                if field.type == "float":
                    # Try converting to float to ensure consistency
                    # The LLM usually returns numbers, but sometimes strings "100.00"
                    if isinstance(value, str):
                        value = value.replace("R$", "").replace(" ", "").replace(",", ".")
                    float(value)
                elif field.type == "date":
                    # Expecting YYYY-MM-DD from LLM instructions
                    if len(str(value)) < 10:
                        errors.append(f"Invalid date format for {field.name}: {value}")
            except ValueError:
                errors.append(f"Invalid type for {field.name}. Expected {field.type}, got {value}")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Validation failed for {contract.doc_type}: {errors}")
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "validated_data": data # Return data even if invalid, for review
        }

validation_service = ValidationService()
