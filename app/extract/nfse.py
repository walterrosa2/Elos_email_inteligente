import re
from typing import List, Tuple
from app.core.models import Cabecalho, Item
from app.extract.common import TextNormalizer

class NFSeExtractor:
    """
    Generic Extractor for NFSe (Service Invoices).
    Municipalities vary wildly. This logic uses common Label-Value proximity.
    """

    def extract(self, text: str, ctx_msg_id: str, ctx_dt_email) -> Tuple[Cabecalho, List[Item]]:
        text_clean = re.sub(r'\s+', ' ', text).strip()
        
        # 1. Number
        # "Número da Nota", "Nº Nota", "Numero:"
        numero = TextNormalizer.extract_key_field(text_clean, r"(N.mero da Nota|N. NFS-e)", r"\d+")
        
        # 2. RPS
        # "RPS N.", "RPS Numero"
        rps_match = re.search(r"RPS\s*(?:N[o.]?)?\s*(\d+)", text_clean, re.IGNORECASE)
        # Store RPS in extra fields? Or map to Serie/Numero?
        # Cabecalho model has generic fields.
        
        # 3. Dates
        # "Data de Emissão", "Competência"
        dt_emissao_match = re.search(r"(?:EMISS.O|COMPET.NCIA)[\s:]*(\d{2}/\d{2}/\d{4})", text_clean, re.IGNORECASE)
        dt_emissao = TextNormalizer.parse_date(dt_emissao_match.group(1)) if dt_emissao_match else None
        
        # 4. Values -> ISS, Total
        # "Valor Liquido", "Valor do Servico"
        val_serv_str = TextNormalizer.extract_key_field(text_clean, r"(VALOR DO SERVI.O|VALOR SERVI.OS)", r"[\d\.,]+")
        val_total = TextNormalizer.to_float(val_serv_str)
        
        # 5. CNPJs
        # Prestador vs Tomador.
        # Usually Prestador comes first in header? Or labeled "Prestador"
        
        prestador_match = re.search(r"PRESTADOR.*?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", text_clean, re.IGNORECASE)
        tomador_match = re.search(r"TOMADOR.*?(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|\d{3}\.?\d{3}\.?\d{3}-?\d{2})", text_clean, re.IGNORECASE)
        
        emit_cnpj = TextNormalizer.clean_digits(prestador_match.group(1)) if prestador_match else None
        dest_doc = TextNormalizer.clean_digits(tomador_match.group(1)) if tomador_match else None
        
        # 6. Codigo Servico / Discriminacao
        # Hard to regex generically.
        
        cabecalho = Cabecalho(
            dt_email=ctx_dt_email,
            msg_id=ctx_msg_id,
            tipo_nf="NFSe",
            numero=numero,
            emissao=dt_emissao,
            emitente_cnpj=emit_cnpj,
            dest_cnpjcpf=dest_doc,
            valor_total=val_total,
            extra_campos={
                "rps": rps_match.group(1) if rps_match else None
            }
        )
        
        # NFSe usually has 1 main service item.
        # We can create 1 item with the total value.
        item = Item(
             item_n=1,
             descricao="SERVICOS PRESTADOS", # Placeholder
             vlr_total=val_total
        )
        
        return cabecalho, [item]
