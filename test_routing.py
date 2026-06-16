import os
import sys
import shutil
from datetime import datetime
from sqlalchemy.orm import Session

# Setup python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.database import SessionLocal, init_db, engine
from app.db.models import Job, EmailContext
from app.routing.service import routing_service
from app.storage.local_adapter import storage

def setup_test_data(db: Session):
    # Limpa dados anteriores de teste
    db.query(Job).filter(Job.message_id.like("test_msg_%")).delete()
    db.query(EmailContext).filter(EmailContext.message_id.like("test_msg_%")).delete()
    db.commit()

    # Criar um contexto de email
    ctx = EmailContext(
        message_id="test_msg_1",
        subject="Faturas para Pagamento",
        sender="fornecedor@teste.com",
        received_at=datetime(2026, 6, 15, 10, 0, 0),
        summary="Email de teste",
        criticality_score="MEDIA"
    )
    db.add(ctx)
    db.commit()

    # Job 1: Nota Fiscal (com emissão em 2026-06-06)
    job_nf = Job(
        job_hash="test_msg_1_hash_nf",
        message_id="test_msg_1",
        sender="fornecedor@teste.com",
        subject="Faturas para Pagamento",
        email_date=ctx.received_at,
        received_at=ctx.received_at,
        attachment_name="NF_123.pdf",
        attachment_hash="hash_nf",
        status="VALIDATED",
        doc_type="NFe_Produto",
        extraction_result={"emissao": "2026-06-06", "valor_total": 1500.00}
    )
    db.add(job_nf)
    db.commit()

    return job_nf.id

def test_date_parsing():
    print("\n--- Testando Parse de Datas ---")
    assert routing_service._parse_date("2026-06-18") == datetime(2026, 6, 18)
    assert routing_service._parse_date("18/06/2026") == datetime(2026, 6, 18)
    assert routing_service._parse_date("2026-06-18T10:30:00") == datetime(2026, 6, 18)
    print("OK: Todos os formatos de data parseados corretamente.")

def test_routing_calculation(db: Session, job_id: int):
    print("\n--- Testando Calculo de Roteamento ---")
    
    # 1. Testar calculo automatico baseado na emissao da NF (06/06)
    # Como dia 06 cai no Periodo 1 [1-10] -> Deve ir para o Dia 01
    info = routing_service.calculate_routing_info(job_id, db)
    assert info is not None
    assert info["reference_date"] == "2026-06-06"
    assert info["payment_day"] == 1
    assert info["target_payment_date"] == "2026-06-01"
    assert info["subfolder"] == "2026-06/Dia_01"
    print(f"OK: NF de emissao 2026-06-06 direcionada corretamente para a pasta: {info['subfolder']}")

    # 2. Adicionar Boleto ao mesmo email (Vencimento em 2026-06-18)
    # Com a priorizacao do boleto ativa, a NF de emissao dia 06 deve herdar o vencimento do Boleto (dia 18)
    # Dia 18 cai no Periodo 2 [11-20] -> Deve ir para o Dia 10
    job_boleto = Job(
        job_hash="test_msg_1_hash_boleto",
        message_id="test_msg_1",
        sender="fornecedor@teste.com",
        subject="Faturas para Pagamento",
        email_date=datetime(2026, 6, 15),
        received_at=datetime(2026, 6, 15),
        attachment_name="Boleto_123.pdf",
        attachment_hash="hash_boleto",
        status="VALIDATED",
        doc_type="Boleto",
        extraction_result={"data_vencimento": "2026-06-18", "valor_documento": 1500.00}
    )
    db.add(job_boleto)
    db.commit()

    # Recalcular informacoes da NF
    info_prioritized = routing_service.calculate_routing_info(job_id, db)
    assert info_prioritized is not None
    assert info_prioritized["reference_date"] == "2026-06-18" # Deve ter herdado a data do boleto!
    assert info_prioritized["payment_day"] == 10
    assert info_prioritized["target_payment_date"] == "2026-06-10"
    assert info_prioritized["subfolder"] == "2026-06/Dia_10"
    print(f"OK: Com prioridade ativa, NF herdou vencimento do Boleto (2026-06-18) e foi para: {info_prioritized['subfolder']}")

