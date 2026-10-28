import pandas as pd
from utils.text import sanitize_name, normalize_inep
from utils.logger import get_logger

logger = get_logger("FrequencyTransformer")

class FrequencyTransformer:
    def __init__(self, calendario_df: pd.DataFrame):
        # R1: Filtra apenas dias letivos (dia_letivo = 'S')
        dias_validos = calendario_df[calendario_df['dia_letivo'] == 'S']['data']
        self.dias_letivos = set(pd.to_datetime(dias_validos).dt.strftime('%Y-%m-%d'))

    def transform(self, raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        logger.info("Aplicando regras de negócio e validações (R1-R10)...")
        df = raw_df.copy()
        
        # Ajuste nos tipos de data
        df['data_aula'] = pd.to_datetime(df['data_aula'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['inicio_matricula'] = pd.to_datetime(df['inicio_matricula'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['fim_matricula'] = pd.to_datetime(df['fim_matricula'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # R4 & R7: Sanitização de Nome e INEP
        df['nome_aluno_sanitizado'] = df['nome_aluno'].apply(sanitize_name)
        df['inep_escola'] = df['inep_escola'].apply(normalize_inep)
        
        # Coluna de auditoria para registros descartados
        df['motivo_descarte'] = None
        
        # R1: Período e dia letivo
        mask_fora_calendario = ~df['data_aula'].isin(self.dias_letivos)
        df.loc[mask_fora_calendario, 'motivo_descarte'] = 'FORA_DO_CALENDARIO_LETIVO'
        
        # R2: Campos obrigatórios
        mask_invalido = (
            df['inep_escola'].isna() | 
            df['codigo_turma'].isna() | 
            df['nome_aluno_sanitizado'].isna() | 
            df['data_aula'].isna()
        )
        df.loc[df['motivo_descarte'].isna() & mask_invalido, 'motivo_descarte'] = 'CAMPOS_OBRIGATORIOS_AUSENTES'
        
        # R3: Situação de frequência válida (P, F, J)
        mask_status = ~df['status_frequencia'].isin(['P', 'F', 'J'])
        df.loc[df['motivo_descarte'].isna() & mask_status, 'motivo_descarte'] = 'STATUS_FREQUENCIA_INVALIDO'
        
        # R6: Vigência da matrícula
        mask_fora_vigencia = (
            (df['inicio_matricula'].notna() & (df['data_aula'] < df['inicio_matricula'])) |
            (df['fim_matricula'].notna() & (df['data_aula'] > df['fim_matricula']))
        )
        df.loc[df['motivo_descarte'].isna() & mask_fora_vigencia, 'motivo_descarte'] = 'FORA_DA_VIGENCIA_MATRICULA'

        # Separação entre Válidos e Inválidos
        df_invalidos = df[df['motivo_descarte'].notna()].copy()
        df_validos = df[df['motivo_descarte'].isna()].copy()

        # R5: Unicidade (1 registro por aluno, turma e dia letivo)
        qtd_antes = len(df_validos)
        df_validos = df_validos.drop_duplicates(
            subset=['rede', 'inep_escola', 'codigo_turma', 'nome_aluno_sanitizado', 'data_nascimento', 'data_aula'],
            keep='first'
        )
        logger.info(f"R5 (Unicidade): {qtd_antes - len(df_validos)} registros duplicados foram removidos.")

        # R10: Mês de referência (AAAA-MM)
        df_validos['mes_referencia'] = df_validos['data_aula'].str.slice(0, 7)
        
        # R3 / R8: Presença numérico (P=1, F/J=0)
        df_validos['is_presente'] = df_validos['status_frequencia'].apply(lambda x: 1 if x == 'P' else 0)

        logger.info(f"Validação concluída: {len(df_validos)} válidos | {len(df_invalidos)} inválidos.")
        return df_validos, df_invalidos