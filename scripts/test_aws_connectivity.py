import sys
import os
import io

# Adicionar a pasta raiz ao PYTHONPATH
sys.path.append(".")

from dotenv import load_dotenv
load_dotenv(override=True)

from app.core.config import settings
import boto3
from botocore.exceptions import ClientError
from pypdf import PdfWriter

def create_mock_pdf():
    # Vamos gerar um PDF de 1 página com pypdf
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

def test_s3_connection():
    print("\n========================================")
    print("[1/2] Testando Conexao com o AWS S3...")
    print("========================================")
    
    bucket_name = os.environ.get("AWS_TEXTRACT_S3_BUCKET")
    prefix = os.environ.get("AWS_TEXTRACT_S3_PREFIX", "uploads")
    
    if not bucket_name:
        print("[ERRO] AWS_TEXTRACT_S3_BUCKET nao foi definido no seu arquivo .env!")
        return False
        
    print(f"Bucket configurado: {bucket_name}")
    print(f"Prefixo: {prefix}")
    
    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        test_key = f"{prefix}/test_conn_win.txt"
        test_content = b"Teste de conectividade AWS do Pipeline ELOS"
        
        print(f"-> Fazendo upload do arquivo de teste: {test_key} ...")
        s3.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)
        print("[OK] Upload realizado com sucesso!")
        
        print("-> Listando objetos no bucket...")
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=5)
        if "Contents" in response:
            print("   Arquivos encontrados:")
            for item in response["Contents"]:
                print(f"   - {item['Key']} ({item['Size']} bytes)")
        else:
            print("   Nenhum arquivo listado (bucket vazio).")
            
        print(f"-> Removendo arquivo de teste: {test_key} ...")
        s3.delete_object(Bucket=bucket_name, Key=test_key)
        print("[OK] Remocao do arquivo de teste concluida!")
        print("CONEXAO S3 ESTABELECIDA COM SUCESSO!")
        return True
        
    except ClientError as e:
        print(f"[ERRO] Erro de conexao com o S3: {e}")
        return False
    except Exception as e:
        print(f"[ERRO] Erro inesperado no S3: {e}")
        return False

def test_textract_connection():
    print("\n========================================")
    print("[2/2] Testando Conexao com o AWS Textract...")
    print("========================================")
    
    try:
        textract = boto3.client(
            "textract",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        print("-> Gerando PDF ficticio de 1 pagina...")
        pdf_bytes = create_mock_pdf()
        
        print("-> Enviando documento para DetectDocumentText...")
        response = textract.detect_document_text(
            Document={'Bytes': pdf_bytes}
        )
        
        print("[OK] Documento processado pelo Textract com sucesso!")
        print(f"Metadados de retorno: {response.get('DocumentMetadata', {})}")
        print("CONEXAO TEXTRACT ESTABELECIDA COM SUCESSO!")
        return True
        
    except ClientError as e:
        print(f"[ERRO] Erro de conexao com o Textract: {e}")
        return False
    except Exception as e:
        print(f"[ERRO] Erro inesperado no Textract: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando testes de conectividade AWS...")
    
    key_id = settings.AWS_ACCESS_KEY_ID
    if key_id:
        print(f"AWS_ACCESS_KEY_ID: {key_id[:8]}... (tamanho: {len(key_id)})")
    else:
        print("AWS_ACCESS_KEY_ID: Nao encontrada (None)")
        
    print(f"AWS_REGION: {settings.AWS_REGION}")
    
    s3_ok = test_s3_connection()
    textract_ok = test_textract_connection()
    
    print("\n========================================")
    print("            RESUMO DO TESTE")
    print("========================================")
    print(f"S3 Connection:       {'OK' if s3_ok else 'FALHA'}")
    print(f"Textract Connection: {'OK' if textract_ok else 'FALHA'}")
    print("========================================")
    
    if s3_ok and textract_ok:
        print("Tudo pronto! As novas credenciais do AWS no .env estao funcionando perfeitamente.")
        sys.exit(0)
    else:
        print("Algumas validacoes falharam. Verifique os logs acima para detalhes.")
        sys.exit(1)
