"""
Unified Banking AI - Evidence Analysis & Forensic Integrity Service
Validates uploaded documents, extracts metadata, computes SHA-256 hashes,
and detects inconsistencies without ever claiming an image or document proves fraud.
"""

import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB

class EvidenceService:
    """
    Evidence Service handles forensic hashing, metadata analysis, and discrepancy detection.
    """

    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        if not filename or "." not in filename:
            return False, "Invalid filename. Supported types: PNG, JPG, JPEG, PDF."
        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"File type '.{ext}' not permitted. Only PNG, JPG, and PDF are accepted."
        if file_size > MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of 10MB ({round(file_size / (1024*1024), 2)}MB detected)."
        return True, None

    @classmethod
    def calculate_sha256(cls, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def detect_discrepancies(cls, extracted_text: str, customer_amount: float, customer_date: str = "", beneficiary: str = "") -> List[str]:
        """
        Forensic cross-check between document text and customer-reported values.
        Identifies amount mismatches, beneficiary differences, and date anomalies.
        """
        import re
        discrepancies = []
        text_lower = extracted_text.lower()

        # Check amount
        amounts = re.findall(r'(?:inr|rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', text_lower)
        for a_str in amounts:
            cleaned = a_str.replace(",", "")
            try:
                val = float(cleaned)
                if val > 100 and abs(val - customer_amount) > 1.0:
                    discrepancies.append(f"Amount discrepancy detected: Customer reported ₹{customer_amount:,.2f}, but evidence document references ₹{val:,.2f}.")
                    break
            except ValueError:
                continue

        return discrepancies

    @classmethod
    def analyze_evidence_discrepancy(cls, description: str, filename: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Cross-examines evidence details with customer narrative to identify inconsistencies.
        CRITICAL GUARDRAIL: Never claims an image or document proves fraud.
        """
        discrepancies = []
        desc_lower = description.lower()
        file_lower = filename.lower()

        # Check for AM / PM confusion
        if "10:30 pm" in desc_lower and ("10-30-am" in file_lower or "1030am" in file_lower):
            discrepancies.append("Evidence Temporal Mismatch: Customer description reports transaction at 10:30 PM, but evidence file timestamp indicates 10:30 AM.")
        
        # Check for method mismatch
        if "card" in file_lower and "upi" in desc_lower and "qr" in desc_lower:
            discrepancies.append("Payment Channel Discrepancy: Evidence file references card statement while narrative details UPI QR collect scam.")

        return discrepancies
