"""
MAARS Lens: Rule Engine Service
==============================
Evaluates statutory compliance rule versions against extracted package facts,
visual measurements, and OCR confidences.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sqlalchemy.orm import selectinload

from app.models.enums import AuditResultType, RuleType, SeverityLevel
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.services.rule_engine.evaluators import evaluate_rule_check
from app.services.rule_engine.exemptions import check_package_exemption


def _get_rule_code(rule_version: ComplianceRuleVersion) -> str:
    """Safely extracts rule_code from linked ComplianceRule or direct attribute fallback."""
    if hasattr(rule_version, "rule") and rule_version.rule and hasattr(rule_version.rule, "rule_code"):
        return rule_version.rule.rule_code
    if hasattr(rule_version, "rule_code"):
        return str(rule_version.rule_code)
    return str(rule_version.rule_id)


def evaluate_single_rule(
    rule_version: ComplianceRuleVersion,
    facts: Dict[str, Any],
    visual_measurements: Optional[Dict[str, Any]] = None,
    ocr_confidences: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluates an individual ComplianceRuleVersion against provided package observations.
    
    Returns a dictionary structured for creating an AuditResult entity.
    """
    check_def = rule_version.check_definition or {}
    operator = check_def.get("operator", "exists")
    target_field = rule_version.target_field
    rule_type = rule_version.rule_type
    code = _get_rule_code(rule_version)

    facts = facts or {}
    ocr_confidences = ocr_confidences or {}
    visual_measurements = visual_measurements or {}

    # 0. Check statutory package exemption
    is_exempt, exempt_reason = check_package_exemption(code, check_def, facts)
    if is_exempt:
        return {
            "rule_version_id": rule_version.id,
            "rule_code": code,
            "rule_version": rule_version.version,
            "statutory_reference": rule_version.statutory_reference,
            "automated_result": AuditResultType.not_applicable,
            "effective_result": AuditResultType.not_applicable,
            "actual_value": str(facts.get(target_field)) if facts.get(target_field) is not None else None,
            "expected_value": "Exempted",
            "fact_confidence": 1.0,
            "measurement_reliable": True,
            "automated_reason": exempt_reason or f"Package exempted from rule '{code}' under statutory provisions.",
            "severity": rule_version.severity,
        }

    # 0b. Data-driven conditional applicability guard (e.g. is_imported, is_multi_pack, requires_dimensions_or_count)
    applicable_flag = check_def.get("applicable_if_flag")
    if applicable_flag and not bool(facts.get(applicable_flag, False)):
        return {
            "rule_version_id": rule_version.id,
            "rule_code": code,
            "rule_version": rule_version.version,
            "statutory_reference": rule_version.statutory_reference,
            "automated_result": AuditResultType.not_applicable,
            "effective_result": AuditResultType.not_applicable,
            "actual_value": str(facts.get(target_field)) if facts.get(target_field) is not None else None,
            "expected_value": f"Applicable only when '{applicable_flag}' is declared",
            "fact_confidence": 1.0,
            "measurement_reliable": True,
            "automated_reason": f"Rule not applicable: package does not exhibit condition '{applicable_flag}'.",
            "severity": rule_version.severity,
        }

    actual_value = facts.get(target_field)
    field_present = target_field in facts and actual_value is not None

    # Determine confidence score
    confidence: Optional[float] = None
    if field_present:
        confidence = float(ocr_confidences.get(target_field, 1.0))
    elif target_field in ocr_confidences:
        confidence = float(ocr_confidences[target_field])

    # 1. Visual measurement requirement check
    if rule_version.requires_visual_measurement or rule_type == RuleType.visual:

        text_regions = visual_measurements.get("text_regions", [])
        matching_region = next((r for r in text_regions if r.get("label") == target_field), None)
        
        is_reliable = bool(matching_region.get("measurement_reliable", False)) if matching_region else False
        if not is_reliable:
            return {
                "rule_version_id": rule_version.id,
                "rule_code": code,
                "rule_version": rule_version.version,
                "statutory_reference": rule_version.statutory_reference,
                "automated_result": AuditResultType.needs_review,
                "effective_result": AuditResultType.needs_review,
                "actual_value": str(actual_value) if actual_value is not None else None,
                "expected_value": str(check_def.get("value") or "Visual measurement required"),
                "fact_confidence": confidence,
                "measurement_reliable": False,
                "automated_reason": "Visual measurement not reliable or physical scaling unverified; requires manual review.",
                "severity": rule_version.severity,
            }

    # 2. Confidence threshold evaluation (for non-visual rules)
    confidence_threshold = check_def.get("confidence_threshold", 0.50)
    if field_present and confidence is not None and confidence < confidence_threshold:
        return {
            "rule_version_id": rule_version.id,
            "rule_code": code,
            "rule_version": rule_version.version,
            "statutory_reference": rule_version.statutory_reference,
            "automated_result": AuditResultType.needs_review,
            "effective_result": AuditResultType.needs_review,
            "actual_value": str(actual_value),
            "expected_value": str(check_def.get("value") or "Valid declaration"),
            "fact_confidence": confidence,
            "measurement_reliable": True,
            "automated_reason": f"Low OCR confidence ({confidence:.2f}) for field '{target_field}' below threshold ({confidence_threshold:.2f}); manual verification required.",
            "severity": rule_version.severity,
        }

    # 3. Handle missing field when not presence check
    if not field_present and operator not in ("exists", "not_empty", "not_null", "present"):
        if rule_type == RuleType.presence:
            automated_result = AuditResultType.fail
            reason = rule_version.failure_message_template or f"Mandatory declaration '{target_field}' missing from package."
        else:
            automated_result = AuditResultType.not_applicable
            reason = f"Target field '{target_field}' not found on package; rule not applicable."

        return {
            "rule_version_id": rule_version.id,
            "rule_code": code,
            "rule_version": rule_version.version,
            "statutory_reference": rule_version.statutory_reference,
            "automated_result": automated_result,
            "effective_result": automated_result,
            "actual_value": None,
            "expected_value": str(check_def.get("value") or "Present"),
            "fact_confidence": confidence or 0.0,
            "measurement_reliable": True,
            "automated_reason": reason,
            "severity": rule_version.severity,
        }

    # 4. Standard operator evaluation
    passed, expected_repr, error_detail = evaluate_rule_check(
        operator=operator,
        check_definition=check_def,
        actual_value=actual_value,
        facts=facts,
        visual_measurements=visual_measurements,
    )

    if passed:
        automated_result = AuditResultType.pass_
        reason = "Declaration complies with statutory requirement."
    else:
        automated_result = AuditResultType.fail
        reason = error_detail or rule_version.failure_message_template or f"Declaration fails rule '{rule_version.statutory_reference}'."


    return {
        "rule_version_id": rule_version.id,
        "rule_code": code,
        "rule_version": rule_version.version,
        "statutory_reference": rule_version.statutory_reference,
        "automated_result": automated_result,
        "effective_result": automated_result,
        "actual_value": str(actual_value) if actual_value is not None else None,
        "expected_value": expected_repr,
        "fact_confidence": confidence,
        "measurement_reliable": True,
        "automated_reason": reason,
        "severity": rule_version.severity,
    }


