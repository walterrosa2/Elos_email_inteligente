from app.db.database import SessionLocal, engine, Base
from app.db.models import Contract, ContractField

# Ensure tables
Base.metadata.create_all(bind=engine)

def seed_contracts():
    db = SessionLocal()
    try:
        contracts_data = [
            {
                "doc_type": "nfe_produto_sefaz",
                "description": "Nota Fiscal Eletrônica de Produtos (DANFE/XML)",
                "system_prompt": "Você é um especialista em extração de dados para NFe (Nota Fiscal Eletrônica). Extraia os seguintes campos do texto fornecido.",
                "keywords": ["danfe", "chave de acesso", "protocolo de autorização", "nfe"],
                "fields": [
                    {"name": "chave_acesso", "description": "Chave de Acesso da NFe (44 dígitos)", "type": "string", "required": False},
                    {"name": "numero_nf", "description": "Número da Nota Fiscal", "type": "string", "required": False},
                    {"name": "serie", "description": "Série da Nota Fiscal", "type": "string", "required": False},
                    {"name": "data_emissao", "description": "Data de Emissão (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "cnpj_emitente", "description": "CNPJ do Emitente", "type": "string", "required": False},
                    {"name": "razao_social_emitente", "description": "Razão Social do Emitente", "type": "string", "required": False},
                    {"name": "cnpj_destinatario", "description": "CNPJ do Destinatário", "type": "string", "required": False},
                    {"name": "razao_social_destinatario", "description": "Nome/Razão Social do Destinatário", "type": "string", "required": False},
                    {"name": "valor_total_nota", "description": "Valor Total da Nota", "type": "number", "required": False},
                    {"name": "valor_icms", "description": "Valor Total do ICMS", "type": "number", "required": False},
                    {"name": "valor_ipi", "description": "Valor Total do IPI", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "nfse_municipal",
                "description": "Nota Fiscal de Serviço (Padrão Municipal Variado)",
                "system_prompt": "Você é um especialista em extração de dados para NFSe (Nota Fiscal de Serviço Municipal). Extraia os seguintes campos.",
                "keywords": ["prefeitura", "nota fiscal de servicos", "prestador de servicos", "issqn"],
                "fields": [
                    {"name": "numero_nota", "description": "Número da Nota Fiscal", "type": "string", "required": False},
                    {"name": "codigo_verificacao", "description": "Código de Verificação", "type": "string", "required": False},
                    {"name": "data_emissao", "description": "Data de Emissão (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "cnpj_prestador", "description": "CNPJ do Prestador de Serviços", "type": "string", "required": False},
                    {"name": "razao_social_prestador", "description": "Razão Social do Prestador", "type": "string", "required": False},
                    {"name": "cnpj_tomador", "description": "CNPJ do Tomador de Serviços", "type": "string", "required": False},
                    {"name": "razao_social_tomador", "description": "Nome/Razão Social do Tomador", "type": "string", "required": False}, # Sometimes missing
                    {"name": "discriminacao_servicos", "description": "Descrição dos serviços prestados", "type": "string", "required": False},
                    {"name": "valor_total_servico", "description": "Valor Total do Serviço", "type": "number", "required": False},
                    {"name": "valor_iss", "description": "Valor do ISS", "type": "number", "required": False},
                    {"name": "iss_retido", "description": "ISS Retido? (Sim/Não)", "type": "string", "required": False},
                ]
            },
            {
                "doc_type": "nfse_nacional",
                "description": "Nota Fiscal de Serviço Eletrônica (Padrão Nacional)",
                "system_prompt": "Você é um especialista em extração de dados para NFSe Nacional. Extraia os campos de acordo com o padrão nacional.",
                "keywords": ["portal da nota fiscal de servico eletronica", "dps", "nfse nacional"],
                "fields": [
                    {"name": "numero_nfse", "description": "Número da NFSe Nacional", "type": "string", "required": False},
                    {"name": "data_competencia", "description": "Data de Competência", "type": "date", "required": False},
                    {"name": "cnpj_prestador", "description": "CNPJ do Prestador", "type": "string", "required": False},
                    {"name": "cnpj_tomador", "description": "CNPJ do Tomador", "type": "string", "required": False},
                    {"name": "codigo_servico", "description": "Código do Serviço (NBS)", "type": "string", "required": False},
                    {"name": "valor_servico", "description": "Valor do Serviço", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "boleto_bancario",
                "description": "Boleto Bancário para Pagamento",
                "system_prompt": "Você é um especialista em extração de dados para Boletos Bancários. Extraia as informações de pagamento.",
                "keywords": ["banco", "beneficiario", "pagador", "linha digitavel"],
                "fields": [
                    {"name": "banco_emissor", "description": "Nome do Banco", "type": "string", "required": False},
                    {"name": "codigo_banco", "description": "Código do Banco (ex: 001, 341)", "type": "string", "required": False},
                    {"name": "linha_digitavel", "description": "Linha Digitável (apenas números)", "type": "string", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "valor_boleto", "description": "Valor do Documento", "type": "number", "required": False},
                    {"name": "beneficiario_nome", "description": "Nome do Beneficiário", "type": "string", "required": False},
                    {"name": "beneficiario_cpf_cnpj", "description": "CPF/CNPJ do Beneficiário", "type": "string", "required": False},
                ]
            },
            {
                "doc_type": "fatura_comercial",
                "description": "Fatura Comercial / Invoice Simples",
                "system_prompt": "Você é um especialista em extração de dados para Faturas Comerciais / Invoices. Extraia os campos solicitados.",
                "keywords": ["fatura", "invoice", "vencimento", "total a pagar"],
                "fields": [
                    {"name": "numero_fatura", "description": "Número da Fatura", "type": "string", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento", "type": "date", "required": False},
                    {"name": "valor_total", "description": "Valor Total a Pagar", "type": "number", "required": False},
                    {"name": "fornecedor_nome", "description": "Nome do Fornecedor", "type": "string", "required": False},
                    {"name": "fornecedor_cnpj", "description": "CNPJ do Fornecedor (se houver)", "type": "string", "required": False},
                ]
            },
            {
                "doc_type": "fatura_energia",
                "description": "Fatura de Energia Elétrica (Concessionárias)",
                "system_prompt": "Você é um especialista em extração de dados para Faturas de Energia Elétrica (Conta de Luz). Extraia os campos necessários.",
                "keywords": ["energia", "conta de luz", "kwh", "concessionaria", "aneel"],
                "fields": [
                    {"name": "concessionaria", "description": "Nome da Concessionária de Energia", "type": "string", "required": False},
                    {"name": "numero_instalacao", "description": "Número da Instalação / Unidade Consumidora", "type": "string", "required": False},
                    {"name": "mes_referencia", "description": "Mês de Referência (MM/YYYY)", "type": "string", "required": False},
                    {"name": "valor_total", "description": "Valor Total da Fatura", "type": "number", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "consumo_kwh", "description": "Consumo Faturado em kWh", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "fatura_telecom",
                "description": "Fatura de Serviços de Telecomunicação (Telefonia/Internet)",
                "system_prompt": "Você é um especialista em extração de dados para Faturas de Telecomunicações (Internet/Telefone). Extraia os campos necessários.",
                "keywords": ["telecomunicacoes", "fatura de servicos", "telefone", "internet", "banda larga", "vivo", "claro", "tim"],
                "fields": [
                    {"name": "operadora", "description": "Nome da Operadora", "type": "string", "required": False},
                    {"name": "codigo_cliente", "description": "Código do Cliente / Assinante", "type": "string", "required": False},
                    {"name": "mes_referencia", "description": "Mês de Referência (MM/YYYY)", "type": "string", "required": False},
                    {"name": "valor_total", "description": "Valor Total da Fatura", "type": "number", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "telefone_principal", "description": "Número do Telefone Principal (se houver)", "type": "string", "required": False},
                ]
            },
            {
                "doc_type": "fatura_cartao_credito",
                "description": "Fatura de Cartão de Crédito",
                "system_prompt": "Você é um especialista em extração de dados para Faturas de Cartão de Crédito. Extraia os campos necessários.",
                "keywords": ["cartao de credito", "fatura do cartao", "pagamento minimo", "limite de credito", "fatura"],
                "fields": [
                    {"name": "emissor", "description": "Banco ou Emissor do Cartão", "type": "string", "required": False},
                    {"name": "final_cartao", "description": "4 últimos dígitos do cartão", "type": "string", "required": False},
                    {"name": "valor_fatura", "description": "Valor Total da Fatura Atual", "type": "number", "required": False},
                    {"name": "valor_minimo", "description": "Valor do Pagamento Mínimo", "type": "number", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento (DD/MM/YYYY)", "type": "date", "required": False},
                ]
            },
            {
                "doc_type": "duplicata_mercantil",
                "description": "Duplicata Mercantil",
                "system_prompt": "Você é um especialista em extração de dados para Duplicatas Mercantis. Extraia os dados financeiros solicitados.",
                "keywords": ["duplicata mercantil", "sacador", "sacado", "valor da duplicata"],
                "fields": [
                    {"name": "numero_duplicata", "description": "Número ou Fatura da Duplicata", "type": "string", "required": False},
                    {"name": "sacador_nome", "description": "Nome do Sacador", "type": "string", "required": False},
                    {"name": "sacador_cnpj", "description": "CNPJ do Sacador", "type": "string", "required": False},
                    {"name": "sacado_nome", "description": "Nome do Sacado", "type": "string", "required": False},
                    {"name": "sacado_cnpj", "description": "CNPJ do Sacado", "type": "string", "required": False},
                    {"name": "valor_duplicata", "description": "Valor da Duplicata", "type": "number", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento (DD/MM/YYYY)", "type": "date", "required": False},
                ]
            },
            {
                "doc_type": "recibo_pagamento",
                "description": "Recibo de Pagamento (RPA / Holerite / Geral)",
                "system_prompt": "Você é um especialista em extração de dados para Recibos e Holerites. Extraia os dados relevantes.",
                "keywords": ["recibo", "recebi(emos) de", "importancia de", "pagamento", "holerite", "recibo de pagamento autônomo", "rpa"],
                "fields": [
                    {"name": "recebedor_nome", "description": "Nome de quem recebeu o dinheiro", "type": "string", "required": False},
                    {"name": "recebedor_cpf_cnpj", "description": "CPF ou CNPJ do Recebedor", "type": "string", "required": False},
                    {"name": "pagador_nome", "description": "Nome de quem efetuou o pagamento", "type": "string", "required": False},
                    {"name": "valor_recebido", "description": "Valor Numérico Recebido", "type": "number", "required": False},
                    {"name": "descricao_pagamento", "description": "Referente a que (descrição)", "type": "string", "required": False},
                    {"name": "data_emissao", "description": "Data de Emissão do Recibo (DD/MM/YYYY)", "type": "date", "required": False},
                ]
            },
            {
                "doc_type": "extrato_bancario",
                "description": "Extrato Bancário Mensal",
                "system_prompt": "Você é um especialista em extração de dados para Extratos Bancários. Extraia os campos de resumo.",
                "keywords": ["extrato de conta corrente", "saldo anterior", "lançamentos", "saldo final", "extrato consolidado"],
                "fields": [
                    {"name": "banco", "description": "Nome do Banco", "type": "string", "required": False},
                    {"name": "agencia", "description": "Número da Agência", "type": "string", "required": False},
                    {"name": "conta", "description": "Número da Conta", "type": "string", "required": False},
                    {"name": "periodo_inicial", "description": "Data Inicial do Extrato (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "periodo_final", "description": "Data Final do Extrato (DD/MM/YYYY)", "type": "date", "required": False},
                    {"name": "saldo_final", "description": "Valor do Saldo Final", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "bordero_pagamento",
                "description": "Borderô de Pagamentos / Remessa",
                "system_prompt": "Você é um especialista em extração de dados para Borderôs de Pagamento / Remessa. Extraia as informações de resumo.",
                "keywords": ["bordero", "remessa de pagamentos", "relatorio de pagamentos", "autorizacao de pagamento"],
                "fields": [
                    {"name": "banco_emissor", "description": "Banco Emissor do Borderô", "type": "string", "required": False},
                    {"name": "data_bordero", "description": "Data de Emissão ou Pagamento do Borderô", "type": "date", "required": False},
                    {"name": "valor_total", "description": "Valor Total do Borderô/Remessa", "type": "number", "required": False},
                    {"name": "quantidade_documentos", "description": "Quantidade de Documentos Listados", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "guia_imposto_darf",
                "description": "Guia de Imposto Federal (DARF)",
                "system_prompt": "Você é um especialista em extração de dados para DARF (Documento de Arrecadação de Receitas Federais). Extraia os campos necessários.",
                "keywords": ["darf", "ministerio da fazenda", "secretaria da receita federal", "documento de arrecadacao"],
                "fields": [
                    {"name": "nome_contribuinte", "description": "Nome / Razão Social do Contribuinte", "type": "string", "required": False},
                    {"name": "cnpj_cpf", "description": "CPF ou CNPJ", "type": "string", "required": False},
                    {"name": "periodo_apuracao", "description": "Período de Apuração", "type": "date", "required": False},
                    {"name": "codigo_receita", "description": "Código da Receita", "type": "string", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento", "type": "date", "required": False},
                    {"name": "valor_principal", "description": "Valor do Principal", "type": "number", "required": False},
                    {"name": "valor_multa_juros", "description": "Valor de Multa ou Juros", "type": "number", "required": False},
                    {"name": "valor_total", "description": "Valor Total do Documento", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "guia_imposto_das",
                "description": "Guia de Imposto do Simples Nacional (DAS)",
                "system_prompt": "Você é um especialista em extração de dados para DAS (Documento de Arrecadação do Simples Nacional). Extraia os campos necessários.",
                "keywords": ["das", "simples nacional", "documento de arrecadacao do simples"],
                "fields": [
                    {"name": "razao_social", "description": "Razão Social", "type": "string", "required": False},
                    {"name": "cnpj", "description": "CNPJ", "type": "string", "required": False},
                    {"name": "periodo_apuracao", "description": "Período de Apuração", "type": "date", "required": False},
                    {"name": "data_vencimento", "description": "Data de Vencimento", "type": "date", "required": False},
                    {"name": "valor_total", "description": "Valor Total do Documento", "type": "number", "required": False},
                ]
            },
            {
                "doc_type": "guia_imposto_gps",
                "description": "Guia da Previdência Social (GPS)",
                "system_prompt": "Você é um especialista em extração de dados para a GPS (Guia da Previdência Social). Extraia os campos necessários.",
                "keywords": ["gps", "guia da previdencia social", "inss", "ministerio da previdencia e assistencia social"],
                "fields": [
                    {"name": "nome_contribuinte", "description": "Nome ou Razão Social", "type": "string", "required": False},
                    {"name": "identificador", "description": "Código Identificador (CNPJ, CEI, NIT)", "type": "string", "required": False},
                    {"name": "competencia", "description": "Mês/Ano de Competência", "type": "string", "required": False},
                    {"name": "codigo_pagamento", "description": "Código de Pagamento", "type": "string", "required": False},
                    {"name": "valor_inss", "description": "Valor do INSS", "type": "number", "required": False},
                    {"name": "valor_outras_entidades", "description": "Valor Outras Entidades", "type": "number", "required": False},
                    {"name": "valor_total", "description": "Valor Total Arrecadado", "type": "number", "required": False},
                ]
            }
        ]

        print("🔄 Upserting Contracts...")
        
        for item in contracts_data:
            doc_type = item["doc_type"]
            
            # Check exist
            existing = db.query(Contract).filter(Contract.doc_type == doc_type).first()
            if existing:
                print(f"Update: {doc_type}")
                existing.description = item["description"]
                existing.system_prompt = item["system_prompt"]
                existing.keywords = item["keywords"]
                # Clear fields to re-add (simple update strategy)
                db.query(ContractField).filter(ContractField.contract_doc_type == doc_type).delete()
            else:
                print(f"Create: {doc_type}")
                new_contract = Contract(
                    doc_type=doc_type,
                    description=item["description"],
                    system_prompt=item["system_prompt"],
                    keywords=item["keywords"]
                )
                db.add(new_contract)
                existing = new_contract # Reference for fields
                
            # Add Fields
            for f in item["fields"]:
                field = ContractField(
                    contract_doc_type=doc_type,
                    name=f["name"],
                    description=f["description"],
                    type=f["type"],
                    required=f["required"]
                )
                db.add(field)

        db.commit()
        print("✅ Contracts created successfully!")

    except Exception as e:
        print(f"❌ Error seeding contracts: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_contracts()
