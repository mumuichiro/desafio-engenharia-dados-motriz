import os
import pandas as pd
from extractors.rede_a import RedeAExtractor
from extractors.rede_b import RedeBExtractor
from extractors.rede_c import RedeCExtractor
from transformers.frequency_transformer import FrequencyTransformer
from loaders.bigquery_loader import BigQueryLoader
from utils.logger import get_logger

logger = get_logger("MainPipeline")

def run():
    logger.info("=== INICIANDO PIPELINE DE DADOS MOTRIZ ===")
    
    # 1. Carrega Calendário Oficial
    calendario_path = "dados/calendario_letivo_2026.csv"
    if not os.path.exists(calendario_path):
        raise FileNotFoundError(f"Calendário não encontrado em: {calendario_path}")
    calendario_df = pd.read_csv(calendario_path)
    
    # 2. Executa Extratores
    # 2. Executa Extratores
    ext_a = RedeAExtractor(sql_dump_path="dados/rede_a/rede_a_dump.sql")
    ext_b = RedeBExtractor(file_path="dados/rede_b/alunos_rede_b.ndjson")
    ext_c = RedeCExtractor(folder_path="dados/rede_c")
    
    df_a = ext_a.extract()
    df_b = ext_b.extract()
    df_c = ext_c.extract()
    
    # Consolidação dos dados brutos
    raw_consolidated = pd.concat([df_a, df_b, df_c], ignore_index=True)
    
    # 3. Transformação e Validação
    transformer = FrequencyTransformer(calendario_df)
    df_validos, df_invalidos = transformer.transform(raw_consolidated)

   # 4. Carga dos Dados (BigQuery com Fallback Local)
    project_id = os.getenv("GCP_PROJECT_ID", "motriz-desafio")
    dataset_id = os.getenv("GCP_DATASET_ID", "educacao_stg")
    
    # Garante a criação da pasta local de saída
    os.makedirs("resultados", exist_ok=True)
    
    try:
        logger.info(f"Tentando carregar dados no BigQuery (Projeto: {project_id}, Dataset: {dataset_id})...")
        loader = BigQueryLoader(project_id=project_id, dataset_id=dataset_id)
        
        loader.load_table(df_validos, "stg_frequencia_validos", write_disposition="WRITE_TRUNCATE")
        loader.load_table(df_invalidos, "stg_frequencia_invalidos", write_disposition="WRITE_TRUNCATE")
        logger.info("=== DADOS CARREGADOS COM SUCESSO NO BIGQUERY ===")
        
    except Exception as e:
        logger.warning(f"Não foi possível conectar ao BigQuery ({type(e).__name__}).")
        logger.info("Executando fallback: Salvando resultados tratados no diretório local /resultados...")
        
        df_validos.to_csv("resultados/stg_frequencia_validos.csv", index=False)
        df_invalidos.to_csv("resultados/stg_frequencia_invalidos.csv", index=False)
        logger.info("=== PIPELINE EXECUTADO E RESULTADOS SALVOS EM /resultados ===")
  
if __name__ == "__main__":
    run()