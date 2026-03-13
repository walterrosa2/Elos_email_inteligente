import pandas as pd
from pathlib import Path
from typing import List
from loguru import logger
from app.core.models import Cabecalho, Item, Erro, Origem

class ExcelReportWriter:
    """
    Manages writing/appending data to the daily Excel file.
    """
    
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def write_batch(self, 
                    cabecalhos: List[Cabecalho], 
                    items: List[Item], 
                    erros: List[Erro], 
                    origens: List[Origem]):
        """
        Appends data to the Excel file, creating it if necessary.
        Uses Pandas for simplicity, managing sheet existence.
        """
        if not any([cabecalhos, items, erros, origens]):
            return

        logger.info(f"Writing/Appending batch to {self.file_path}...")
        
        # Convert Pydantic models to DataFrames
        df_cab = pd.DataFrame([c.model_dump() for c in cabecalhos]) if cabecalhos else pd.DataFrame()
        df_item = pd.DataFrame([i.model_dump() for i in items]) if items else pd.DataFrame()
        df_erro = pd.DataFrame([e.model_dump() for e in erros]) if erros else pd.DataFrame()
        df_origem = pd.DataFrame([o.model_dump() for o in origens]) if origens else pd.DataFrame()

        # Handle Extra Fields flattening if necessary
        # (Assuming model_dump() handles dicts, but they become json strings or objects in df)
        # For Excel, ideally we flatten them into columns EXTRA_key?
        # For V1 MVP: Keeping as dict column or user can flatten in refined version.
        
        # Write/Append Logic
        try:
            if self.file_path.exists():
                with pd.ExcelWriter(self.file_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    # Helper to append without header if sheet exists
                    self._append_to_sheet(writer, df_cab, "CABECALHO")
                    self._append_to_sheet(writer, df_item, "ITENS")
                    self._append_to_sheet(writer, df_erro, "ERROS")
                    self._append_to_sheet(writer, df_origem, "ORIGEM")
            else:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                with pd.ExcelWriter(self.file_path, mode='w', engine='openpyxl') as writer:
                    df_cab.to_excel(writer, sheet_name="CABECALHO", index=False)
                    df_item.to_excel(writer, sheet_name="ITENS", index=False)
                    df_erro.to_excel(writer, sheet_name="ERROS", index=False)
                    df_origem.to_excel(writer, sheet_name="ORIGEM", index=False)
                    
            logger.info("Batch written successfully.")
            
        except Exception as e:
            logger.error(f"Failed to write Excel: {e}")
            raise

    def _append_to_sheet(self, writer, df, sheet_name):
        if df.empty:
            return
            
        # Check if sheet exists to decide on header
        try:
            writer.book[sheet_name]
            start_row = writer.book[sheet_name].max_row
            header = False
        except KeyError:
            start_row = 0
            header = True
            
        df.to_excel(writer, sheet_name=sheet_name, index=False, header=header, startrow=start_row)
