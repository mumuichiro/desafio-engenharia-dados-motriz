import os
import re
import pandas as pd
from extractors.base import BaseExtractor
from utils.logger import get_logger

logger = get_logger("RedeAExtractor")

class RedeAExtractor(BaseExtractor):
    def __init__(self, sql_dump_path: str = "dados/rede_a/rede_a_dump.sql"):
        super().__init__(source_name="Rede A")
        self.sql_dump_path = sql_dump_path

    def extract(self) -> pd.DataFrame:
        logger.info("Iniciando extração do dump SQL da Rede A...")
        
        if not os.path.exists(self.sql_dump_path):
            raise FileNotFoundError(f"Arquivo de dump não encontrado em: {self.sql_dump_path}")

        # Tenta ler com utf-8 e faz fallback para latin1 se necessário
        try:
            with open(self.sql_dump_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(self.sql_dump_path, 'r', encoding='latin1') as f:
                content = f.read()

        escolas = {}
        turmas = {}
        alunos = {}
        matriculas = {}
        frequencias = []

        # 1. Tenta extrair via instrução COPY (padrão do pg_dump)
        copy_blocks = re.findall(r"COPY educacao\.(\w+)\s*\((.*?)\)\s*FROM stdin;(.*?)\\\.", content, re.DOTALL | re.IGNORECASE)

        if copy_blocks:
            for table_name, cols_raw, data_raw in copy_blocks:
                cols = [c.strip() for c in cols_raw.split(",")]
                lines = [l.strip() for l in data_raw.strip().splitlines() if l.strip()]

                for line in lines:
                    vals = line.split("\t")
                    row = dict(zip(cols, vals))

                    if table_name == "escola":
                        escolas[row.get("id")] = {
                            "codigo_inep": row.get("codigo_inep"),
                            "nome": row.get("nome")
                        }
                    elif table_name == "turma":
                        turmas[row.get("id")] = {
                            "escola_id": row.get("escola_id"),
                            "serie": row.get("serie"),
                            "codigo": row.get("codigo"),
                            "turno": row.get("turno")
                        }
                    elif table_name == "aluno":
                        alunos[row.get("id")] = {
                            "nome": row.get("nome"),
                            "data_nascimento": row.get("data_nascimento")
                        }
                    elif table_name == "matricula":
                        matriculas[(row.get("aluno_id"), row.get("turma_id"))] = row.get("data_matricula")
                    elif table_name == "frequencia":
                        frequencias.append({
                            "aluno_id": row.get("aluno_id"),
                            "turma_id": row.get("turma_id"),
                            "data_aula": row.get("data_aula"),
                            "presente": row.get("presente")
                        })

        # 2. Se não encontrou COPY, tenta extrair via instruções INSERT
        if not frequencias:
            insert_statements = re.findall(r"INSERT INTO educacao\.(\w+)[^\(]*\((.*?)\)\s*VALUES\s*(.*?);", content, re.DOTALL | re.IGNORECASE)
            for table_name, cols_raw, values_raw in insert_statements:
                rows = re.findall(r"\((.*?)\)", values_raw)
                for r in rows:
                    vals = [v.strip().strip("'\"") for v in r.split(",")]
                    if table_name == "escola" and len(vals) >= 3:
                        escolas[vals[0]] = {"codigo_inep": vals[1], "nome": vals[2]}
                    elif table_name == "turma" and len(vals) >= 5:
                        turmas[vals[0]] = {"escola_id": vals[1], "serie": vals[2], "codigo": vals[3], "turno": vals[4]}
                    elif table_name == "aluno" and len(vals) >= 3:
                        alunos[vals[0]] = {"nome": vals[1], "data_nascimento": vals[2]}
                    elif table_name == "matricula" and len(vals) >= 4:
                        matriculas[(vals[1], vals[2])] = vals[3]
                    elif table_name == "frequencia" and len(vals) >= 5:
                        frequencias.append({
                            "aluno_id": vals[1],
                            "turma_id": vals[2],
                            "data_aula": vals[3],
                            "presente": vals[4]
                        })

        records = []
        for freq in frequencias:
            a_id, t_id = freq["aluno_id"], freq["turma_id"]
            aluno = alunos.get(a_id, {})
            turma = turmas.get(t_id, {})
            escola = escolas.get(turma.get("escola_id"), {})
            data_mat = matriculas.get((a_id, t_id))

            p_val = str(freq["presente"]).lower()
            if p_val in ['true', 't', '1']:
                status = 'P'
            elif p_val in ['false', 'f', '0']:
                status = 'F'
            else:
                status = 'IGNORAR'

            records.append({
                "rede": "Rede A",
                "inep_escola": escola.get("codigo_inep"),
                "nome_escola": escola.get("nome"),
                "codigo_turma": turma.get("codigo"),
                "serie": turma.get("serie"),
                "turno": turma.get("turno"),
                "codigo_aluno": a_id,
                "nome_aluno": aluno.get("nome"),
                "data_nascimento": aluno.get("data_nascimento"),
                "data_aula": freq["data_aula"],
                "status_frequencia": status,
                "inicio_matricula": data_mat,
                "fim_matricula": None
            })

        df = pd.DataFrame(records)
        logger.info(f"Rede A extraída com sucesso: {len(df)} registros.")
        return df