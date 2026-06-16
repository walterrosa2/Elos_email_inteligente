import shutil
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import Job, EmailContext
from app.core.logging import logger
from app.core.settings_service import settings_service
from app.storage.local_adapter import storage

DEFAULT_SETTINGS = {
    "server_root_path": "dados/servidor_pagamentos",
    "periods": [
        {"start_day": 1, "end_day": 10, "payment_day": 1, "destination_folder": ""},
        {"start_day": 11, "end_day": 20, "payment_day": 10, "destination_folder": ""},
        {"start_day": 21, "end_day": 31, "payment_day": 20, "destination_folder": ""}
    ],
    "rules_by_doc_type": {
        "Boleto": "data_vencimento",
        "NFe_Produto": "emissao",
        "NFSe": "emissao",
        "NFSe_Nacional": "emissao",
        "Fatura_Comercial": "data_vencimento",
        "Duplicata": "data_vencimento"
    },
    "prioritize_boleto": True
}

class RoutingService:
    def get_routing_settings(self) -> dict:
        """Obtem as configuracoes de roteamento do banco de dados com fallback seguro."""
        return settings_service.get_setting("payment_routing_settings", DEFAULT_SETTINGS)

    def save_routing_settings(self, settings: dict):
        """Salva as configuracoes de roteamento no banco de dados."""
        settings_service.set_setting(
            "payment_routing_settings", 
            settings, 
            description="Configuracoes de Roteamento de Pagamentos (V3.0)"
        )

    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Tenta fazer o parse de uma string de data em varios formatos comuns."""
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            return date_str
        
        date_str = str(date_str).strip()
        # Formatos comuns a tentar
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y"
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return datetime(parsed.year, parsed.month, parsed.day)
            except ValueError:
                continue
                
        # Regex para tentar extrair YYYY-MM-DD
        match = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', date_str)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass
                
        # Regex para tentar extrair DD/MM/YYYY
        match_br = re.search(r'(\d{2})[-/](\d{2})[-/](\d{4})', date_str)
        if match_br:
            try:
                return datetime(int(match_br.group(3)), int(match_br.group(2)), int(match_br.group(1)))
            except ValueError:
                pass
                
        return None

    def _get_boleto_date_for_email(self, message_id: str, db: Session) -> Optional[datetime]:
        """Busca se ha algum Boleto no mesmo email e retorna sua data de vencimento."""
        if not message_id:
            return None
            
        jobs = db.query(Job).filter(Job.message_id == message_id).all()
        for j in jobs:
            doc_type = j.doc_type or ""
            if "boleto" in doc_type.lower():
                extracted = j.extraction_result or {}
                # Buscar chaves de vencimento comuns
                venc_keys = ["data_vencimento", "vencimento", "data_venc", "venc"]
                for key in venc_keys:
                    val = extracted.get(key)
                    if val:
                        parsed = self._parse_date(val)
                        if parsed:
                            logger.info(f"Encontrou data de Boleto ({parsed.strftime('%Y-%m-%d')}) no Job {j.id} para o email {message_id}")
                            return parsed
        return None

    def calculate_routing_info(self, job_id: int, db: Session) -> Optional[dict]:
        """
        Calcula as informacoes de roteamento para um Job especifico usando a lógica
        de eleição da maior data de vencimento (Boleto, NF ou Corpo) com fallback
        para recebimento.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        # 1. Coletar datas e contextos candidatos do e-mail e dos anexos
        candidates = [] # Lista de dicionarios: {"date": datetime, "source": str, "context": str}

        # 1.1 Vencimento no corpo do e-mail
        from app.db.models import EmailContext
        ctx = db.query(EmailContext).filter(EmailContext.message_id == job.message_id).first()
        if ctx and ctx.detected_due_date:
            parsed = self._parse_date(ctx.detected_due_date)
            if parsed:
                candidates.append({
                    "date": parsed,
                    "source": "Corpo do E-mail",
                    "context": ctx.due_date_context or f"Mencionado no corpo do e-mail: {ctx.detected_due_date}"
                })

        # 1.2 Vencimentos em todos os anexos do mesmo e-mail (incluindo o próprio)
        all_jobs = db.query(Job).filter(Job.message_id == job.message_id).all()
        settings = self.get_routing_settings()
        rules = settings.get("rules_by_doc_type", {})
        
        for j in all_jobs:
            due_val = j.original_due_date
            due_context = j.due_date_context
            source_label = f"Anexo ({j.attachment_name})"
            
            # Fallback para extraction_result para compatibilidade retrograda
            if not due_val and j.extraction_result and j.doc_type:
                rule_key = rules.get(j.doc_type)
                if rule_key:
                    due_val = j.extraction_result.get(rule_key)
                    if due_val:
                        due_context = f"Identificado no anexo {j.attachment_name} ({rule_key}): {due_val}"
            
            if due_val:
                parsed = self._parse_date(due_val)
                if parsed:
                    candidates.append({
                        "date": parsed,
                        "source": source_label,
                        "context": due_context or f"Identificado no anexo {j.attachment_name}: {due_val}"
                    })

        # 2. Decidir qual candidato usar (Maior Data)
        elected_date = None
        elected_source = None
        elected_context = None

        if candidates:
            # Encontrar a maior data entre as candidatas
            elected = max(candidates, key=lambda x: x["date"])
            elected_date = elected["date"]
            elected_source = elected["source"]
            elected_context = elected["context"]
        else:
            # Fallback final: Data de recebimento do e-mail
            ref_received = job.received_at or (ctx.received_at if ctx else None) or datetime.now()
            # Truncar horas
            elected_date = datetime(ref_received.year, ref_received.month, ref_received.day)
            elected_source = "Data de Recebimento do E-mail (Fallback)"
            elected_context = f"E-mail recebido em {ref_received.strftime('%d/%m/%Y %H:%M')}. Nenhum vencimento detectado."

        # Salvar/Atualizar metadados calculados no próprio Job no DB para fins de auditoria/visualização
        job.detected_due_date = elected_date.strftime("%Y-%m-%d")
        job.due_date_source = elected_source
        job.due_date_context = elected_context
        db.commit()

        # 3. Calcular dia de pagamento com base nas configurações de períodos
        settings = self.get_routing_settings()
        day = elected_date.day
        periods = settings.get("periods", [])
        payment_day = None
        destination_folder = None

        for period in periods:
            start = period.get("start_day", 1)
            end = period.get("end_day", 31)
            if start <= day <= end:
                payment_day = period.get("payment_day")
                destination_folder = period.get("destination_folder")
                break

        if payment_day is None:
            payment_day = 1 if day <= 10 else (10 if day <= 20 else 20)

        # Montar a data de pagamento final
        try:
            target_payment_date = datetime(elected_date.year, elected_date.month, payment_day)
        except ValueError:
            target_payment_date = datetime(elected_date.year, elected_date.month, 28)

        # Determinar subpasta
        if destination_folder and str(destination_folder).strip():
            subfolder = str(destination_folder).strip()
        else:
            subfolder = f"{elected_date.strftime('%Y-%m')}/Dia_{payment_day:02d}"

        return {
            "reference_date": elected_date.strftime("%Y-%m-%d"),
            "payment_day": payment_day,
            "target_payment_date": target_payment_date.strftime("%Y-%m-%d"),
            "subfolder": subfolder,
            "due_date_source": elected_source,
            "due_date_context": elected_context
        }

    def route_job(self, job_id: int, db: Session, custom_payment_date: Optional[str] = None) -> dict:
        """
        Direciona o arquivo fisico do Job para a pasta correta no servidor de pagamentos.
        Se custom_payment_date for fornecido, ignora o calculo automatico e usa essa data.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} nao encontrado.")

        if not job.storage_uri:
            raise ValueError(f"Job {job_id} nao possui arquivo associado.")

        settings = self.get_routing_settings()
        server_root = Path(settings.get("server_root_path", "dados/servidor_pagamentos"))

        # Determinar info de roteamento
        subfolder = None
        target_payment_date_str = None
        
        if custom_payment_date:
            parsed = self._parse_date(custom_payment_date)
            if parsed:
                # Se veio customizado, precisamos achar o dia de pagamento correspondente daquela data
                day = parsed.day
                periods = settings.get("periods", [])
                payment_day = None
                destination_folder = None
                for period in periods:
                    if period.get("start_day", 1) <= day <= period.get("end_day", 31):
                        payment_day = period.get("payment_day")
                        destination_folder = period.get("destination_folder")
                        break
                if payment_day is None:
                    payment_day = 1 if day <= 10 else (10 if day <= 20 else 20)
                
                # Se destination_folder for configurado e não estiver vazio, usar ele.
                if destination_folder and str(destination_folder).strip():
                    subfolder = str(destination_folder).strip()
                else:
                    subfolder = f"{parsed.strftime('%Y-%m')}/Dia_{payment_day:02d}"
                target_payment_date_str = datetime(parsed.year, parsed.month, payment_day).strftime("%Y-%m-%d")
        
        if not subfolder:
            info = self.calculate_routing_info(job.id, db)
            if not info:
                raise ValueError("Nao foi possivel extrair datas de referencia e nao ha data customizada informada.")
            subfolder = info["subfolder"]
            target_payment_date_str = info["target_payment_date"]

        # Resolver o caminho do arquivo local (staging)
        local_path = storage.resolve_path(job.storage_uri)
        if not local_path or not local_path.exists():
            raise FileNotFoundError(f"Arquivo local de staging nao localizado em {job.storage_uri}")

        # Definir a pasta destino final no servidor
        dest_dir = server_root / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_file_path = dest_dir / job.attachment_name

        # Efetuar a copia
        logger.info(f"Direcionando arquivo de {local_path} para {dest_file_path}")
        shutil.copy2(local_path, dest_file_path)

        # Atualizar metadados no DB
        job.direction_status = "ROUTED"
        job.routed_at = datetime.now()
        job.routed_path = str(dest_file_path.absolute())
        job.target_payment_date = target_payment_date_str
        db.commit()

        logger.info(f"Job {job.id} direcionado com sucesso para {dest_file_path}")
        
        return {
            "status": "success",
            "job_id": job.id,
            "routed_path": str(dest_file_path.absolute()),
            "target_payment_date": target_payment_date_str
        }

    def route_email_jobs(self, message_id: str, db: Session) -> List[dict]:
        """Roteia todos os jobs validos de um determinado email agrupado."""
        jobs = db.query(Job).filter(
            Job.message_id == message_id,
            Job.status.in_(["VALIDATED", "APPROVED", "COMPLETED", "REVIEW_PENDING", "EXPORTED"])
        ).all()
        
        results = []
        for j in jobs:
            try:
                res = self.route_job(j.id, db)
                results.append(res)
            except Exception as e:
                logger.error(f"Erro ao rotear Job {j.id} do email {message_id}: {e}")
                j.direction_status = "FAILED"
                db.commit()
                results.append({
                    "status": "failed",
                    "job_id": j.id,
                    "error": str(e)
                })
        return results

routing_service = RoutingService()
