from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.models.notification import Notification

async def create_notification(db: AsyncSession, user_id: uuid.UUID, title: str, message: str, notification_type: str, reference_type: str = None, reference_id: uuid.UUID = None) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        reference_type=reference_type,
        reference_id=reference_id
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif

async def notify_violation(db: AsyncSession, violation, inspection) -> list[str]:
    targets = []
    if violation.retailer_id:
        await create_notification(
            db, violation.retailer_id, "Violation Issued",
            f"A violation has been issued for your establishment.",
            "violation", "violation", violation.id
        )
        targets.append("retailer")
    
    # Area officer mock
    targets.append("area_officer_email")
    return targets
