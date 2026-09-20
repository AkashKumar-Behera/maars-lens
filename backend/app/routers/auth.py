from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.enums import UserRole
from app.core.ratelimit import limiter
import httpx
import uuid
import secrets
from app.models.user import Profile as UserProfile, Retailer, Customer
from app.core.security import encrypt_data

router = APIRouter(prefix="", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    # For retailers
    business_name: str | None = None
    address: str | None = None

class RegisterResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    full_name: str

class CustomerRegisterRequest(BaseModel):
    contact_channel: str | None = None

class CustomerRegisterResponse(BaseModel):
    id: uuid.UUID
    customer_code: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user: UserProfile = Depends(get_current_user)
):
    if request.role in [UserRole.admin, UserRole.officer]:
        if not current_user or current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Only admins can create officer/admin accounts")
    
    # In a real app, call Supabase Auth API
    # Here we mock user creation
    user_id = uuid.uuid4()
    
    profile = UserProfile(
        id=user_id,
        email=request.email,
        full_name=request.full_name,
        role=request.role,
        is_active=True
    )
    db.add(profile)
    
    if request.role == UserRole.retailer and request.business_name:
        retailer = Retailer(
            profile_id=user_id,
            business_name=request.business_name,
            address=request.address
        )
        db.add(retailer)
        
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/register/customer", response_model=CustomerRegisterResponse)
async def register_customer(request: CustomerRegisterRequest, db: AsyncSession = Depends(get_db)):
    user_id = uuid.uuid4()
    
    # Generate customer code: CUST-XXXXXX
    random_str = secrets.token_hex(3).upper()
    customer_code = f"CUST-{random_str}"
    
    encrypted_contact = None
    if request.contact_channel:
        encrypted_contact = encrypt_data(request.contact_channel)
        
    customer = Customer(
        id=user_id,
        customer_code=customer_code,
        contact_encrypted=encrypted_contact
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    
    return CustomerRegisterResponse(id=customer.id, customer_code=customer.customer_code)

@router.post("/login", response_model=LoginResponse)
@limiter.limit("20/minute")
async def login(request: Request, payload: LoginRequest):
    # Allowed demo passwords for local development
    valid_passwords = {"Password123!", "MAARS@123"}
    if payload.password not in valid_passwords:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please use 'Password123!' or 'MAARS@123'.",
        )

    # Derive role from email for demo authentication
    role = "customer"
    email_lower = payload.email.lower()
    if "admin" in email_lower:
        role = "admin"
    elif "officer" in email_lower:
        role = "officer"
    elif "retailer" in email_lower:
        role = "retailer"
    
    # Stable demo UUIDs
    role_to_id = {
        "officer": "a0000000-0000-0000-0000-000000000001",
        "admin": "a0000000-0000-0000-0000-000000000002",
        "retailer": "a0000000-0000-0000-0000-000000000003",
        "customer": "a0000000-0000-0000-0000-000000000004",
    }
    user_id = role_to_id.get(role, str(uuid.uuid4()))

    from jose import jwt
    from app.core.config import settings
    token_payload = {
        "sub": user_id,
        "id": user_id,
        "email": payload.email,
        "role": role,
        "user_metadata": {"role": role, "email": payload.email},
        "app_metadata": {"role": role},
    }
    token = jwt.encode(token_payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return LoginResponse(access_token=token, token_type="bearer")

@router.get("/me")
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    return current_user
