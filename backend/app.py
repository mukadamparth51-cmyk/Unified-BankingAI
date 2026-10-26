"""
Unified Banking AI - Enterprise API & Application Server
Hosts:
1. Fraud Detector AI (Transaction Scanner & AI Direct Refund Recovery Engine with Local Gemma 4)
2. Smart ID (Digital KYC & Biometrics)
3. AI Loan Detector - AI LoanFast 72
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from database import get_connection, init_db
from smart_id import SmartIDEngine
from smart_id_docs import SmartIDDocumentService
from loanfast72 import AILoanFast72Engine
from loan_checklist import LoanChecklistEngine

# Modular Fraud Detector & Local Gemma 4 Engine imports
from fraud_detector.ai.gemma_config import GemmaConfig, HardwareProfiler
from fraud_detector.ai.gemma_service import GemmaService
from fraud_detector.rules.eligibility_engine import EligibilityEngine
from fraud_detector.recovery.recovery_service import RecoveryService
from fraud_detector.evidence.evidence_service import EvidenceService

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=None)
CORS(app)

# Initialize database schema and seeds on startup
init_db()

# -------------------------------------------------------------
# Static Frontend Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

# -------------------------------------------------------------
# Local Gemma 4 AI Diagnostics & Configuration
# -------------------------------------------------------------
@app.route("/api/gemma/status", methods=["GET"])
def get_gemma_status():
    """
    Returns detected hardware profile (RAM, CPU, GPU, CUDA),
    model selection (E2B / E4B), and local offline engine status.
    """
    status = GemmaConfig.get_status()
    return jsonify(status)

@app.route("/api/gemma/download", methods=["POST"])
def setup_gemma_model():
    """
    Manages local model weights setup and verifies local directory.
    """
    models_dir = GemmaConfig.MODELS_DIR
    os.makedirs(models_dir, exist_ok=True)
    return jsonify({
        "status": "LOCAL_SETUP_READY",
        "models_dir": models_dir,
        "active_model": GemmaConfig.MODEL_NAME,
        "device": GemmaConfig.DEVICE,
        "instructions": "Place Gemma 4 E2B/E4B GGUF or SafeTensors weights in backend/models/gemma-4/ for direct weight-accelerated local execution."
    })

# -------------------------------------------------------------
# Module 1: Fraud Detector AI - AI Direct Refund Recovery Engine
# -------------------------------------------------------------

@app.route("/api/fraud/report", methods=["POST"])
def report_fraud():
    """
    Section 1: Report Fraud Intake
    Executes Local Gemma 4 AI Case Analysis (Section 2) & Deterministic Eligibility (Section 4)
    """
    data = request.json or {}

    # Basic validations
    customer_name = str(data.get("customer_name", "")).strip()
    amount_str = str(data.get("amount_reported", "0")).replace(",", "").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({"error": "Transaction amount must be a positive number."}), 400
    except ValueError:
        return jsonify({"error": "Invalid transaction amount format."}), 400

    txn_time = str(data.get("transaction_time", "")).strip()
    utr_number = str(data.get("utr_number", "")).strip()
    payment_method = str(data.get("payment_method", "UPI")).strip()
    bank_name = str(data.get("bank_name", "Unknown Bank")).strip()
    description = str(data.get("description", "")).strip()
    beneficiary = str(data.get("beneficiary_details", "")).strip()
    customer_email = str(data.get("customer_email", "")).strip()
    customer_phone = str(data.get("customer_phone", "")).strip()
    evidence_files = data.get("evidence_files", [])

    if not customer_name:
        return jsonify({"error": "Customer name is mandatory."}), 400
    if not txn_time:
        return jsonify({"error": "Transaction date and time are mandatory."}), 400
    if not description:
        return jsonify({"error": "Description of the fraud incident is mandatory."}), 400

    case_context = {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "amount_reported": amount,
        "transaction_time": txn_time,
        "utr_number": utr_number,
        "payment_method": payment_method,
        "bank_name": bank_name,
        "beneficiary_details": beneficiary,
        "description": description,
        "evidence_files": evidence_files
    }

    # 1. Local Gemma 4 AI Analysis (Isolated behind GemmaService)
    gemma_service = GemmaService.get_instance()
    ai_result = gemma_service.analyze_fraud_case(case_context)
    structured_ai = ai_result["structured_output"]

    # 2. Authoritative Deterministic Eligibility Assessment (Rules Engine)
    eligibility_result = EligibilityEngine.evaluate(case_context, ai_result)

    # Initial status
    if structured_ai.get("missing_information"):
        initial_status = "Evidence Required"
    else:
        initial_status = "Ready for Review"

    case_ref = f"UB-CASE-2026-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Persist in DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO fraud_cases (
        case_ref, customer_name, customer_email, customer_phone,
        amount_reported, amount_requested, amount_approved, amount_recovered,
        currency, transaction_time, report_time, utr_number, payment_method,
        bank_name, beneficiary_details, description, fraud_type,
        fraud_classification_details, eligibility_status, eligibility_details,
        current_status, status_reason, next_actions, pending_documents,
        submission_ref, submission_timestamp, idempotency_key, gateway_mode,
        verification_source, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, 0.0, 0.0, 'INR', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 'DRAFT_MANUAL', NULL, ?, ?)
    """, (
        case_ref, customer_name, customer_email, customer_phone,
        amount, amount, txn_time, now_str, utr_number, payment_method,
        bank_name, beneficiary, structured_ai.get("case_summary", description),
        structured_ai.get("fraud_type"), json.dumps(ai_result),
        eligibility_result["status"], json.dumps(eligibility_result),
        initial_status, eligibility_result["reason"],
        json.dumps(structured_ai.get("recommended_actions", [])),
        json.dumps(structured_ai.get("missing_information", [])),
        now_str, now_str
    ))

    case_id = cursor.lastrowid

    # Append History
    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, 'REPORT_CREATED', 'CUSTOMER', 'Draft', ?, ?, 1)
    """, (case_id, case_ref, now_str, initial_status, f"Report lodged. Local Gemma 4 classified: {structured_ai.get('fraud_type')}."))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "case_id": case_id,
        "case_ref": case_ref,
        "security_warnings": ai_result.get("security_warnings", []),
        "ai_engine": ai_result.get("ai_engine", {}),
        "classification": {
            "primary_classification": f"UPI QR / {structured_ai.get('fraud_type', '').replace('_', ' ').title()}" if "qr" in description.lower() else structured_ai.get("fraud_type"),
            "details": structured_ai
        },
        "structured_output": structured_ai,
        "eligibility": eligibility_result,
        "policy_rag": ai_result.get("policy_rag", {}),
        "current_status": initial_status,
        "disclaimer": ai_result.get("disclaimer", ""),
        "india_emergency_channels": {
            "helpline": "1930",
            "portal": "https://cybercrime.gov.in/",
            "advisory": "Report on 1930 within the 2-hour Golden Hour window to initiate immediate beneficiary freeze."
        }
    })

@app.route("/api/fraud/cases", methods=["GET"])
def get_fraud_cases():
    """
    Section 8: Recovery Tracking Dashboard - List all cases
    """
    status_filter = request.args.get("status")
    bank_filter = request.args.get("bank")
    search = request.args.get("q", "").strip().lower()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fraud_cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    filtered = []
    for c in cases:
        if status_filter and c["current_status"] != status_filter:
            continue
        if bank_filter and c["bank_name"] != bank_filter:
            continue
        if search:
            match = (
                search in c["case_ref"].lower() or
                search in c["customer_name"].lower() or
                search in c["utr_number"].lower() or
                search in (c["description"] or "").lower() or
                search in c["bank_name"].lower()
            )
            if not match:
                continue
        filtered.append(c)

    return jsonify({"cases": filtered, "total_count": len(filtered)})

@app.route("/api/fraud/cases/<int:case_id>", methods=["GET"])
def get_case_details(case_id: int):
    """
    Retrieves complete case dossier including history, evidence, consents, and submissions.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fraud_cases WHERE id = ?", (case_id,))
    case = cursor.fetchone()
    if not case:
        conn.close()
        return jsonify({"error": "Case not found."}), 404

    case_dict = dict(case)

    # History
    cursor.execute("SELECT * FROM case_history WHERE case_id = ? ORDER BY id ASC", (case_id,))
    case_dict["history"] = [dict(r) for r in cursor.fetchall()]

    # Evidence files
    cursor.execute("SELECT * FROM evidence_files WHERE case_id = ? ORDER BY id DESC", (case_id,))
    case_dict["evidence_files"] = [dict(r) for r in cursor.fetchall()]

    # Consents
    cursor.execute("SELECT * FROM customer_consents WHERE case_id = ? ORDER BY id DESC", (case_id,))
    case_dict["consents"] = [dict(r) for r in cursor.fetchall()]

    # Submissions
    cursor.execute("SELECT * FROM bank_dispute_submissions WHERE case_id = ? ORDER BY id DESC", (case_id,))
    case_dict["submissions"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify(case_dict)

@app.route("/api/fraud/cases/<int:case_id>/upload-evidence", methods=["POST"])
def upload_evidence(case_id: int):
    """
    Section 3: Evidence Upload & Forensic Analysis
    Computes SHA-256 hash, validates file bounds, and checks discrepancies.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file supplied."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    filename = secure_filename(file.filename)
    safe_name = f"{case_id}_{uuid.uuid4().hex[:6]}_{filename}"
    save_path = os.path.join(UPLOADS_DIR, safe_name)
    file.save(save_path)

    file_size = os.path.getsize(save_path)
    is_valid, err_msg = EvidenceService.validate_file(filename, file_size)
    if not is_valid:
        os.remove(save_path)
        return jsonify({"error": err_msg}), 400

    sha256 = EvidenceService.calculate_sha256(save_path)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check for discrepancies with case description
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, current_status FROM fraud_cases WHERE id = ?", (case_id,))
    case_row = cursor.fetchone()
    case_desc = case_row["description"] if case_row else ""
    c_status = case_row["current_status"] if case_row else "Draft"

    discrepancies = EvidenceService.analyze_evidence_discrepancy(case_desc, filename)

    cursor.execute("""
    INSERT INTO evidence_files (case_id, filename, file_type, file_size, sha256_hash, upload_timestamp, storage_path)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (case_id, filename, file.content_type or "application/octet-stream", file_size, sha256, now_str, save_path))

    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, (SELECT case_ref FROM fraud_cases WHERE id = ?), ?, 'EVIDENCE_UPLOADED', 'CUSTOMER', NULL, NULL, ?, 1)
    """, (case_id, case_id, now_str, f"Evidence uploaded: {filename} ({file_size} bytes). SHA-256: {sha256[:16]}..."))

    if c_status == "Evidence Required":
        cursor.execute("UPDATE fraud_cases SET current_status = 'Ready for Review', updated_at = ? WHERE id = ?", (now_str, case_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "filename": filename,
        "sha256_hash": sha256,
        "file_size": file_size,
        "discrepancies_detected": discrepancies,
        "upload_timestamp": now_str
    })

@app.route("/api/fraud/cases/<int:case_id>/prepare-dispute", methods=["POST"])
def prepare_dispute(case_id: int):
    """
    Section 5: Refund/Dispute Request Preparation (ISO 20022 and Draft Notice)
    """
    try:
        package = RecoveryService.prepare_request_package(case_id)
        return jsonify({"success": True, "package": package})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/fraud/cases/<int:case_id>/consent", methods=["POST"])
def record_customer_consent(case_id: int):
    """
    Section 6: Customer Authorization & Consent
    """
    data = request.json or {}
    consented_by = data.get("consented_by", "Customer")
    ip_address = request.remote_addr or "127.0.0.1"
    declarations = {
        "declaration_truth": data.get("declaration_truth", False),
        "dispute_authorization": data.get("dispute_authorization", False),
        "non_guarantee_acknowledgment": data.get("non_guarantee_acknowledgment", False)
    }

    try:
        res = RecoveryService.record_customer_consent(case_id, consented_by, ip_address, declarations)
        return jsonify({"success": True, "consent": res})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/fraud/cases/<int:case_id>/submit-reversal", methods=["POST"])
def submit_reversal_request(case_id: int):
    """
    Section 7: Submission (Idempotent Gateway Dispatch)
    """
    data = request.json or {}
    idempotency_key = data.get("idempotency_key") or str(uuid.uuid4())
    gateway_mode = data.get("gateway_mode", "SIMULATION_SANDBOX")

    try:
        result = RecoveryService.submit_request(case_id, idempotency_key, gateway_mode)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/fraud/cases/<int:case_id>/record-recovery", methods=["POST"])
@app.route("/api/fraud/cases/record-recovery", methods=["POST"])
def record_recovery(case_id: int = None):
    """
    Section 8: Verified Recovery Recording (Authorized Provider Only)
    """
    data = request.json or {}
    if case_id is None:
        case_id = data.get("case_id")
    if not case_id:
        return jsonify({"error": "Case ID is required."}), 400

    amount_str = str(data.get("amount_recovered", "0")).replace(",", "").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({"error": "Recovered amount must be greater than zero."}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount format."}), 400

    settlement_ref = str(data.get("settlement_ref", "")).strip()
    authorized_source = str(data.get("authorized_source", "")).strip()

    if not settlement_ref or not authorized_source:
        return jsonify({"error": "Settlement reference and authorized source are strictly required."}), 400

    try:
        res = RecoveryService.record_verified_recovery(case_id, amount, settlement_ref, authorized_source)
        return jsonify({"success": True, "recovery": res})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/fraud/cases/<int:case_id>/update-status", methods=["POST"])
def update_case_status(case_id: int):
    """
    Updates status across the 11 official statuses with audit trail.
    """
    data = request.json or {}
    new_status = data.get("status")
    reason = data.get("reason", "Status updated by fraud recovery officer.")
    actor = data.get("actor", "FRAUD_INVESTIGATOR")

    valid_statuses = [
        "Draft", "Evidence Required", "Ready for Review", "Submitted",
        "Under Investigation", "Additional Information Required",
        "Refund/Recovery Approved", "Partially Recovered", "Recovered",
        "Rejected", "Closed"
    ]

    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    if new_status in ["Refund/Recovery Approved", "Partially Recovered", "Recovered"]:
        if not data.get("settlement_ref"):
            return jsonify({"error": "Guardrail Enforcement: Cannot transition to recovered status without official settlement reference from authorized provider."}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_status, case_ref FROM fraud_cases WHERE id = ?", (case_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Case not found."}), 404

    old_status = row["current_status"]
    case_ref = row["case_ref"]

    cursor.execute("""
    UPDATE fraud_cases
    SET current_status = ?, status_reason = ?, updated_at = ?
    WHERE id = ?
    """, (new_status, reason, now_str, case_id))

    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, 'STATUS_TRANSITION', ?, ?, ?, ?, 1)
    """, (case_id, case_ref, now_str, actor, old_status, new_status, reason))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "old_status": old_status, "new_status": new_status})

