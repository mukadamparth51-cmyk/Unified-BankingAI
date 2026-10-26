"""
Unified Banking AI - End-to-End Verification Test Suite
Tests all 3 modules and the complete AI Direct Refund Recovery Engine lifecycle.
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from database import init_db

class UnifiedBankingE2ETestCase(unittest.TestCase):
    test_case_id = 1

    @classmethod
    def setUpClass(cls):
        init_db()
        from database import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM customer_documents WHERE id > 11")
        c.execute("UPDATE customer_documents SET is_active = 1 WHERE id <= 11")
        c.execute("UPDATE customer_documents SET verification_status = 'rejected' WHERE id = 7")
        conn.commit()
        conn.close()
        cls.client = app.test_client()

    def test_01_health_and_index(self):
        """Verify frontend is served cleanly"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Unified Banking AI", res.data)
        self.assertIn(b"Fraud Detector AI", res.data)
        self.assertIn(b"Smart ID", res.data)
        self.assertIn(b"AI Loan Detector", res.data)

    def test_02_customer_fraud_report_intake_and_analyzer(self):
        """Test customer fraud intake, sanitization, AI classification, and RBI eligibility"""
        payload = {
            "customer_name": "Siddharth Rao",
            "customer_phone": "+91 98210 99881",
            "customer_email": "siddharth.r@example.com",
            "amount_reported": "62000",
            "transaction_time": "2026-10-25T14:30",
            "utr_number": "419283746501",
            "payment_method": "UPI",
            "bank_name": "State Bank of India",
            "beneficiary_details": "mule_seller@paytm (SBI A/C 9918237190)",
            "description": "Received call from OLX buyer. Asked me to scan QR code and my pin was 1234 to receive advance payment of ₹62,000. Amount was instantly debited.",
            "evidence_files": ["bank_sms_debit.png"]
        }
        res = self.client.post("/api/fraud/report", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertTrue(data["case_ref"].startswith("UB-CASE-2026-"))
        # Verify AI Classification
        self.assertIn("QR", data["classification"]["primary_classification"])
        # Verify credential sanitization occurred (pin was 1234 should trigger security warning)
        self.assertTrue(len(data["security_warnings"]) > 0)
        self.assertIn("Security Alert", data["security_warnings"][0])
        # Verify RBI eligibility status is one of the 5 allowed statuses
        allowed_statuses = [
            "Potentially eligible",
            "More information required",
            "Manual review required",
            "Eligibility uncertain",
            "Not eligible under the currently verified criteria"
        ]
        self.assertIn(data["eligibility"]["status"], allowed_statuses)
        # Store for subsequent test steps
        self.__class__.test_case_id = data["case_id"]

    def test_03_recovery_tracking_dashboard_kpis_and_list(self):
        """Test Recovery Tracking Dashboard metrics and case query"""
        res = self.client.get("/api/fraud/metrics")
        self.assertEqual(res.status_code, 200)
        metrics = res.get_json()
        self.assertGreater(metrics["reported_amount"], 0)
        self.assertGreaterEqual(metrics["total_cases"], 3)

        res_cases = self.client.get("/api/fraud/cases")
        self.assertEqual(res_cases.status_code, 200)
        cases_data = res_cases.get_json()
        self.assertGreater(len(cases_data["cases"]), 0)

    def test_04_direct_refund_engine_dossier_and_consent(self):
        """Test ISO 20022 dispute package preparation and customer consent authorization"""
        case_id = self.__class__.test_case_id
        # 1. Prepare dispute
        res_prep = self.client.post(f"/api/fraud/cases/{case_id}/prepare-dispute")
        self.assertEqual(res_prep.status_code, 200)
        pkg = res_prep.get_json()["package"]
        self.assertIn("U03", pkg["dispute_reason_code"])
        self.assertIn("DISPUTE & REVERSAL NOTICE", pkg["formal_letter"])

        # 2. Record consent
        consent_payload = {
            "consented_by": "Siddharth Rao",
            "declaration_truth": True,
            "dispute_authorization": True,
            "non_guarantee_acknowledgment": True
        }
        res_consent = self.client.post(f"/api/fraud/cases/{case_id}/consent", json=consent_payload)
        self.assertEqual(res_consent.status_code, 200)
        consent_res = res_consent.get_json()["consent"]
        self.assertEqual(consent_res["status"], "CONSENT_VERIFIED")
        self.assertIsNotNone(consent_res["signature_hash"])

    def test_05_direct_reversal_submission_with_idempotency(self):
        """Test reversal submission with idempotency controls preventing duplicates"""
        case_id = self.__class__.test_case_id
        import uuid
        idem_key = str(uuid.uuid4())

        sub_payload = {
            "idempotency_key": idem_key,
            "gateway_mode": "SIMULATION_SANDBOX"
        }
        res1 = self.client.post(f"/api/fraud/cases/{case_id}/submit-reversal", json=sub_payload)
        self.assertEqual(res1.status_code, 200)
        d1 = res1.get_json()
        self.assertEqual(d1["status"], "SUCCESS")
        self.assertEqual(d1["new_case_status"], "Under Investigation")
        self.assertTrue(d1["submission_ref"].startswith("UDIR-SANDBOX-"))

        # Re-submitting with the EXACT same idempotency key must be detected and return cached hit
        res2 = self.client.post(f"/api/fraud/cases/{case_id}/submit-reversal", json=sub_payload)
        self.assertEqual(res2.status_code, 200)
        d2 = res2.get_json()
        self.assertEqual(d2["status"], "DUPLICATE_IDEMPOTENT_HIT")
        self.assertEqual(d2["submission_reference"], d1["submission_ref"])

    def test_06_verified_recovery_settlement_and_guardrail(self):
        """Test settlement recording and guardrail requiring authorized confirmation"""
        case_id = self.__class__.test_case_id

        # 1. Negative test: Attempt to mark recovery without settlement ref
        bad_payload = {"amount_recovered": "62000"}
        bad_res = self.client.post(f"/api/fraud/cases/{case_id}/record-recovery", json=bad_payload)
        self.assertEqual(bad_res.status_code, 400)

        # 2. Positive test: Valid settlement confirmation from authorized provider
        good_payload = {
            "amount_recovered": "62000",
            "settlement_ref": "NPCI-UDIR-SETTLE-88190",
            "authorized_source": "NPCI UDIR Inter-Bank Settlement Switch"
        }
        good_res = self.client.post(f"/api/fraud/cases/{case_id}/record-recovery", json=good_payload)
        self.assertEqual(good_res.status_code, 200)
        rec_data = good_res.get_json()["recovery"]
        self.assertEqual(rec_data["new_case_status"], "Recovered")
        self.assertEqual(rec_data["total_recovered"], 62000.0)

    def test_07_module_1_transaction_fraud_scanner(self):
        """Test Module 1 existing Real-Time Fraud Scanner"""
        payload = {
            "account_id": "AC-449102",
            "amount": 150000,
            "channel": "UPI",
            "location": "Bengaluru",
            "time_of_day": "Night"
        }
        res = self.client.post("/api/fraud/scan-transaction", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(data["risk_score"], 60)
        self.assertEqual(data["risk_level"], "High")

    def test_08_module_2_smart_id(self):
        """Test Module 2 Smart ID Digital KYC, Biometric Liveness, and AML Screening"""
        payload = {
            "full_name": "Priya Sharma",
            "id_type": "PAN Card",
            "id_number": "ABCDE1234F"
        }
        res = self.client.post("/api/smart-id/verify", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["verification_status"], "VERIFIED")
        self.assertGreater(data["face_match_score"], 90.0)
        self.assertTrue(data["liveness_verified"])
        self.assertIn("CLEAR", data["aml_status"])
        self.assertIsNotNone(data["tamper_evident_certificate_hash"])

    def test_09_module_3_loanfast_72(self):
        """Test Module 3 AI LoanFast 72-Hour Credit Risk & Underwriting Engine"""
        payload = {
            "applicant_name": "Aarav Mehta",
            "monthly_income": 120000,
            "existing_obligations": 25000,
            "cibil_score": 775,
            "loan_requested": 400000,
            "tenor_months": 36,
            "employment_type": "Salaried"
        }
        res = self.client.post("/api/loan/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("Approved", data["decision_status"])
        self.assertEqual(data["approved_amount"], 400000.0)
        self.assertGreater(data["monthly_emi"], 0)
        self.assertEqual(data["dti_ratio"], 20.8)
        self.assertIn("AI LoanFast 72-Hour Guaranteed SLA", data["turnaround_sla"])

    def test_10_gemma_hardware_profiling_and_status(self):
        """Test Gemma 4 hardware detection, device selection, and model status API"""
        res = self.client.get("/api/gemma/status")
        self.assertEqual(res.status_code, 200)
        status = res.get_json()
        self.assertIn("configuration", status)
        self.assertIn("gemma-4", status["configuration"]["active_model"].lower())
        self.assertEqual(status["configuration"]["device"], "cpu")
        self.assertIn("hardware", status)
        self.assertGreater(status["hardware"]["cpu_cores"], 0)
        self.assertGreater(status["hardware"]["total_ram_gb"], 0)
        self.assertEqual(status["hardware"]["inference_type"], "Multi-Threaded CPU INT4 Quantized Inference")

    def test_11_gemma_structured_output_schema_validation(self):
        """Test Gemma structured output schema enforcement and normalization"""
        from fraud_detector.ai.schemas import GemmaStructuredOutputSchema

        raw_output = {
            "fraud_type": "social_engineering_payment_deception",
            "confidence": 0.88,
            "case_summary": "Customer tricked into scanning QR code.",
            "missing_information": ["Bank debit advice statement"],
            "evidence_findings": ["Debit alert confirms ₹62,000 deduction"],
            "inconsistencies": [],
            "inconsistency_detected": False,
            "urgency_level": "CRITICAL_GOLDEN_HOUR",
            "recommended_actions": ["Lodge 1930 CFCFRMS complaint immediately"],
            "draft_refund_request": "DRAFT — NOT YET SUBMITTED: Formal dispute for ₹62,000 debit"
        }
        valid, validated_data, errors = GemmaStructuredOutputSchema.validate(raw_output)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(validated_data["fraud_type"], "social_engineering_payment_deception")
        self.assertIn("[CUSTOMER REPORTED]", validated_data["case_summary"])
        self.assertTrue(validated_data["draft_refund_request"].startswith("DRAFT — NOT YET SUBMITTED"))

    def test_12_gemma_malformed_ai_output_and_safe_fallback(self):
        """Test extraction and safe fallback on malformed AI output (markdown fences, trailing commas)"""
        from fraud_detector.ai.gemma_service import GemmaService

        service = GemmaService.get_instance()

        # 1. Output wrapped in markdown fences with trailing comma
        malformed_json_str = """
        ```json
        {
            "fraud_type": "unauthorized_upi_transaction",
            "confidence": 0.85,
            "case_summary": "Customer reported fraudulent debit after clicking link.",
            "missing_information": [],
            "evidence_findings": ["SMS shows unauthorized transaction"],
            "inconsistencies": [],
            "inconsistency_detected": false,
            "urgency_level": "HIGH",
            "recommended_actions": ["Block UPI handle"],
            "draft_refund_request": "DRAFT — NOT YET SUBMITTED dispute",
        }
        ```
        """
        parsed = service.extract_json_safely(malformed_json_str)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["fraud_type"], "unauthorized_upi_transaction")

        # 2. Complete non-JSON garbage string safely falls back to local deterministic synthesis
        garbage = "I am an AI model and here is what happened to the user without any json."
        fallback = service.extract_json_safely(garbage)
        self.assertIsNone(fallback)

    def test_13_gemma_offline_local_inference_no_network(self):
        """Test GemmaService local execution without any paid cloud LLM or internet dependency"""
        from fraud_detector.ai.gemma_service import GemmaService

        service = GemmaService.get_instance()
        context = {
            "customer_name": "Deepak Verma",
            "customer_phone": "+91 97110 55432",
            "customer_email": "deepak.v@example.com",
            "amount_reported": 85000.0,
            "transaction_time": "2026-10-26T09:15",
            "utr_number": "419827361524",
            "payment_method": "Bank Transfer (NEFT)",
            "bank_name": "Punjab National Bank",
            "beneficiary_details": "Unknown Corporate A/C 9901827361",
            "description": "Unauthorized NEFT transfer of ₹85,000 without my knowledge or consent.",
            "evidence_files": []
        }
        res = service.analyze_fraud_case(context)
        self.assertIn("structured_output", res)
        self.assertIn("ai_engine", res)
        self.assertIn("gemma-4", res["ai_engine"]["model"].lower())
        self.assertTrue(res["ai_engine"]["offline_mode"])
        self.assertIn("policy_rag", res)
        self.assertIn("disclaimer", res)

    def test_14_evidence_forensics_and_discrepancy_detection(self):
        """Test EvidenceService bounds, SHA-256 integrity, and discrepancy detection"""
        from fraud_detector.evidence.evidence_service import EvidenceService

        # Validation of extension and size
        valid, err = EvidenceService.validate_file("screenshot.png", 1024 * 500)
        self.assertTrue(valid)
        self.assertIsNone(err)

        bad_ext, err = EvidenceService.validate_file("malicious.exe", 1024)
        self.assertFalse(bad_ext)

        # Discrepancy detection between extracted text and customer claims
        extracted_text = "Transaction successful to Beneficiary SBI A/C 1234567890 for INR 25,000 on 2026-10-24."
        discrepancies = EvidenceService.detect_discrepancies(
            extracted_text=extracted_text,
            customer_amount=50000.0,  # Customer claimed 50,000, evidence says 25,000
            customer_date="2026-10-26",
            beneficiary="Mule Trader"
        )
        self.assertTrue(len(discrepancies) > 0)
        self.assertTrue(any("Amount discrepancy" in d for d in discrepancies))

    def _generate_test_pdf_bytes(self, title="Test PDF", details="Test content"):
        content = f"BT /F1 14 Tf 50 700 Td ({title}) Tj 0 -20 Td ({details}) Tj ET"
        stream_len = len(content.encode("latin1"))
        pdf = f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length {stream_len} >>\nstream\n{content}\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n310\n%%EOF"
        return pdf.encode("latin1")

    def test_15_smart_id_pdf_upload_and_validation(self):
        """Test authenticated customer PDF document upload, magic bytes, and size validation"""
        import io

        # 1. Negative: non-PDF file rejection
        bad_data = {"file": (io.BytesIO(b"Plain text file content"), "document.txt"), "document_type": "PAN Card"}
        res = self.client.post("/api/smart-id/documents/upload", data=bad_data, content_type="multipart/form-data", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Only official PDF documents", res.get_json()["error"])

        # 2. Negative: file with .pdf name but non-PDF header (corrupted)
        fake_pdf = {"file": (io.BytesIO(b"NOT A REAL PDF HEADER JUST REGULAR TEXT AND GARBAGE " * 5), "fake.pdf"), "document_type": "PAN Card"}
        res = self.client.post("/api/smart-id/documents/upload", data=fake_pdf, content_type="multipart/form-data", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Security Alert", res.get_json()["error"])

        # 3. Positive: Valid PDF upload
        valid_pdf_bytes = self._generate_test_pdf_bytes("PAN Card Valid", "Rohan Deshmukh PAN")
        upload_data = {
            "file": (io.BytesIO(valid_pdf_bytes), "rohan_pan_test.pdf"),
            "document_type": "PAN Card"
        }
        res_ok = self.client.post("/api/smart-id/documents/upload", data=upload_data, content_type="multipart/form-data", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(res_ok.status_code, 200)
        data = res_ok.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["owner_id"], "CUST-101")
        self.assertEqual(data["document_type"], "PAN Card")
        self.assertEqual(data["verification_status"], "uploaded")
        self.assertIsNotNone(data["file_hash"])

    def test_16_smart_id_private_storage_not_public(self):
        """Test that documents reside in private storage and are not accessible via public URLs"""
        # Query a seeded document
        res = self.client.get("/api/smart-id/documents?customer_id=CUST-101", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(res.status_code, 200)
        docs = res.get_json()["documents"]
        self.assertGreater(len(docs), 0)
        first_doc = docs[0]
        stored_fn = first_doc["stored_filename"]

        # Attempt to access stored filename directly via public static route /<path:path>
        res_public = self.client.get(f"/storage/documents/{stored_fn}")
        # Must not be directly served as a static asset from frontend directory
        self.assertNotEqual(res_public.headers.get("Content-Type"), "application/pdf")

    def test_17_smart_id_row_level_security_and_isolation(self):
        """Test Row-Level Security: Customer B cannot preview, download, or view Customer A's documents"""
        # Get Customer A (CUST-101) documents
        res_a = self.client.get("/api/smart-id/documents?customer_id=CUST-101", headers={"X-Customer-Id": "CUST-101"})
        doc_a_id = res_a.get_json()["documents"][0]["id"]

        # Customer B (CUST-102) attempts to preview Customer A's document
        res_sneak_preview = self.client.get(f"/api/smart-id/documents/{doc_a_id}/preview", headers={"X-Customer-Id": "CUST-102"})
        self.assertEqual(res_sneak_preview.status_code, 403)
        self.assertIn("Access Denied", res_sneak_preview.get_json()["error"])

        # Customer B attempts to download Customer A's document
        res_sneak_download = self.client.get(f"/api/smart-id/documents/{doc_a_id}/download", headers={"X-Customer-Id": "CUST-102"})
        self.assertEqual(res_sneak_download.status_code, 403)

        # Customer B attempts to list Customer A's documents
        res_sneak_list = self.client.get("/api/smart-id/documents?customer_id=CUST-101", headers={"X-Customer-Id": "CUST-102"})
        self.assertEqual(res_sneak_list.status_code, 403)

    def test_18_smart_id_authorized_preview_and_download(self):
        """Test authorized preview (inline) and download (attachment) for document owner and bank manager"""
        # 1. Owner preview
        res_owner = self.client.get("/api/smart-id/documents?customer_id=CUST-101", headers={"X-Customer-Id": "CUST-101"})
        doc_id = res_owner.get_json()["documents"][0]["id"]

        preview_res = self.client.get(f"/api/smart-id/documents/{doc_id}/preview", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(preview_res.status_code, 200)
        self.assertEqual(preview_res.headers.get("Content-Type"), "application/pdf")
        self.assertIn("inline", preview_res.headers.get("Content-Disposition", ""))

        # 2. Owner download
        download_res = self.client.get(f"/api/smart-id/documents/{doc_id}/download", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(download_res.status_code, 200)
        self.assertEqual(download_res.headers.get("Content-Type"), "application/pdf")
        self.assertIn("attachment", download_res.headers.get("Content-Disposition", ""))

        # 3. Bank Manager preview (authorized role MGR-001)
        mgr_preview = self.client.get(f"/api/smart-id/documents/{doc_id}/preview", headers={"X-Customer-Id": "CUST-101", "X-Actor-Id": "MGR-001", "X-Actor-Role": "bank_manager"})
        self.assertEqual(mgr_preview.status_code, 200)

    def test_19_smart_id_document_replacement_workflow(self):
        """Test replacing an expired or rejected document with a new version"""
        import io
        # Query Priya Sharma (CUST-102) who has a rejected Salary Slip and expired Passport
        res = self.client.get("/api/smart-id/documents?customer_id=CUST-102", headers={"X-Customer-Id": "CUST-102"})
        docs = res.get_json()["documents"]
        rejected_doc = next((d for d in docs if d["verification_status"] == "rejected"), None)
        self.assertIsNotNone(rejected_doc)
        rej_id = rejected_doc["id"]

        # Upload replacement
        new_pdf = self._generate_test_pdf_bytes("Salary Slip Sep 2026 Replacement", "Clear employer seal and verified net pay")
        replace_payload = {"file": (io.BytesIO(new_pdf), "priya_salary_replacement.pdf")}
        rep_res = self.client.post(f"/api/smart-id/documents/{rej_id}/replace", data=replace_payload, content_type="multipart/form-data", headers={"X-Customer-Id": "CUST-102"})
        self.assertEqual(rep_res.status_code, 200)
        rep_data = rep_res.get_json()
        self.assertEqual(rep_data["version"], rejected_doc["version"] + 1)
        self.assertIn(rep_data["verification_status"], ["uploaded", "pending_verification"])

    def test_20_smart_id_document_statuses_and_review(self):
        """Test document statuses and bank manager review adjudication"""
        # Bank manager reviews document
        res_list = self.client.get("/api/smart-id/documents?customer_id=CUST-103", headers={"X-Customer-Id": "CUST-103", "X-Actor-Role": "bank_manager"})
        doc_id = res_list.get_json()["documents"][0]["id"]

        # Manager approves
        review_payload = {"status": "verified"}
        mgr_res = self.client.post(f"/api/smart-id/documents/{doc_id}/review", json=review_payload, headers={"X-Actor-Role": "bank_manager", "X-Actor-Id": "MGR-001"})
        self.assertEqual(mgr_res.status_code, 200)
        self.assertEqual(mgr_res.get_json()["verification_status"], "verified")

        # Manager rejects without reason (must fail 400)
        bad_review = {"status": "rejected"}
        bad_res = self.client.post(f"/api/smart-id/documents/{doc_id}/review", json=bad_review, headers={"X-Actor-Role": "bank_manager", "X-Actor-Id": "MGR-001"})
        self.assertEqual(bad_res.status_code, 400)

    def test_21_smart_loan_checklist_gatekeeping_blocks_incomplete(self):
        """Test that missing, expired, or rejected documents block loan eligibility assessment"""
        # Priya Sharma (CUST-102) has expired Passport, rejected Salary Slip, and missing Bank Statement
        check_res = self.client.get("/api/loan/checklist?loan_type=Personal+Loan", headers={"X-Customer-Id": "CUST-102"})
        self.assertEqual(check_res.status_code, 200)
        checklist = check_res.get_json()
        self.assertFalse(checklist["can_proceed"])
        self.assertEqual(checklist["summary_status"], "DOCUMENTS_REQUIRED")
        self.assertGreater(len(checklist["blocking_reasons"]), 0)

        # Attempt to evaluate loan for CUST-102 must be BLOCKED with HTTP 400
        eval_payload = {
            "applicant_name": "Priya Sharma",
            "monthly_income": 95000,
            "existing_obligations": 15000,
            "cibil_score": 760,
            "loan_requested": 300000,
            "tenor_months": 24,
            "employment_type": "Salaried",
            "loan_type": "Personal Loan"
        }
        blocked_eval = self.client.post("/api/loan/evaluate", json=eval_payload, headers={"X-Customer-Id": "CUST-102"})
        self.assertEqual(blocked_eval.status_code, 400)
        b_data = blocked_eval.get_json()
        self.assertFalse(b_data["can_proceed"])
        self.assertIn("Document Checklist Incomplete", b_data["error"])
        self.assertGreater(len(b_data["blocking_reasons"]), 0)

    def test_22_smart_loan_checklist_gatekeeping_permits_complete(self):
        """Test that a complete document checklist allows loan underwriting and bank manager review"""
        # Rohan Deshmukh (CUST-101) has all 4 documents verified and valid
        check_res = self.client.get("/api/loan/checklist?loan_type=Personal+Loan", headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(check_res.status_code, 200)
        checklist = check_res.get_json()
        self.assertTrue(checklist["can_proceed"])
        self.assertEqual(checklist["summary_status"], "READY_FOR_EVALUATION")
        self.assertEqual(len(checklist["blocking_reasons"]), 0)

        # Evaluate loan for CUST-101 must SUCCEED with HTTP 200
        eval_payload = {
            "applicant_name": "Rohan Deshmukh",
            "monthly_income": 145000,
            "existing_obligations": 20000,
            "cibil_score": 790,
            "loan_requested": 400000,
            "tenor_months": 36,
            "employment_type": "Salaried",
            "loan_type": "Personal Loan"
        }
        ok_eval = self.client.post("/api/loan/evaluate", json=eval_payload, headers={"X-Customer-Id": "CUST-101"})
        self.assertEqual(ok_eval.status_code, 200)
        res_data = ok_eval.get_json()
        self.assertTrue(res_data["can_proceed"])
        self.assertIn("Approved", res_data["decision_status"])
        self.assertIsNotNone(res_data["document_checklist"])

if __name__ == "__main__":
    unittest.main()
