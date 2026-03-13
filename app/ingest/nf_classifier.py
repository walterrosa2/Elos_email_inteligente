import re

class NFClassifier:
    """
    Classifies the type of Fiscal Document based on extracted text.
    Types: NFE, NFCE, CTE, NFSE, OUTROS.
    """
    
    # Regex patterns for stronger matching
    REGEX_CHAVE = r"\b[0-9]{44}\b"
    REGEX_NFE_TITLE = r"(DANFE|NOTA FISCAL ELETR.NICA|NFE)"
    REGEX_CTE_TITLE = r"(DACTE|CONHECIMENTO DE TRANSPORTE|CTE)"
    REGEX_NFSE_KEYWORDS = [r"PRESTADOR DE SERVI.OS", r"TOMADOR DE SERVI.OS", r"NOTA FISCAL DE SERVI.OS", r"ISSQN", r"RPS"]

    def classify(self, text: str) -> str:
        """
        Returns the classification string.
        """
        if not text:
            return "UNKNOWN"
            
        text_norm = text.upper().replace("\n", " ")
        
        # 1. Check for Access Key (NFe/CTe)
        has_chave = re.search(self.REGEX_CHAVE, text_norm)
        
        if has_chave:
            # Disambiguate NFe vs CTe
            if re.search(self.REGEX_CTE_TITLE, text_norm):
                return "CTE"
            # Default to NFe if Key present and not CTe explicitly
            return "NFE"
            
        # 2. Check for NFe explicit title without key (less likely but possible if OCR bad)
        if re.search(self.REGEX_NFE_TITLE, text_norm):
             return "NFE"
             
        # 3. NFSe Checks (Keywords)
        matches = 0
        for pat in self.REGEX_NFSE_KEYWORDS:
            if re.search(pat, text_norm):
                matches += 1
        
        if matches >= 2: # Heuristic: at least 2 keywords
            return "NFSE"
            
        # 4. NFCe
        if "NFC-E" in text_norm or "CONSUMIDOR ELETR" in text_norm:
            return "NFCE"
        # 5. New Documents: Faturas, Boletos, Recibos, Extratos e Impostos
        if "ENERGIA EL" in text_norm or "CONTA DE LUZ" in text_norm or "ANEEL" in text_norm:
            return "fatura_energia"
            
        if "TELECOMUNICA" in text_norm or "VIVO" in text_norm or "CLARO" in text_norm or "TIM" in text_norm:
            if "FATURA" in text_norm or "VENCIMENTO" in text_norm:
                return "fatura_telecom"
                
        if "CARTAO DE CREDITO" in text_norm or "PAGAMENTO MINIMO" in text_norm:
            return "fatura_cartao_credito"
            
        if "DUPLICATA MERCANTIL" in text_norm or "SACADOR" in text_norm:
            return "duplicata_mercantil"
            
        if "RECIBO" in text_norm or "RECEBI(EMOS) DE" in text_norm or "HOLERITE" in text_norm or "RECIBO DE PAGAMENTO" in text_norm:
            return "recibo_pagamento"
            
        if "EXTRATO" in text_norm and ("SALDO" in text_norm or "CONTA CORRENTE" in text_norm):
            return "extrato_bancario"
            
        if "BORDERO" in text_norm or "REMESSA DE PAGAMENTO" in text_norm:
            return "bordero_pagamento"
            
        if "DARF" in text_norm or "DOCUMENTO DE ARRECADACAO DE RECEITAS FEDERAIS" in text_norm:
            return "guia_imposto_darf"
            
        if "DAS" in text_norm and "SIMPLES NACIONAL" in text_norm:
            return "guia_imposto_das"
            
        if "GPS" in text_norm and "GUIA DA PREVIDENCIA SOCIAL" in text_norm:
            return "guia_imposto_gps"
            
        if "BOLETO" in text_norm or "LINHA DIGITAVEL" in text_norm:
             return "boleto_bancario"

        if "FATURA" in text_norm or "INVOICE" in text_norm:
             return "fatura_comercial"

        return "UNKNOWN"
