import json
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
from app.core.config import settings
from app.db.models import EmailContext
import openai

class EmailAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        # Ensure OpenAI client is ready
        openai.api_key = settings.OPENAI_API_KEY

    def analyze_pending_contexts(self, start_date=None, end_date=None):
        """Finds EmailContexts without analysis and processes them."""
        # Find pending (where criticality_score is null)
        # We limit to 5 per cycle to avoid blocking too long
        query = self.db.query(EmailContext).filter(EmailContext.criticality_score is None)
        
        if start_date:
            query = query.filter(EmailContext.received_at >= start_date)
        if end_date:
            query = query.filter(EmailContext.received_at <= end_date)
            
        pending = query.limit(5).all()
        
        if not pending:
            return 0
        
        count = 0
        for ctx in pending:
            try:
                self._analyze_single_email(ctx)
                count += 1
            except Exception as e:
                logger.error(f"Failed to analyze email {ctx.message_id}: {e}")
        
        return count

    def _analyze_single_email(self, ctx: EmailContext):
        """Calls LLM to analyze tone, criticality, and summary."""
        if not ctx.body_text or len(ctx.body_text) < 10:
            # Skip empty or too short
            ctx.criticality_score = "BAIXA"
            ctx.tone = "Neutro"
            ctx.summary = "E-mail sem conteúdo relevante."
            self.db.commit()
            return

        from app.core.settings_service import settings_service
        
        default_prompt = """Você é um auditor sênior de comunicações corporativas. 
Analise o corpo do e-mail e extraia as seguintes informações em formato JSON:

1. "resumo": Uma frase curta resumindo a solicitação.
2. "tom": O tom da conversa (Ex: "Formal", "Amigável", "Agressivo", "Urgente", "Nervoso").
3. "criticidade": Nível de urgência/risco (1 a 5, onde 5 é Crítico).
4. "acao_necessaria": true/false (Se requer ação humana imediata).

Critérios de Criticidade:
- 5 (CRITICA): Ameaça de cancelamento, risco jurídico, prazos vencidos hoje, pagamentos atrasados bloqueando serviço.
- 4 (ALTA): Solicitação de prioridade explícita ("Urgente", "ASAP"), diretores envolvidos.
- 3 (MEDIA): Solicitação padrão com prazo.
- 1-2 (BAIXA): Informativos, agradecimentos, conversa de rotina."""

        system_prompt = settings_service.get_setting("openai_prompt_criticidade", default_prompt)
        
        user_msg = f"Assunto: {ctx.subject}\n\nCorpo:\n{ctx.body_text[:3000]}" # Truncate to avoid huge costs

        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            data = json.loads(result_json)
            
            # Map score number to Label (optional, or keep number)
            score_num = data.get("criticidade", 1)
            score_map = {1: "BAIXA", 2: "BAIXA", 3: "MEDIA", 4: "ALTA", 5: "CRITICA"}
            score_label = score_map.get(score_num, "MEDIA")
            
            ctx.raw_analysis_json = data
            ctx.summary = data.get("resumo", "")
            ctx.tone = data.get("tom", "Neutro")
            ctx.criticality_score = score_label
            ctx.action_required = data.get("acao_necessaria", False)
            ctx.analysis_date = datetime.now()
            
            self.db.commit()
            logger.info(f"Analyzed Email {ctx.message_id}: {score_label} - {ctx.tone}")

        except Exception as e:
            logger.error(f"LLM Analysis Error: {e}")
            raise
