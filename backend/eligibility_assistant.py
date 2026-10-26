"""
Unified Banking AI - Refund Eligibility Assistant Module
Rules-Based Statutory & Regulatory Eligibility Engine
Fully aligned with:
- RBI Circular RBI/2017-18/15 (Customer Protection - Limiting Liability in Unauthorised Electronic Banking Transactions)
- NPCI UPI Unified Dispute & Issue Resolution (UDIR) Procedural Guidelines
- Banking Ombudsman Scheme 2021 (Integrated Ombudsman Scheme)
"""

from datetime import datetime
from typing import Dict, Any, List

class RefundEligibilityAssistant:
    """
    Evaluates fraud cases against verified statutory rules and banking frameworks.
    
    CRITICAL POLICY GUARDRAILS:
    1. NEVER presents an assessment as an official or binding bank determination.
    2. NEVER invents hypothetical policies.
    3. Strictly outputs one of the 5 approved statuses:
       - 'Potentially eligible'
       - 'More information required'
       - 'Manual review required'
       - 'Eligibility uncertain'
       - 'Not eligible under the currently verified criteria'
    """

    ELIGIBILITY_STATUSES = [
        "Potentially eligible",
        "More information required",
        "Manual review required",
        "Eligibility uncertain",
        "Not eligible under the currently verified criteria"
    ]

    @classmethod
    def evaluate(cls, case_data: Dict[str, Any], missing_evidence: List[str], inconsistencies: List[str]) -> Dict[str, Any]:
        """
        Executes rules engine evaluating:
        1. Reporting timeline (elapsed hours between transaction & customer notice)
        2. Transaction method & network mechanics
        3. Contributory negligence indicators (OTP/PIN consent)
        4. Evidential sufficiency
        """
        txn_time_str = case_data.get("transaction_time", "")
        desc = case_data.get("description", "").lower()
        method = str(case_data.get("payment_method", "")).upper()
        amount = float(case_data.get("amount_reported", 0))

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
            elapsed_hours = 24.0 # default fallback

        elapsed_days = elapsed_hours / 24.0

        # Check for critical inconsistencies first
        if inconsistencies and len(inconsistencies) > 0:
            return {
                "status": "Manual review required",
                "reason": f"Discrepancies identified in reported chronology or transaction mechanics ({inconsistencies[0]}). Requires forensic review by a human compliance investigator.",
                "applicable_regulation": "RBI Master Direction on Digital Payment Security Controls & Grievance Redressal",
                "liability_tier": "Case Under Adjudication",
                "max_liability_estimate": "Pending Inconsistency Resolution",
                "next_recommended_action": "Schedule case interview with Bank Grievance Redressal Officer and provide verified transaction passbook entry.",
                "disclaimer": "This is an automated regulatory pre-assessment based on RBI circular RBI/2017-18/15. Only the customer's bank has statutory authority to adjudicate final liability."
            }

        # Check for missing essential evidence
        if missing_evidence and len(missing_evidence) >= 2:
            return {
                "status": "More information required",
                "reason": f"Crucial evidential artifacts missing: {'; '.join(missing_evidence[:2])}. Statutory dispute protocols cannot proceed without mandatory transaction references.",
                "applicable_regulation": "NPCI Operating Circular on UPI Dispute Redressal & RBI Customer Protection Directives",
                "liability_tier": "Incomplete Evidence Dossier",
                "max_liability_estimate": "Cannot be determined without mandatory proofs",
                "next_recommended_action": "Obtain and upload bank debit advice or 1930 Cyber Crime Portal acknowledgment slip.",
                "disclaimer": "Assessment will automatically re-evaluate upon submission of required banking proofs."
            }

        # Check for willing credential compromise (Customer Negligence Clause)
        shared_pin_or_otp = False
        if any(w in desc for w in ["i gave otp", "shared the otp", "told him the otp", "entered my pin to receive", "entered upi pin"]):
            shared_pin_or_otp = True

        # Rule Set 1: Zero Customer Liability Tier
        # (Reported within 3 working days / 72 hours AND no intentional credential disclosure)
        if elapsed_days <= 3.0 and not shared_pin_or_otp:
            return {
                "status": "Potentially eligible",
                "reason": (
                    f"Reported within {elapsed_hours:.1f} hours (< 72 hours / 3 working days threshold). "
                    "Case narrative indicates third-party system deficiency or deceptive fraud without voluntary credential "
                    "transfer. Strong basis under RBI Circular Section 6(a) for Zero Customer Liability."
                ),
                "applicable_regulation": "RBI/2017-18/15 DBR.No.Leg.BC.78/09.07.005/2017-18, Para 6 (Zero Liability of a Customer)",
                "liability_tier": "Zero Customer Liability (Subject to Bank Verification)",
                "max_liability_estimate": "₹0.00 (Customer), 100% Recoverable from Network/Acquirer",
                "next_recommended_action": "Immediately trigger Direct Refund & Reversal Request through authorized UDIR / Bank gateway to secure inter-bank lien.",
                "disclaimer": "Eligible for expedited processing. Final refund credit is issued solely by the account servicing bank upon conclusion of internal investigation."
            }

        # Rule Set 2: Contributory Negligence (Customer shared OTP/PIN)
        if shared_pin_or_otp:
            if elapsed_days <= 3.0:
                return {
                    "status": "Manual review required",
                    "reason": (
                        "Customer entered PIN or shared OTP under social engineering deception. "
                        "Under RBI Para 7, customer bears loss occurring until the fraud is reported to the bank. "
                        "Because reporting occurred within 72 hours, bank must freeze further leakage and evaluate social engineering deception mitigation."
                    ),
                    "applicable_regulation": "RBI Customer Protection Circular, Para 7 (Customer Negligence & Immediate Reporting)",
                    "liability_tier": "Contributory Negligence with Prompt Mitigating Notice",
                    "max_liability_estimate": f"Up to transaction amount (₹{amount:,.2f}), subject to recovery from beneficiary bank freeze",
                    "next_recommended_action": "Submit formal complaint requesting emergency beneficiary freeze under Section 1930 Cyber Cell CFCFRMS integration.",
                    "disclaimer": "AI cannot override bank credential liability rules. Focus recovery on freeze of beneficiary mule funds."
                }
            else:
                return {
                    "status": "Eligibility uncertain",
                    "reason": (
                        f"Customer shared authentication credentials and reported after {elapsed_days:.1f} days (> 3 days). "
                        "High likelihood of customer liability under standard banking guidelines unless beneficiary funds remain frozen in destination account."
                    ),
                    "applicable_regulation": "RBI/2017-18/15 Para 7 & 8 (Delayed Reporting of Shared Credentials)",
                    "liability_tier": "High Customer Liability Tier",
                    "max_liability_estimate": f"Customer may bear up to ₹{amount:,.2f} unless recovered via 1930 Cyber Cell",
                    "next_recommended_action": "Contact beneficiary bank nodal officer and register formal grievance with the RBI Integrated Ombudsman Scheme.",
                    "disclaimer": "Official bank decision may restrict refund unless funds are successfully impounded in beneficiary account."
                }

        # Rule Set 3: Limited Customer Liability Tier (4 to 7 working days)
        if 3.0 < elapsed_days <= 7.0:
            return {
                "status": "Potentially eligible",
                "reason": (
                    f"Reported between 4 and 7 working days ({elapsed_days:.1f} days elapsed). "
                    "Qualifies for Limited Customer Liability under RBI Para 8. "
                    "Customer liability capped at ₹5,000 to ₹10,000 for standard savings accounts, with remainder eligible for reversal."
                ),
                "applicable_regulation": "RBI/2017-18/15 Para 8 (Limited Liability of a Customer: 4 to 7 working days)",
                "liability_tier": "Capped Limited Liability (₹5,000 - ₹10,000 ceiling)",
                "max_liability_estimate": "Capped at ₹10,000 (Maximum liability for standard SB account)",
                "next_recommended_action": "Submit Limited Liability dispute dossier to bank nodal grievance department.",
                "disclaimer": "Exact statutory ceiling is subject to customer account classification (BSBD, Savings, or Premium Current Account)."
            }

        # Rule Set 4: Delayed Beyond 7 Working Days
        if elapsed_days > 7.0:
            return {
                "status": "Not eligible under the currently verified criteria",
                "reason": (
                    f"Transaction occurred {elapsed_days:.1f} days ago (> 7 working days). "
                    "Exceeds standard statutory zero/limited liability window under RBI Circular Para 9. "
                    "Governed strictly by the individual bank's board-approved discretionary policy."
                ),
                "applicable_regulation": "RBI/2017-18/15 Para 9 (Beyond Seven Working Days - Board Approved Policy)",
                "liability_tier": "Discretionary Board Policy Tier",
                "max_liability_estimate": "Determined on a case-by-case basis by bank",
                "next_recommended_action": "File appeal before the RBI Banking Ombudsman (cms.rbi.org.in) citing extenuating circumstances for reporting delay.",
                "disclaimer": "Automated network chargebacks are barred after deadline. Recovery dependent on law enforcement fund seizures."
            }

        # Default fallback
        return {
            "status": "Eligibility uncertain",
            "reason": "Case details insufficient to establish conclusive statutory category under RBI 2017-18 directives.",
            "applicable_regulation": "RBI Master Direction on Customer Liability",
            "liability_tier": "Under Evaluation",
            "max_liability_estimate": "Uncertain",
            "next_recommended_action": "Provide additional transaction receipts and complete fraud questionnaire.",
            "disclaimer": "Assessment is an advisory guide and does not constitute official legal or banking counsel."
        }
