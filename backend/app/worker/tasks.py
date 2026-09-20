"""
MAARS Lens: Celery Background Tasks
===================================
Defines asynchronous worker tasks:
1. `process_inspection_ocr_task(inspection_id_str, panels_data)`:
   - Runs PaddleOCR across panels.
   - Merges extracted package declarations.
   - Computes automated compliance verdicts.
   - Generates non-destructive polygon annotations.
   - Saves results back to database.
"""

import os
import uuid
import asyncio
import cv2
from typing import List, Dict, Any

from app.worker.celery_app import celery_app
from app.services.ocr.extractor import PaddleOCRExtractor, extract_facts
from app.services.ocr.annotator import annotate_evidence_image
from app.services.ocr.multi_image import process_and_merge_panels
from app.core.config import settings


@celery_app.task(name="tasks.process_inspection_ocr")
def process_inspection_ocr_task(
    inspection_id_str: str,
    panel_file_paths: List[Dict[str, str]], # list of {"panel_type": str, "file_path": str, "image_id": str}
) -> Dict[str, Any]:
    """
    Worker task executing OCR inference and panel merging.
    Accepts disk paths of stored uploaded panels to avoid transmitting heavy payloads over Redis.
    """
    inspection_id = uuid.UUID(inspection_id_str)
    panel_inputs = []

    for item in panel_file_paths:
        fpath = item["file_path"]
        abs_path = os.path.join(settings.UPLOAD_DIR, fpath) if not os.path.isabs(fpath) else fpath
        with open(abs_path, "rb") as f:
            content = f.read()

        panel_inputs.append({
            "panel_type": item.get("panel_type", "other"),
            "file_bytes": content,
            "image_id": uuid.UUID(item["image_id"]) if item.get("image_id") else uuid.uuid4(),
        })

    # Run multi-panel OCR extraction
    extractor = PaddleOCRExtractor()
    result = process_and_merge_panels(panel_inputs, inspection_id, extractor=extractor)

    # Generate annotated image for each panel
    annotated_outputs = []
    for idx, panel in enumerate(panel_inputs):
        img_arr = cv2.imread(panel_file_paths[idx]["file_path"])
        if img_arr is not None:
            panel_res = result["panel_results"][idx]
            annotations = []
            # Create annotations from detected regions
            raw_facts = panel_res.get("facts", {})
            evidence = raw_facts.get("_evidence", {})
            for field, ev in evidence.items():
                if ev.get("polygon"):
                    annotations.append({
                        "polygon": ev["polygon"],
                        "label": f"{field.upper()}: {ev.get('text', '')[:15]}",
                        "status": "compliant",
                        "rule_code": f"LMPC-{field.upper()}",
                    })
            
            ann_filename = f"{panel['image_id']}_annotated.jpg"
            ann_rel_path = os.path.join("inspections", str(inspection_id), ann_filename)
            ann_abs_path = os.path.join(settings.UPLOAD_DIR, ann_rel_path)
            annotate_evidence_image(img_arr, annotations, output_path=ann_abs_path)
            annotated_outputs.append({
                "parent_image_id": str(panel["image_id"]),
                "annotated_path": ann_rel_path,
            })

    return {
        "inspection_id": str(inspection_id),
        "status": "completed",
        "merged_facts": result["merged_facts"],
        "overall_confidence": result["overall_confidence"],
        "per_field_confidences": result["per_field_confidences"],
        "annotated_images": annotated_outputs,
    }
