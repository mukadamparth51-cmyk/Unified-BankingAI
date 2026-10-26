# Unified Banking AI

Enterprise Autonomous Financial Cybersecurity, Direct Dispute Recovery, and Intelligent Credit Underwriting Suite.

---

## 🏛️ Project Architecture & Core Modules

The platform maintains three core modules in strict order:

### 1. Fraud Detector AI
* **Real-Time Transaction Anomaly & Velocity Scanner**: Live algorithmic scoring of electronic debits against suspicious thresholds and velocity limits.
* **AI Direct Refund Recovery Engine (Powered by Local Gemma 4 AI)**:
  * **Local Open-Weight Gemma 4 AI**: Runs locally and offline via hardware-aware profiling (`gemma_config.py` selects **Gemma 4 E2B** INT4 CPU or **Gemma 4 E4B** CUDA GPU) with zero paid cloud LLM dependencies.
  * **Regulatory Policy RAG**: Grounds inference with verified statutory frameworks (**RBI Circular RBI/2017-18/15** on Zero Liability and **NPCI UDIR guidelines** for UPI reversals).
  * **Customer Fraud Report**: Multi-channel intake (UPI, Card, IMPS/NEFT, NetBanking) with automated credential sanitization (never stores or requests OTPs, PINs, or CVVs).
  * **AI Fraud Case Analyzer**: Classifies fraud typologies, detects evidence gaps and chronological contradictions, and formats structured dispute briefs.
  * **Direct Dispute & ISO 20022 Reversal Request**: Client-server idempotency protection (`Idempotency-Key` UUIDv4) and SHA-256 consent signatures.
  * **11-Stage Recovery Tracking Dashboard**: Real-time dispute tracking with strict guardrails preventing cases from being marked recovered without authorized settlement references.
  * **Golden Hour Advisory**: Instant escalation to India's National Cyber Crime Helpline **1930** and **cybercrime.gov.in** for immediate lien freezes.

### 2. Smart ID
* **AI Digital Identity & KYC Verification**: Format validation for Aadhaar (UIDAI masked), PAN, Passport, and Voter ID.
* **Biometric 3D Liveness Simulation**: Micro-expression matching and anti-spoofing deepfake defense.
* **AML & Sanctions Screening**: Screening against international PEP, OFAC, and UN sanctions databases.
* **NEW: Private Document Vault**:
  * Authenticated PDF document upload and replacement workflows.
  * Private, non-public storage with path-traversal protection.
  * Row-Level Security (RLS) ensuring strict isolation across customer profiles.
  * 6 document verification lifecycle states: `uploaded`, `missing`, `pending_verification`, `verified`, `rejected`, and `expired`.
  * Inline streaming PDF preview (zero modal popups) and secure authorized download.
  * Tamper-evident immutable audit logging for all document operations.

### 3. AI Loan Detector — AI LoanFast 72
* **72-Hour SLA Underwriting Engine**: Instant credit risk scoring, Debt-to-Income (DTI) analysis, risk tiering, and EMI calculation.
* **Explainable AI (XAI)**: Transparent underwriting drivers and risk classifications.
* **NEW: Cross-Module Document Checklist Gatekeeper**:
  * Connects securely to Smart ID to fetch active document status.
  * Evaluates statutory requirements across 5 loan types:
    * *Instant Fast-Track Loan (LoanFast 72)*
    * *Personal Loan*
    * *Home Loan*
    * *Vehicle Loan*
    * *Business / MSME Loan*
  * **Gatekeeper Enforcement**: Strictly blocks credit evaluation (HTTP 400) if any mandatory document is missing, expired, or rejected.
  * **Statutory Compliance Disclaimer**: *"Do not treat document presence as proof of authenticity or guarantee loan approval."*

---

## 🔒 Security & Privacy Principles

1. **Zero Credential Ingestion**: Sensitive authentication secrets (OTPs, PINs, passwords, CVVs) are stripped and redacted before processing.
2. **Local AI Privacy**: Gemma 4 runs directly on the user's workstation. Sensitive transaction details never leave the machine.
3. **Row-Level Security (RLS)**: Customers cannot view, preview, or download another customer's documents.
4. **Tamper-Evident SHA-256 Hashing**: All evidence and identity certificates are fingerprinted cryptographically.
5. **Idempotency Protection**: Reversal requests require cryptographic idempotency tokens to prevent duplicate debit reversals.

---

## 🚀 Quick Start Guide

### 1. Requirements
* Python 3.10+
* Windows / Linux / macOS
* Dependencies:
  ```bash
  pip install -r requirements.txt
  ```
  *(or `pip install flask flask-cors`)*

### 2. Launch the Application
Run the launcher:
```bash
python run.py
```

Open your browser at:
```
http://localhost:5000
```

### 3. Run the Automated Test Suite
```bash
python backend/test_suite.py
```
*(Runs 22 comprehensive integration tests covering all 3 modules, RLS security, Gemma fallback, and loan gatekeeping).*
