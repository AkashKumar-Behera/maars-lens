"""
MAARS Lens: Celery Worker & Security Hardening Unit Tests
=========================================================
Tests for Batch 3:
1. Multi-claim role extraction (user_metadata, app_metadata, root claims).
2. Image security verification (15MB file size limit, path traversal defense).
3. Celery worker task execution logic (direct execution).
"""

import os
import uuid
import pytest
from fastapi import HTTPException

from app.core.auth import get_current_user, require_role
from app.services.ocr.multi_image import validate_and_hash_image
from app.worker.tasks import process_inspection_ocr_task


def test_auth_claim_extraction():
    """Verify require_role inspects user_metadata, app_metadata, and root claim."""
    # Test 1: Role in app_metadata
    user_app_meta = {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "officer@maars.gov.in",
        "app_metadata": {"role": "officer"},
    }
    officer_checker = require_role("officer")
    validated = officer_checker(user_app_meta)
    assert validated["id"] == user_app_meta["id"]

    # Test 2: Role in user_metadata
    user_user_meta = {
        "id": "22222222-2222-2222-2222-222222222222",
        "email": "admin@maars.gov.in",
        "user_metadata": {"role": "admin"},
    }
    admin_checker = require_role("admin")
    validated_admin = admin_checker(user_user_meta)
    assert validated_admin["id"] == user_user_meta["id"]

    # Test 3: Role in root
    user_root = {
        "id": "33333333-3333-3333-3333-333333333333",
        "email": "officer2@maars.gov.in",
        "role": "officer",
    }
    validated_root = officer_checker(user_root)
    assert validated_root["id"] == user_root["id"]

    # Test 4: Insufficient role
    unauth_user = {
        "id": "44444444-4444-4444-4444-444444444444",
        "email": "customer",
        "role": "customer",
    }
    with pytest.raises(HTTPException) as exc:
        officer_checker(unauth_user)
    assert exc.value.status_code == 403


def test_upload_security_filename_sanitization():
    """Verify filename traversal attacks are sanitized and valid relative path returned."""
    from app.services.ocr.multi_image import save_image_to_storage
    sample_content = b"Mock image bytes for testing upload validation"
    
    # Path traversal attack filename
    malicious_filename = "../../../etc/passwd.jpg"
    inspection_id = uuid.uuid4()
    saved_rel_path = save_image_to_storage(sample_content, inspection_id, malicious_filename)
    
    assert "passwd.jpg" in saved_rel_path
    assert ".." not in saved_rel_path
    assert str(inspection_id) in saved_rel_path


def test_upload_security_oversized_file():
    """Verify files larger than 15MB are strictly rejected."""
    oversized_len = 15 * 1024 * 1024 + 1024
    
    class FakeOversizedBytes:
        def __len__(self):
            return oversized_len
        def startswith(self, prefix):
            return False

    with pytest.raises(ValueError) as exc:
        validate_and_hash_image(FakeOversizedBytes())
    assert "15MB" in str(exc.value)


def test_celery_task_execution(tmp_path):
    """Verify process_inspection_ocr_task executes cleanly with fixture data."""
    fixture_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "fixtures", "labels", "01_compliant_bilingual.png")
    )
    assert os.path.exists(fixture_path)

    inspection_id = str(uuid.uuid4())
    img_id = str(uuid.uuid4())
    
    panel_info = [{
        "panel_type": "front",
        "file_path": fixture_path,
        "image_id": img_id,
    }]

    # Directly execute task function (synchronous invocation of Celery task logic)
    result = process_inspection_ocr_task(inspection_id, panel_info)
    
    assert result["inspection_id"] == inspection_id
    assert result["status"] == "completed"
    assert "merged_facts" in result
    assert "overall_confidence" in result
    assert result["overall_confidence"] > 0.5
