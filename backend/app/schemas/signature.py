from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class OfficerSignatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    officer_id: UUID
    signature_storage_path: str
    signature_hash: str
    is_active: bool
    uploaded_at: datetime
    disclaimer: str = (
        "Administrative signature asset representation only; "
        "not a legally valid Digital Signature Certificate (DSC) or electronic signature."
    )
