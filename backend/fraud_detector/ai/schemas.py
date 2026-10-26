"""
Unified Banking AI - Gemma 4 Output Schemas & Validation
Defines strict structured output requirements and validation for local Gemma 4 AI inference.
"""

from typing import Dict, Any, List, Tuple

VALID_FRAUD_TYPES = [
    "unauthorized_upi_transaction",
    "card_transaction_dispute",
    "bank_transfer_fraud",
    "account_takeover_suspicion",
    "social_engineering_payment_deception",
    "other_suspected_fraud"
]

class GemmaStructuredOutputSchema:
    """
    Validates and enforces strict structured output from Gemma 4.
    Ensures application logic never relies on unverified free-form AI text.
    """

    @classmethod
    def validate(cls, data: Any) -> Tuple[bool, Dict[str, Any], List[str]]:
        errors = []

        if not isinstance(data, dict):
            return False, {}, ["AI output root must be a valid JSON dictionary."]

        # 1. fraud_type
        fraud_type = str(data.get("fraud_type", "")).strip().lower()
        if fraud_type not in VALID_FRAUD_TYPES:
            # Check for close match or normalize
            normalized = None
            for vt in VALID_FRAUD_TYPES:
                if vt in fraud_type or fraud_type in vt:
                    normalized = vt
                    break
            if normalized:
                fraud_type = normalized
            else:
                fraud_type = "other_suspected_fraud"

        # 2. confidence
        try:
            confidence = float(data.get("confidence", 0.75))
            confidence = max(0.0, min(1.0, round(confidence, 2)))
        except (ValueError, TypeError):
            confidence = 0.70

        # 3. case_summary
        case_summary = str(data.get("case_summary", "")).strip()
        if not case_summary:
            errors.append("Field 'case_summary' is required.")
        else:
            # Ensure case summary contains explicit distinction if missing
            if "CUSTOMER REPORTED" not in case_summary and "Customer reported" not in case_summary:
                case_summary = f"[CUSTOMER REPORTED] {case_summary}"

        # 4. missing_information
        raw_missing = data.get("missing_information", [])
        if not isinstance(raw_missing, list):
            raw_missing = [str(raw_missing)]
        missing_information = [str(item).strip() for item in raw_missing if str(item).strip()]

        # 5. evidence_needed
        raw_evidence = data.get("evidence_needed", [])
        if not isinstance(raw_evidence, list):
            raw_evidence = [str(raw_evidence)]
        evidence_needed = [str(item).strip() for item in raw_evidence if str(item).strip()]

        # 6. inconsistencies
        raw_inconsistencies = data.get("inconsistencies", [])
        if not isinstance(raw_inconsistencies, list):
            raw_inconsistencies = [str(raw_inconsistencies)]
        inconsistencies = [str(item).strip() for item in raw_inconsistencies if str(item).strip()]

        # 7. recommended_actions
        raw_actions = data.get("recommended_actions", [])
        if not isinstance(raw_actions, list):
            raw_actions = [str(raw_actions)]
        recommended_actions = [str(item).strip() for item in raw_actions if str(item).strip()]

        # 8. uncertainty
        uncertainty = str(data.get("uncertainty", "")).strip()
        if not uncertainty:
            uncertainty = "Suspected fraud classification based on preliminary customer intake. Formal adjudication requires issuing and beneficiary bank ledger verification."

        # 9. refund_request_draft
        refund_request_draft = str(data.get("refund_request_draft") or data.get("draft_refund_request") or "").strip()
        if not refund_request_draft:
            refund_request_draft = "DRAFT — NOT YET SUBMITTED\nFormal dispute request notice pending customer authorization."
        elif not refund_request_draft.startswith("DRAFT — NOT YET SUBMITTED"):
            refund_request_draft = f"DRAFT — NOT YET SUBMITTED\n\n{refund_request_draft}"

        validated_payload = {
            "fraud_type": fraud_type,
            "confidence": confidence,
            "case_summary": case_summary,
            "missing_information": missing_information,
            "evidence_needed": evidence_needed,
            "inconsistencies": inconsistencies,
            "inconsistency_detected": len(inconsistencies) > 0,
            "recommended_actions": recommended_actions,
            "uncertainty": uncertainty,
            "refund_request_draft": refund_request_draft,
            "draft_refund_request": refund_request_draft
        }

        is_valid = len(errors) == 0
        return is_valid, validated_payload, errors
