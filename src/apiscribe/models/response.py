from pydantic import BaseModel
from typing import Dict, Optional


class ResponseModel(BaseModel):
    status_code: int
    headers: Dict[str, str]
    body: Optional[dict] = None
