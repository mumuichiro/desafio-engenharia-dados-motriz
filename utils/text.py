import unicodedata
import re
import pandas as pd

def sanitize_name(text: str | None) -> str | None:
    """
    Atende à Regra R4:
    - Converte para minúsculas
    - Remove acentuação e diacríticos
    - Remove espaços extras no início/fim e no meio da string
    """
    if not text or not isinstance(text, str):
        return None
    
    nfd_text = unicodedata.normalize('NFD', text)
    clean_text = ''.join(char for char in nfd_text if unicodedata.category(char) != 'Mn')
    
    clean_text = clean_text.lower().strip()
    return re.sub(r'\s+', ' ', clean_text)


def normalize_inep(inep_val: str | int | float | None) -> str | None:
    """
    Atende à Regra R7:
    Normaliza o código INEP para exatamente 8 dígitos numéricos.
    """
    if inep_val is None or pd.isna(inep_val):
        return None
    
    digits = re.sub(r'\D', '', str(inep_val).split('.')[0])
    if not digits:
        return None
    
    return digits.zfill(8)