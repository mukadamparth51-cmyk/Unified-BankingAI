"""
Unified Banking AI - Database Module
Enterprise-grade SQLite schema and repository for:
1. Fraud Detector AI & AI Direct Refund Recovery Engine
2. Smart ID (Digital KYC & Biometrics)
3. AI Loan Detector - AI LoanFast 72
"""

import sqlite3
import os
import json
import hashlib
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "unified_banking.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fraud Detector AI & AI Direct Refund Recovery Engine Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fraud_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_ref TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_email TEXT,
        customer_phone TEXT,
        amount_reported REAL NOT NULL,
        amount_requested REAL NOT NULL,
        amount_approved REAL DEFAULT 0.0,
        amount_recovered REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'INR',
        transaction_time TEXT NOT NULL,
        report_time TEXT NOT NULL,
        utr_number TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        beneficiary_details TEXT,
        description TEXT NOT NULL,
        fraud_type TEXT,
        fraud_classification_details TEXT,
        eligibility_status TEXT NOT NULL,
        eligibility_details TEXT,
        current_status TEXT NOT NULL,
        status_reason TEXT,
        next_actions TEXT,
        pending_documents TEXT,
        submission_ref TEXT,
        submission_timestamp TEXT,
        idempotency_key TEXT,
        gateway_mode TEXT DEFAULT 'SIMULATION_SANDBOX',
        verification_source TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        case_ref TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        action_type TEXT NOT NULL,
        actor TEXT NOT NULL,
        status_from TEXT,
        status_to TEXT,
        details TEXT NOT NULL,
        verified INTEGER DEFAULT 0,
        FOREIGN KEY (case_id) REFERENCES fraud_cases(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        sha256_hash TEXT NOT NULL,
        upload_timestamp TEXT NOT NULL,
        storage_path TEXT,
        FOREIGN KEY (case_id) REFERENCES fraud_cases(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_consents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        case_ref TEXT NOT NULL,
        consent_type TEXT NOT NULL,
        consented_by TEXT NOT NULL,
        ip_address TEXT,
        consent_text TEXT NOT NULL,
        digital_signature_hash TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES fraud_cases(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bank_dispute_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        idempotency_key TEXT UNIQUE NOT NULL,
        provider TEXT NOT NULL,
        gateway_mode TEXT NOT NULL,
        request_payload TEXT NOT NULL,
        response_payload TEXT NOT NULL,
        status_code INTEGER NOT NULL,
        reference_id TEXT NOT NULL,
        retry_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES fraud_cases(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_fraud_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_ref TEXT UNIQUE NOT NULL,
        account_id TEXT NOT NULL,
        amount REAL NOT NULL,
        channel TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        rules_triggered TEXT,
        recommended_action TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Smart ID Module Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smart_id_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        verification_ref TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        id_type TEXT NOT NULL,
        id_number_masked TEXT NOT NULL,
        ocr_confidence REAL NOT NULL,
        face_match_score REAL NOT NULL,
        liveness_detected INTEGER NOT NULL,
        aml_status TEXT NOT NULL,
        pep_flag INTEGER DEFAULT 0,
        risk_score INTEGER NOT NULL,
        verification_status TEXT NOT NULL,
        certificate_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 3. AI Loan Detector - AI LoanFast 72 Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loan_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_ref TEXT UNIQUE NOT NULL,
        applicant_name TEXT NOT NULL,
        monthly_income REAL NOT NULL,
        existing_obligations REAL NOT NULL,
        dti_ratio REAL NOT NULL,
        cibil_score INTEGER NOT NULL,
        loan_requested REAL NOT NULL,
        tenor_months INTEGER NOT NULL,
        risk_tier TEXT NOT NULL,
        decision_status TEXT NOT NULL,
        approved_amount REAL DEFAULT 0.0,
        interest_rate REAL DEFAULT 0.0,
        monthly_emi REAL DEFAULT 0.0,
        turnaround_sla TEXT DEFAULT '72 Hours',
        xai_factors TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 4. Authenticated Customers & Smart ID Document Vault Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        role TEXT DEFAULT 'customer',
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL,
        document_type TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        stored_filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        file_hash TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        expiry_date TEXT,
        verification_status TEXT NOT NULL,
        rejection_reason TEXT,
        version INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        verified_by TEXT,
        verified_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES customers(customer_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        owner_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        ip_address TEXT,
        details TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed initial demonstration data if empty
    seed_demo_data(cursor, conn)

    conn.close()

def create_dummy_pdf(file_path: str, title: str, details: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if os.path.exists(file_path):
        return
    clean_title = re.sub(r'[()]', '', title)
    clean_details = re.sub(r'[()]', '', details)
    content = f"""BT
/F1 16 Tf
50 720 Td
({clean_title}) Tj
/F1 10 Tf
0 -30 Td
(SECURE BANKING DOCUMENT VAULT - SMART ID) Tj
0 -25 Td
({clean_details}) Tj
0 -25 Td
(Issued under RBI & UIDAI Compliance Standards) Tj
0 -25 Td
(Cryptographic Integrity: Verified by Unified Banking AI) Tj
ET"""
    stream_len = len(content.encode("latin1", errors="replace"))
    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{content}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000335 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
420
%%EOF"""
    with open(file_path, "wb") as f:
        f.write(pdf.encode("latin1", errors="replace"))

def seed_customers_and_documents(cursor, conn):
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        customers = [
            ("CUST-101", "Rohan Deshmukh", "rohan.d@example.com", "+91 98201 12345", "customer", now_str),
            ("CUST-102", "Priya Sharma", "priya.s@example.com", "+91 98765 43210", "customer", now_str),
            ("CUST-103", "Aarav Mehta", "aarav.m@example.com", "+91 98110 55432", "customer", now_str),
            ("MGR-001", "Vikram Malhotra", "manager@bank.com", "+91 99000 11223", "bank_manager", now_str)
        ]
        cursor.executemany("""
        INSERT INTO customers (customer_id, full_name, email, phone, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, customers)
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM customer_documents")
    if cursor.fetchone()[0] == 0:
        storage_dir = os.path.join(os.path.dirname(__file__), "storage", "documents")
        os.makedirs(storage_dir, exist_ok=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        demo_docs = [
            # Rohan Deshmukh (CUST-101) - Complete & Verified (All 4 docs valid)
            ("CUST-101", "PAN Card", "rohan_pan_card.pdf", "DOC_CUST101_PAN.pdf", "PAN Card - ROHAN DESHMUKH", "Permanent Account Number: ABCDE1234F", None, "verified", None, "MGR-001", now_str),
            ("CUST-101", "Aadhaar Card", "rohan_aadhaar.pdf", "DOC_CUST101_AADHAAR.pdf", "Aadhaar Card - ROHAN DESHMUKH", "Masked UIDAI Aadhaar: XXXX-XXXX-8921", None, "verified", None, "MGR-001", now_str),
            ("CUST-101", "Salary Slip", "rohan_salary_sep2026.pdf", "DOC_CUST101_SALARY.pdf", "Salary Slip Sep 2026 - ROHAN DESHMUKH", "Employer: Infosys Ltd | Net Pay: INR 1,45,000", None, "verified", None, "MGR-001", now_str),
            ("CUST-101", "Bank Statement", "rohan_hdfc_statement_6m.pdf", "DOC_CUST101_BANKSTMT.pdf", "HDFC Bank Statement - ROHAN DESHMUKH", "Account: 501002910291 | Period: Apr 2026 - Sep 2026", None, "verified", None, "MGR-001", now_str),

            # Priya Sharma (CUST-102) - Missing & Expired / Rejected docs
            ("CUST-102", "PAN Card", "priya_pan_card.pdf", "DOC_CUST102_PAN.pdf", "PAN Card - PRIYA SHARMA", "Permanent Account Number: PQRST5678K", None, "verified", None, "MGR-001", now_str),
            ("CUST-102", "Passport", "priya_passport_old.pdf", "DOC_CUST102_PASSPORT.pdf", "Passport - PRIYA SHARMA", "Passport No: Z9182736 - EXPIRED", "2025-01-15", "expired", "Document expired on 2025-01-15. Please replace with valid passport.", None, None),
            ("CUST-102", "Salary Slip", "priya_salary_damaged.pdf", "DOC_CUST102_SALARY.pdf", "Salary Slip - PRIYA SHARMA", "Employer: Tech Corp - REJECTED SCAN", None, "rejected", "Blurred scan, employer seal and net salary amount are illegible.", "MGR-001", now_str),
            # Note: Bank Statement is missing for Priya Sharma

            # Aarav Mehta (CUST-103) - Pending verification
            ("CUST-103", "PAN Card", "aarav_pan.pdf", "DOC_CUST103_PAN.pdf", "PAN Card - AARAV MEHTA", "Permanent Account Number: LMNOP9012Z", None, "verified", None, "MGR-001", now_str),
            ("CUST-103", "Aadhaar Card", "aarav_aadhaar.pdf", "DOC_CUST103_AADHAAR.pdf", "Aadhaar Card - AARAV MEHTA", "Masked UIDAI Aadhaar: XXXX-XXXX-4412", None, "verified", None, "MGR-001", now_str),
            ("CUST-103", "Salary Slip", "aarav_salary_oct2026.pdf", "DOC_CUST103_SALARY.pdf", "Salary Slip Oct 2026 - AARAV MEHTA", "Employer: Tata Consultancy Services | Net Pay: INR 1,25,000", None, "pending_verification", None, None, None),
            ("CUST-103", "Bank Statement", "aarav_sbi_statement_12m.pdf", "DOC_CUST103_BANKSTMT.pdf", "SBI Bank Statement - AARAV MEHTA", "Account: 3019283746 | Period: Oct 2025 - Sep 2026", None, "uploaded", None, None, None)
        ]

        for owner_id, doc_type, orig_fn, stored_fn, title, details, expiry, status, rej_reason, v_by, v_at in demo_docs:
            f_path = os.path.join(storage_dir, stored_fn)
            create_dummy_pdf(f_path, title, details)
            f_size = os.path.getsize(f_path) if os.path.exists(f_path) else 1024
            with open(f_path, "rb") as f:
                f_hash = hashlib.sha256(f.read()).hexdigest()

            cursor.execute("""
            INSERT INTO customer_documents (
                owner_id, document_type, original_filename, stored_filename, file_path,
                file_size, file_hash, upload_date, expiry_date, verification_status,
                rejection_reason, version, is_active, verified_by, verified_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?)
            """, (
                owner_id, doc_type, orig_fn, stored_fn, f_path,
                f_size, f_hash, now_str, expiry, status,
                rej_reason, v_by, v_at, now_str, now_str
            ))
            doc_id = cursor.lastrowid

            # Initial audit log
            cursor.execute("""
            INSERT INTO document_audit_logs (
                document_id, owner_id, actor_id, actor_role, action, ip_address, details, timestamp
            ) VALUES (?, ?, ?, 'customer', 'INITIAL_UPLOAD', '127.0.0.1', ?, ?)
            """, (doc_id, owner_id, owner_id, f"Document seeded for demo customer {owner_id} ({doc_type})", now_str))

        conn.commit()

def seed_demo_data(cursor, conn):
    seed_customers_and_documents(cursor, conn)
    cursor.execute("SELECT COUNT(*) FROM fraud_cases")
    if cursor.fetchone()[0] > 0:
        return

    now = datetime.now()
    t_minus_1h = datetime.fromtimestamp(now.timestamp() - 3600).strftime("%Y-%m-%d %H:%M:%S")
    t_minus_18h = datetime.fromtimestamp(now.timestamp() - 18 * 3600).strftime("%Y-%m-%d %H:%M:%S")
    t_minus_48h = datetime.fromtimestamp(now.timestamp() - 48 * 3600).strftime("%Y-%m-%d %H:%M:%S")
    t_minus_96h = datetime.fromtimestamp(now.timestamp() - 96 * 3600).strftime("%Y-%m-%d %H:%M:%S")

    # Seed Case 1: Under Investigation (UPI Collect Scam)
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
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "UB-CASE-2026-9041",
        "Rohan Deshmukh",
        "rohan.d@example.com",
        "+91 98201 12345",
        45000.0,
        45000.0,
        45000.0,
        0.0,
        "INR",
        t_minus_18h,
        t_minus_1h,
        "418290192837",
        "UPI",
        "HDFC Bank",
        "fraudulent_seller@oksbi (Acct: 3091823901, IFSC: SBIN0001823)",
        "Received a call from a fake OLX buyer who asked to scan a QR code to receive token advance payment. Instead, amount was debited from my account.",
        "UPI Collect / QR Code Deception",
        json.dumps({
            "confidence": 0.94,
            "category": "QR / UPI Reverse Debit Scam",
            "mule_risk": "High",
            "indicators": ["QR scan to receive money myth", "Instant debit", "Suspicious VPA"],
            "uncertainty_note": "Beneficiary account flagged in CFCFRMS; awaiting confirmation of funds hold from acquiring bank."
        }),
        "Potentially eligible",
        json.dumps({
            "basis": "RBI Circular RBI/2017-18/15 - Reported within 3 working days (18 hours elapsed)",
            "liability_tier": "Limited/Zero Contributory Review",
            "citation": "Section 6(a) Limiting Customer Liability"
        }),
        "Under Investigation",
        "Dispute dispatched to NPCI UDIR and Beneficiary Bank Nodal Officer. Lien placed on recipient wallet.",
        json.dumps([
            "Await NPCI UDIR 48-hour response cycle",
            "Dial 1930 to link State Cyber Cell NCRP Acknowledgment",
            "Monitor HDFC grievance ticket #HDFC-DIS-8910"
        ]),
        json.dumps([]),
        "UDIR-IN-2026-881923",
        t_minus_1h,
        "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
        "SIMULATION_SANDBOX",
        "NPCI UDIR Gateway Sandbox (Simulated Official Track)",
        t_minus_1h,
        t_minus_1h
    ))
    case_1_id = cursor.lastrowid

    # History for Case 1
    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_1_id, "UB-CASE-2026-9041", t_minus_18h, "INCIDENT_REPORTED", "CUSTOMER", "Draft", "Evidence Required", "Initial fraud report filed by customer for ₹45,000 via UPI.", 1))

    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_1_id, "UB-CASE-2026-9041", t_minus_1h, "AI_ANALYSIS_COMPLETE", "AI_ANALYZER", "Evidence Required", "Ready for Review", "AI classified fraud type as UPI QR Deception. Eligibility calculated as Potentially eligible.", 1))

    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_1_id, "UB-CASE-2026-9041", t_minus_1h, "DISPUTE_SUBMITTED", "BANK_UDIR_GATEWAY", "Ready for Review", "Under Investigation", "Formal dispute request submitted to NPCI UDIR network. Reference: UDIR-IN-2026-881923.", 1))

    # Seed Case 2: Partially Recovered (Unauthorized Card Skim)
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
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "UB-CASE-2026-8722",
        "Ananya Sharma",
        "ananya.s@example.com",
        "+91 99302 98765",
        82000.0,
        82000.0,
        82000.0,
        50000.0,
        "INR",
        t_minus_96h,
        t_minus_48h,
        "TXN992817263510",
        "Credit Card",
        "ICICI Bank",
        "Overseas Merchant POS DUBAI_DIGITAL_EXCHANGE",
        "Unauthorized international transaction debited from card while physical card was in possession. No OTP received or entered.",
        "Unauthorized Card Not Present / Skimming",
        json.dumps({
            "confidence": 0.98,
            "category": "Third-Party Card Compromise (Zero Liability Scope)",
            "mule_risk": "Critical",
            "indicators": ["Cross-border mismatch", "No 3DS challenge logged", "Cardholder in India"]
        }),
        "Potentially eligible",
        json.dumps({
            "basis": "RBI Zero Liability Framework - Third-party breach notified without customer contributory negligence",
            "liability_tier": "Zero Customer Liability",
            "citation": "RBI Circular Sec 6(a) Bank/System deficiency"
        }),
        "Partially Recovered",
        "Bank approved chargeback. First tranche of ₹50,000 credited back by issuing bank. Balance ₹32,000 under acquirer reconciliation.",
        json.dumps([
            "Monitor issuing bank settlement for balance ₹32,000",
            "Card replacement issued and old credentials permanently purged"
        ]),
        json.dumps([]),
        "ICICI-CB-2026-44019",
        t_minus_48h,
        "a71e4fae-1dec-22d0-b865-00a0c91e7ee1",
        "SIMULATION_SANDBOX",
        "ICICI Bank Dispute Clearing House (Verified Settlement Advice #ICICI-ST-882)",
        t_minus_96h,
        t_minus_18h
    ))
    case_2_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_2_id, "UB-CASE-2026-8722", t_minus_48h, "DISPUTE_SUBMITTED", "BANK_GATEWAY", "Ready for Review", "Submitted", "Chargeback filed under Reason Code 104: Fraudulent CNP Transaction.", 1))

    cursor.execute("""
    INSERT INTO case_history (case_id, case_ref, timestamp, action_type, actor, status_from, status_to, details, verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_2_id, "UB-CASE-2026-8722", t_minus_18h, "SETTLEMENT_CREDIT", "ICICI_DISPUTE_GATEWAY", "Submitted", "Partially Recovered", "Verified interim credit of ₹50,000 posted to customer card account. Acquirer response pending for ₹32,000.", 1))

    # Seed Case 3: Evidence Required (Remote Access Scam)
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
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "UB-CASE-2026-6105",
        "Vikram Singhania",
        "vikram.s@example.com",
        "+91 97110 54321",
        120000.0,
        120000.0,
        0.0,
        0.0,
        "INR",
        t_minus_48h,
        t_minus_18h,
        "IMPS4091823019",
        "Bank Transfer",
        "State Bank of India",
        "Beneficiary A/C: 918201928374 (Canara Bank)",
        "Caller posed as electricity department officer warning power disconnection. Directed me to install 'QuickSupport' app and approve a ₹10 test recharge. Later ₹1,20,000 was siphoned via IMPS.",
        "Remote Access Trojan / Screen Sharing Impersonation",
        json.dumps({
            "confidence": 0.96,
            "category": "Remote Desktop APK Takeover",
            "mule_risk": "Critical",
            "indicators": ["Screen-sharing app installed", "Electricity bill panic lure", "Immediate unauthorized IMPS"]
        }),
        "More information required",
        json.dumps({
            "basis": "Customer facilitated app installation but did not willingly transfer funds; Cyber Cell Acknowledgment needed to determine negligence tier",
            "liability_tier": "Conditional / Board Approved Evaluation",
            "citation": "Section 7 Customer Protection Framework"
        }),
        "Evidence Required",
        "Pending National Cyber Crime Reporting Portal (1930 / cybercrime.gov.in) complaint acknowledgment slip and bank SMS screenshot.",
        json.dumps([
            "Upload 1930 Cyber Crime Complaint Acknowledgment PDF/Image",
            "Upload Bank Statement showing unauthorized IMPS debit entry",
            "Provide registered mobile call logs with caller number"
        ]),
        json.dumps([
            "Cyber Cell Acknowledgment (1930 Portal)",
            "Bank Account Statement highlighting transaction",
            "Device app screenshot showing AnyDesk/QuickSupport installation"
        ]),
        None,
        None,
        None,
        "DRAFT_MANUAL",
        None,
        t_minus_18h,
        t_minus_18h
    ))

    # Seed Transaction Scan
    cursor.execute("""
    INSERT INTO transaction_fraud_scans (
        scan_ref, account_id, amount, channel, risk_score, risk_level, rules_triggered, recommended_action, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "SCAN-2026-00192",
        "AC-881920194",
        95000.0,
        "UPI",
        88,
        "High",
        json.dumps(["Unusual transfer velocity: 3rd transfer in 10 mins", "Unverified beneficiary VPA handle", "Geo-IP mismatch (Reported IP: Delhi, Normal: Pune)"]),
        "Immediate OTP 2FA Step-up & Outbound verification call recommended",
        t_minus_1h
    ))

    # Seed Smart ID Verification
    cursor.execute("""
    INSERT INTO smart_id_verifications (
        verification_ref, full_name, id_type, id_number_masked, ocr_confidence,
        face_match_score, liveness_detected, aml_status, pep_flag, risk_score,
        verification_status, certificate_hash, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "SMARTID-2026-771",
        "Priya Nandakumar",
        "Aadhaar Card (UIDAI Masked)",
        "XXXX-XXXX-8921",
        0.985,
        96.4,
        1,
        "CLEAR (Screened against OFAC & UN Sanctions)",
        0,
        12,
        "VERIFIED",
        "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        t_minus_1h
    ))

    # Seed AI LoanFast 72 Application
    cursor.execute("""
    INSERT INTO loan_applications (
        application_ref, applicant_name, monthly_income, existing_obligations,
        dti_ratio, cibil_score, loan_requested, tenor_months, risk_tier,
        decision_status, approved_amount, interest_rate, monthly_emi,
        turnaround_sla, xai_factors, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "LOANFAST-2026-442",
        "Aarav Mehta",
        125000.0,
        28000.0,
        22.4,
        782,
        500000.0,
        36,
        "Low Risk Tier (Prime Tier A)",
        "Approved (Instant Decision)",
        500000.0,
        10.5,
        16250.0,
        "Turnaround in 42 minutes (SLA: 72 Hours)",
        json.dumps({
            "positive_factors": ["High CIBIL Score (782)", "Low DTI ratio (22.4%)", "Stable 36-month salaried profile", "Zero bounce history"],
            "caution_factors": ["Requested amount at 4x monthly net salary (well within 6x ceiling)"]
        }),
        t_minus_1h
    ))

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Unified Banking AI database initialized and seeded successfully.")
