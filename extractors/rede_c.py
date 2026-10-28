from pathlib import Path
import pandas as pd
from extractors.base import BaseExtractor
from utils.logger import get_logger

logger = get_logger("RedeCExtractor")

class RedeCExtractor(BaseExtractor):
    def __init__(self, folder_path: str):
        super().__init__(source_name="Rede C")
        self.folder_path = Path(folder_path)

    def extract(self) -> pd.DataFrame:
        logger.info("Iniciando varredura das planilhas CSV (Rede C)...")
        all_dfs = []
        
        for csv_file in self.folder_path.glob("frequencia_*.csv"):
            try:
                df = pd.read_csv(csv_file, sep=None, engine='python', encoding='utf-8')
            except (UnicodeDecodeError, pd.errors.ParserError):
                df = pd.read_csv(csv_file, sep=None, engine='python', encoding='latin1')
                
            df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]
            
            rename_map = {
                'codigo_inep': 'inep_escola',
                'inep': 'inep_escola',
                'escola': 'nome_escola',
                'turma': 'codigo_turma',
                'matricula': 'codigo_aluno',
                'aluno': 'nome_aluno',
                'dt_nascimento': 'data_nascimento',
                'data': 'data_aula',
                'situacao': 'status_frequencia',
                'frequencia': 'status_frequencia'
            }
            df = df.rename(columns=rename_map)
            
            df['rede'] = 'Rede C'
            df['inicio_matricula'] = None
            df['fim_matricula'] = None
            
            all_dfs.append(df)
            
        df_final = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        logger.info(f"Rede C extraída com sucesso: {len(df_final)} registros.")
        return df_final