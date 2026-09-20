import logging

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body_html: str) -> bool:
    # Use setting.EMAIL_DRY_RUN in a real app
    # Mock behavior
    logger.info(f"DRY RUN: Sending email to {to_email} | Subject: {subject}")
    return True

async def queue_email(db, to_email_encrypted: bytes, subject: str, body_html: str, notification_id=None):
    # Mock email queue
    pass

async def process_email_queue(db):
    pass
