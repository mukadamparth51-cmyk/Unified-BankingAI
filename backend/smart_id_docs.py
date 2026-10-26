"""
Unified Banking AI - Module 2: Smart ID Document Service
Secure, row-level authorized, tamper-evident document vault for authenticated banking customers.
Handles PDF validation, private storage, RLS access control, expiry tracking, and audit logging.
"""

import os
import re
import uuid
import hashlib
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from werkzeug.utils import secure_filename

from database import get_connection

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "storage", "documents"))
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB

VALID_STATUSES = ["uploaded", "missing", "pending_verification", "verified", "rejected", "expired"]
VALID_DOCUMENT_TYPES = [
    "PAN Card",
    "Aadhaar Card",
    "Passport",
    "Salary Slip",
    "Bank Statement",
    "ITR / Form 16",
    "Utility Bill / Address Proof",
    "Driving License"
]

class SmartIDDocumentService:
    """
    Manages customer financial and identity documents in private storage.
    Enforces Row-Level Security (RLS), PDF format validation, and comprehensive audit trails.
    """

    @classmethod
    def get_storage_dir(cls) -> str:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        return STORAGE_DIR

    @classmethod
    def validate_pdf_bytes(cls, filename: str, file_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Enforces strict file constraints:
        1. Filename must end with .pdf
        2. File must not be empty (> 100 bytes)
        3. File must not exceed 10 MB
        4. Magic bytes must begin with %PDF
        """
        if not filename or not filename.lower().endswith(".pdf"):
            return False, "Invalid file format. Only official PDF documents (.pdf) are permitted."

        if not file_bytes or len(file_bytes) < 100:
            return False, "File is empty or corrupted. Please upload a valid PDF document."

        if len(file_bytes) > MAX_FILE_SIZE:
            mb_size = round(len(file_bytes) / (1024 * 1024), 2)
            return False, f"File size exceeds 10MB limit ({mb_size}MB detected). Please optimize the PDF."

        if not file_bytes.startswith(b"%PDF"):
            return False, "Security Alert: Invalid document signature. The file header does not match the standard PDF specification."

        return True, None

    @classmethod
    def log_audit(cls, doc_id: Optional[int], owner_id: str, actor_id: str, actor_role: str, action: str, ip_address: str, details: str):
        conn = get_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO document_audit_logs (
            document_id, owner_id, actor_id, actor_role, action, ip_address, details, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, owner_id, actor_id, actor_role, action, ip_address, details, now_str))
        conn.commit()
        conn.close()

    @classmethod
    def check_authorization(cls, owner_id: str, actor_id: str, actor_role: str) -> bool:
        """
        Row-Level Security check:
        Only the document owner or an authorized bank manager/auditor may access document data.
        """
        if actor_role in ["bank_manager", "admin", "auditor"]:
            return True
        return str(owner_id).strip().upper() == str(actor_id).strip().upper()

    @classmethod
    def upload_document(
        cls,
        owner_id: str,
        document_type: str,
        original_filename: str,
        file_bytes: bytes,
        expiry_date: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: str = "customer",
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Saves uploaded PDF into private storage and records metadata in database.
        """
        if not actor_id:
            actor_id = owner_id

        if not cls.check_authorization(owner_id, actor_id, actor_role):
            cls.log_audit(None, owner_id, actor_id, actor_role, "SECURITY_VIOLATION", ip_address, "Unauthorized upload attempt for another customer")
            raise PermissionError("Access Denied: Row-level security prohibits uploading documents on behalf of another customer.")

        if document_type not in VALID_DOCUMENT_TYPES:
            raise ValueError(f"Invalid document type '{document_type}'. Allowed: {', '.join(VALID_DOCUMENT_TYPES)}")

        # Validate PDF
        is_valid, err = cls.validate_pdf_bytes(original_filename, file_bytes)
        if not is_valid:
            raise ValueError(err)

        # Validate Expiry format if provided
        clean_expiry = None
        is_already_expired = False
        if expiry_date and str(expiry_date).strip():
            clean_expiry = str(expiry_date).strip()
            try:
                exp_dt = datetime.strptime(clean_expiry, "%Y-%m-%d").date()
                if exp_dt < date.today():
                    is_already_expired = True
            except ValueError:
                raise ValueError("Invalid expiry date format. Expected YYYY-MM-DD.")

        # Determine initial verification status
        if is_already_expired:
            initial_status = "expired"
            rejection_reason = f"Document is already expired (expiry date: {clean_expiry})."
        else:
            initial_status = "uploaded"
            rejection_reason = None

        storage_dir = cls.get_storage_dir()
        safe_orig = secure_filename(original_filename) or "document.pdf"
        doc_slug = re.sub(r'[^a-zA-Z0-9]', '_', document_type).upper()
        stored_filename = f"DOC_{owner_id}_{doc_slug}_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(storage_dir, stored_filename)

        # Path traversal guard
        real_path = os.path.abspath(file_path)
        if os.path.commonpath([real_path, storage_dir]) != storage_dir:
            raise SecurityError("Directory traversal detected in destination filename.")

        with open(real_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        cursor = conn.cursor()

        # Check if customer exists, if not auto-register for testing
        cursor.execute("SELECT COUNT(*) FROM customers WHERE customer_id = ?", (owner_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO customers (customer_id, full_name, email, phone, role, created_at)
            VALUES (?, ?, ?, ?, 'customer', ?)
            """, (owner_id, f"Customer {owner_id}", f"{owner_id.lower()}@example.com", "+91 98000 00000", now_str))

        # Check if there is an existing active document of this type for this owner
        cursor.execute("""
        SELECT id, version FROM customer_documents
        WHERE owner_id = ? AND document_type = ? AND is_active = 1
        ORDER BY version DESC LIMIT 1
        """, (owner_id, document_type))
        prev_row = cursor.fetchone()
        version = (prev_row["version"] + 1) if prev_row else 1

        if prev_row:
            # Supersede previous active document
            cursor.execute("UPDATE customer_documents SET is_active = 0 WHERE id = ?", (prev_row["id"],))

        cursor.execute("""
        INSERT INTO customer_documents (
            owner_id, document_type, original_filename, stored_filename, file_path,
            file_size, file_hash, upload_date, expiry_date, verification_status,
            rejection_reason, version, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            owner_id, document_type, safe_orig, stored_filename, real_path,
            file_size, file_hash, now_str, clean_expiry, initial_status,
            rejection_reason, version, now_str, now_str
        ))
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()

        cls.log_audit(doc_id, owner_id, actor_id, actor_role, "UPLOAD", ip_address, f"Uploaded {document_type} (v{version}) - Hash: {file_hash[:12]}...")

        return {
            "success": True,
            "document_id": doc_id,
            "owner_id": owner_id,
            "document_type": document_type,
            "original_filename": safe_orig,
            "file_size": file_size,
            "file_hash": file_hash,
            "upload_date": now_str,
            "expiry_date": clean_expiry,
            "verification_status": initial_status,
            "rejection_reason": rejection_reason,
            "version": version
        }

    @classmethod
    def replace_document(
        cls,
        doc_id: int,
        original_filename: str,
        file_bytes: bytes,
        expiry_date: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: str = "customer",
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Replaces an existing (e.g. expired or rejected) document with a newly uploaded version.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()
        conn.close()

        if not doc:
            raise ValueError(f"Document ID {doc_id} not found.")

        owner_id = doc["owner_id"]
        doc_type = doc["document_type"]

        if not actor_id:
            actor_id = owner_id

        if not cls.check_authorization(owner_id, actor_id, actor_role):
            cls.log_audit(doc_id, owner_id, actor_id, actor_role, "SECURITY_VIOLATION", ip_address, "Unauthorized replacement attempt")
            raise PermissionError("Access Denied: You are not authorized to replace another customer's document.")

        # Upload as new version using upload_document
        res = cls.upload_document(
            owner_id=owner_id,
            document_type=doc_type,
            original_filename=original_filename,
            file_bytes=file_bytes,
            expiry_date=expiry_date,
            actor_id=actor_id,
            actor_role=actor_role,
            ip_address=ip_address
        )

        cls.log_audit(res["document_id"], owner_id, actor_id, actor_role, "REPLACE", ip_address, f"Replaced previous document ID {doc_id} with new version {res['version']}")
        return res

    @classmethod
    def get_customer_documents(cls, owner_id: str, actor_id: Optional[str] = None, actor_role: str = "customer") -> List[Dict[str, Any]]:
        """
        Retrieves all active documents for a customer with row-level security.
        Automatically updates statuses for any documents that have reached their expiry date.
        """
        if not actor_id:
            actor_id = owner_id

        if not cls.check_authorization(owner_id, actor_id, actor_role):
            raise PermissionError("Access Denied: Cross-customer isolation prevents reading other customers' documents.")

        conn = get_connection()
        cursor = conn.cursor()

        # Update any expired documents automatically
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute("""
        UPDATE customer_documents
        SET verification_status = 'expired',
            rejection_reason = 'Document passed valid expiry date (' || expiry_date || '). Please upload a renewed document.',
            updated_at = ?
        WHERE owner_id = ? AND is_active = 1 AND expiry_date IS NOT NULL AND expiry_date < ? AND verification_status != 'expired'
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), owner_id, today_str))
        conn.commit()

        cursor.execute("""
        SELECT * FROM customer_documents
        WHERE owner_id = ? AND is_active = 1
        ORDER BY document_type ASC
        """, (owner_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Add computed flags
        for doc in rows:
            doc["is_expired"] = bool(doc.get("expiry_date") and doc["expiry_date"] < today_str)
            doc["can_replace"] = doc["verification_status"] in ["rejected", "expired"]

        return rows

    @classmethod
    def get_document_for_access(
        cls,
        doc_id: int,
        actor_id: str,
        actor_role: str = "customer",
        action: str = "PREVIEW",
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Secure document file accessor for preview or download.
        Guarantees RLS, directory traversal safety, and audit logging.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()
        conn.close()

        if not doc:
            raise ValueError(f"Document ID {doc_id} not found.")

        doc_dict = dict(doc)
        owner_id = doc_dict["owner_id"]

        if not cls.check_authorization(owner_id, actor_id, actor_role):
            cls.log_audit(doc_id, owner_id, actor_id, actor_role, "SECURITY_VIOLATION", ip_address, f"Unauthorized {action} attempt on document {doc_id}")
            raise PermissionError(f"Access Denied: You do not have permission to {action.lower()} this document.")

        file_path = doc_dict["file_path"]
        storage_dir = cls.get_storage_dir()

        # Verify path containment
        real_path = os.path.abspath(file_path)
        if os.path.commonpath([real_path, storage_dir]) != storage_dir or not os.path.exists(real_path):
            cls.log_audit(doc_id, owner_id, actor_id, actor_role, "FILE_NOT_FOUND", ip_address, f"File missing from private storage: {file_path}")
            raise FileNotFoundError("Document binary is missing from private storage repository.")

        # Log authorized access
        cls.log_audit(doc_id, owner_id, actor_id, actor_role, action, ip_address, f"Authorized {action.lower()} of {doc_dict['document_type']} by {actor_id} ({actor_role})")

        return {
            "document_id": doc_id,
            "owner_id": owner_id,
            "document_type": doc_dict["document_type"],
            "original_filename": doc_dict["original_filename"],
            "file_path": real_path,
            "file_size": doc_dict["file_size"],
            "verification_status": doc_dict["verification_status"]
        }

    @classmethod
    def review_document(
        cls,
        doc_id: int,
        new_status: str,
        rejection_reason: Optional[str],
        actor_id: str,
        actor_role: str,
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Bank manager document verification/rejection review workflow.
        """
        if actor_role not in ["bank_manager", "admin", "auditor"]:
            cls.log_audit(doc_id, "SYSTEM", actor_id, actor_role, "SECURITY_VIOLATION", ip_address, "Non-manager attempted document status adjudication")
            raise PermissionError("Access Denied: Only bank managers or compliance officers may review document verification status.")

        if new_status not in ["verified", "rejected", "pending_verification"]:
            raise ValueError(f"Invalid review status '{new_status}'. Allowed: verified, rejected, pending_verification.")

        if new_status == "rejected" and not (rejection_reason and rejection_reason.strip()):
            raise ValueError("Rejection reason is mandatory when rejecting a customer document.")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()

        if not doc:
            conn.close()
            raise ValueError(f"Document ID {doc_id} not found.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        UPDATE customer_documents
        SET verification_status = ?,
            rejection_reason = ?,
            verified_by = ?,
            verified_at = ?,
            updated_at = ?
        WHERE id = ?
        """, (new_status, rejection_reason if new_status == "rejected" else None, actor_id, now_str, now_str, doc_id))
        conn.commit()
        conn.close()

        cls.log_audit(doc_id, doc["owner_id"], actor_id, actor_role, f"STATUS_CHANGE_{new_status.upper()}", ip_address, f"Status updated to '{new_status}' by {actor_id}. Reason: {rejection_reason or 'Approved'}")

        return {
            "success": True,
            "document_id": doc_id,
            "verification_status": new_status,
            "rejection_reason": rejection_reason if new_status == "rejected" else None,
            "verified_by": actor_id,
            "verified_at": now_str
        }

    @classmethod
    def get_audit_logs(cls, owner_id: Optional[str] = None, doc_id: Optional[int] = None, actor_id: str = "MGR-001", actor_role: str = "bank_manager") -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM document_audit_logs WHERE 1=1"
        params = []

        if actor_role not in ["bank_manager", "admin", "auditor"]:
            query += " AND owner_id = ?"
            params.append(actor_id)
        elif owner_id:
            query += " AND owner_id = ?"
            params.append(owner_id)

        if doc_id:
            query += " AND document_id = ?"
            params.append(doc_id)

        query += " ORDER BY id DESC LIMIT 50"
        cursor.execute(query, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
