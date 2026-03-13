import json
from typing import Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.contracts.manager import Contract
from openai import OpenAI

class ExtractionService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def extract_data(self, text: str, contract: Contract, job_id: int = None, filename: str = None) -> Dict[str, Any]:
        """
        Extracts data from the text based on the provided Contract schema.
        """
        logger.info(f"Starting extraction for contract: {contract.doc_type}")
        
        # Build schema representation for the prompt
        schema_desc = {
            field.name: f"{field.type} - {field.description}" + (" (Required)" if field.required else "")
            for field in contract.fields
        } if contract.fields else "Extract any relevant key-value pairs representing the core information of this document (parties, dates, values, numbers, specific identifiers)."
        
        # Prepare prompt
        file_label = f"Filename: {filename}\n" if filename else ""
        
        prompt = f"""
        {contract.system_prompt}
        
        {file_label}
        Extract the requested data from the document text.
        Schema or instructions:
        {json.dumps(schema_desc, indent=2, ensure_ascii=False) if contract.fields else schema_desc}
        
        Return the result as a strict JSON object (flat, key-value pairs only). Do not include markdown formatting like ```json.
        
        Document Text (truncated):
        {text[:12000]}
        """
        # Increased token limit for extraction (approx 12k chars ~ 3-4k tokens)

        # Audit: Save Prompt
        if job_id:
            from app.core.audit import audit
            audit.save_text(job_id, "03_extract_prompt", prompt, filename=filename)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extraction engine. Output strictly valid JSON matching the requested schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Audit: Save Response
            if job_id:
                audit.save_text(job_id, "03_extract_response", content, filename=filename)

            extracted_data = json.loads(content)
            
            return extracted_data

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

extraction_service = ExtractionService()