def evaluate_rules(
    rule_versions: List[ComplianceRuleVersion],
    facts: Dict[str, Any],
    visual_measurements: Optional[Dict[str, Any]] = None,
    ocr_confidences: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Evaluates a batch of ComplianceRuleVersion models synchronously."""
    return [
        evaluate_single_rule(
            rule_version=rv,
            facts=facts,
            visual_measurements=visual_measurements,
            ocr_confidences=ocr_confidences,
        )
        for rv in rule_versions
    ]


async def run_audit(
    facts: Dict[str, Any],
    visual_measurements: Optional[Dict[str, Any]],
    ocr_confidences: Optional[Dict[str, float]],
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    """
    Queries all active ComplianceRuleVersion records from the DB and runs compliance evaluation.
    Only active versions (is_active == True) are evaluated.
    """
    stmt = (
        select(ComplianceRuleVersion)
        .options(selectinload(ComplianceRuleVersion.rule))
        .where(ComplianceRuleVersion.is_active == True)
        .order_by(ComplianceRuleVersion.created_at.asc())
    )
    result = await db.execute(stmt)
    active_versions = result.scalars().all()

    return evaluate_rules(
        rule_versions=active_versions,
        facts=facts,
        visual_measurements=visual_measurements,
        ocr_confidences=ocr_confidences,
    )