def test_physical_routing(db: Session, job_id: int):
    print("\n--- Testando Redirecionamento Fisico (Copia) ---")
    
    # Criar um arquivo dummy de staging
    job = db.query(Job).filter(Job.id == job_id).first()
    staging_file = Path(routing_service.get_routing_settings()["server_root_path"]) / "temp_staging.pdf"
    staging_file.parent.mkdir(parents=True, exist_ok=True)
    staging_file.write_text("DUMMY PDF CONTENT")
    
    job.storage_uri = str(staging_file)
    db.commit()
    
    # Executar roteamento da NF (que devera ir para a pasta Dia_10 do boleto anterior)
    res = routing_service.route_job(job_id, db)
    assert res["status"] == "success"
    
    dest_path = Path(res["routed_path"])
    assert dest_path.exists()
    assert dest_path.name == "NF_123.pdf"
    assert "Dia_10" in str(dest_path)
    
    # Validar status no banco
    assert job.direction_status == "ROUTED"
    assert job.routed_path == str(dest_path.absolute())
    
    print(f"OK: Arquivo copiado com sucesso para: {dest_path}")
    
    # Limpar arquivos criados
    if staging_file.exists():
        staging_file.unlink()
    if dest_path.exists():
        dest_path.unlink()
        # Remove as pastas de teste se vazias
        try:
            dest_path.parent.rmdir()
            dest_path.parent.parent.rmdir()
        except:
            pass

def test_custom_destination_folder(db: Session, job_id: int):
    print("\n--- Testando Caminho Customizado (destination_folder) ---")
    
    # Salvar configurações com um destination_folder customizado para todos os períodos
    orig_settings = routing_service.get_routing_settings()
    custom_settings = orig_settings.copy()
    custom_settings["periods"] = [
        {"start_day": 1, "end_day": 10, "payment_day": 1, "destination_folder": "Junho_2026/Customizado_Lote_1"},
        {"start_day": 11, "end_day": 20, "payment_day": 10, "destination_folder": "Junho_2026/Customizado_Lote_2"},
        {"start_day": 21, "end_day": 31, "payment_day": 20, "destination_folder": "Junho_2026/Customizado_Lote_3"}
    ]
    routing_service.save_routing_settings(custom_settings)
    
    try:
        # Forçar o recálculo para a NF do dia 06 (que herdou a data do boleto 18/06 -> Período 2)
        info = routing_service.calculate_routing_info(job_id, db)
        assert info is not None
        assert info["subfolder"] == "Junho_2026/Customizado_Lote_2"
        print(f"OK: Direcionamento respeitou a pasta customizada do período 2: {info['subfolder']}")
    finally:
        # Restaurar as configurações originais
        routing_service.save_routing_settings(orig_settings)

def test_v4_routing_election(db: Session):
    print("\n--- Testando Eleição de Maior Vencimento (V4.0) ---")
    # Limpeza
    db.query(Job).filter(Job.message_id == "test_v4_msg").delete()
    db.query(EmailContext).filter(EmailContext.message_id == "test_v4_msg").delete()
    db.commit()

    received_date = datetime(2026, 6, 10, 12, 0, 0)

    # 1. E-mail com vencimento no corpo (dia 25/06)
    ctx = EmailContext(
        message_id="test_v4_msg",
        subject="Faturas Consolidadas",
        sender="financeiro@empresa.com",
        received_at=received_date,
        body_text="Favor efetuar os pagamentos. A data limite geral no corpo é 2026-06-25.",
        detected_due_date="2026-06-25",
        due_date_context="limite geral no corpo é 2026-06-25"
    )
    db.add(ctx)
    db.commit()

    # 2. Anexo 1: NF com vencimento 20/06
    job_nf = Job(
        job_hash="test_v4_hash_nf",
        message_id="test_v4_msg",
        sender="financeiro@empresa.com",
        subject="Faturas Consolidadas",
        email_date=received_date,
        received_at=received_date,
        attachment_name="NF_V4.pdf",
        attachment_hash="hash_nf_v4",
        status="VALIDATED",
        original_due_date="2026-06-20",
        due_date_context="Vencimento da NF em 20/06/2026"
    )
    db.add(job_nf)

    # 3. Anexo 2: Boleto com vencimento 30/06 (Maior data)
    job_boleto = Job(
        job_hash="test_v4_hash_boleto",
        message_id="test_v4_msg",
        sender="financeiro@empresa.com",
        subject="Faturas Consolidadas",
        email_date=received_date,
        received_at=received_date,
        attachment_name="Boleto_V4.pdf",
        attachment_hash="hash_boleto_v4",
        status="VALIDATED",
        original_due_date="2026-06-30",
        due_date_context="Vencimento do boleto: 30/06/2026"
    )
    db.add(job_boleto)
    db.commit()

    # Calcular rota para o job da NF
    info = routing_service.calculate_routing_info(job_nf.id, db)
    assert info is not None
    # Deve eleger a maior data: 30/06 (Boleto)
    assert info["reference_date"] == "2026-06-30"
    assert "Boleto_V4.pdf" in info["due_date_source"]
    assert "30/06/2026" in info["due_date_context"]
    
    # Calcular rota para o job do Boleto
    info_b = routing_service.calculate_routing_info(job_boleto.id, db)
    assert info_b is not None
    assert info_b["reference_date"] == "2026-06-30"

    print("OK: Maior vencimento (30/06) eleito com sucesso.")

    # 4. Fallback: remover vencimentos e ver se faz fallback para data de recebimento do e-mail (10/06)
    ctx.detected_due_date = None
    job_nf.original_due_date = None
    job_boleto.original_due_date = None
    db.commit()

    info_fallback = routing_service.calculate_routing_info(job_nf.id, db)
    assert info_fallback is not None
    assert info_fallback["reference_date"] == "2026-06-10" # Data de recebimento
    assert "Fallback" in info_fallback["due_date_source"]

    print("OK: Fallback para data de recebimento do e-mail verificado com sucesso.")

    # Cleanup
    db.query(Job).filter(Job.message_id == "test_v4_msg").delete()
    db.query(EmailContext).filter(EmailContext.message_id == "test_v4_msg").delete()
    db.commit()

