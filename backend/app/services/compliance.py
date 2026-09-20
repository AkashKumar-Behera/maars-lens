"""
MAARS Lens: Compliance & Finalization Core Service
=================================================
Implements locked compliance lifecycle rules:
1. assert_inspection_unfinalized(inspection) -> finalization guard.
2. compute_effective_result(...) -> automated + manual review -> effective.
3. aggregate_compliance(...) -> rule results -> overall compliance verdict.
4. compute_inspection_compliance(...) -> automated_compliance & final_compliance.
"""

from typing import Iterable, Optional, Any, Union
from uuid import UUID
from datetime import datetime

from app.models.enums import AuditResultType, ComplianceStatus
from app.models.inspection import Inspection
from app.models.audit import AuditResult


class InspectionAlreadyFinalizedError(ValueError):
    """Raised when attempting to modify or re-finalize a finalized inspection."""
    pass


class InvalidManualReviewError(ValueError):
    """Raised when a manual review submission violates compliance rules."""
    pass


def assert_inspection_unfinalized(inspection: Union[Inspection, bool, Any]) -> None:
    """
    Guard asserting that an inspection is NOT yet finalized.
    Finalized inspections are strictly immutable.
    
    Accepts an Inspection model instance, an object with `is_finalized` attr,
    or a raw boolean flag.
    """
    if hasattr(inspection, "is_finalized"):
        is_finalized = bool(inspection.is_finalized)
    elif isinstance(inspection, bool):
        is_finalized = inspection
    elif isinstance(inspection, dict):
        is_finalized = bool(inspection.get("is_finalized", False))
    else:
        is_finalized = bool(inspection)

    if is_finalized:
        raise InspectionAlreadyFinalizedError(
            "Inspection is finalized and immutable. Modifications are forbidden."
        )


def compute_effective_result(
    automated_result: AuditResultType,
    manual_review_result: Optional[AuditResultType] = None,
    manual_review_reason: Optional[str] = None,
) -> AuditResultType:
    """
    Computes effective_result based on automated_result and optional manual_review_result.
    
    Locked Rules:
    - client cannot directly set effective_result
    - manual_review_reason is mandatory whenever manual_review_result is provided
    - manual_review_result cannot be 'not_applicable'
    - if manual_review_result is present and valid, it overrides to become effective_result
    - otherwise, effective_result equals automated_result
    """
    if manual_review_result is not None:
        if manual_review_result == AuditResultType.not_applicable:
            raise InvalidManualReviewError("not_applicable is not a permissible manual review result.")

        if not manual_review_reason or not manual_review_reason.strip():
            raise InvalidManualReviewError(
                "manual_review_reason is mandatory whenever manual_review_result is provided."
            )

        return manual_review_result

    return automated_result


def aggregate_compliance(results: Iterable[Union[AuditResultType, str]]) -> ComplianceStatus:
    """
    Aggregates individual audit verdicts into an overall ComplianceStatus.
    
    Hierarchy:
    1. If ANY evaluated rule fails -> non_compliant
    2. Else if ANY evaluated rule needs review -> needs_review
    3. If zero applicable rules (empty list or all not_applicable) -> needs_review
       (Locked rule: "no applicable rules -> needs_review")
    4. Else (at least one applicable rule evaluated and all passed) -> compliant
    """
    has_fail = False
    has_needs_review = False
    applicable_count = 0

    for item in results:
        val = item.value if isinstance(item, AuditResultType) else str(item)
        if val == AuditResultType.fail.value:
            has_fail = True
            applicable_count += 1
            break  # Short-circuit: failure dominates
        elif val == AuditResultType.needs_review.value:
            has_needs_review = True
            applicable_count += 1
        elif val == AuditResultType.pass_.value:
            applicable_count += 1
        # 'not_applicable' does not increment applicable_count

    if has_fail:
        return ComplianceStatus.non_compliant
    if has_needs_review:
        return ComplianceStatus.needs_review
    if applicable_count == 0:
        return ComplianceStatus.needs_review
    return ComplianceStatus.compliant


def compute_inspection_compliance(
    audit_results: Iterable[Union[AuditResult, dict, Any]]
) -> tuple[ComplianceStatus, ComplianceStatus]:
    """
    Computes both dual-layer compliance verdicts for an inspection:
    - automated_compliance: aggregated purely from automated_result values
    - final_compliance: aggregated purely from effective_result values
    
    Returns:
        tuple of (automated_compliance, final_compliance)
    """
    automated_list: list[AuditResultType] = []
    effective_list: list[AuditResultType] = []

    for item in audit_results:
        if isinstance(item, dict):
            auto_val = item.get("automated_result")
            eff_val = item.get("effective_result")
        else:
            auto_val = getattr(item, "automated_result", None)
            eff_val = getattr(item, "effective_result", None)

        if auto_val is not None:
            automated_list.append(auto_val)
        if eff_val is not None:
            effective_list.append(eff_val)

    automated_compliance = aggregate_compliance(automated_list)
    final_compliance = aggregate_compliance(effective_list)

    return automated_compliance, final_compliance
