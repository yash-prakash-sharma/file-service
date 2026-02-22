from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class FileResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    content_type: Optional[str] = None
    size: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
