from pathlib import Path
from datetime import datetime
from app.core.models import Cabecalho, Item, Origem
from app.outputs.excel_writer import ExcelReportWriter

def test_excel_writer():
    print("Testing ExcelReportWriter...")
    
    # Create dummy data
    cab = Cabecalho(
        dt_email=datetime.now(),
        msg_id="1",
        tipo_nf="NFe",
        chave="12345678901234567890123456789012345678901234",
        numero="100",
        serie="1",
        emissao=datetime.now(),
        emitente_cnpj="12345678000199",
        valor_total=100.0
    )
    
    item = Item(
        item_n=1,
        descricao="Test Item",
        qtde=1.0,
        vlr_unit=100.0,
        vlr_total=100.0
    )
    
    origem = Origem(
        dt_email=datetime.now(),
        msg_id="1",
        remetente="test@example.com",
        assunto="Test Email",
        arquivo="test.pdf",
        hash_arquivo="abc",
        caminho_original="/tmp/test.pdf"
    )
    
    output_path = Path("test_output.xlsx")
    if output_path.exists():
        output_path.unlink()
        
    writer = ExcelReportWriter(output_path)
    
    try:
        writer.write_batch([cab], [item], [], [origem])
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_writer()
