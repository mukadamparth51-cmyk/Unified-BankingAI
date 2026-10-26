"""
Unified Banking AI - Idempotency & Duplicate Submission Protection
Ensures financial requests and chargeback submissions are strictly idempotent.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional

from database import get_connection

class IdempotencyManager:
    """
    Manages idempotency keys, prevents duplicate chargeback submissions,
    and safeguards against network timeouts, retries, and race conditions.
    """

    @classmethod
    def generate_key(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def check_existing_submission(cls, idempotency_key: str) -> Optional[Dict[str, Any]]:
        if not idempotency_key:
            return None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bank_dispute_submissions WHERE idempotency_key = ?", (idempotency_key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "case_id": row["case_id"],
                "idempotency_key": row["idempotency_key"],
                "provider": row["provider"],
                "gateway_mode": row["gateway_mode"],
                "reference_id": row["reference_id"],
                "status_code": row["status_code"],
                "response_payload": json.loads(row["response_payload"]) if row["response_payload"] else {},
                "created_at": row["created_at"]
            }
        return None

    @classmethod
    def record_submission(
        cls,
        case_id: int,
        idempotency_key: str,
        provider: str,
        gateway_mode: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
        status_code: int,
        reference_id: str,
        retry_count: int = 0
    ) -> int:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO bank_dispute_submissions (
            case_id, idempotency_key, provider, gateway_mode, request_payload,
            response_payload, status_code, reference_id, retry_count, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id, idempotency_key, provider, gateway_mode,
            json.dumps(request_payload), json.dumps(response_payload),
            status_code, reference_id, retry_count, now_str
        ))
        sub_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return sub_id
