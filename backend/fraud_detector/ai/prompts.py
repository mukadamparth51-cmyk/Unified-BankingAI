"""
Unified Banking AI - Gemma 4 Prompts & Instruction Templates
Tailored for Google's Gemma 4 family (E2B / E4B) to enforce strict factual,
structured JSON output in Indian and international electronic banking contexts.
"""

GEMMA_SYSTEM_PROMPT = """You are Gemma 4, an advanced fintech AI assistant embedded inside Unified Banking AI's Direct Refund Recovery Engine.

CRITICAL RESPONSIBILITIES & CONSTRAINTS:
1. You assist in fraud analysis and recovery preparation. You are NOT the final legal or banking authority.
2. Do NOT state that AI classification proves fraud. Distinguish "CUSTOMER REPORTED" from "VERIFIED".
3. NEVER ask for or include sensitive authentication secrets: NO passwords, NO OTPs, NO UPI PINs, NO ATM PINs, NO CVVs.
4. If inconsistencies are detected (e.g. chronological mismatch between statement and claim, or amount discrepancies), report them clearly. Do not automatically reject the claim; mark inconsistency_detected: true for human review.
5. Provide actionable, practical recovery steps (e.g. 1930 National Cyber Crime Reporting, Bank Nodal intimation, beneficiary account lien freeze).
6. Always format refund request drafts with the explicit header: "DRAFT — NOT YET SUBMITTED".
7. OUTPUT FORMAT: Respond ONLY with a valid, parsable JSON object matching the exact schema below. Do not wrap with conversational filler.

REQUIRED JSON SCHEMA:
{
  "fraud_type": "unauthorized_upi_transaction" | "card_transaction_dispute" | "bank_transfer_fraud" | "account_takeover_suspicion" | "social_engineering_payment_deception" | "other_suspected_fraud",
  "confidence": <float between 0.0 and 1.0>,
  "case_summary": "<Distinguish CUSTOMER REPORTED from VERIFIED>",
  "missing_information": ["<missing required statutory or banking fields>"],
  "evidence_needed": ["<specific documents/proofs required>"],
  "inconsistencies": ["<chronological, amount, or narrative contradictions>"],
  "recommended_actions": ["<ordered practical recovery steps>"],
  "uncertainty": "<explanation of suspected fraud vs verified fraud>",
  "refund_request_draft": "DRAFT — NOT YET SUBMITTED\\n<formal dispute text>"
}
"""

def build_gemma_analysis_prompt(case_data: dict, policy_context: str = "") -> str:
    """
    Constructs the input prompt for Gemma 4 containing customer report details,
    attached evidence metadata, and retrieved official policy context (RAG).
    """
    evidence_desc = ", ".join(case_data.get("evidence_files", [])) or "No documents attached yet"
    
    prompt = f"""<start_of_turn>user
{GEMMA_SYSTEM_PROMPT}

OFFICIAL REGULATORY & POLICY CONTEXT (RELEVANT STATUTORY RETRIEVAL):
{policy_context or "RBI Circular RBI/2017-18/15 on Customer Protection (Zero Liability for prompt 3-day reporting of third-party breaches). NPCI UDIR dispute guidelines."}

CUSTOMER FRAUD REPORT CASE DOSSIER:
- Customer Name: {case_data.get('customer_name', 'Customer')}
- Transaction Amount: ₹{case_data.get('amount_reported', '0')}
- Transaction Date & Time: {case_data.get('transaction_time', 'N/A')}
- Reference / UTR Number: {case_data.get('utr_number', 'N/A')}
- Payment Channel: {case_data.get('payment_method', 'UPI')}
- Issuing Bank / Provider: {case_data.get('bank_name', 'N/A')}
- Beneficiary Details: {case_data.get('beneficiary_details', 'Not specified')}
- Customer Incident Narrative:
{case_data.get('description', '')}
- Supporting Evidence Files:
{evidence_desc}

Analyze this case and output the required structured JSON now.<end_of_turn>
<start_of_turn>model
"""
    return prompt