def test_v4_quarentena_sem_vencimento(db: Session):
    print("\n--- Testando Quarentena Sem Vencimento (V4.0) ---")
    
    # Criar um arquivo dummy de staging
    temp_dir = Path(routing_service.get_routing_settings()["server_root_path"]) / "test_quarentena_staging"
    temp_dir.mkdir(parents=True, exist_ok=True)
    staging_file = temp_dir / "documento_sem_venc.pdf"
    staging_file.write_text("DUMMY CONTENT")
    
    # Criar Job associado
    job = Job(
        job_hash="test_v4_hash_quarentena",
        message_id="test_v4_msg_quarentena",
        sender="fornecedor@teste.com",
        subject="Arquivo para Quarentena",
        email_date=datetime.now(),
        received_at=datetime.now(),
        attachment_name="documento_sem_venc.pdf",
        attachment_hash="hash_quarentena",
        status="STAGED",
        storage_uri=str(staging_file)
    )
    db.add(job)
    db.commit()
    
    try:
        # Lógica de movimentação (simulando pipeline)
        local_path = storage.resolve_path(job.storage_uri)
        assert local_path.exists()
        
        sem_venc_dir = local_path.parent / "Sem Vencimento"
        sem_venc_dir.mkdir(parents=True, exist_ok=True)
        new_path = sem_venc_dir / local_path.name
        
        shutil.move(str(local_path), str(new_path))
        
        relative_new_path = Path(job.storage_uri).parent / "Sem Vencimento" / local_path.name
        job.storage_uri = str(relative_new_path).replace("\\", "/")
        job.status = "EXTRACTED"
        db.commit()
        
        # Asserts
        assert Path(new_path).exists()
        assert "Sem Vencimento" in job.storage_uri
        print(f"OK: Arquivo movido com sucesso para a quarentena em: {job.storage_uri}")
        
    finally:
        # Cleanup
        if staging_file.exists():
            staging_file.unlink()
        dest_moved = temp_dir / "Sem Vencimento" / "documento_sem_venc.pdf"
        if dest_moved.exists():
            dest_moved.unlink()
            try:
                dest_moved.parent.rmdir()
                temp_dir.rmdir()
            except:
                pass
        
        db.query(Job).filter(Job.job_hash == "test_v4_hash_quarentena").delete()
        db.commit()

if __name__ == "__main__":
    from pathlib import Path
    
    init_db()
    db = SessionLocal()
    try:
        test_date_parsing()
        job_id = setup_test_data(db)
        test_routing_calculation(db, job_id)
        test_custom_destination_folder(db, job_id)
        test_v4_routing_election(db)
        test_v4_quarentena_sem_vencimento(db)
        test_physical_routing(db, job_id)
        print("\n[SUCESSO] TODOS OS TESTES PASSARAM COM SUCESSO!")
    finally:
        # Cleanup final no DB
        db.query(Job).filter(Job.message_id.like("test_msg_%")).delete()
        db.query(EmailContext).filter(EmailContext.message_id.like("test_msg_%")).delete()
        db.commit()
        db.close()