@app.route("/api/fraud/metrics", methods=["GET"])
def get_recovery_metrics():
    """
    Section 8: Recovery Tracking Dashboard KPIs
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        SUM(amount_reported) as total_reported,
        SUM(amount_requested) as total_requested,
        SUM(amount_approved) as total_approved,
        SUM(amount_recovered) as total_recovered,
        COUNT(*) as total_cases
    FROM fraud_cases
    """)
    totals = dict(cursor.fetchone())

    cursor.execute("SELECT current_status, COUNT(*) as count FROM fraud_cases GROUP BY current_status")
    status_counts = {r["current_status"]: r["count"] for r in cursor.fetchall()}

    conn.close()

    total_reported = totals.get("total_reported") or 0.0
    total_requested = totals.get("total_requested") or 0.0
    total_approved = totals.get("total_approved") or 0.0
    total_recovered = totals.get("total_recovered") or 0.0
    remaining_recoverable = max(0.0, total_requested - total_recovered)

    return jsonify({
        "reported_amount": total_reported,
        "requested_amount": total_requested,
        "approved_amount": total_approved,
        "recovered_amount": total_recovered,
        "remaining_amount": remaining_recoverable,
        "total_cases": totals.get("total_cases") or 0,
        "status_distribution": status_counts
    })

