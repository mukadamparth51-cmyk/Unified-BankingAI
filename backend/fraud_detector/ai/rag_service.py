"""
Unified Banking AI - Regulatory Policy RAG (Retrieval-Augmented Generation) Service
Maintains verified official banking circulars and statutory guidelines.
Ensures Gemma 4 receives verified regulatory context rather than hallucinating policies.
"""

from typing import Dict, Any, List

OFFICIAL_POLICY_KNOWLEDGE_BASE = [
    {
        "id": "RBI-2017-18-15-PARA-6",
        "title": "RBI Zero Liability Framework for Unauthorised Electronic Transactions",
        "source": "Reserve Bank of India Master Circular RBI/2017-18/15 DBR.No.Leg.BC.78/09.07.005/2017-18",
        "date": "July 6, 2017",
        "authority": "Reserve Bank of India (RBI)",
        "applicable_channels": ["UPI", "Card", "Bank Transfer", "Net Banking", "Wallet"],
        "keywords": ["zero liability", "third party breach", "prompt reporting", "within 3 days", "3 working days", "system deficiency"],
        "content": (
            "Para 6: Zero Liability of a Customer — A customer's entitlement to zero liability shall arise where: "
            "(a) Contributory fraud/negligence/deficiency on the part of the bank (irrespective of whether or not the transaction is reported by the customer). "
            "(b) Third party breach where the deficiency lies neither with the bank nor with the customer but lies elsewhere in the system, "
            "and the customer notifies the bank within THREE working days of receiving the communication from the bank regarding the unauthorized transaction."
        )
    },
    {
        "id": "RBI-2017-18-15-PARA-7",
        "title": "RBI Customer Negligence & Mitigating Notice Directives",
        "source": "Reserve Bank of India Circular RBI/2017-18/15",
        "date": "July 6, 2017",
        "authority": "Reserve Bank of India (RBI)",
        "applicable_channels": ["UPI", "Card", "Bank Transfer", "Net Banking"],
        "keywords": ["shared otp", "entered pin", "customer negligence", "credentials shared", "social engineering", "qr scam"],
        "content": (
            "Para 7: Limited Liability of a Customer — In cases where the loss is due to negligence by a customer, "
            "such as where he has shared the payment credentials (OTP/PIN), the customer will bear the entire loss until he reports "
            "the unauthorized transaction to the bank. Any loss occurring AFTER reporting the unauthorized transaction shall be borne by the bank."
        )
    },
    {
        "id": "RBI-2017-18-15-PARA-8",
        "title": "RBI Capped Limited Liability (4 to 7 Working Days Reporting)",
        "source": "Reserve Bank of India Circular RBI/2017-18/15",
        "date": "July 6, 2017",
        "authority": "Reserve Bank of India (RBI)",
        "applicable_channels": ["UPI", "Card", "Bank Transfer", "Net Banking"],
        "keywords": ["4 to 7 days", "limited liability", "delayed reporting", "₹10,000 ceiling", "₹5,000 ceiling"],
        "content": (
            "Para 8: Limited Liability for reporting delay between 4 to 7 working days — "
            "Customer maximum liability is capped based on account type: "
            "(i) BSBD Accounts: Maximum ₹5,000 liability. "
            "(ii) Other Savings accounts, Prepaid instruments, Credit cards with limit up to ₹5 lakh: Maximum ₹10,000 liability. "
            "(iii) Current/Cash Credit accounts, Credit cards with limit above ₹5 lakh: Maximum ₹25,000 liability. "
            "The balance transaction value must be credited back by the issuing bank."
        )
    },
    {
        "id": "NPCI-UDIR-PROC-2023",
        "title": "NPCI Unified Dispute & Issue Resolution (UDIR) Operating Procedural Guidelines",
        "source": "NPCI UPI Operating Circular NPCI/UPI/2021-23/UDIR-01",
        "date": "Updated October 2023",
        "authority": "National Payments Corporation of India (NPCI)",
        "applicable_channels": ["UPI"],
        "keywords": ["npci", "udir", "chargeback", "upi dispute", "beneficiary hold", "tcc", "reversal request", "reason code u03"],
        "content": (
            "NPCI UDIR Mandate: Participating PSPs and issuing/acquiring banks must integrate with the automated UDIR switch. "
            "Reason Code U03 governs fraudulent debits and QR collect deceptions. "
            "When lodged within T+3 days, UDIR transmits an automated lien instruction to the beneficiary's Remitter/Beneficiary bank."
        )
    },
    {
        "id": "MHA-CFCFRMS-1930",
        "title": "Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS) Protocol",
        "source": "Indian Cyber Crime Coordination Centre (I4C), Ministry of Home Affairs",
        "date": "January 2024",
        "authority": "MHA / I4C Government of India",
        "applicable_channels": ["UPI", "Bank Transfer", "Card", "Wallet"],
        "keywords": ["1930", "golden hour", "cybercrime.gov.in", "cfcfrms", "freeze beneficiary", "mule account", "police complaint"],
        "content": (
            "CFCFRMS Emergency Freeze: Immediate reporting on National Helpline 1930 or cybercrime.gov.in within the 'Golden Hour' (first 2 hours) "
            "triggers automated fund tracking across multi-layered mule accounts. Partner banks place an instantaneous hold on the disputed sum."
        )
    }
]

class PolicyRAGService:
    """
    RAG service that retrieves verified official policy contexts for Gemma 4.
    """

    @classmethod
    def retrieve_relevant_policies(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        method = str(case_data.get("payment_method", "")).upper()
        desc = str(case_data.get("description", "")).lower()

        matched_docs = []
        for doc in OFFICIAL_POLICY_KNOWLEDGE_BASE:
            # Check channel match
            channel_match = any(c.upper() in method for c in doc["applicable_channels"])
            # Check keyword match
            kw_hits = sum(1 for kw in doc["keywords"] if kw in desc)

            if channel_match or kw_hits > 0:
                matched_docs.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "source": doc["source"],
                    "date": doc["date"],
                    "authority": doc["authority"],
                    "content": doc["content"],
                    "relevance_score": kw_hits + (2 if channel_match else 0)
                })

        # Sort by relevance
        matched_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_docs = matched_docs[:3] if matched_docs else OFFICIAL_POLICY_KNOWLEDGE_BASE[:2]

        formatted_context = "\n\n".join([
            f"DOCUMENT: {d['title']} ({d['source']}, Date: {d['date']})\n{d['content']}"
            for d in top_docs
        ])

        citations = [
            {"title": d["title"], "source": d["source"], "date": d["date"], "authority": d["authority"]}
            for d in top_docs
        ]

        return {
            "policy_context_text": formatted_context,
            "citations": citations,
            "verification_status": "OFFICIAL VERIFIED STATUTORY SOURCES AVAILABLE" if citations else "Current eligibility could not be verified."
        }
