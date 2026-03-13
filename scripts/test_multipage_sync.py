import io
import sys
from unittest.mock import MagicMock, patch

# Ajustar PYTHONPATH
sys.path.append(".")

from app.textract.service import TextractService
from pypdf import PdfWriter

def create_mock_pdf(pages=2):
    writer = PdfWriter()
    for i in range(pages):
        writer.add_blank_page(width=72, height=72)
    
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

@patch('app.textract.service.boto3.client')
def test_multipage_logic(mock_boto):
    # Mock do retorno do Textract
    mock_client = MagicMock()
    mock_boto.return_value = mock_client
    
    # Simular retorno para cada página
    mock_client.detect_document_text.side_effect = [
        {'Blocks': [{'BlockType': 'LINE', 'Text': 'Nota 1'}], 'DocumentMetadata': {'Pages': 1}},
        {'Blocks': [{'BlockType': 'LINE', 'Text': 'Nota 2'}], 'DocumentMetadata': {'Pages': 1}}
    ]
    
    service = TextractService()
    pdf_bytes = create_mock_pdf(2)
    
    print("--- Testando Lógica Multipágina (Split-and-Sync) ---")
    result = service.process_document_multipage(pdf_bytes, filename="fatura_dupla.pdf")
    
    print(f"Total de páginas detectadas: {result['pages']}")
    print("Conteúdo extraído:")
    print(result['text'])
    
    assert result['pages'] == 2
    assert "Nota 1" in result['text']
    assert "Nota 2" in result['text']
    assert "--- PAGE 1 ---" in result['text']
    assert "--- PAGE 2 ---" in result['text']
    
    print("\n--- Teste de Lógica Multipágina Concluído com Sucesso! ---")

if __name__ == "__main__":
    test_multipage_logic()
