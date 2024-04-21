from pydantic import BaseModel
from typing import List, Dict

class DreamSymbolList(BaseModel):
    symbols: List[str]

class SymbolsUrls(BaseModel):
    data: Dict[str, str]