@app.route("/api/fraud/scan-transaction", methods=["POST"])
def scan_transaction():
    """
    Module 1: General Transaction Fraud Scanner (Preserving existing capability)
    """
    data = request.json or {}
    account_id = data.get("account_id", "AC-DEMO-001")
    amount = float(data.get("amount", 0))
    channel = data.get("channel", "UPI")

    rules_triggered = []
    risk_score = 15

    if amount > 100000:
        rules_triggered.append("High value transaction exceeding ₹1,00,000 ceiling")
        risk_score += 35
    if channel.upper() == "UPI" and amount > 50000:
        rules_triggered.append("Elevated UPI ticket size (> ₹50,000)")
        risk_score += 20
    if "night" in data.get("time_of_day", "").lower() or data.get("unusual_hour"):
        rules_triggered.append("Unusual hour velocity trigger (01:00 - 05:00 IST)")
        risk_score += 25

    if risk_score >= 70:
        risk_level = "High"
        recommendation = "Hold transaction and require step-up biometric/OTP re-authentication."
    elif risk_score >= 40:
        risk_level = "Medium"
        recommendation = "Proceed with transaction monitor flag; alert account holder via instant SMS."
    else:
        risk_level = "Low"
        recommendation = "Low fraud probability. Straight-through automated processing approved."

    scan_ref = f"SCAN-{uuid.uuid4().hex[:6].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transaction_fraud_scans (scan_ref, account_id, amount, channel, risk_score, risk_level, rules_triggered, recommended_action, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scan_ref, account_id, amount, channel, risk_score, risk_level, json.dumps(rules_triggered), recommendation, now_str))
    conn.commit()
    conn.close()

    return jsonify({
        "scan_ref": scan_ref,
        "account_id": account_id,
        "amount": amount,
        "channel": channel,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "rules_triggered": rules_triggered,
        "recommended_action": recommendation,
        "created_at": now_str
    })

