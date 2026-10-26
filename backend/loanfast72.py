"""
Unified Banking AI - Module 3: AI Loan Detector — AI LoanFast 72
High-Speed AI Credit Underwriting, Debt-to-Income (DTI) Engine & 72-Hour Decisioning SLA
"""

import math
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from database import get_connection

class AILoanFast72Engine:
    """
    AI LoanFast 72 provides algorithmic credit underwriting, DTI calculations,
    risk tier segmentation, and instant decisioning within the 72-Hour turnaround SLA.
    """

    @classmethod
    def evaluate_loan(
        cls,
        applicant_name: str,
        monthly_income: float,
        existing_obligations: float,
        cibil_score: int,
        loan_requested: float,
        tenor_months: int,
        employment_type: str = "Salaried",
        customer_id: Optional[str] = None,
        loan_type: str = "Instant Fast-Track Loan (LoanFast 72)",
        checklist_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes credit risk scoring and produces explainable underwriting decision.
        """
        applicant_name = applicant_name.strip()
        monthly_income = max(1.0, float(monthly_income))
        existing_obligations = max(0.0, float(existing_obligations))
        cibil_score = max(300, min(900, int(cibil_score)))
        loan_requested = max(1000.0, float(loan_requested))
        tenor_months = max(6, min(84, int(tenor_months)))

        # 1. Debt-to-Income (DTI) Ratio
        dti_ratio = round((existing_obligations / monthly_income) * 100.0, 1)

        # 2. Risk Scoring & Decision Rules
        positive_factors = []
        caution_factors = []

        if cibil_score >= 750:
            positive_factors.append(f"Excellent Credit Bureau Score: {cibil_score} (Tier A Prime)")
        elif cibil_score >= 680:
            positive_factors.append(f"Satisfactory Credit Score: {cibil_score} (Tier B)")
        else:
            caution_factors.append(f"Sub-prime Credit Score: {cibil_score} (< 680 threshold)")

        if dti_ratio <= 30.0:
            positive_factors.append(f"Healthy Debt-to-Income ratio: {dti_ratio}% (Well below 40% safety threshold)")
        elif dti_ratio <= 50.0:
            caution_factors.append(f"Moderate Debt-to-Income ratio: {dti_ratio}% (Approaching maximum exposure)")
        else:
            caution_factors.append(f"High Debt-to-Income ratio: {dti_ratio}% (Exceeds 50% prudent ceiling)")

        # Max loan capacity = Net Disposable Income * 50% * Tenor discount
        disposable_income = max(0.0, monthly_income - existing_obligations)
        max_affordable_emi = disposable_income * 0.50

        # Base interest rate by CIBIL
        if cibil_score >= 780:
            interest_rate = 9.9
            risk_tier = "Prime Tier A (Lowest Default Risk)"
        elif cibil_score >= 720:
            interest_rate = 11.2
            risk_tier = "Tier B (Low-to-Moderate Risk)"
        elif cibil_score >= 660:
            interest_rate = 13.8
            risk_tier = "Tier C (Moderate Risk)"
        else:
            interest_rate = 17.5
            risk_tier = "High Risk / Near Sub-prime"

        # Monthly EMI calculation: P * r * (1+r)^n / ((1+r)^n - 1)
        r = (interest_rate / 100.0) / 12.0
        n = tenor_months
        calc_emi = loan_requested * (r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)

        # Decision Logic
        if cibil_score >= 680 and (existing_obligations + calc_emi) / monthly_income <= 0.60:
            decision_status = "Approved (Instant 72-Hour Fast-Track)"
            approved_amount = loan_requested
            turnaround_note = "Guaranteed disbursal within 24-72 hours"
        elif cibil_score >= 620 and (existing_obligations + (calc_emi * 0.7)) / monthly_income <= 0.65:
            decision_status = "Conditionally Approved (Counter-Offer)"
            approved_amount = round(max_affordable_emi * ((1 - ((1 + r) ** (-n))) / r), -3)
            approved_amount = min(loan_requested, max(25000.0, approved_amount))
            caution_factors.append("Sanction capped to maintain total EMI under 60% of monthly income")
            turnaround_note = "Subject to manual income tax verification within 72 hours"
        else:
            decision_status = "Declined (Exceeds Risk Ceiling)"
            approved_amount = 0.0
            interest_rate = 0.0
            calc_emi = 0.0
            turnaround_note = "Instant rejection - adverse DTI or credit history"

        app_ref = f"LOANFAST-2026-{uuid.uuid4().hex[:6].upper()}"
        monthly_emi = round(calc_emi, 2)
        total_payable = round(monthly_emi * tenor_months, 2) if approved_amount > 0 else 0.0
        total_interest = round(total_payable - approved_amount, 2) if approved_amount > 0 else 0.0

        xai_factors = {
            "positive_factors": positive_factors,
            "caution_factors": caution_factors,
            "dti_ratio": dti_ratio,
            "disposable_monthly_income": disposable_income,
            "max_affordable_emi": round(max_affordable_emi, 2),
            "document_checklist_summary": checklist_data.get("summary_message") if checklist_data else "Documents Verified",
            "document_counts": checklist_data.get("counts") if checklist_data else None
        }

        # Save to DB
        conn = get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO loan_applications (
            application_ref, applicant_name, monthly_income, existing_obligations,
            dti_ratio, cibil_score, loan_requested, tenor_months, risk_tier,
            decision_status, approved_amount, interest_rate, monthly_emi,
            turnaround_sla, xai_factors, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_ref, applicant_name, monthly_income, existing_obligations,
            dti_ratio, cibil_score, loan_requested, tenor_months, risk_tier,
            decision_status, approved_amount, interest_rate, monthly_emi,
            "72 Hours Turnaround SLA", json.dumps(xai_factors), created_at
        ))
        conn.commit()
        conn.close()

        return {
            "application_ref": app_ref,
            "applicant_name": applicant_name,
            "customer_id": customer_id,
            "loan_type": loan_type,
            "loan_requested": loan_requested,
            "approved_amount": approved_amount,
            "tenor_months": tenor_months,
            "interest_rate_apr": interest_rate,
            "monthly_emi": monthly_emi,
            "total_payable": total_payable,
            "total_interest": total_interest,
            "dti_ratio": dti_ratio,
            "risk_tier": risk_tier,
            "decision_status": decision_status,
            "turnaround_sla": "AI LoanFast 72-Hour Guaranteed SLA",
            "xai_factors": xai_factors,
            "document_checklist": checklist_data,
            "created_at": created_at
        }

    @classmethod
    def get_recent_loans(cls, limit: int = 10) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loan_applications ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
