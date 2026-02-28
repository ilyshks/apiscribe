from pydantic import BaseModel
from typing import Optional


class EndpointModel(BaseModel):
    path: str
    method: str
    request_schema: Optional[dict] = None
    response_schema: Optional[dict] = None
