"""
MAARS Lens: Statutory Rules Loader
==================================
Loads externalized Legal Metrology rule configurations from JSON/DB.
- All rules contain rule_code, source_reference, description, check_definition,
  severity, active flag, version, and default legal_verified=False.
- Never hardcodes legal thresholds into python code.
"""

import json
import os
from typing import List, Dict, Any

from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.models.enums import RuleType, SeverityLevel, RuleVerificationStatus
from uuid import uuid4


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "statutory_rules.json")


def load_statutory_rules_config() -> List[Dict[str, Any]]:
    """Loads raw rule definitions from the external configuration file."""
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rules", [])


def build_statutory_rule_entities(author_id: Any = None) -> List[ComplianceRuleVersion]:
    """
    Constructs in-memory ComplianceRuleVersion entities linked to ComplianceRule
    from the externalized statutory configuration.
    """
    admin_id = author_id or uuid4()
    raw_rules = load_statutory_rules_config()
    entities: List[ComplianceRuleVersion] = []

    type_mapping = {
        "presence": RuleType.presence,
        "pattern": RuleType.pattern,
        "computed": RuleType.computed,
        "visual": RuleType.visual,
    }

    severity_mapping = {
        "critical": SeverityLevel.critical,
        "major": SeverityLevel.major,
        "minor": SeverityLevel.minor,
        "info": SeverityLevel.info,
    }

    for r in raw_rules:
        rule_obj = ComplianceRule(
            id=uuid4(),
            rule_code=r["rule_code"],
            category=r.get("category", "General"),
        )

        rtype = type_mapping.get(r.get("rule_type", "presence"), RuleType.presence)
        sev = severity_mapping.get(r.get("severity", "major"), SeverityLevel.major)
        is_verified = r.get("legal_verified", False)
        vstatus = RuleVerificationStatus.verified if is_verified else RuleVerificationStatus.demo

        # Embed exemptions into check_definition
        check_def = dict(r.get("check_definition", {}))
        if "exemptions" in r:
            check_def["exemptions"] = r["exemptions"]

        version_obj = ComplianceRuleVersion(
            id=uuid4(),
            rule_id=rule_obj.id,
            version=r.get("version", 1),
            statutory_reference=r.get("source_reference", r["rule_code"]),
            rule_type=rtype,
            target_field=r.get("target_field", "unknown"),
            check_definition=check_def,
            severity=sev,
            description_en=r.get("description", ""),
            failure_message_template=f"{r.get('description', '')} missing or non-compliant.",
            requires_visual_measurement=(rtype == RuleType.visual),
            measurement_unit="mm" if rtype == RuleType.visual else None,
            verification_status=vstatus,
            is_active=r.get("active", True),
            created_by=admin_id,
        )
        version_obj.rule = rule_obj
        entities.append(version_obj)

    return entities