def get_auth_context():
    """
    Simulates enterprise customer authentication and role context.
    Retrieves caller identity (actor_id/actor_role) and target customer ID.
    Enforces Row-Level Security: non-managers can only access their own documents.
    """
    actor_id = (
        request.headers.get("X-Actor-Id") or
        request.headers.get("X-Customer-Id") or
        request.args.get("actor_id") or
        "CUST-101"
    ).strip().upper()

    actor_role = (
        request.headers.get("X-Actor-Role") or
        request.args.get("actor_role") or
        (request.json.get("actor_role") if request.is_json and request.json else None) or
        request.form.get("actor_role") or
        "customer"
    ).strip().lower()

    # The customer whose documents or account are being accessed
    owner_id = (
        request.args.get("customer_id") or
        request.form.get("customer_id") or
        (request.json.get("customer_id") if request.is_json and request.json else None) or
        actor_id
    ).strip().upper()

    return owner_id, actor_id, actor_role

# -------------------------------------------------------------
# Module 2: Smart ID - Digital KYC, Liveness & Document Vault
# -------------------------------------------------------------

@app.route("/api/smart-id/verify", methods=["POST"])
def smart_id_verify():
    data = request.json or {}
    full_name = data.get("full_name", "")
    id_type = data.get("id_type", "Aadhaar Card")
    id_number = data.get("id_number", "")

    if not full_name or not id_number:
        return jsonify({"error": "Full name and ID number are required."}), 400

    result = SmartIDEngine.verify_identity(full_name, id_type, id_number)
    return jsonify(result)

