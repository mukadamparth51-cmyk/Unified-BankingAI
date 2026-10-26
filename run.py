"""
Unified Banking AI - Server Runner
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import app, init_db

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print(" UNIFIED BANKING AI - ENTERPRISE PLATFORM")
    print(f" Server running at: http://127.0.0.1:{port}")
    print(" Modules Active:")
    print("   1. Fraud Detector AI (AI Direct Refund Recovery Engine)")
    print("   2. Smart ID (Digital KYC & AML Watchlist)")
    print("   3. AI Loan Detector - AI LoanFast 72 (72-Hour SLA)")
    print("=" * 70)
    app.run(host="127.0.0.1", port=port, debug=False)
