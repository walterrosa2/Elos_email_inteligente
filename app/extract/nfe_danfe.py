import re
from typing import List, Tuple
from app.core.models import Cabecalho, Item
from app.extract.common import TextNormalizer

class NFeExtractor:
    """
    Extracts data from NFe (DANFE) text content.
    """

    def extract(self, text: str, ctx_msg_id: str, ctx_dt_email) -> Tuple[Cabecalho, List[Item]]:
        """
        Main extraction method.
        Returns Tuple(Cabecalho, List[Item]).
        """
        # Normalize spaces
        text_clean = re.sub(r'\s+', ' ', text).strip()
        
        # 1. Chave de Acesso
        chave_match = re.search(r"\b(\d{44})\b", text_clean)
        chave = chave_match.group(1) if chave_match else None
        
        # 2. Basic Fields
        numero = TextNormalizer.extract_key_field(text_clean, r"N.\s*", r"\d{1,9}")
        serie = TextNormalizer.extract_key_field(text_clean, r"S.RIE", r"\d{1,3}")
        
        # Datas
        # Usually checking "Data de Emissão" or just looking for first date
        # Strategy: find all dates, take first as emission if valid? 
        # Or look relative to keyword matches?
        dt_emissao_match = re.search(r"DATA DE EMISS.O[\s:]*(\d{2}/\d{2}/\d{4})", text_clean, re.IGNORECASE)
        dt_emissao = TextNormalizer.parse_date(dt_emissao_match.group(1)) if dt_emissao_match else None

        # Values
        # Regex for values can be tricky due to similar labels.
        # "VALOR TOTAL DA NOTA"
        vlr_total_str = TextNormalizer.extract_key_field(text_clean, r"TOTAL DA NOTA", r"[\d\.,]+")
        val_total = TextNormalizer.to_float(vlr_total_str)
        
        vlr_prod_str = TextNormalizer.extract_key_field(text_clean, r"TOTAL DOS PRODUTOS", r"[\d\.,]+")
        val_prod = TextNormalizer.to_float(vlr_prod_str)

        # CNPJs
        # Find all 14-digit numbers valid?
        # Typically first one is Emitente, second Destinatario? 
        # Or look for "EMITENTE" / "DESTINATARIO"
        
        cnpjs = re.findall(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", text_clean)
        clean_cnpjs = [TextNormalizer.clean_digits(x) for x in cnpjs]
        
        emit_cnpj = clean_cnpjs[0] if len(clean_cnpjs) > 0 else None
        dest_cnpj = clean_cnpjs[1] if len(clean_cnpjs) > 1 else None

        # Create Cabecalho
        cabecalho = Cabecalho(
            dt_email=ctx_dt_email,
            msg_id=ctx_msg_id,
            tipo_nf="NFe",
            chave=chave,
            numero=numero,
            serie=serie,
            emissao=dt_emissao,
            emitente_cnpj=emit_cnpj,
            dest_cnpjcpf=dest_cnpj, # standardized field name
            valor_total=val_total,
            valor_produtos=val_prod
            # Other fields...
        )
        
        # Items extraction (Placeholder / Simple Header detection)
        # NFe items are usually in a table. Regex table parsing is hard.
        # Simple heuristic: Look for lines starting with Item Code or Index?
        # For V1, we might return empty items or try to capture "DADOS DOS PRODUTOS / SERVICOS" block
        
        items = []
        # TODO: Implement robust item extraction loop here.
        
        return cabecalho, items