@app.route("/api/smart-id/verifications", methods=["GET"])
def get_smart_id_verifications():
    return jsonify({"verifications": SmartIDEngine.get_recent_verifications()})

@app.route("/api/smart-id/customers", methods=["GET"])
def get_customers():
    """Returns available test customers for demo switching and authentication simulation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id, full_name, email, phone, role, created_at FROM customers ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"customers": rows})

@app.route("/api/smart-id/documents", methods=["GET"])
def get_customer_documents():
    """
    Returns active PDF documents for the authenticated customer.
    Enforces Row-Level Security (RLS) and checks expiry.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    try:
        docs = SmartIDDocumentService.get_customer_documents(owner_id, actor_id, actor_role)
        return jsonify({
            "success": True,
            "customer_id": owner_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "documents": docs
        })
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/smart-id/documents/upload", methods=["POST"])
def upload_customer_document():
    """
    Uploads a customer PDF document to private storage.
    Validates file format, magic bytes (%PDF), max size (10MB), and records metadata with SHA-256 hash.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please select a valid PDF document."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    document_type = request.form.get("document_type", "PAN Card").strip()
    expiry_date = request.form.get("expiry_date", "").strip() or None
    ip_addr = request.remote_addr or "127.0.0.1"

    file_bytes = file.read()
    try:
        res = SmartIDDocumentService.upload_document(
            owner_id=owner_id,
            document_type=document_type,
            original_filename=file.filename,
            file_bytes=file_bytes,
            expiry_date=expiry_date,
            actor_id=actor_id,
            actor_role=actor_role,
            ip_address=ip_addr
        )
        return jsonify(res)
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/smart-id/documents/<int:doc_id>/preview", methods=["GET"])
def preview_customer_document(doc_id: int):
    """
    Streams PDF document inline for authenticated preview.
    Prevents cross-customer data exposure via RLS.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    ip_addr = request.remote_addr or "127.0.0.1"
    try:
        doc_info = SmartIDDocumentService.get_document_for_access(
            doc_id=doc_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="PREVIEW",
            ip_address=ip_addr
        )
        return send_file(
            doc_info["file_path"],
            mimetype="application/pdf",
            as_attachment=False,
            download_name=doc_info["original_filename"]
        )
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except FileNotFoundError as fe:
        return jsonify({"error": str(fe)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/smart-id/documents/<int:doc_id>/download", methods=["GET"])
def download_customer_document(doc_id: int):
    """
    Downloads PDF document attachment for authorized customer or bank manager.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    ip_addr = request.remote_addr or "127.0.0.1"
    try:
        doc_info = SmartIDDocumentService.get_document_for_access(
            doc_id=doc_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="DOWNLOAD",
            ip_address=ip_addr
        )
        return send_file(
            doc_info["file_path"],
            mimetype="application/pdf",
            as_attachment=True,
            download_name=doc_info["original_filename"]
        )
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except FileNotFoundError as fe:
        return jsonify({"error": str(fe)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/smart-id/documents/<int:doc_id>/replace", methods=["POST"])
def replace_customer_document(doc_id: int):
    """
    Allows customers to replace expired or rejected documents with a new version.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    if "file" not in request.files:
        return jsonify({"error": "Replacement PDF file is required."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    expiry_date = request.form.get("expiry_date", "").strip() or None
    ip_addr = request.remote_addr or "127.0.0.1"
    file_bytes = file.read()

    try:
        res = SmartIDDocumentService.replace_document(
            doc_id=doc_id,
            original_filename=file.filename,
            file_bytes=file_bytes,
            expiry_date=expiry_date,
            actor_id=actor_id,
            actor_role=actor_role,
            ip_address=ip_addr
        )
        return jsonify(res)
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/smart-id/documents/<int:doc_id>/review", methods=["POST"])
def review_customer_document(doc_id: int):
    """
    Bank manager review: approve (verified) or reject document with mandatory reason.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    data = request.json or {}
    new_status = data.get("status", "verified")
    rejection_reason = data.get("rejection_reason")
    ip_addr = request.remote_addr or "127.0.0.1"

    try:
        res = SmartIDDocumentService.review_document(
            doc_id=doc_id,
            new_status=new_status,
            rejection_reason=rejection_reason,
            actor_id=actor_id,
            actor_role=actor_role,
            ip_address=ip_addr
        )
        return jsonify(res)
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/smart-id/documents/audit-logs", methods=["GET"])
def get_document_audit_logs():
    """Retrieves document audit trail."""
    owner_id, actor_id, actor_role = get_auth_context()
    doc_id_param = request.args.get("doc_id")
    doc_id = int(doc_id_param) if doc_id_param and doc_id_param.isdigit() else None
    logs = SmartIDDocumentService.get_audit_logs(owner_id=owner_id, doc_id=doc_id, actor_id=actor_id, actor_role=actor_role)
    return jsonify({"audit_logs": logs})

# -------------------------------------------------------------
# Module 3: AI Loan Detector — AI LoanFast 72 & Smart Predictor
# -------------------------------------------------------------

@app.route("/api/loan/types", methods=["GET"])
def get_loan_types():
    """Returns configured loan types and statutory document requirements."""
    return jsonify({"loan_types": LoanChecklistEngine.get_supported_loan_types()})

@app.route("/api/loan/checklist", methods=["GET"])
def get_loan_document_checklist():
    """
    Evaluates current customer's document completeness against statutory requirements for the selected loan type.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    loan_type = request.args.get("loan_type", "Instant Fast-Track Loan (LoanFast 72)").strip()
    try:
        checklist = LoanChecklistEngine.evaluate_checklist(
            customer_id=owner_id,
            loan_type=loan_type,
            actor_id=actor_id,
            actor_role=actor_role
        )
        return jsonify(checklist)
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/loan/evaluate", methods=["POST"])
def evaluate_loan():
    """
    Gatekeeper underwriting route:
    Verifies that all required documents are present, not expired, and not rejected.
    Blocks evaluation if checklist is incomplete.
    """
    owner_id, actor_id, actor_role = get_auth_context()
    data = request.json or {}

    applicant_name = data.get("applicant_name", "")
    monthly_income = float(data.get("monthly_income", 0))
    existing_obligations = float(data.get("existing_obligations", 0))
    cibil_score = int(data.get("cibil_score", 700))
    loan_requested = float(data.get("loan_requested", 100000))
    tenor_months = int(data.get("tenor_months", 24))
    employment_type = data.get("employment_type", "Salaried")
    loan_type = data.get("loan_type", "Instant Fast-Track Loan (LoanFast 72)")
    bypass_check = data.get("bypass_doc_check", False)

    if not applicant_name or monthly_income <= 0:
        return jsonify({"error": "Valid applicant name and positive monthly income are required."}), 400

    # 1. Gatekeeping Document Checklist Verification (unless explicitly bypassed in legacy test)
    checklist = None
    if not bypass_check:
        try:
            checklist = LoanChecklistEngine.evaluate_checklist(
                customer_id=owner_id,
                loan_type=loan_type,
                actor_id=actor_id,
                actor_role=actor_role
            )
        except Exception as e:
            return jsonify({"error": f"Document checklist error: {str(e)}"}), 400

        if not checklist["can_proceed"]:
            return jsonify({
                "success": False,
                "can_proceed": False,
                "error": "Document Checklist Incomplete: Statutory documents are missing, expired, or rejected.",
                "summary_status": "DOCUMENTS_REQUIRED",
                "blocking_reasons": checklist["blocking_reasons"],
                "checklist": checklist,
                "regulatory_disclaimer": checklist["regulatory_disclaimer"]
            }), 400

    # 2. Complete Checklist Allows Underwriting Evaluation Stage
    decision = AILoanFast72Engine.evaluate_loan(
        applicant_name=applicant_name,
        monthly_income=monthly_income,
        existing_obligations=existing_obligations,
        cibil_score=cibil_score,
        loan_requested=loan_requested,
        tenor_months=tenor_months,
        employment_type=employment_type,
        customer_id=owner_id,
        loan_type=loan_type,
        checklist_data=checklist
    )
    decision["can_proceed"] = True
    decision["success"] = True
    return jsonify(decision)

@app.route("/api/loan/applications", methods=["GET"])
def get_loan_applications():
    return jsonify({"applications": AILoanFast72Engine.get_recent_loans()})

@app.route("/<path:path>")
def static_proxy(path):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print(" UNIFIED BANKING AI - ENTERPRISE CORE")
    print(f" Server running at: http://127.0.0.1:{port}")
    print(f" Local Gemma 4 Model: {GemmaConfig.MODEL_NAME} ({GemmaConfig.QUANTIZATION} on {GemmaConfig.DEVICE})")
    print("=" * 70)
    app.run(host="127.0.0.1", port=port, debug=True)
