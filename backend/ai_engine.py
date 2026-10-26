"""
Unified Banking AI - AI Fraud Case Analyzer Module
Advanced Natural Language & Heuristic Case Intelligence Engine
Adheres to strict Fintech Cybersecurity and Regulatory Standards.
"""

import re
from datetime import datetime
from typing import Dict, Any, List

class AIFraudCaseAnalyzer:
    """
    AI Fraud Case Analyzer provides classification, evidence gap analysis,
    inconsistency detection, and recovery roadmap recommendations.
    
    IMPORTANT ARCHITECTURAL GUARDRAIL:
    AI analysis generates intelligence and decision support. It does NOT
    independently prove legal fraud, establish bank liability, or guarantee
    any recovery of funds.
    """

    # Patterns indicating credential leakage or high-risk inputs that MUST never be stored
    SENSITIVE_PATTERNS = [
        (r'\b(?:otp|one[- ]time[- ]password)(?:\s+(?:is|was))?[:\s=]+([0-9]{4,8})\b', "OTP"),
        (r'\b(?:pin|upi[- ]pin|atm[- ]pin)(?:\s+(?:is|was))?[:\s=]+([0-9]{4,6})\b', "PIN"),
        (r'\b(?:cvv|cvc|security code)(?:\s+(?:is|was))?[:\s=]+([0-9]{3,4})\b', "CVV"),
        (r'\b(?:password|pwd)(?:\s+(?:is|was))?[:\s=]+(\S+)\b', "PASSWORD"),
    ]

    FRAUD_PATTERNS = {
        "UPI Collect / QR Code Deception": [
            r'qr\s*code', r'scan\s*(?:to\s*receive|and\s*get)', r'collect\s*request',
            r'entered\s*upi\s*pin\s*to\s*receive', r'olx', r'quikr', r'marketplace',
            r'seller\s*sent\s*qr', r'receive\s*money\s*by\s*scanning'
        ],
        "Remote Access Trojan / Screen Sharing Impersonation": [
            r'anydesk', r'teamviewer', r'quicksupport', r'rustdesk', r'screen\s*share',
            r'installed\s*app', r'remote\s*access', r'electricity\s*bill', r'power\s*cut',
            r'apk\s*download', r'customer\s*care\s*asked\s*to\s*install'
        ],
        "Fake Customer Care / Search Engine Poisoning": [
            r'google\s*search\s*number', r'customer\s*care\s*helpline', r'fake\s*executive',
            r'toll\s*free\s*scam', r'called\s*number\s*from\s*internet', r'bank\s*support\s*fake'
        ],
        "Investment / Task / Part-Time Job Ponzi": [
            r'telegram\s*group', r'crypto\s*investment', r'task\s*earning', r'like\s*youtube\s*videos',
            r'guaranteed\s*returns', r'part\s*time\s*job', r'vip\s*level', r'commission\s*bonus'
        ],
        "Unauthorized Card Not Present / Skimming": [
            r'card\s*not\s*present', r'international\s*pos', r'dubai', r'unauthorized\s*card\s*charge',
            r'card\s*cloning', r'skimming', r'card\s*in\s*my\s*wallet', r'never\s*shared\s*card\s*details'
        ],
        "SIM Swap & Account Takeover": [
            r'sim\s*swap', r'no\s*network\s*signal', r'esim\s*transfer', r'telecom\s*alert',
            r'otp\s*diverted', r'unauthorized\s*netbanking\s*login'
        ],
        "Impersonation / Digital Arrest Extortion": [
            r'digital\s*arrest', r'cbi', r'police\s*officer', r'customs\s*officer',
            r'fedex\s*parcel', r'narcotics', r'skype\s*call\s*police', r'arrest\s*warrant'
        ],
        "Phishing Link / Malicious Website": [
            r'clicked\s*link', r'sms\s*link', r'reward\s*points\s*expiry', r'lottery',
            r'kyc\s*update\s*link', r'pan\s*card\s*block\s*sms'
        ]
    }

    @classmethod
    def sanitize_input(cls, text: str) -> tuple[str, List[str]]:
        """
        Scans and redacts any accidentally provided passwords, OTPs, PINs, or CVVs.
        Returns (sanitized_text, warnings)
        """
        if not text:
            return "", []

        warnings = []
        sanitized = text

        for pattern, cred_type in cls.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, sanitized, flags=re.IGNORECASE)
            if matches:
                warnings.append(f"Security Alert: Sensitive {cred_type} detected and permanently redacted for your security. Unified Banking AI never requests or stores authentication credentials.")
                sanitized = re.sub(pattern, f"[REDACTED-{cred_type}]", sanitized, flags=re.IGNORECASE)

        return sanitized, warnings

    @classmethod
    def classify_fraud_type(cls, description: str, payment_method: str) -> Dict[str, Any]:
        """
        Classifies fraud into standardized banking typologies and calculates confidence.
        """
        desc_lower = description.lower()
        scores = {}

        for category, patterns in cls.FRAUD_PATTERNS.items():
            match_count = 0
            for pat in patterns:
                if re.search(pat, desc_lower):
                    match_count += 1
            if match_count > 0:
                scores[category] = match_count

        if scores:
            best_cat = max(scores, key=scores.get)
            confidence = min(0.98, 0.65 + (scores[best_cat] * 0.11))
        else:
            # Fallback heuristic based on payment method
            if payment_method.upper() == "UPI":
                best_cat = "Suspected UPI Payment Deception"
                confidence = 0.55
            elif "CARD" in payment_method.upper():
                best_cat = "Suspected Unauthorized Card Transaction"
                confidence = 0.55
            else:
                best_cat = "Unspecified Unauthorized Transfer"
                confidence = 0.45

        # Determine mule risk
        if "Telegram" in best_cat or "Investment" in best_cat or "Digital Arrest" in best_cat:
            mule_risk = "Critical Multi-Layered Mule Syndicate"
        elif "UPI" in best_cat or "Remote Access" in best_cat:
            mule_risk = "High Instant Cashout Risk (Mule Account Hop)"
        else:
            mule_risk = "Moderate / Direct Acquiring Settlement"

        return {
            "primary_classification": best_cat,
            "confidence": round(confidence, 2),
            "mule_risk": mule_risk,
            "all_matches": scores
        }

    @classmethod
    def identify_missing_information(cls, case_data: Dict[str, Any]) -> List[str]:
        """
        Identifies critical evidential and statutory gaps required for successful
        banking dispute or 1930 Cyber Cell registration.
        """
        missing = []
        utr = str(case_data.get("utr_number", "")).strip()
        desc = case_data.get("description", "").strip()
        beneficiary = case_data.get("beneficiary_details", "").strip()
        evidence_files = case_data.get("evidence_files", [])

        # Check UTR
        if not utr or len(utr) < 8 or utr.lower() in ["none", "na", "unknown", "000000000000"]:
            missing.append("Valid 12-digit UPI/IMPS UTR or Bank RRN is missing. UTR is strictly mandatory for NPCI inter-bank trace.")

        # Check Beneficiary Info
        if not beneficiary or len(beneficiary) < 4:
            missing.append("Beneficiary Details (UPI VPA handle, Beneficiary Account Number or IFSC) are missing. This aids in placing recipient account liens.")

        # Check Evidence attachments
        if not evidence_files or len(evidence_files) == 0:
            missing.append("Bank Debit SMS screenshot or official account debit statement is missing.")

        # Check Cyber Cell FIR / Acknowledgment
        if not re.search(r'\b(?:1930|ncrp|cyber\s*crime|acknowledgement|fir)\b', desc.lower()):
            missing.append("National Cyber Crime Reporting Portal (cybercrime.gov.in / 1930) complaint reference number not yet linked.")

        return missing

    @classmethod
    def detect_inconsistencies(cls, case_data: Dict[str, Any]) -> List[str]:
        """
        Detects temporal, logical, and regulatory inconsistencies requiring human fraud investigator review.
        """
        inconsistencies = []
        txn_time_str = case_data.get("transaction_time", "")
        desc = case_data.get("description", "").lower()
        amount = float(case_data.get("amount_reported", 0))

        # 1. Temporal Inconsistency: Transaction in the future
        try:
            # Handle standard datetime strings
            txn_dt = None
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    txn_dt = datetime.strptime(txn_time_str[:19], fmt)
                    break
                except ValueError:
                    pass

            if txn_dt and txn_dt > datetime.now():
                inconsistencies.append("Temporal Contradiction: Transaction date/time is recorded in the future.")
        except Exception:
            pass

        # 2. UPI Limit Inconsistency
        method = str(case_data.get("payment_method", "")).upper()
        if method == "UPI" and amount > 500000:
            inconsistencies.append(f"Regulatory Threshold Warning: Standard UPI limit is ₹1,00,000 per txn (₹5,00,000 for approved educational/hospital categories). Reported UPI amount of ₹{amount:,.2f} exceeds standard network ceiling.")

        # 3. Contradictory statements
        if "never shared pin" in desc and "entered upi pin" in desc:
            inconsistencies.append("Logical Contradiction: Narrative states 'never shared pin' but also indicates 'entered upi pin'. Clarification required.")

        if "card in wallet" in desc and "atm cash withdrawal" in desc and "cloned" not in desc:
            inconsistencies.append("Physical ATM Inconsistency: Cash withdrawal claimed while physical card remained in possession without skimming or magnetic stripe cloning evidence.")

        return inconsistencies

    @classmethod
    def generate_case_summary(cls, case_data: Dict[str, Any], classification: Dict[str, Any], missing: List[str], inconsistencies: List[str]) -> Dict[str, Any]:
        """
        Produces an executive-level, audit-ready structured summary of the fraud case.
        """
        amount = float(case_data.get("amount_reported", 0))
        bank = case_data.get("bank_name", "Unknown Bank")
        method = case_data.get("payment_method", "Electronic Payment")
        utr = case_data.get("utr_number", "N/A")

        summary_text = (
            f"Customer reported suspected financial fraud of ₹{amount:,.2f} originating through {method} "
            f"on {case_data.get('transaction_time', 'N/A')} from issuing institution {bank}. "
            f"The incident exhibits primary characteristics of '{classification['primary_classification']}' "
            f"with an algorithmic confidence score of {int(classification['confidence'] * 100)}%. "
            f"Mule syndicate risk is assessed as '{classification['mule_risk']}'."
        )

        uncertainty_analysis = (
            "IMPORTANT NOTICE: Suspected Fraud vs. Verified Fraud Distinction — "
            "At this stage, this case is classified as 'Suspected Fraud'. AI analysis does not and cannot legally "
            "substantiate fraudulent intent or guarantee refund eligibility. Inter-bank trace, beneficiary account "
            "lien confirmation, and final adjudication are subject to statutory verification by the issuing bank, "
            "acquiring bank, NPCI, and Law Enforcement Agencies (NCRP/State Cyber Cell)."
        )

        recommended_next_steps = [
            "Step 1: Immediate Emergency Reporting — Dial 1930 or submit incident ticket on https://cybercrime.gov.in within the 'Golden Hour' to request beneficiary account freeze.",
            f"Step 2: Issuing Bank Formal Intimation — File formal dispute ticket with {bank} citing UTR: {utr} and request immediate UDIR recall.",
            "Step 3: Preserve Evidential Chain — Retain unaltered SMS alerts, call logs, WhatsApp/Telegram transcripts, and bank debit advice.",
            "Step 4: Statutory Timeline Monitoring — Under RBI Circular RBI/2017-18/15, if reported within 3 working days without customer contributory negligence, zero liability applies."
        ]

        return {
            "executive_summary": summary_text,
            "uncertainty_analysis": uncertainty_analysis,
            "missing_evidence_count": len(missing),
            "inconsistency_count": len(inconsistencies),
            "recommended_next_steps": recommended_next_steps,
            "disclaimer": "AI Direct Refund Recovery Engine acts strictly as a case preparation, audit, and dispute facilitation assistant. We do not hold depository authority and never guarantee fund recovery."
        }
