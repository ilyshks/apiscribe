from pydantic import BaseModel
from typing import Dict, Optional


class RequestModel(BaseModel):
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[dict] = None
