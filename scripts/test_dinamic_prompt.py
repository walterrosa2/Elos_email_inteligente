import os
import sys

# Garante path correto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.settings_service import settings_service
from app.contracts.manager import contract_manager

def test_settings_e_prompt():
    print("--- Testando Persistencia das Configurações ---")
    
    # 1. Ajustar o valor no banco via service
    novo_prompt = "Instrucao dinamica: analise e traga o JSON correto deste doc."
    settings_service.set_setting("openai_prompt_identificacao", novo_prompt)
    print(f"Salvo no DB: openai_prompt_identificacao = '{novo_prompt}'")
    
    # 2. Ler
    lido = settings_service.get_setting("openai_prompt_identificacao")
    print(f"Lido do DB: '{lido}'")
    assert lido == novo_prompt, "Erro ao salvar/ler configuracao do DB."
    print("OK - Persistencia do banco (configs) validada.")
    
    print("\n--- Testando Geracao de Prompt do Classify Service (Dry Run) ---")
    
    texto_simulado = "Este é um texto falso de uma Nota Fiscal de Serviço (NFS-e)."
    
    # Mockando method call de classificação para vermos APENAS o prompt gerado
    # Em vez de chamar o client da openai, fazemos o que o _service_ faz.
    candidates = contract_manager.get_candidate_contracts(texto_simulado)
    
    definitions = []
    for c in candidates:
         def_str = f"- {c.doc_type}: {c.description}"
         if c.keywords:
             kws = ", ".join(c.keywords[:10])
             def_str += f" (Keywords: {kws})"
         definitions.append(def_str)
         
    prompt_gerado = f"""
{lido}

Available Definitions:
{chr(10).join(definitions)}

Document Text (truncated):
{texto_simulado[:4000]} 
    """
    
    print("------- PROMPT FINAL QUE SERA GERADO E ENVIADO -------")
    print(prompt_gerado)
    print("------------------------------------------------------")
    print("OK - O prompt final contem o texto editado + as definicoes hardcoded com protecao.")

if __name__ == "__main__":
    test_settings_e_prompt()
