from pydantic import BaseModel, Field
from typing import Optional, Dict


class EndpointModel(BaseModel):

    path: str
    method: str

    request_schema: Optional[dict] = None

    responses: Dict[int, dict] = Field(default_factory=dict)

    request_count: int = 1

    request_field_counts: Dict[str, int] = Field(default_factory=dict)