"""
Unified Banking AI - Deterministic Eligibility Rules Engine
Authoritative backend rules engine strictly adhering to:
- RBI Circular RBI/2017-18/15 (Limiting Customer Liability in Unauthorised Electronic Banking Transactions)
- NPCI UPI Unified Dispute & Issue Resolution (UDIR) Operating Circulars
- Banking Ombudsman Scheme 2021

IMPORTANT ARCHITECTURAL RULE:
Gemma 4 provides natural language explanations and summaries, but this
deterministic rules engine remains authoritative for the case's statutory status.
"""

from datetime import datetime
from typing import Dict, Any, List

class EligibilityEngine:
    """
    Authoritative rules engine determining statutory refund eligibility.
    Strictly outputs one of the 5 approved statuses.
    """

    ELIGIBILITY_STATUSES = [
        "Potentially eligible",
        "More information required",
        "Manual review required",
        "Eligibility uncertain",
        "Not eligible under currently verified criteria"
    ]

    @classmethod
    def evaluate(cls, case_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates eligibility against verified statutory rules using case facts
        and structured AI indicators from Gemma 4.
        """
        txn_time_str = str(case_data.get("transaction_time", ""))
        desc = str(case_data.get("description", "")).lower()
        amount = float(case_data.get("amount_reported", 0))

        structured_ai = ai_analysis.get("structured_output", {})
        missing_info = structured_ai.get("missing_information", [])
        inconsistencies = structured_ai.get("inconsistencies", [])

        # Calculate elapsed hours between transaction and report
        elapsed_hours = 0.0
        try:
            txn_dt = None
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    txn_dt = datetime.strptime(txn_time_str[:19], fmt)
                    break
                except ValueError:
                    pass

            if txn_dt:
                now = datetime.now()
                elapsed_hours = max(0.0, (now - txn_dt).total_seconds() / 3600.0)
        except Exception:
            elapsed_hours = 24.0 # safe fallback

        elapsed_days = elapsed_hours / 24.0

        # Rule 1: Discrepancies & Contradictions Require Manual Forensic Review
        if inconsistencies and len(inconsistencies) > 0:
            return {
                "status": "Manual review required",
                "authority_engine": "Deterministic Rules Engine (Authoritative)",
                "statutory_basis": "RBI Master Direction on Grievance Redressal & Fraud Monitoring",
                "reason": f"Discrepancies identified in reported chronology or transaction mechanics ({inconsistencies[0]}). Requires forensic review by a human compliance investigator.",
                "liability_tier": "Case Under Adjudication",
                "max_liability_estimate": "Pending Inconsistency Resolution",
                "next_recommended_action": "Schedule case interview with Bank Grievance Redressal Officer and provide verified transaction passbook entry.",
                "disclaimer": "This is an automated regulatory assessment based on RBI Circular RBI/2017-18/15. Only the account-servicing bank has statutory authority to issue binding liability decisions."
            }

        # Rule 2: Crucial Missing Artifacts Require More Information
        if missing_info and len(missing_info) >= 2:
            return {
                "status": "More information required",
                "authority_engine": "Deterministic Rules Engine (Authoritative)",
                "statutory_basis": "NPCI UPI Operating Circular on Dispute Redressal & RBI Customer Protection Directives",
                "reason": f"Crucial evidential artifacts missing: {'; '.join(missing_info[:2])}. Statutory dispute protocols cannot proceed without mandatory transaction references.",
                "liability_tier": "Incomplete Evidence Dossier",
                "max_liability_estimate": "Cannot be determined without mandatory proofs",
                "next_recommended_action": "Obtain and upload bank debit advice or 1930 Cyber Crime Portal acknowledgment slip.",
                "disclaimer": "Assessment will automatically re-evaluate upon submission of required banking proofs."
            }

        # Check for willing credential sharing (Customer Negligence Clause)
        shared_credentials = any(w in desc for w in ["i gave otp", "shared the otp", "told him the otp", "entered my pin to receive", "entered upi pin"])

        # Rule 3: Zero Customer Liability Tier
        # (Reported within 3 working days / 72 hours AND no intentional credential disclosure)
        if elapsed_days <= 3.0 and not shared_credentials:
            return {
                "status": "Potentially eligible",
                "authority_engine": "Deterministic Rules Engine (Authoritative)",
                "statutory_basis": "RBI/2017-18/15 DBR.No.Leg.BC.78/09.07.005/2017-18, Para 6 (Zero Liability of a Customer)",
                "reason": (
                    f"Reported within {elapsed_hours:.1f} hours (< 72 hours / 3 working days threshold). "
                    "Case narrative indicates third-party system deficiency or deceptive fraud without voluntary credential "
                    "transfer. Strong basis under RBI Circular Section 6(a) for Zero Customer Liability."
                ),
                "liability_tier": "Zero Customer Liability (Subject to Bank Verification)",
                "max_liability_estimate": "₹0.00 (Customer), 100% Recoverable from Network/Acquirer",
                "next_recommended_action": "Immediately trigger Direct Refund & Reversal Request through authorized UDIR / Bank gateway to secure inter-bank lien.",
                "disclaimer": "Eligible for expedited processing. Final refund credit is issued solely by the account servicing bank upon conclusion of internal investigation."
            }

        # Rule 4: Contributory Negligence (Shared PIN/OTP)
        if shared_credentials:
            if elapsed_days <= 3.0:
                return {
                    "status": "Manual review required",
                    "authority_engine": "Deterministic Rules Engine (Authoritative)",
                    "statutory_basis": "RBI Customer Protection Circular, Para 7 (Customer Negligence & Immediate Reporting)",
                    "reason": (
                        "Customer entered PIN or shared OTP under social engineering deception. "
                        "Under RBI Para 7, customer bears loss occurring until the fraud is reported to the bank. "
                        "Because reporting occurred within 72 hours, bank must freeze further leakage and evaluate social engineering deception mitigation."
                    ),
                    "liability_tier": "Contributory Negligence with Prompt Mitigating Notice",
                    "max_liability_estimate": f"Up to transaction amount (₹{amount:,.2f}), subject to recovery from beneficiary bank freeze",
                    "next_recommended_action": "Submit formal complaint requesting emergency beneficiary freeze under Section 1930 Cyber Cell CFCFRMS integration.",
                    "disclaimer": "AI cannot override bank credential liability rules. Focus recovery on freeze of beneficiary mule funds."
                }
            else:
                return {
                    "status": "Eligibility uncertain",
                    "authority_engine": "Deterministic Rules Engine (Authoritative)",
                    "statutory_basis": "RBI/2017-18/15 Para 7 & 8 (Delayed Reporting of Shared Credentials)",
                    "reason": (
                        f"Customer shared authentication credentials and reported after {elapsed_days:.1f} days (> 3 days). "
                        "High likelihood of customer liability under standard banking guidelines unless beneficiary funds remain frozen in destination account."
                    ),
                    "liability_tier": "High Customer Liability Tier",
                    "max_liability_estimate": f"Customer may bear up to ₹{amount:,.2f} unless recovered via 1930 Cyber Cell",
                    "next_recommended_action": "Contact beneficiary bank nodal officer and register formal grievance with the RBI Integrated Ombudsman Scheme.",
                    "disclaimer": "Official bank decision may restrict refund unless funds are successfully impounded in beneficiary account."
                }

        # Rule 5: Limited Customer Liability Tier (4 to 7 working days)
        if 3.0 < elapsed_days <= 7.0:
            return {
                "status": "Potentially eligible",
                "authority_engine": "Deterministic Rules Engine (Authoritative)",
                "statutory_basis": "RBI/2017-18/15 Para 8 (Limited Liability of a Customer: 4 to 7 working days)",
                "reason": (
                    f"Reported between 4 and 7 working days ({elapsed_days:.1f} days elapsed). "
                    "Qualifies for Limited Customer Liability under RBI Para 8. "
                    "Customer liability capped at ₹5,000 to ₹10,000 for standard savings accounts, with remainder eligible for reversal."
                ),
                "liability_tier": "Capped Limited Liability (₹5,000 - ₹10,000 ceiling)",
                "max_liability_estimate": "Capped at ₹10,000 (Maximum liability for standard SB account)",
                "next_recommended_action": "Submit Limited Liability dispute dossier to bank nodal grievance department.",
                "disclaimer": "Exact statutory ceiling is subject to customer account classification (BSBD, Savings, or Premium Current Account)."
            }

        # Rule 6: Delayed Beyond 7 Working Days
        if elapsed_days > 7.0:
            return {
                "status": "Not eligible under currently verified criteria",
                "authority_engine": "Deterministic Rules Engine (Authoritative)",
                "statutory_basis": "RBI/2017-18/15 Para 9 (Beyond Seven Working Days - Board Approved Policy)",
                "reason": (
                    f"Transaction occurred {elapsed_days:.1f} days ago (> 7 working days). "
                    "Exceeds standard statutory zero/limited liability window under RBI Circular Para 9. "
                    "Governed strictly by the individual bank's board-approved discretionary policy."
                ),
                "liability_tier": "Discretionary Board Policy Tier",
                "max_liability_estimate": "Determined on a case-by-case basis by bank",
                "next_recommended_action": "File appeal before the RBI Banking Ombudsman (cms.rbi.org.in) citing extenuating circumstances for reporting delay.",
                "disclaimer": "Automated network chargebacks are barred after deadline. Recovery dependent on law enforcement fund seizures."
            }

        # Fallback
        return {
            "status": "Eligibility uncertain",
            "authority_engine": "Deterministic Rules Engine (Authoritative)",
            "statutory_basis": "RBI Master Direction on Customer Liability",
            "reason": "Case details insufficient to establish conclusive statutory category under RBI 2017-18 directives.",
            "liability_tier": "Under Evaluation",
            "max_liability_estimate": "Current eligibility could not be verified.",
            "next_recommended_action": "Provide additional transaction receipts and complete fraud questionnaire.",
            "disclaimer": "Assessment is an advisory guide and does not constitute official legal or banking counsel."
        }
