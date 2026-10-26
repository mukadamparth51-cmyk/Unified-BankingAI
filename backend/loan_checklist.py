"""
Unified Banking AI - Module 3: Smart Loan Predictor Checklist Engine
Performs secure cross-module document validation from Smart ID.
Enforces required document checklists per loan type, detects missing/expired/rejected documents,
and acts as the authoritative gatekeeper before credit risk underwriting can proceed.
"""

from typing import Dict, Any, List, Optional
from datetime import date

from smart_id_docs import SmartIDDocumentService

LOAN_DOCUMENT_CONFIG = {
    "Personal Loan": {
        "name": "Personal Loan",
        "description": "Unsecured personal loan for salaried individuals and professionals.",
        "max_amount": 1500000.0,
        "required_documents": [
            {"type": "PAN Card", "category": "Mandatory Tax Identity", "description": "Government issued PAN card for income tax tracing"},
            {"type": "Aadhaar Card", "category": "Address & KYC Proof", "description": "UIDAI masked Aadhaar card for KYC verification"},
            {"type": "Salary Slip", "category": "Income Proof", "description": "Recent 3-month salary statement showing net earnings"},
            {"type": "Bank Statement", "category": "Banking Financials", "description": "Latest 6-month primary operative bank account statement"}
        ]
    },
    "Home Loan": {
        "name": "Home Loan",
        "description": "Secured residential mortgage and property financing.",
        "max_amount": 10000000.0,
        "required_documents": [
            {"type": "PAN Card", "category": "Mandatory Tax Identity", "description": "Primary applicant PAN card"},
            {"type": "Aadhaar Card", "category": "Permanent Address Proof", "description": "UIDAI masked Aadhaar or Voter ID"},
            {"type": "ITR / Form 16", "category": "Tax Returns (2 Years)", "description": "Income Tax Returns with computation of total income"},
            {"type": "Bank Statement", "category": "12-Month Operative Account", "description": "Full 12-month bank statement showing regular inflows"}
        ]
    },
    "Vehicle Loan": {
        "name": "Vehicle Loan",
        "description": "Secured automobile financing for two-wheelers and four-wheelers.",
        "max_amount": 2500000.0,
        "required_documents": [
            {"type": "PAN Card", "category": "Mandatory Tax Identity", "description": "Permanent Account Number verification"},
            {"type": "Aadhaar Card", "category": "Resident Address Proof", "description": "Aadhaar Card or Passport address page"},
            {"type": "Salary Slip", "category": "Income Verification", "description": "Current employer pay slip with PF deductions"},
            {"type": "Bank Statement", "category": "6-Month Statement", "description": "Salary crediting bank account statement"}
        ]
    },
    "Business / MSME Loan": {
        "name": "Business / MSME Loan",
        "description": "Commercial business term loans and working capital credit lines.",
        "max_amount": 5000000.0,
        "required_documents": [
            {"type": "PAN Card", "category": "Business / Promoter Identity", "description": "Proprietorship or Company PAN"},
            {"type": "ITR / Form 16", "category": "Audited Financials", "description": "Past 2-year business ITR and balance sheet"},
            {"type": "Bank Statement", "category": "12-Month Current Account", "description": "Primary business current account statement"},
            {"type": "Utility Bill / Address Proof", "category": "Principal Business Place", "description": "Electricity or broadband utility bill (< 2 months)"}
        ]
    },
    "Instant Fast-Track Loan (LoanFast 72)": {
        "name": "Instant Fast-Track Loan (LoanFast 72)",
        "description": "High-velocity algorithmic pre-approval with guaranteed 72-hour turnaround.",
        "max_amount": 500000.0,
        "required_documents": [
            {"type": "PAN Card", "category": "Mandatory Tax Identity", "description": "Instant CIBIL & NSDL PAN validation"},
            {"type": "Aadhaar Card", "category": "UIDAI Biometric / KYC", "description": "Aadhaar XML / Masked PDF for instant e-KYC"},
            {"type": "Salary Slip", "category": "Current Pay Slip", "description": "Latest pay slip confirming monthly disposable income"}
        ]
    }
}

