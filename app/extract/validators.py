from typing import List
from app.core.models import Cabecalho, Item, Erro

class Validator:
    """
    Business logic validation.
    """
    
    @staticmethod
    def validate_nf(cab: Cabecalho, items: List[Item]) -> List[Erro]:
        errors = []
        
        # 1. Critical fields presence
        if not cab.emitente_cnpj and not cab.emitente_razao:
            errors.append(Erro(
                dt_email=cab.dt_email,
                msg_id=cab.msg_id,
                arquivo="N/A", # Needs context
                motivo="Emitente não identificado",
                acao_sugerida="Verificar OCR ou layout (CNPJ ausente)"
            ))

        if not cab.valor_total and not cab.valor_produtos:
             errors.append(Erro(
                dt_email=cab.dt_email,
                msg_id=cab.msg_id,
                arquivo="N/A",
                motivo="Valor Total Zerado/Não Encontrado",
                acao_sugerida="Verificar extração de valores"
            ))

        # 2. Sum Consistency (only if items present)
        # Assuming cab.valor_produtos matches sum of items.vlr_total
        # Sometimes valor_total includes taxes/freight, so strict check might fail.
        if items:
            sum_items = sum((i.vlr_total or 0.0) for i in items)
            # Tolerance 1.00 for rounding diffs
            diff = abs(sum_items - (cab.valor_produtos or 0.0))
            
            # If diff is large, maybe items are unit prices?
            # Or maybe cab.valor_produtos is 0?
            
            if diff > 1.00 and (cab.valor_produtos or 0) > 0:
                # This is soft validation, maybe just warn log?
                # or create error record
                pass # Logic to be refined based on real data
        
        return errors
