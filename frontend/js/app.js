/**
 * Unified Banking AI - Core Frontend Controller
 * Powers:
 * 1. Fraud Detector AI (AI Direct Refund Recovery Engine, Dashboard, Transaction Scanner)
 * 2. Smart ID (Digital KYC, Biometric Liveness, AML Watchlist)
 * 3. AI Loan Detector - AI LoanFast 72
 */

class UnifiedBankingApp {
  constructor() {
    this.currentCaseId = null;
    this.currentCaseData = null;
    this.stagedEvidenceFiles = [];
    this.idempotencyKey = null;

    this.activeCustomerId = "CUST-101";
    this.activeCustomerName = "Rohan Deshmukh";
    this.activeActorRole = "customer";
    this.currentReplacingDocId = null;

    this.initElements();
    this.bindEvents();
    this.loadGemmaStatus();
    this.loadDashboardData();
    this.loadCustomerProfiles();
    this.loadSmartIdDocuments();
    this.loadLoanChecklist();
    this.loadAuditLogs();
    this.setInitialDefaults();
  }

  initElements() {
    // Session Switcher
    this.activeCustomerSelect = document.getElementById("activeCustomerSelect");
    this.activeRoleChip = document.getElementById("activeRoleChip");

    // Navigation
    this.moduleTabs = document.querySelectorAll(".nav-tab");
    this.moduleViews = document.querySelectorAll(".module-view");
    this.subTabs = document.querySelectorAll(".sub-tab");
    this.subTabContents = document.querySelectorAll(".subtab-content");

    // Module 1: Customer Fraud Report Form
    this.fraudReportForm = document.getElementById("fraudReportForm");
    this.evidenceDropzone = document.getElementById("evidenceDropzone");
    this.evidenceFileInput = document.getElementById("evidenceFileInput");
    this.uploadedFilesList = document.getElementById("uploadedFilesList");
    this.btnSubmitReport = document.getElementById("btnSubmitReport");

    // Module 1: AI Results
    this.analysisPlaceholder = document.getElementById("analysisPlaceholder");
    this.analysisContent = document.getElementById("analysisContent");
    this.analysisStatusChip = document.getElementById("analysisStatusChip");

    // Stepper for Direct Reversal
    this.reversalCard = document.getElementById("directReversalCard");
    this.stepItems = document.querySelectorAll(".step-item");
    this.stepContents = document.querySelectorAll(".step-content");

    // Dashboard
    this.dashboardSearch = document.getElementById("dashboardSearch");
    this.dashboardStatusFilter = document.getElementById("dashboardStatusFilter");
    this.btnRefreshDashboard = document.getElementById("btnRefreshDashboard");
    this.casesTableBody = document.getElementById("casesTableBody");

    // Modals & Dossier
    this.inlineDossierCard = document.getElementById("inlineDossierCard");

    // Module 1: Transaction Scanner
    this.txnScanForm = document.getElementById("txnScanForm");

    // Module 2: Smart ID
    this.smartIdForm = document.getElementById("smartIdForm");

    // Module 2: Document Vault
    this.docUploadForm = document.getElementById("docUploadForm");
    this.vaultDocType = document.getElementById("vaultDocType");
    this.vaultExpiryDate = document.getElementById("vaultExpiryDate");
    this.vaultPdfFile = document.getElementById("vaultPdfFile");
    this.btnUploadDoc = document.getElementById("btnUploadDoc");
    this.btnUploadDocText = document.getElementById("btnUploadDocText");
    this.customerDocsTableBody = document.getElementById("customerDocsTableBody");
    this.vaultOwnerChip = document.getElementById("vaultOwnerChip");
    this.replacementAlertBanner = document.getElementById("replacementAlertBanner");
    this.btnCancelReplace = document.getElementById("btnCancelReplace");
    this.replacingDocTitle = document.getElementById("replacingDocTitle");
    this.replacingDocVersion = document.getElementById("replacingDocVersion");
    this.replacingDocReason = document.getElementById("replacingDocReason");
    this.replaceDocId = document.getElementById("replaceDocId");

    // Metrics
    this.metricTotalDocs = document.getElementById("metricTotalDocs");
    this.metricVerifiedDocs = document.getElementById("metricVerifiedDocs");
    this.metricPendingDocs = document.getElementById("metricPendingDocs");
    this.metricRejectedDocs = document.getElementById("metricRejectedDocs");
    this.metricExpiredDocs = document.getElementById("metricExpiredDocs");

    // Inline Preview
    this.inlineDocPreviewCard = document.getElementById("inlineDocPreviewCard");
    this.inlinePdfFrame = document.getElementById("inlinePdfFrame");
    this.previewDocTitle = document.getElementById("previewDocTitle");
    this.previewDocMeta = document.getElementById("previewDocMeta");
    this.previewStatusBadge = document.getElementById("previewStatusBadge");
    this.btnClosePreview = document.getElementById("btnClosePreview");

    // Audit Logs
    this.smartIdAuditCard = document.getElementById("smartIdAuditCard");
    this.btnRefreshAuditLogs = document.getElementById("btnRefreshAuditLogs");
    this.auditLogsTableBody = document.getElementById("auditLogsTableBody");

    // Module 3: LoanFast 72 & Checklist
    this.loanFastForm = document.getElementById("loanFastForm");
    this.loanTypeSelect = document.getElementById("loanTypeSelect");
    this.loanChecklistContainer = document.getElementById("loanChecklistContainer");
    this.checklistStatusBadge = document.getElementById("checklistStatusBadge");
    this.checklistItemsList = document.getElementById("checklistItemsList");
    this.gatekeeperAlertBanner = document.getElementById("gatekeeperAlertBanner");
    this.gatekeeperAlertTitle = document.getElementById("gatekeeperAlertTitle");
    this.gatekeeperAlertText = document.getElementById("gatekeeperAlertText");
    this.btnGoToSmartId = document.getElementById("btnGoToSmartId");
    this.btnEvaluateLoan = document.getElementById("btnEvaluateLoan");
  }

