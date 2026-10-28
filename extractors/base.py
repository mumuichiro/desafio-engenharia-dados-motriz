from abc import ABC, abstractmethod
import pandas as pd

class BaseExtractor(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Extrai os dados da fonte e devolve um DataFrame padronizado."""
        pass