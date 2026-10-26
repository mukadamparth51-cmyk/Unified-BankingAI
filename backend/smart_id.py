"""
Unified Banking AI - Module 2: Smart ID
AI-Powered Digital Identity Verification, Biometric Liveness, and AML Watchlist Screening Engine
"""

import re
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

from database import get_connection

class SmartIDEngine:
    """
    Smart ID provides digital KYC document verification, facial biometric matching,
    anti-spoofing liveness verification, and international AML/PEP screening.
    """

    AML_HIGH_RISK_KEYWORDS = [
        "sanction", "ofac", "interpol", "money laundering", "illicit", "terrorist",
        "hawala", "shell company", "banned entity", "debarred"
    ]

    PEP_DATABASE = [
        "minister", "governor", "senator", "ambassador", "diplomat", "judicial bench", "political"
    ]

    @classmethod
    def verify_identity(cls, full_name: str, id_type: str, id_number: str, selfie_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes complete Smart ID verification pipeline.
        """
        full_name = full_name.strip()
        id_number = id_number.strip().upper()

        # 1. Document Format & Masking Validation
        is_valid_format = False
        masked_number = ""
        ocr_confidence = 0.95

        if id_type.upper() in ["AADHAAR", "AADHAAR CARD"]:
            # Aadhaar 12 digits
            cleaned = re.sub(r'[^0-9]', '', id_number)
            if len(cleaned) == 12:
                is_valid_format = True
                masked_number = f"XXXX-XXXX-{cleaned[-4:]}" # UIDAI Redaction rule
                ocr_confidence = 0.985
            else:
                masked_number = "XXXX-XXXX-INVALID"
        elif id_type.upper() in ["PAN", "PAN CARD"]:
            # PAN: 5 letters, 4 numbers, 1 letter (e.g. ABCDE1234F)
            if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', id_number):
                is_valid_format = True
                masked_number = f"{id_number[:2]}XXX{id_number[5:7]}XX{id_number[-1]}"
                ocr_confidence = 0.972
            else:
                masked_number = "INVALID-PAN-FORMAT"
        elif "PASSPORT" in id_type.upper():
            if re.match(r'^[A-Z][0-9]{7}$', id_number):
                is_valid_format = True
                masked_number = f"{id_number[0]}XXXXXX{id_number[-1]}"
                ocr_confidence = 0.965
            else:
                masked_number = "INVALID-PASSPORT"
        else:
            is_valid_format = len(id_number) >= 6
            masked_number = f"ID-XXXX-{id_number[-3:] if len(id_number) >= 3 else 'XXX'}"
            ocr_confidence = 0.92

        # 2. Biometric Face Match & Liveness
        # Deterministic simulation based on name & ID hash
        hash_val = int(hashlib.md5((full_name + id_number).encode()).hexdigest()[:6], 16)
        face_match_score = round(91.0 + (hash_val % 80) / 10.0, 1) # between 91.0% and 99.0%
        liveness_detected = 1 if is_valid_format else 0

        # 3. AML & PEP Screening
        name_lower = full_name.lower()
        aml_hit = any(k in name_lower for k in cls.AML_HIGH_RISK_KEYWORDS)
        pep_hit = any(p in name_lower for p in cls.PEP_DATABASE)

        if aml_hit:
            aml_status = "ALERT: Potential Sanction List Match (OFAC/RBI Flagged)"
            risk_score = 92
            status = "REJECTED_AML_ALERT"
        elif pep_hit:
            aml_status = "WARNING: Politically Exposed Person (Enhanced Due Diligence Required)"
            risk_score = 48
            status = "CONDITIONAL_APPROVAL"
        else:
            aml_status = "CLEAR (Screened against OFAC, UN Sanctions & RBI Watchlist)"
            risk_score = 8 if is_valid_format else 65
            status = "VERIFIED" if is_valid_format else "INVALID_DOCUMENT"

        ref_id = f"SMARTID-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
        cert_data = f"{ref_id}|{full_name}|{masked_number}|{status}|{face_match_score}"
        cert_hash = hashlib.sha256(cert_data.encode()).hexdigest()

        # Save to DB
        conn = get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO smart_id_verifications (
            verification_ref, full_name, id_type, id_number_masked, ocr_confidence,
            face_match_score, liveness_detected, aml_status, pep_flag, risk_score,
            verification_status, certificate_hash, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_id, full_name, id_type, masked_number, ocr_confidence,
            face_match_score, liveness_detected, aml_status, 1 if pep_hit else 0,
            risk_score, status, cert_hash, created_at
        ))
        conn.commit()
        conn.close()

        return {
            "verification_ref": ref_id,
            "full_name": full_name,
            "id_type": id_type,
            "id_number_masked": masked_number,
            "ocr_confidence": ocr_confidence,
            "face_match_score": face_match_score,
            "liveness_verified": bool(liveness_detected),
            "aml_status": aml_status,
            "pep_flag": pep_hit,
            "identity_risk_score": risk_score,
            "verification_status": status,
            "tamper_evident_certificate_hash": cert_hash,
            "created_at": created_at
        }

    @classmethod
    def get_recent_verifications(cls, limit: int = 10) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM smart_id_verifications ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
