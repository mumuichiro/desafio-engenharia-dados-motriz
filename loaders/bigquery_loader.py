from google.cloud import bigquery
import pandas as pd
from utils.logger import get_logger

logger = get_logger("BigQueryLoader")

class BigQueryLoader:
    def __init__(self, project_id: str, dataset_id: str):
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id

    def load_table(self, df: pd.DataFrame, table_name: str, write_disposition: str = "WRITE_TRUNCATE"):
        table_ref = f"{self.client.project}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            autodetect=True
        )
        
        logger.info(f"Carregando {len(df)} registros em {table_ref}...")
        job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        logger.info(f"Carga concluída com sucesso em {table_ref}.")