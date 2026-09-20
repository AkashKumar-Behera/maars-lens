from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ReportVerificationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    inspection_id: UUID
    report_hash: str

class ReportVerificationResponse(BaseModel):
    """
    Public-safe verification response.
    Exposes only safe verification metadata, never raw signatures or sensitive internal artifacts.
    """
    model_config = ConfigDict(from_attributes=True)

    report_hash: str
    is_valid: bool
    verified_at: datetime
    disclaimer: str = (
        "LEGAL DISCLAIMER: The inspecting officer signature representation embedded in this report "
        "is an administrative visual record asset stored for platform verification and tamper-evidence hashing. "
        "It does NOT constitute a legally valid Digital Signature Certificate (DSC) or an electronic signature "
        "under the Information Technology Act or applicable statutory provisions."
    )