  bindEvents() {
    // Module Tabs Switching (Strictly 1, 2, 3 in Order)
    this.moduleTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        const targetModule = tab.dataset.module;
        this.switchModule(targetModule);
      });
    });

    // Sub-Tabs for Module 1
    this.subTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        const targetSubtab = tab.dataset.subtab;
        this.switchSubTab(targetSubtab);
      });
    });

    // Evidence Upload Drag & Drop
    if (this.evidenceDropzone) {
      this.evidenceDropzone.addEventListener("click", () => this.evidenceFileInput.click());
      this.evidenceDropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        this.evidenceDropzone.classList.add("drag-over");
      });
      this.evidenceDropzone.addEventListener("dragleave", () => {
        this.evidenceDropzone.classList.remove("drag-over");
      });
      this.evidenceDropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        this.evidenceDropzone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
          this.handleFileSelect(e.dataTransfer.files[0]);
        }
      });
      this.evidenceFileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
          this.handleFileSelect(e.target.files[0]);
        }
      });
    }

    // Customer Fraud Report Submit
    if (this.fraudReportForm) {
      this.fraudReportForm.addEventListener("submit", (e) => this.handleFraudReportSubmit(e));
    }

    // Direct Reversal Step Navigation & Submission
    const btnLaunch = document.getElementById("btnLaunchReversalEngine");
    if (btnLaunch) {
      btnLaunch.addEventListener("click", () => {
        this.reversalCard.scrollIntoView({ behavior: "smooth" });
        this.loadReversalDossier();
      });
    }

    const btnProceedToConsent = document.getElementById("btnProceedToConsent");
    if (btnProceedToConsent) {
      btnProceedToConsent.addEventListener("click", () => this.setReversalStep(2));
    }

    const btnSignConsent = document.getElementById("btnSignConsent");
    if (btnSignConsent) {
      btnSignConsent.addEventListener("click", () => this.handleConsentSigning());
    }

    const btnExecuteSubmission = document.getElementById("btnExecuteSubmission");
    if (btnExecuteSubmission) {
      btnExecuteSubmission.addEventListener("click", () => this.handleReversalSubmission());
    }

    const btnCopyLetter = document.getElementById("btnCopyLetter");
    if (btnCopyLetter) {
      btnCopyLetter.addEventListener("click", () => {
        const text = document.getElementById("dossierLetterText").innerText;
        navigator.clipboard.writeText(text).then(() => {
          this.showToast("Dispute Letter copied to clipboard!", "success");
        });
      });
    }

    // Dashboard Search & Filters
    if (this.dashboardSearch) {
      this.dashboardSearch.addEventListener("input", () => this.loadDashboardData());
    }
    if (this.dashboardStatusFilter) {
      this.dashboardStatusFilter.addEventListener("change", () => this.loadDashboardData());
    }
    if (this.btnRefreshDashboard) {
      this.btnRefreshDashboard.addEventListener("click", () => {
        this.loadDashboardData();
        this.showToast("Recovery Dashboard refreshed.", "success");
      });
    }

    // Transaction Scanner Form
    if (this.txnScanForm) {
      this.txnScanForm.addEventListener("submit", (e) => this.handleTxnScanSubmit(e));
    }

    // Smart ID Form
    if (this.smartIdForm) {
      this.smartIdForm.addEventListener("submit", (e) => this.handleSmartIdSubmit(e));
    }

    // Session Switcher
    if (this.activeCustomerSelect) {
      this.activeCustomerSelect.addEventListener("change", (e) => this.handleCustomerChange(e));
    }

    // Document Upload Form
    if (this.docUploadForm) {
      this.docUploadForm.addEventListener("submit", (e) => this.handleDocUpload(e));
    }

    // Cancel Replacement
    if (this.btnCancelReplace) {
      this.btnCancelReplace.addEventListener("click", () => this.cancelReplacementMode());
    }

    // Close Preview
    if (this.btnClosePreview) {
      this.btnClosePreview.addEventListener("click", () => this.closeInlinePreview());
    }

    // Refresh Audit Logs
    if (this.btnRefreshAuditLogs) {
      this.btnRefreshAuditLogs.addEventListener("click", () => this.loadAuditLogs());
    }

    // Loan Type Select Change
    if (this.loanTypeSelect) {
      this.loanTypeSelect.addEventListener("change", () => this.loadLoanChecklist());
    }

    // Go to Smart ID button
    if (this.btnGoToSmartId) {
      this.btnGoToSmartId.addEventListener("click", () => {
        this.switchModule("smart-id");
        const vault = document.getElementById("smartIdVaultCard");
        if (vault) vault.scrollIntoView({ behavior: "smooth" });
      });
    }

    // LoanFast 72 Form
    if (this.loanFastForm) {
      this.loanFastForm.addEventListener("submit", (e) => this.handleLoanFastSubmit(e));
    }
  }

  setInitialDefaults() {
    // Set default transaction time to 2 hours ago
    const repTxnTime = document.getElementById("repTxnTime");
    if (repTxnTime) {
      const now = new Date();
      now.setHours(now.getHours() - 2);
      const iso = now.toISOString().slice(0, 16);
      repTxnTime.value = iso;
    }
  }

  // --------------------------------------------------------------------------
  // Navigation
  // --------------------------------------------------------------------------
  switchModule(moduleId) {
    this.moduleTabs.forEach(tab => {
      const isMatch = tab.dataset.module === moduleId;
      tab.classList.toggle("active", isMatch);
      tab.setAttribute("aria-selected", isMatch ? "true" : "false");
    });

    this.moduleViews.forEach(view => {
      view.classList.toggle("hidden", view.id !== `module-${moduleId}`);
    });
  }

  switchSubTab(subtabId) {
    this.subTabs.forEach(tab => {
      tab.classList.toggle("active", tab.dataset.subtab === subtabId);
    });

    this.subTabContents.forEach(content => {
      content.classList.toggle("hidden", content.id !== `subtab-${subtabId}`);
    });

    if (subtabId === "tracking-dashboard") {
      this.loadDashboardData();
    }
  }

  // --------------------------------------------------------------------------
  // File Upload
  // --------------------------------------------------------------------------
  handleFileSelect(file) {
    if (!file) return;
    this.stagedEvidenceFiles.push(file);
    this.renderStagedFiles();
    this.showToast(`Evidence staged: ${file.name}`, "success");
  }

  renderStagedFiles() {
    if (!this.uploadedFilesList) return;
    this.uploadedFilesList.innerHTML = this.stagedEvidenceFiles.map((f, i) => `
      <div class="file-chip">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>${f.name} (${Math.round(f.size / 1024)} KB)</span>
        <button type="button" class="btn-close" style="font-size: 1rem; line-height: 1;" onclick="window.app.removeStagedFile(${i})">&times;</button>
      </div>
    `).join("");
  }

  removeStagedFile(index) {
    this.stagedEvidenceFiles.splice(index, 1);
    this.renderStagedFiles();
  }

  // --------------------------------------------------------------------------
  // 1 & 2 & 3: Customer Fraud Report Intake & AI Case Analyzer
  // --------------------------------------------------------------------------
  async handleFraudReportSubmit(e) {
    e.preventDefault();
    this.btnSubmitReport.disabled = true;
    this.btnSubmitReport.innerHTML = `
      <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>
      Analyzing with AI Case Analyzer...
    `;

    const payload = {
      customer_name: document.getElementById("repCustomerName").value.trim(),
      customer_phone: document.getElementById("repCustomerPhone").value.trim(),
      amount_reported: document.getElementById("repAmount").value,
      transaction_time: document.getElementById("repTxnTime").value,
      utr_number: document.getElementById("repUtr").value.trim(),
      payment_method: document.getElementById("repPaymentMethod").value,
      bank_name: document.getElementById("repBank").value,
      beneficiary_details: document.getElementById("repBeneficiary").value.trim(),
      description: document.getElementById("repDescription").value.trim(),
      evidence_files: this.stagedEvidenceFiles.map(f => f.name)
    };

    try {
      const res = await fetch("/api/fraud/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Failed to process fraud report.");
      }

      this.currentCaseId = data.case_id;
      this.currentCaseData = data;

      // Upload any staged files
      if (this.stagedEvidenceFiles.length > 0) {
        for (const file of this.stagedEvidenceFiles) {
          const formData = new FormData();
          formData.append("file", file);
          await fetch(`/api/fraud/cases/${data.case_id}/upload-evidence`, {
            method: "POST",
            body: formData
          });
        }
        this.stagedEvidenceFiles = [];
        this.renderStagedFiles();
      }

      // Display security warnings if any credential was redacted
      if (data.security_warnings && data.security_warnings.length > 0) {
        data.security_warnings.forEach(w => this.showToast(w, "warning"));
      }

      this.renderAnalysisResults(data);
      this.showToast(`Fraud Case ${data.case_ref} registered and analyzed!`, "success");

      // Auto-load Step 1 of Reversal Engine
      this.loadReversalDossier();

    } catch (err) {
      this.showToast(err.message, "danger");
    } finally {
      this.btnSubmitReport.disabled = false;
      this.btnSubmitReport.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        Run AI Fraud Case Analyzer & Assess Eligibility
      `;
    }
  }

  renderAnalysisResults(data) {
    if (!this.analysisContent) return;
    this.analysisPlaceholder.classList.add("hidden");
    this.analysisContent.classList.remove("hidden");

    // Header
    document.getElementById("resCaseRef").innerText = data.case_ref;
    const statusChip = document.getElementById("resCaseStatus");
    statusChip.innerText = data.current_status;
    statusChip.className = `status-chip ${this.getStatusChipClass(data.current_status)}`;

    this.analysisStatusChip.innerText = "Analysis Complete";
    this.analysisStatusChip.className = "status-chip chip-success";

    // AI Classification
    document.getElementById("resFraudType").innerText = data.classification.primary_classification;
    document.getElementById("resConfidence").innerText = `${Math.round(data.classification.confidence * 100)}%`;
    document.getElementById("resMuleRisk").innerText = data.classification.mule_risk;
    document.getElementById("resExecutiveSummary").innerText = data.case_summary.executive_summary;
    document.getElementById("resUncertaintyNote").innerText = data.case_summary.uncertainty_analysis;

    // Missing evidence & inconsistencies
    const missingBox = document.getElementById("missingEvidenceBox");
    const missingList = document.getElementById("resMissingList");
    const combinedGaps = [...(data.missing_evidence || []), ...(data.inconsistencies || [])];

    if (combinedGaps.length > 0) {
      missingBox.classList.remove("hidden");
      missingList.innerHTML = combinedGaps.map(g => `<li>${g}</li>`).join("");
    } else {
      missingBox.classList.add("hidden");
    }

    // 3. Refund Eligibility Assistant
    const elig = data.eligibility;
    const eligCard = document.getElementById("resEligibilityCard");
    const eligStatus = document.getElementById("resEligibilityStatus");
    const eligReason = document.getElementById("resEligibilityReason");
    const eligCite = document.getElementById("resRegulationCite");

    eligStatus.innerText = elig.status;
    eligReason.innerText = elig.reason;
    eligCite.innerText = elig.applicable_regulation || "RBI Circular RBI/2017-18/15";

    // Set eligibility card color class
    eligCard.className = "eligibility-badge-card";
    if (elig.status === "Potentially eligible") {
      eligCard.classList.add("eligible");
    } else if (elig.status === "More information required") {
      eligCard.classList.add("more-info");
    } else if (elig.status === "Manual review required") {
      eligCard.classList.add("review-required");
    } else if (elig.status === "Eligibility uncertain") {
      eligCard.classList.add("uncertain");
    } else {
      eligCard.classList.add("not-eligible");
    }
  }

  // --------------------------------------------------------------------------
  // 4. Direct Refund and Reversal Request Engine
  // --------------------------------------------------------------------------
  async loadReversalDossier() {
    if (!this.currentCaseId) return;

    try {
      const res = await fetch(`/api/fraud/cases/${this.currentCaseId}/prepare-dispute`, {
        method: "POST"
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load dispute dossier.");

      const pkg = data.package;
      document.getElementById("dossierIsoPayload").innerText = JSON.stringify(pkg.iso_payload, null, 2);
      document.getElementById("dossierLetterText").innerText = pkg.formal_letter;

      // Populate signer default
      const signerInput = document.getElementById("consentSignerName");
      if (signerInput && !signerInput.value) {
        signerInput.value = pkg.iso_payload.CustomerDetails.Name || "";
      }

      // Generate Idempotency Key
      this.idempotencyKey = crypto.randomUUID();
      const idempElem = document.getElementById("reversalIdempotencyKey");
      if (idempElem) {
        idempElem.innerText = this.idempotencyKey;
      }

      this.setReversalStep(1);
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  setReversalStep(stepNum) {
    this.stepItems.forEach(item => {
      const idx = parseInt(item.dataset.step);
      item.classList.toggle("active", idx === stepNum);
    });

    this.stepContents.forEach((content, index) => {
      content.classList.toggle("hidden", index + 1 !== stepNum);
    });
  }

  async handleConsentSigning() {
    const chkTruth = document.getElementById("chkTruth").checked;
    const chkAuth = document.getElementById("chkAuth").checked;
    const chkNon = document.getElementById("chkNonGuarantee").checked;
    const signer = document.getElementById("consentSignerName").value.trim();

    if (!chkTruth || !chkAuth || !chkNon) {
      this.showToast("All 3 mandatory declarations must be checked to proceed.", "warning");
      return;
    }
    if (!signer) {
      this.showToast("Please enter your legal signature name.", "warning");
      return;
    }

    try {
      const res = await fetch(`/api/fraud/cases/${this.currentCaseId}/consent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consented_by: signer,
          declaration_truth: chkTruth,
          dispute_authorization: chkAuth,
          non_guarantee_acknowledgment: chkNon
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to record consent.");

      this.showToast("Digital consent verified and cryptographically recorded!", "success");
      this.setReversalStep(3);
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  async handleReversalSubmission() {
    const btnSubmit = document.getElementById("btnExecuteSubmission");
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `
      <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>
      Submitting with Idempotency Protection...
    `;

    const gatewayMode = document.querySelector('input[name="gatewayMode"]:checked')?.value || "SIMULATION_SANDBOX";

    try {
      const res = await fetch(`/api/fraud/cases/${this.currentCaseId}/submit-reversal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idempotency_key: this.idempotencyKey,
          gateway_mode: gatewayMode
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Submission failed.");

      // Render Confirmation Step 4
      document.getElementById("subRefDisplay").innerText = data.submission_ref || data.submission_reference;
      document.getElementById("subModeDisplay").innerText = data.gateway_mode || gatewayMode;
      document.getElementById("subTimeDisplay").innerText = data.submission_timestamp || new Date().toISOString();
      document.getElementById("subStatusDisplay").innerText = data.new_case_status || "Under Investigation";

      if (gatewayMode === "SIMULATION_SANDBOX") {
        document.getElementById("submissionTitle").innerText = "Dispute Lodged in NPCI UDIR Sandbox";
        document.getElementById("submissionSubtitle").innerText = "Simulated bank clearing switch confirmed receipt. Case is actively tracked under investigation.";
      } else if (gatewayMode === "AUTHORIZED_API") {
        document.getElementById("submissionTitle").innerText = "Dispute Submitted via Authorized Bank API";
        document.getElementById("submissionSubtitle").innerText = "Official live dispute reference generated. Hold placed on beneficiary rails.";
      } else {
        document.getElementById("submissionTitle").innerText = "Manual Dispute Dossier Prepared";
        document.getElementById("submissionSubtitle").innerText = "Formal dispute packet ready. Escalation links generated for Bank Nodal Desk and Ombudsman.";
      }

      this.setReversalStep(4);
      this.showToast("Dispute request successfully dispatched!", "success");
      this.loadDashboardData();

    } catch (err) {
      this.showToast(err.message, "danger");
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        Submit Dispute Request to Gateway
      `;
    }
  }

  async loadGemmaStatus() {
    try {
      const res = await fetch("/api/gemma/status");
      if (res.ok) {
        const data = await res.json();
        const hw = data.hardware || {};
        const cfg = data.configuration || {};

        const hwEl = document.getElementById("gemmaHwProfile");
        const gpuEl = document.getElementById("gemmaGpuProfile");
        const execEl = document.getElementById("gemmaExecProfile");
        const modelBadge = document.getElementById("gemmaModelBadge");
        const statusBadge = document.getElementById("gemmaStatusBadge");

        if (hwEl) {
          hwEl.textContent = `${hw.cpu_name || 'Multi-Core CPU'} (${hw.cpu_cores || 14} Cores) • ${hw.total_ram_gb || 15.44} GB RAM`;
        }
        if (gpuEl) {
          gpuEl.textContent = `${hw.gpu_name || 'Intel Graphics'} (CUDA: ${hw.cuda_available ? 'Available' : 'Disabled / Not Present'})`;
        }
        if (execEl) {
          execEl.textContent = hw.inference_type || `${cfg.quantization || '4-bit'} Quantized ${cfg.device ? cfg.device.toUpperCase() : 'CPU'} Inference`;
        }
        if (modelBadge) {
          modelBadge.textContent = hw.recommended_model || cfg.active_model || "Gemma 4 E2B";
        }
        if (statusBadge) {
          statusBadge.textContent = "● " + (data.engine_status || "LOCAL ENGINE ACTIVE");
        }
      }
    } catch (e) {
      console.warn("Gemma status check failed:", e);
    }
  }

  // --------------------------------------------------------------------------
  // 5. Recovery Tracking Dashboard
  // --------------------------------------------------------------------------
  async loadDashboardData() {
    try {
      // 1. Load Metrics
      const metricsRes = await fetch("/api/fraud/metrics");
      const metrics = await metricsRes.json();

      document.getElementById("kpiReported").innerText = `₹${(metrics.reported_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
      document.getElementById("kpiRequested").innerText = `₹${(metrics.requested_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
      document.getElementById("kpiApproved").innerText = `₹${(metrics.approved_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
      document.getElementById("kpiRecovered").innerText = `₹${(metrics.recovered_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
      document.getElementById("kpiRemaining").innerText = `₹${(metrics.remaining_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

      // 2. Load Cases with filters
      const q = this.dashboardSearch ? encodeURIComponent(this.dashboardSearch.value.trim()) : "";
      const status = this.dashboardStatusFilter ? encodeURIComponent(this.dashboardStatusFilter.value) : "";
      const casesRes = await fetch(`/api/fraud/cases?q=${q}&status=${status}`);
      const casesData = await casesRes.json();

      this.renderCasesTable(casesData.cases || []);

    } catch (err) {
      console.error("Dashboard load failed:", err);
    }
  }

  renderCasesTable(cases) {
    if (!this.casesTableBody) return;

    if (cases.length === 0) {
      this.casesTableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-muted py-4">No fraud recovery cases matching current criteria.</td>
        </tr>
      `;
      return;
    }

    this.casesTableBody.innerHTML = cases.map(c => `
      <tr>
        <td>
          <strong class="font-mono text-primary">${c.case_ref}</strong>
          <span class="text-xs text-muted block">${c.transaction_time}</span>
        </td>
        <td>
          <strong>${c.customer_name}</strong>
          <span class="text-xs text-muted block">${c.customer_phone || ""}</span>
        </td>
        <td>
          <div>₹${c.amount_reported.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
          <span class="text-xs text-muted">Req: ₹${c.amount_requested.toLocaleString("en-IN")}</span>
        </td>
        <td>
          <strong class="${c.amount_recovered > 0 ? 'text-success' : 'text-muted'}">
            ₹${(c.amount_recovered || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </strong>
        </td>
        <td>
          <div>${c.payment_method}</div>
          <span class="text-xs text-muted">${c.bank_name}</span>
        </td>
        <td>
          <span class="status-chip ${this.getStatusChipClass(c.current_status)}">
            ${c.current_status}
          </span>
        </td>
        <td>
          <span class="text-xs font-semibold ${c.eligibility_status === 'Potentially eligible' ? 'text-success' : 'text-muted'}">
            ${c.eligibility_status}
          </span>
        </td>
        <td>
          <button type="button" class="btn btn-outline btn-sm" onclick="window.app.openCaseModal(${c.id})">
            View Case Dossier
          </button>
        </td>
      </tr>
    `).join("");
  }

  getStatusChipClass(status) {
    switch (status) {
      case "Draft": return "chip-draft";
      case "Evidence Required": return "chip-evidence";
      case "Ready for Review": return "chip-ready";
      case "Submitted": return "chip-submitted";
      case "Under Investigation": return "chip-investigation";
      case "Additional Information Required": return "chip-additional";
      case "Refund/Recovery Approved": return "chip-approved";
      case "Partially Recovered": return "chip-partially";
      case "Recovered": return "chip-recovered";
      case "Rejected": return "chip-rejected";
      case "Closed": return "chip-closed";
      default: return "chip-secondary";
    }
  }

  // --------------------------------------------------------------------------
  // Inline Case Dossier & History Audit (No popup modal)
  // --------------------------------------------------------------------------
  async openCaseModal(caseId) {
    try {
      const res = await fetch(`/api/fraud/cases/${caseId}`);
      const c = await res.json();
      if (!res.ok) throw new Error(c.error || "Failed to load case.");

      document.getElementById("inlineCaseTitle").innerText = `Case Dossier: ${c.case_ref}`;
      document.getElementById("inlineCaseRef").innerText = `${c.customer_name} • ${c.bank_name} • UTR: ${c.utr_number}`;

      const historyHtml = (c.history || []).map(h => `
        <div class="timeline-item">
          <div class="timeline-dot"></div>
          <div class="timeline-meta">${h.timestamp} • <strong>${h.actor}</strong> [${h.action_type}]</div>
          <div class="timeline-details">${h.details}</div>
        </div>
      `).join("");

      const evidenceHtml = (c.evidence_files || []).map(f => `
        <div class="file-chip">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          <strong>${f.filename}</strong>
          <span class="hash-tag">SHA-256: ${f.sha256_hash.slice(0, 16)}...</span>
        </div>
      `).join("") || '<p class="text-sm text-muted">No evidence files uploaded yet.</p>';

      const dossierBody = document.getElementById("inlineCaseBody");
      dossierBody.innerHTML = `
        <div class="modal-dossier-grid">
          <div class="metric-row">
            <div class="metric-box">
              <span class="metric-label">Reported Amount</span>
              <strong>₹${c.amount_reported.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong>
            </div>
            <div class="metric-box">
              <span class="metric-label">Approved for Recovery</span>
              <strong>₹${(c.amount_approved || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong>
            </div>
            <div class="metric-box">
              <span class="metric-label">Actually Recovered</span>
              <strong class="text-success">₹${(c.amount_recovered || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong>
            </div>
          </div>

          <div class="summary-box mt-4">
            <strong>Incident Description:</strong>
            <p class="text-sm">${c.description}</p>
          </div>

          <div class="summary-box mt-2">
            <strong>Statutory Eligibility Assessment:</strong>
            <p class="text-sm"><strong>${c.eligibility_status}</strong>: ${c.status_reason || "Adjudicated under RBI 2017-18 framework."}</p>
          </div>

          <div class="mt-4">
            <h5>Uploaded Evidence Files (Forensic Hash):</h5>
            <div class="file-chips-container mt-2">${evidenceHtml}</div>
          </div>

          <div class="mt-4">
            <h5>Audit Chronology & Dispute History:</h5>
            <div class="timeline">${historyHtml}</div>
          </div>
        </div>
      `;

      const card = document.getElementById("inlineDossierCard");
      if (card) {
        card.classList.remove("hidden");
        card.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  closeInlineDossier() {
    const card = document.getElementById("inlineDossierCard");
    if (card) card.classList.add("hidden");
  }

  closeCaseModal() {
    this.closeInlineDossier();
  }



  // --------------------------------------------------------------------------
  // Module 1: Transaction Scanner (Existing capability)
  // --------------------------------------------------------------------------
  async handleTxnScanSubmit(e) {
    e.preventDefault();
    const payload = {
      account_id: document.getElementById("scanAccount").value.trim(),
      amount: document.getElementById("scanAmount").value,
      channel: document.getElementById("scanChannel").value,
      location: document.getElementById("scanLocation").value.trim(),
      time_of_day: document.getElementById("scanTime").value
    };

    try {
      const res = await fetch("/api/fraud/scan-transaction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Scan failed.");

      const badge = document.getElementById("scanResultBadge");
      badge.innerText = `${data.risk_level} Risk (${data.risk_score}/100)`;
      badge.className = `status-chip ${data.risk_score >= 70 ? 'chip-danger' : (data.risk_score >= 40 ? 'chip-warning' : 'chip-success')}`;

      const resultView = document.getElementById("scanResultView");
      resultView.innerHTML = `
        <div class="metric-row">
          <div class="metric-box">
            <span class="metric-label">Scan Ref</span>
            <strong class="font-mono text-primary">${data.scan_ref}</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Fraud Probability</span>
            <strong>${data.risk_score}%</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Action</span>
            <strong>${data.risk_level}</strong>
          </div>
        </div>
        <div class="summary-box mt-2">
          <strong>Recommended Automated Action:</strong>
          <p class="text-sm">${data.recommended_action}</p>
        </div>
        <div class="callout-warning mt-2">
          <h5>Rules Triggered:</h5>
          <ul class="bullet-list">
            ${(data.rules_triggered || []).map(r => `<li>${r}</li>`).join("")}
          </ul>
        </div>
      `;
      this.showToast("Transaction risk scan complete.", "success");
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  // --------------------------------------------------------------------------
  // Module 2: Smart ID
  // --------------------------------------------------------------------------
  async handleSmartIdSubmit(e) {
    e.preventDefault();
    const payload = {
      full_name: document.getElementById("idFullName").value.trim(),
      id_type: document.getElementById("idDocType").value,
      id_number: document.getElementById("idDocNumber").value.trim()
    };

    try {
      const res = await fetch("/api/smart-id/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Identity verification failed.");

      const badge = document.getElementById("smartIdBadge");
      badge.innerText = data.verification_status;
      badge.className = `status-chip ${data.verification_status === 'VERIFIED' ? 'chip-success' : 'chip-danger'}`;

      const container = document.getElementById("smartIdResultContainer");
      container.innerHTML = `
        <div class="summary-box">
          <div class="meta-label">Digital KYC Certificate</div>
          <h4 class="text-primary font-mono">${data.verification_ref}</h4>
          <span class="text-xs text-muted">Issued: ${data.created_at}</span>
        </div>

        <div class="metric-row mt-2">
          <div class="metric-box">
            <span class="metric-label">Masked Identifier</span>
            <strong>${data.id_number_masked}</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Biometric Face Match</span>
            <strong class="text-success">${data.face_match_score}%</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Liveness Check</span>
            <strong>${data.liveness_verified ? '3D Active Pass' : 'Failed'}</strong>
          </div>
        </div>

        <div class="summary-box mt-2">
          <strong>AML Watchlist & PEP Status:</strong>
          <p class="text-sm ${data.pep_flag ? 'text-warning' : 'text-success'}">${data.aml_status}</p>
        </div>

        <div class="mt-2 text-xs text-muted font-mono" style="word-break: break-all; background: #f8fafc; padding: 0.5rem; border-radius: 4px;">
          Certificate SHA-256: ${data.tamper_evident_certificate_hash}
        </div>
      `;
      this.showToast("Smart ID verification completed successfully!", "success");
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  // --------------------------------------------------------------------------
  // Module 2: Smart ID - Session & Customer Management
  // --------------------------------------------------------------------------
  async loadCustomerProfiles() {
    try {
      const res = await fetch("/api/smart-id/customers");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load customers.");
      if (this.activeCustomerSelect && data.customers && data.customers.length) {
        const currentVal = this.activeCustomerSelect.value;
        this.activeCustomerSelect.innerHTML = data.customers.map(c => `
          <option value="${c.customer_id}" data-name="${c.full_name}" data-role="${c.role}">
            ${c.customer_id}: ${c.full_name} (${c.role === 'bank_manager' ? 'Bank Manager Oversight' : 'Customer'})
          </option>
        `).join("");
        if (currentVal) this.activeCustomerSelect.value = currentVal;
      }
    } catch (err) {
      console.warn("loadCustomerProfiles error:", err);
    }
  }

  handleCustomerChange(e) {
    const selectedOption = e.target.selectedOptions[0];
    if (!selectedOption) return;
    this.activeCustomerId = selectedOption.value;
    this.activeCustomerName = selectedOption.dataset.name || "Customer";
    this.activeActorRole = selectedOption.dataset.role || "customer";

    if (this.activeRoleChip) {
      this.activeRoleChip.innerText = this.activeActorRole === "bank_manager" ? "Bank Manager" : "Customer";
      this.activeRoleChip.className = `status-chip ${this.activeActorRole === "bank_manager" ? "chip-warning" : "chip-primary"}`;
    }

    if (this.vaultOwnerChip) {
      this.vaultOwnerChip.innerText = `Session: ${this.activeCustomerId} (${this.activeCustomerName})`;
    }

    const loanApplicantInput = document.getElementById("loanApplicantName");
    if (loanApplicantInput && this.activeActorRole !== "bank_manager") {
      loanApplicantInput.value = this.activeCustomerName;
    }

    this.cancelReplacementMode();
    this.closeInlinePreview();
    this.loadSmartIdDocuments();
    this.loadLoanChecklist();
    this.loadAuditLogs();
    this.showToast(`Switched active profile to ${this.activeCustomerId} (${this.activeCustomerName})`, "info");
  }

  // --------------------------------------------------------------------------
  // Module 2: Smart ID - Document Vault
  // --------------------------------------------------------------------------
  async loadSmartIdDocuments() {
    if (!this.customerDocsTableBody) return;
    this.customerDocsTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">Fetching secure customer documents...</td></tr>`;

    try {
      const res = await fetch(`/api/smart-id/documents?customer_id=${this.activeCustomerId}`, {
        headers: {
          "X-Actor-Id": this.activeCustomerId,
          "X-Actor-Role": this.activeActorRole,
          "X-Customer-Id": this.activeCustomerId
        }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load documents.");

      const docs = data.documents || [];
      this.updateDocumentMetrics(docs);

      if (docs.length === 0) {
        this.customerDocsTableBody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center text-muted py-4">
              No documents uploaded yet for ${this.activeCustomerId}. Use the secure intake form above to deposit PDFs.
            </td>
          </tr>
        `;
        return;
      }

      this.customerDocsTableBody.innerHTML = docs.map(doc => {
        const isExpired = doc.expiry_date && doc.expiry_date < new Date().toISOString().slice(0, 10);
        let statusBadgeClass = "chip-secondary";
        let statusText = doc.verification_status.toUpperCase();

        if (doc.verification_status === "verified") {
          statusBadgeClass = "chip-verified";
          statusText = "VERIFIED";
        } else if (doc.verification_status === "rejected") {
          statusBadgeClass = "chip-rejected";
          statusText = "REJECTED";
        } else if (doc.verification_status === "expired" || isExpired) {
          statusBadgeClass = "chip-expired";
          statusText = "EXPIRED";
        } else if (doc.verification_status === "pending_verification") {
          statusBadgeClass = "chip-pending";
          statusText = "PENDING REVIEW";
        } else if (doc.verification_status === "uploaded") {
          statusBadgeClass = "chip-uploaded";
          statusText = "UPLOADED";
        }

        const sizeKb = (doc.file_size / 1024).toFixed(1);
        const canReplace = doc.verification_status === "rejected" || doc.verification_status === "expired" || isExpired;
        const isManager = this.activeActorRole === "bank_manager";

        return `
          <tr>
            <td class="font-mono text-xs">#${doc.id}</td>
            <td><strong>${doc.document_type}</strong></td>
            <td>
              <div class="text-sm">${doc.original_filename}</div>
              <div class="text-xs text-muted font-mono">${sizeKb} KB | SHA: ${doc.file_hash.substring(0, 10)}...</div>
            </td>
            <td class="text-xs text-muted">${doc.upload_date}</td>
            <td class="text-xs">${doc.expiry_date ? (isExpired ? `<span class="text-danger font-semibold">${doc.expiry_date} (EXPIRED)</span>` : doc.expiry_date) : '<span class="text-muted">Lifetime</span>'}</td>
            <td>
              <span class="status-chip ${statusBadgeClass}">${statusText}</span>
              ${doc.rejection_reason ? `<div class="text-xs text-danger mt-1">Reason: ${doc.rejection_reason}</div>` : ''}
            </td>
            <td class="text-xs font-mono">v${doc.version || 1}</td>
            <td class="text-right">
              <div class="btn-action-group">
                <button type="button" class="btn-xs btn-action-preview" onclick="window.app.previewDocumentById(${doc.id})" title="Inline Preview">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  Preview
                </button>
                <button type="button" class="btn-xs btn-action-download" onclick="window.app.downloadDocumentById(${doc.id})" title="Secure Download">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                  Download
                </button>
                ${canReplace ? `
                  <button type="button" class="btn-xs btn-action-replace" onclick="window.app.startReplacementModeById(${doc.id}, '${doc.document_type}', ${doc.version || 1}, '${doc.rejection_reason || 'Document expired or rejected'}')" title="Replace Document">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                    Replace
                  </button>
                ` : ''}
                ${isManager ? `
                  <button type="button" class="btn-xs btn-review-approve" onclick="window.app.reviewDocument(${doc.id}, 'verified')" title="Approve Verification">
                    &check; Verify
                  </button>
                  <button type="button" class="btn-xs btn-review-reject" onclick="window.app.reviewDocument(${doc.id}, 'rejected')" title="Reject Document">
                    &times; Reject
                  </button>
                ` : ''}
              </div>
            </td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      this.customerDocsTableBody.innerHTML = `<tr><td colspan="8" class="text-danger py-4 text-center">Error: ${err.message}</td></tr>`;
      this.showToast(err.message, "danger");
    }
  }

  updateDocumentMetrics(docs) {
    if (!this.metricTotalDocs) return;
    const total = docs.length;
    const verified = docs.filter(d => d.verification_status === "verified").length;
    const pending = docs.filter(d => d.verification_status === "pending_verification" || d.verification_status === "uploaded").length;
    const rejected = docs.filter(d => d.verification_status === "rejected").length;
    const expired = docs.filter(d => d.verification_status === "expired" || (d.expiry_date && d.expiry_date < new Date().toISOString().slice(0, 10))).length;

    this.metricTotalDocs.innerText = total;
    this.metricVerifiedDocs.innerText = verified;
    this.metricPendingDocs.innerText = pending;
    this.metricRejectedDocs.innerText = rejected;
    this.metricExpiredDocs.innerText = expired;
  }

  async handleDocUpload(e) {
    e.preventDefault();
    if (!this.vaultPdfFile.files.length) {
      this.showToast("Please choose a PDF document to upload.", "warning");
      return;
    }

    const file = this.vaultPdfFile.files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      this.showToast("Security guardrail: Only genuine PDF (.pdf) documents are permitted.", "danger");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("expiry_date", this.vaultExpiryDate.value || "");
    formData.append("actor_role", this.activeActorRole);

    const isReplacing = Boolean(this.currentReplacingDocId);
    let url = "/api/smart-id/documents/upload";
    if (isReplacing) {
      url = `/api/smart-id/documents/${this.currentReplacingDocId}/replace`;
    } else {
      formData.append("document_type", this.vaultDocType.value);
    }

    this.btnUploadDoc.disabled = true;
    this.btnUploadDocText.innerText = isReplacing ? "Replacing Document..." : "Uploading to Private Vault...";

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "X-Actor-Id": this.activeCustomerId,
          "X-Actor-Role": this.activeActorRole,
          "X-Customer-Id": this.activeCustomerId
        },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Upload failed.");

      this.showToast(data.message || "Document securely saved in private storage!", "success");
      this.docUploadForm.reset();
      this.cancelReplacementMode();
      this.loadSmartIdDocuments();
      this.loadLoanChecklist();
      this.loadAuditLogs();
    } catch (err) {
      this.showToast(err.message, "danger");
    } finally {
      this.btnUploadDoc.disabled = false;
      this.btnUploadDocText.innerText = "Upload Document to Private Vault";
    }
  }

  startReplacementModeById(docId, docType, version, reason) {
    this.currentReplacingDocId = docId;
    if (this.replaceDocId) this.replaceDocId.value = docId;
    if (this.replacingDocTitle) this.replacingDocTitle.innerText = docType;
    if (this.replacingDocVersion) this.replacingDocVersion.innerText = `v${version} -> v${version + 1}`;
    if (this.replacingDocReason) this.replacingDocReason.innerText = reason ? `Deficiency Notice: ${reason}` : "";
    if (this.vaultDocType) {
      this.vaultDocType.value = docType;
      this.vaultDocType.disabled = true;
    }
    if (this.replacementAlertBanner) this.replacementAlertBanner.classList.remove("hidden");
    if (this.btnUploadDocText) this.btnUploadDocText.innerText = `Upload Replacement Document (v${version + 1})`;

    const uploadBox = document.querySelector(".doc-upload-box");
    if (uploadBox) uploadBox.scrollIntoView({ behavior: "smooth" });
  }

  cancelReplacementMode() {
    this.currentReplacingDocId = null;
    if (this.replaceDocId) this.replaceDocId.value = "";
    if (this.replacementAlertBanner) this.replacementAlertBanner.classList.add("hidden");
    if (this.vaultDocType) this.vaultDocType.disabled = false;
    if (this.btnUploadDocText) this.btnUploadDocText.innerText = "Upload Document to Private Vault";
  }

  previewDocumentById(docId) {
    if (!this.inlineDocPreviewCard || !this.inlinePdfFrame) return;
    this.inlineDocPreviewCard.classList.remove("hidden");
    if (this.previewDocTitle) this.previewDocTitle.innerText = `Inline Document Preview (ID: #${docId})`;
    if (this.previewDocMeta) this.previewDocMeta.innerText = `Streaming authenticated PDF for ${this.activeCustomerId} via Row-Level Security`;
    this.inlinePdfFrame.src = `/api/smart-id/documents/${docId}/preview?customer_id=${this.activeCustomerId}&actor_id=${this.activeCustomerId}&actor_role=${this.activeActorRole}`;
    this.inlineDocPreviewCard.scrollIntoView({ behavior: "smooth" });
    setTimeout(() => this.loadAuditLogs(), 1000);
  }

  closeInlinePreview() {
    if (this.inlineDocPreviewCard) this.inlineDocPreviewCard.classList.add("hidden");
    if (this.inlinePdfFrame) this.inlinePdfFrame.src = "about:blank";
  }

  downloadDocumentById(docId) {
    const downloadUrl = `/api/smart-id/documents/${docId}/download?customer_id=${this.activeCustomerId}&actor_id=${this.activeCustomerId}&actor_role=${this.activeActorRole}`;
    window.open(downloadUrl, "_blank");
    this.showToast("Initiating authorized document download with audit log...", "info");
    setTimeout(() => this.loadAuditLogs(), 1200);
  }

  async reviewDocument(docId, newStatus) {
    let rejectionReason = null;
    if (newStatus === "rejected") {
      rejectionReason = prompt("Enter mandatory rejection reason for compliance audit log:", "Illegible document or missing statutory details");
      if (!rejectionReason) return;
    }

    try {
      const res = await fetch(`/api/smart-id/documents/${docId}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Actor-Id": this.activeCustomerId,
          "X-Actor-Role": this.activeActorRole,
          "X-Customer-Id": this.activeCustomerId
        },
        body: JSON.stringify({
          status: newStatus,
          rejection_reason: rejectionReason
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Review submission failed.");

      this.showToast(`Document #${docId} status updated to ${newStatus.toUpperCase()}`, "success");
      this.loadSmartIdDocuments();
      this.loadLoanChecklist();
      this.loadAuditLogs();
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  async loadAuditLogs() {
    if (!this.auditLogsTableBody) return;
    try {
      const res = await fetch(`/api/smart-id/documents/audit-logs?customer_id=${this.activeCustomerId}`, {
        headers: {
          "X-Actor-Id": this.activeCustomerId,
          "X-Actor-Role": this.activeActorRole,
          "X-Customer-Id": this.activeCustomerId
        }
      });
      const data = await res.json();
      if (!res.ok) return;

      const logs = data.audit_logs || [];
      if (!logs.length) {
        this.auditLogsTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-3">No audit activity recorded yet.</td></tr>`;
        return;
      }

      this.auditLogsTableBody.innerHTML = logs.slice(0, 10).map(log => `
        <tr>
          <td class="text-xs font-mono">${log.timestamp}</td>
          <td class="text-xs font-semibold">${log.actor_id}</td>
          <td><span class="status-chip chip-secondary">${log.actor_role}</span></td>
          <td><strong>${log.action}</strong></td>
          <td class="text-xs">#${log.document_id || '-'} ${log.document_type ? `(${log.document_type})` : ''}</td>
          <td class="text-xs font-mono">${log.ip_address}</td>
          <td class="text-xs text-muted">${log.details || ''}</td>
        </tr>
      `).join("");
    } catch (err) {
      console.warn("loadAuditLogs error:", err);
    }
  }

  // --------------------------------------------------------------------------
  // Module 3: Smart Loan Predictor & Cross-Module Checklist Gatekeeper
  // --------------------------------------------------------------------------
  async loadLoanChecklist() {
    if (!this.checklistItemsList) return;
    const loanType = this.loanTypeSelect ? this.loanTypeSelect.value : "Instant Fast-Track Loan (LoanFast 72)";

    try {
      const res = await fetch(`/api/loan/checklist?loan_type=${encodeURIComponent(loanType)}&customer_id=${this.activeCustomerId}`, {
        headers: {
          "X-Actor-Id": this.activeCustomerId,
          "X-Actor-Role": this.activeActorRole,
          "X-Customer-Id": this.activeCustomerId
        }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to evaluate checklist.");

      if (this.checklistStatusBadge) {
        if (data.can_proceed) {
          this.checklistStatusBadge.innerText = "READY FOR UNDERWRITING";
          this.checklistStatusBadge.className = "status-chip chip-verified";
        } else {
          this.checklistStatusBadge.innerText = `ACTION REQUIRED (${data.blocking_reasons.length} BLOCKERS)`;
          this.checklistStatusBadge.className = "status-chip chip-danger";
        }
      }

      const items = data.checklist || [];
      this.checklistItemsList.innerHTML = items.map(item => {
        let chipClass = "chip-secondary";
        let icon = "&quest;";
        if (item.status === "verified") {
          chipClass = "chip-verified";
          icon = "&check;";
        } else if (item.status === "expired") {
          chipClass = "chip-expired";
          icon = "&excl;";
        } else if (item.status === "rejected") {
          chipClass = "chip-rejected";
          icon = "&times;";
        } else if (item.status === "pending_verification" || item.status === "uploaded") {
          chipClass = "chip-pending";
          icon = "&#9203;";
        } else if (item.status === "missing") {
          chipClass = "chip-missing";
          icon = "&empty;";
        }

        return `
          <div class="checklist-item ${item.is_blocking ? 'item-blocking' : 'item-verified'}">
            <div class="checklist-item-info">
              <div>
                <span class="checklist-item-title">${item.document_type}</span>
                <span class="text-xs text-muted font-mono">(${item.category})</span>
                <div class="checklist-item-desc">${item.action_needed}</div>
              </div>
            </div>
            <div class="checklist-item-status">
              <span class="status-chip ${chipClass}">${icon} ${item.badge}</span>
            </div>
          </div>
        `;
      }).join("");

      if (this.gatekeeperAlertBanner) {
        if (data.can_proceed) {
          this.gatekeeperAlertBanner.className = "alert-box alert-success mt-2";
          if (this.gatekeeperAlertTitle) this.gatekeeperAlertTitle.innerText = "Checklist Complete & Verified";
          if (this.gatekeeperAlertText) this.gatekeeperAlertText.innerText = data.summary_message;
        } else {
          this.gatekeeperAlertBanner.className = "alert-box alert-warning mt-2";
          if (this.gatekeeperAlertTitle) this.gatekeeperAlertTitle.innerText = "Document Checklist Incomplete";
          if (this.gatekeeperAlertText) this.gatekeeperAlertText.innerText = `${data.summary_message} Missing or expired documents prevent algorithmic risk evaluation.`;
        }
      }

      if (this.btnEvaluateLoan) {
        this.btnEvaluateLoan.disabled = !data.can_proceed;
        if (!data.can_proceed) {
          this.btnEvaluateLoan.title = "Underwriting locked: resolve required document deficiencies in Smart ID to enable credit assessment.";
        } else {
          this.btnEvaluateLoan.title = "All required documents present and valid. Ready for credit underwriting.";
        }
      }
    } catch (err) {
      console.warn("loadLoanChecklist error:", err);
    }
  }

  // --------------------------------------------------------------------------
  // Module 3: AI LoanFast 72
  // --------------------------------------------------------------------------
  async handleLoanFastSubmit(e) {
    e.preventDefault();
    const payload = {
      applicant_name: document.getElementById("loanApplicantName").value.trim(),
      monthly_income: document.getElementById("loanIncome").value,
      existing_obligations: document.getElementById("loanObligations").value,
      cibil_score: document.getElementById("loanCibil").value,
      employment_type: document.getElementById("loanEmployment").value,
      loan_requested: document.getElementById("loanAmount").value,
      tenor_months: document.getElementById("loanTenor").value,
      loan_type: this.loanTypeSelect ? this.loanTypeSelect.value : "Instant Fast-Track Loan (LoanFast 72)",
      customer_id: this.activeCustomerId
    };

    try {
      const res = await fetch("/api/loan/evaluate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Actor-Id": this.activeCustomerId,
          "X-Actor-Role": this.activeActorRole,
          "X-Customer-Id": this.activeCustomerId
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Loan underwriting failed.");

      const badge = document.getElementById("loanDecisionBadge");
      badge.innerText = data.decision_status.includes("Approved") ? "Approved" : "Review Required";
      badge.className = `status-chip ${data.approved_amount > 0 ? 'chip-success' : 'chip-danger'}`;

      const container = document.getElementById("loanResultContainer");
      container.innerHTML = `
        <div class="summary-box">
          <div class="meta-label">72-Hour Decision Reference</div>
          <h4 class="text-primary font-mono">${data.application_ref}</h4>
          <span class="text-xs text-muted">${data.turnaround_sla}</span>
        </div>

        <div class="metric-row mt-2">
          <div class="metric-box">
            <span class="metric-label">Sanctioned Amount</span>
            <strong class="text-success">₹${data.approved_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Approved APR</span>
            <strong>${data.interest_rate_apr}%</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Monthly EMI</span>
            <strong>₹${data.monthly_emi.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong>
          </div>
        </div>

        <div class="metric-row mt-2">
          <div class="metric-box">
            <span class="metric-label">Debt-to-Income (DTI)</span>
            <strong>${data.dti_ratio}%</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Tenor</span>
            <strong>${data.tenor_months} Months</strong>
          </div>
          <div class="metric-box">
            <span class="metric-label">Risk Classification</span>
            <span class="text-xs font-semibold">${data.risk_tier}</span>
          </div>
        </div>

        <div class="summary-box mt-2">
          <strong>Explainable AI (XAI) Underwriting Factors:</strong>
          <ul class="bullet-list text-sm mt-1">
            ${(data.xai_factors.positive_factors || []).map(f => `<li class="text-success">&check; ${f}</li>`).join("")}
            ${(data.xai_factors.caution_factors || []).map(f => `<li class="text-warning">&excl; ${f}</li>`).join("")}
          </ul>
        </div>

        <div class="regulatory-disclaimer-card mt-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          <div class="disclaimer-text">
            <strong>Statutory Notice:</strong> Do not treat document presence as proof of authenticity or guarantee loan approval. Final sanction is subject to human bank manager review and verification.
          </div>
        </div>
      `;
      this.showToast("LoanFast 72 underwriting complete!", "success");
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  }

  // --------------------------------------------------------------------------
  // Notifications
  // --------------------------------------------------------------------------
  showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      <span>${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.25s ease";
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }
}

// Bootstrap
document.addEventListener("DOMContentLoaded", () => {
  window.app = new UnifiedBankingApp();
});
