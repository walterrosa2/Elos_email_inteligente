import json
from typing import Tuple
from app.core.config import settings
from app.core.logging import logger
from app.contracts.manager import contract_manager
from openai import OpenAI

class ClassificationService:
    def __init__(self):
         self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
         self.model = settings.OPENAI_MODEL

    def classify_document(self, text: str, job_id: int = None, filename: str = None) -> Tuple[str, float, str]:
        """
        Classifies the document text into one of the known contracts.
        Returns: (doc_type, confidence, reasoning)
        """
        candidates = contract_manager.get_candidate_contracts(text)
        [c.doc_type for c in candidates]
        
        if not candidates:
            return "unknown", 0.0, "No matching keywords found for any contract."

        # Build rich definitions for the prompt
        definitions = []
        for c in candidates:
             def_str = f"- {c.doc_type}: {c.description}"
             if c.keywords:
                 # Limit keywords to avoid token explosion if huge list
                 kws = ", ".join(c.keywords[:10])
                 def_str += f" (Keywords: {kws})"
             definitions.append(def_str)
             
        # Obter prompt base do banco ou usar o padrão
        from app.core.settings_service import settings_service
        
        default_prompt = "Analyze the following document text and classify it into one of the provided Document Types.\nIf the document does not fit any of these types closely, classify as 'unknown'.\n\nReturn a JSON object with:\n- \"doc_type\": The best matching document type (or \"unknown\").\n- \"confidence\": A float between 0.0 and 1.0 indicating certainty.\n- \"reasoning\": A brief explanation of why this type was chosen, citing specific content matches."
        
        base_prompt = settings_service.get_setting("openai_prompt_identificacao", default_prompt)

        prompt = f"""
{base_prompt}

Available Definitions:
{chr(10).join(definitions)}

Document Text (truncated):
{text[:4000]} 
        """
        # Truncating text to avoid token limits for classification phase
        
        # Audit: Save Prompt
        if job_id:
            from app.core.audit import audit
            audit.save_text(job_id, "02_classify_prompt", prompt, filename=filename)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document classifier agent. Important: Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Audit: Save Response
            if job_id:
                audit.save_text(job_id, "02_classify_response", content, filename=filename)

            result = json.loads(content)
            
            return result.get("doc_type", "unknown"), result.get("confidence", 0.0), result.get("reasoning", "")

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "error", 0.0, str(e)

classification_service = ClassificationService()