class LoanChecklistEngine:
    """
    Evaluates customer document completeness and validity prior to credit risk underwriting.
    Blocks evaluation when required documents are missing, expired, or rejected.
    """

    @classmethod
    def get_supported_loan_types(cls) -> List[Dict[str, Any]]:
        return [
            {
                "loan_type": k,
                "name": v["name"],
                "description": v["description"],
                "max_amount": v["max_amount"],
                "required_count": len(v["required_documents"]),
                "required_types": [d["type"] for d in v["required_documents"]]
            }
            for k, v in LOAN_DOCUMENT_CONFIG.items()
        ]

    @classmethod
    def evaluate_checklist(
        cls,
        customer_id: str,
        loan_type: str = "Instant Fast-Track Loan (LoanFast 72)",
        actor_id: Optional[str] = None,
        actor_role: str = "customer"
    ) -> Dict[str, Any]:
        """
        Cross-examines the customer's Smart ID documents against statutory requirements for the loan type.
        """
        if loan_type not in LOAN_DOCUMENT_CONFIG:
            loan_type = "Instant Fast-Track Loan (LoanFast 72)"

        config = LOAN_DOCUMENT_CONFIG[loan_type]
        required_specs = config["required_documents"]

        if not actor_id:
            actor_id = customer_id

        # Securely retrieve customer documents from Smart ID with RLS
        docs = SmartIDDocumentService.get_customer_documents(customer_id, actor_id, actor_role)
        docs_by_type = {d["document_type"]: d for d in docs}

        checklist_items = []
        blocking_reasons = []
        today_str = date.today().strftime("%Y-%m-%d")

        missing_count = 0
        expired_count = 0
        rejected_count = 0
        pending_count = 0
        verified_count = 0

        for req in required_specs:
            doc_type = req["type"]
            category = req["category"]
            description = req["description"]

            if doc_type not in docs_by_type:
                missing_count += 1
                item_status = "missing"
                badge = "MISSING"
                action_needed = f"Upload {doc_type} in Smart ID Document Vault."
                blocking_reasons.append(f"Missing Document: {doc_type} is required for {loan_type} ({category}).")
                doc_metadata = None
            else:
                doc = docs_by_type[doc_type]
                doc_metadata = {
                    "document_id": doc["id"],
                    "original_filename": doc["original_filename"],
                    "file_size": doc["file_size"],
                    "file_hash": doc["file_hash"],
                    "upload_date": doc["upload_date"],
                    "expiry_date": doc.get("expiry_date"),
                    "version": doc.get("version", 1),
                    "rejection_reason": doc.get("rejection_reason")
                }

                # Check expiry
                if doc.get("expiry_date") and doc["expiry_date"] < today_str:
                    expired_count += 1
                    item_status = "expired"
                    badge = "EXPIRED"
                    action_needed = f"Document expired on {doc['expiry_date']}. Please upload replacement in Smart ID."
                    blocking_reasons.append(f"Expired Document: {doc_type} expired on {doc['expiry_date']}. Must be replaced before assessment.")
                elif doc["verification_status"] == "rejected":
                    rejected_count += 1
                    item_status = "rejected"
                    badge = "REJECTED"
                    reason = doc.get("rejection_reason") or "Quality or compliance check failed"
                    action_needed = f"Rejected: {reason}. Upload compliant replacement in Smart ID."
                    blocking_reasons.append(f"Rejected Document: {doc_type} was rejected ({reason}).")
                elif doc["verification_status"] in ["pending_verification", "uploaded"]:
                    pending_count += 1
                    item_status = doc["verification_status"]
                    badge = "PENDING REVIEW"
                    action_needed = "Document present. Awaiting final verification by Bank Manager."
                elif doc["verification_status"] == "verified":
                    verified_count += 1
                    item_status = "verified"
                    badge = "VERIFIED"
                    action_needed = "Compliant and verified."
                else:
                    item_status = doc["verification_status"]
                    badge = item_status.upper()
                    action_needed = "Review required."

            checklist_items.append({
                "document_type": doc_type,
                "category": category,
                "description": description,
                "status": item_status,
                "badge": badge,
                "action_needed": action_needed,
                "is_blocking": item_status in ["missing", "expired", "rejected"],
                "document": doc_metadata
            })

        # Eligibility assessment can proceed ONLY if zero missing, zero expired, and zero rejected documents
        can_proceed = (missing_count == 0 and expired_count == 0 and rejected_count == 0)

        if can_proceed:
            summary_message = "All required documents are present and valid. Proceed to Credit Risk Underwriting and Bank Manager Review."
            summary_status = "READY_FOR_EVALUATION"
        else:
            summary_message = f"Document checklist incomplete. {len(blocking_reasons)} item(s) require customer attention before loan evaluation can proceed."
            summary_status = "DOCUMENTS_REQUIRED"

        return {
            "customer_id": customer_id,
            "loan_type": loan_type,
            "loan_name": config["name"],
            "loan_description": config["description"],
            "max_loan_amount": config["max_amount"],
            "can_proceed": can_proceed,
            "summary_status": summary_status,
            "summary_message": summary_message,
            "counts": {
                "total_required": len(required_specs),
                "verified": verified_count,
                "pending": pending_count,
                "missing": missing_count,
                "expired": expired_count,
                "rejected": rejected_count
            },
            "blocking_reasons": blocking_reasons,
            "checklist": checklist_items,
            "regulatory_disclaimer": (
                "Do not treat document presence as proof of authenticity or guarantee loan approval. "
                "Document checklist completion enables algorithmic underwriting and bank manager review. "
                "Final credit decision is based on credit bureau score, debt-to-income analysis, and authorized review."
            )
        }
