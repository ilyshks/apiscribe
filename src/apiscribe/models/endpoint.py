from pydantic import BaseModel
from typing import Optional, Dict


class EndpointModel(BaseModel):

    path: str
    method: str

    request_schema: Optional[dict] = None
    response_schema: Optional[dict] = None

    request_count: int = 0

    request_field_counts: Dict[str, int] = {}