from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID
from app.models.enums import UserRole, ContactChannelType

class RegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    email: EmailStr
    password: str
    role: UserRole
    full_name: str
    phone: str
    employee_id: Optional[str] = None
    business_name: Optional[str] = None
    shop_address: Optional[str] = None
    area_id: Optional[UUID] = None
    license_number: Optional[str] = None

class CustomerSessionHandshake(BaseModel):
    """
    Handshake after Supabase Anonymous Auth signInAnonymously().
    customer_code is purely a human-readable display reference.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    contact_channel: Optional[str] = None
    contact_channel_type: ContactChannelType = ContactChannelType.none

class CustomerSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    customer_code: str # Reference code for looking up status
    message: str

class LoginRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    email: EmailStr
    password: str


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    employee_id: Optional[str] = None
    is_active: bool
    onboarding_completed: bool
    business_name: Optional[str] = None
    shop_address: Optional[str] = None
    area_id: Optional[UUID] = None
    customer_code: Optional[str] = None

class RegisterResponse(BaseModel):
    user_id: UUID
    role: UserRole
    message: str

