"""
MAARS Lens: Core Services Package
=================================
Exports core SIH prototype services:
- Compliance & Finalization guards
- Report hashing & PDF generation
- Statutory rule engine
"""

from app.services.compliance import (
    assert_inspection_unfinalized,
    InspectionAlreadyFinalizedError,
    InvalidManualReviewError,
    compute_effective_result,
    aggregate_compliance,
    compute_inspection_compliance,
)

from app.services.pdf.generator import (
    compute_report_hash,
    generate_report_pdf,
)

from app.services.rule_engine.engine import (
    evaluate_single_rule,
    evaluate_rules,
    run_audit,
)

from app.core.security import (
    encrypt_data,
    decrypt_data,
    get_aesgcm,
)

__all__ = [
    "assert_inspection_unfinalized",
    "InspectionAlreadyFinalizedError",
    "InvalidManualReviewError",
    "compute_effective_result",
    "aggregate_compliance",
    "compute_inspection_compliance",
    "compute_report_hash",
    "generate_report_pdf",
    "evaluate_single_rule",
    "evaluate_rules",
    "run_audit",
    "encrypt_data",
    "decrypt_data",
    "get_aesgcm",
]
