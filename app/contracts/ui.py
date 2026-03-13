import streamlit as st
from app.contracts.manager import contract_manager, Contract, ContractField
from app.core.settings_service import settings_service

def render_contracts_ui():
    st.header("📜 Gestão de Contratos (Schemas)")
    st.info("Defina os tipos de documentos, seus campos e regras de extração.")

    # List existing contracts
    col_h, col_r = st.columns([4, 1])
    with col_h:
        contracts = contract_manager.list_contracts()
    with col_r:
        if st.button("🔄 Recarregar"):
            contract_manager.reload_contracts()
            st.rerun()

    contract_names = [c.doc_type for c in contracts]
    
    # Selection: Existing or New
    selected_name = st.selectbox("Selecione um contrato para editar ou crie novo:", ["➕ Criar Novo"] + contract_names)
    
    if selected_name == "➕ Criar Novo":
        # Empty state for new contract
        doc_type = st.text_input("Tipo do Documento (Código Único, ex: 'NF_SEFAZ')", help="Usado internamente. Sem espaços, letras maiúsculas.")
        desc = st.text_input("Descrição", help="Descreva o documento para o Classificador.")
        prompt = st.text_area("System Prompt (Exemplo)", height=150, help="Instruções para o LLM extrair os dados.", value="You are an expert...")
        keywords_str = st.text_input("Palavras-chave (separadas por vírgula)", help="Para auxiliar a classificação rápida.")
        
        # Fields Editor
        st.subheader("Campos para Extração")
        # Default empty list for fields
        fields_data = [{"name": "novo_campo", "type": "string", "description": "descrição do campo", "required": False}]
        
        edited_fields = st.data_editor(fields_data, num_rows="dynamic", width="stretch")
        
        if st.button("💾 Salvar Novo Contrato", type="primary"):
            if not doc_type:
                st.error("Tipo do Documento é obrigatório.")
                return
            
            # Build DTO
            try:
                fields_objs = []
                for f in edited_fields:
                    fields_objs.append(ContractField(
                        name=f["name"],
                        description=f["description"],
                        type=f["type"],
                        required=f["required"]
                    ))
                
                kw_list = [k.strip() for k in keywords_str.split(",") if k.strip()]
                
                new_c = Contract(
                    doc_type=doc_type,
                    description=desc,
                    system_prompt=prompt,
                    keywords=kw_list,
                    fields=fields_objs,
                    version="1.0"
                )
                
                if contract_manager.save_contract(new_c):
                    st.success(f"Contrato {doc_type} salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar contrato no banco de dados.")
                    
            except Exception as e:
                st.error(f"Erro na validação: {e}")

    else:
        # Edit Existing
        c = contract_manager.get_contract(selected_name)
        if not c:
            st.error("Erro ao carregar contrato.")
            return
            
        st.subheader(f"Editando: {c.doc_type} (v{c.version})")
        
        # Form
        with st.form(key=f"form_{c.doc_type}"):
            new_desc = st.text_input("Descrição", value=c.description)
            new_prompt = st.text_area("System Prompt", value=c.system_prompt, height=200)
            new_keywords = st.text_input("Palavras-chave", value=", ".join(c.keywords))
            
            st.markdown("### Campos")
            # Convert fields to list of dicts for data_editor
            current_fields = [f.dict() for f in c.fields]
            edited_fields = st.data_editor(current_fields, num_rows="dynamic", width="stretch", key=f"editor_{c.doc_type}")
            
            submitted = st.form_submit_button("💾 Atualizar Contrato")
            
            if submitted:
                try:
                     # Rebuild Fields
                    fields_objs = []
                    for f in edited_fields:
                        # Handle if user didn't change anything, data_editor returns same dicts
                        # Handle types (sometimes data_editor converts booleans/etc)
                        fields_objs.append(ContractField(
                            name=str(f["name"]),
                            description=str(f["description"]),
                            type=str(f["type"]),
                            required=bool(f.get("required", False))
                        ))
                    
                    kw_list = [k.strip() for k in new_keywords.split(",") if k.strip()]
                    
                    updated_c = Contract(
                        doc_type=c.doc_type, # Read-only PK
                        description=new_desc,
                        system_prompt=new_prompt,
                        keywords=kw_list,
                        fields=fields_objs,
                        version=c.version # Increment logic could go here
                    )
                    
                    if contract_manager.save_contract(updated_c):
                        st.success("Contrato atualizado!")
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar.")
                
                except Exception as e:
                    st.error(f"Erro: {e}")

def render_global_settings_ui():
    st.header("⚙️ Configurações Globais do Pipeline")
    st.info("Configurações que afetam todo o processo de ingestão e processamento.")

    # 1. Allowed Extensions
    st.subheader("📁 Filtro de Extensões")
    st.write("Somente anexos com as extensões abaixo serão baixados e processados.")
    
    current_exts = settings_service.get_allowed_extensions()
    
    # UI to edit
    exts_str = st.text_input(
        "Extensões Permitidas (separadas por vírgula)", 
        value=", ".join(current_exts),
        help="Ex: .pdf, .xlsx, .csv, .xml, .txt"
    )
    
    if st.button("💾 Salvar Filtro de Extensões"):
        # Process input
        new_exts = [e.strip().lower() for e in exts_str.split(",") if e.strip()]
        
        # Ensure they start with dot
        new_exts = [e if e.startswith(".") else f".{e}" for e in new_exts]
        
        settings_service.set_setting(
            "allowed_extensions", 
            new_exts, 
            "Lista de extensões de arquivos permitidas para download de anexos."
        )
        st.success("Configurações de extensões atualizadas!")
        st.rerun()
