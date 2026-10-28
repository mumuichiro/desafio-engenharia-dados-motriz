import json
import pandas as pd
from extractors.base import BaseExtractor
from utils.logger import get_logger

logger = get_logger("RedeBExtractor")

class RedeBExtractor(BaseExtractor):
    def __init__(self, file_path: str):
        super().__init__(source_name="Rede B")
        self.file_path = file_path

    def extract(self) -> pd.DataFrame:
        logger.info("Iniciando parsing do arquivo NDJSON (Rede B)...")
        records = []
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                doc = json.loads(line)
                
                codigo_aluno = doc.get("codigo_aluno")
                nome_aluno = doc.get("nome")
                nascimento = doc.get("nascimento")
                
                if isinstance(nascimento, dict) and "$date" in nascimento:
                    nascimento = nascimento["$date"][:10]
                
                for mat in doc.get("matriculas", []):
                    escola = mat.get("escola", {})
                    turma = mat.get("turma", {})
                    
                    inep = escola.get("inep")
                    nome_escola = escola.get("nome")
                    cod_turma = turma.get("codigo")
                    serie = turma.get("serie")
                    turno = turma.get("turno")
                    
                    inicio_mat = mat.get("inicio")
                    fim_mat = mat.get("fim")
                    
                    if isinstance(inicio_mat, dict) and "$date" in inicio_mat:
                        inicio_mat = inicio_mat["$date"][:10]
                    if isinstance(fim_mat, dict) and "$date" in fim_mat:
                        fim_mat = fim_mat["$date"][:10]
                    
                    for p in mat.get("presencas", []):
                        dt_aula = p.get("data")
                        if isinstance(dt_aula, dict) and "$date" in dt_aula:
                            dt_aula = dt_aula["$date"][:10]
                            
                        records.append({
                            "rede": "Rede B",
                            "inep_escola": inep,
                            "nome_escola": nome_escola,
                            "codigo_turma": cod_turma,
                            "serie": serie,
                            "turno": turno,
                            "codigo_aluno": codigo_aluno,
                            "nome_aluno": nome_aluno,
                            "data_nascimento": nascimento,
                            "data_aula": dt_aula,
                            "status_frequencia": self._normalize_status(p.get("status")),
                            "inicio_matricula": inicio_mat,
                            "fim_matricula": fim_mat
                        })
                        
        df = pd.DataFrame(records)
        logger.info(f"Rede B extraída com sucesso: {len(df)} registros.")
        return df

    @staticmethod
    def _normalize_status(val) -> str:
        if val is None or pd.isna(val):
            return 'IGNORAR'
        v = str(val).strip().lower()
        if v in ['p', 'presenca', 'presente', '1', 'true']:
            return 'P'
        if v in ['f', 'falta', 'ausente', '0', 'false']:
            return 'F'
        if v in ['j', 'justificada']:
            return 'J'
        return 'IGNORAR'