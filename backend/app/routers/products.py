import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.inspection import Inspection
from app.models.enums import ComplianceStatus, InspectionStatus

router = APIRouter(prefix="", tags=["products"])


class InspectionSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: uuid.UUID
    created_at: datetime
    status: InspectionStatus
    automated_compliance: Optional[ComplianceStatus] = None
    final_compliance: Optional[ComplianceStatus] = None
    is_finalized: bool


class ProductHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    barcode: Optional[str] = None
    manufacturer_name: Optional[str] = None
    total_inspections: int
    inspections: List[InspectionSummaryItem]


@router.get("/{product_id}/history", response_model=ProductHistoryResponse)
async def get_product_history(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves the inspection history for a specific product.
    Shows past inspection verdicts (automated and final compliance) for repeat scan tracking.
    """
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found.",
        )

    # Fetch associated inspections
    insp_stmt = (
        select(Inspection)
        .where(Inspection.product_id == product_id)
        .order_by(Inspection.created_at.desc())
    )
    insp_result = await db.execute(insp_stmt)
    inspections = insp_result.scalars().all()

    inspection_items = [
        InspectionSummaryItem(
            inspection_id=i.id,
            created_at=i.created_at,
            status=i.status,
            automated_compliance=i.automated_compliance,
            final_compliance=i.final_compliance,
            is_finalized=i.is_finalized,
        )
        for i in inspections
    ]

    return ProductHistoryResponse(
        product_id=product.id,
        brand_name=product.brand_name,
        product_name=product.product_name,
        barcode=product.barcode,
        manufacturer_name=product.manufacturer_name,
        total_inspections=len(inspection_items),
        inspections=inspection_items,
    )
