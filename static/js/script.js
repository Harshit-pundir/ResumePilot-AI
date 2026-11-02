/**
 * ResumePilot AI - Unified Frontend Application Script
 * Modular architecture: UI, Upload, Analysis, AI Coach, History, and Auth
 */
(() => {
    'use strict';

    /* ==========================================================================
       Utility Helpers
       ========================================================================== */
    const escapeHtml = (str = '') =>
        String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');

    const formatBytes = (bytes) => {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    /* ==========================================================================
       Toast Notifications
       ========================================================================== */
    const toastEl = document.getElementById('toast');
    let toastTimer = null;

    const showToast = (message) => {
        if (!toastEl) return;
        toastEl.textContent = message;
        toastEl.classList.remove('hidden');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toastEl.classList.add('hidden');
        }, 2800);
    };

    /* ==========================================================================
       Mobile Navigation
       ========================================================================== */
    const initMobileNav = () => {
        const toggleBtn = document.getElementById('mobile-nav-toggle');
        const mobileMenu = document.getElementById('mobile-nav-menu');

        if (!toggleBtn || !mobileMenu) return;

        const toggleMenu = () => {
            const isOpen = mobileMenu.classList.toggle('is-open');
            toggleBtn.classList.toggle('is-open', isOpen);
            toggleBtn.setAttribute('aria-expanded', String(isOpen));
        };

        toggleBtn.addEventListener('click', toggleMenu);

        // Close on navigation click
        mobileMenu.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('is-open');
                toggleBtn.classList.remove('is-open');
                toggleBtn.setAttribute('aria-expanded', 'false');
            });
        });
    };

    /* ==========================================================================
       Double Submit Prevention (Forms)
       ========================================================================== */
    const initFormProtection = () => {
        const authForms = document.querySelectorAll('#login-form, #register-form, .logout-form');
        authForms.forEach((form) => {
            form.addEventListener('submit', function () {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('is-loading');
                }
            });
        });
    };

    /* ==========================================================================
       History Page Date & Score Formatting
       ========================================================================== */
    const initHistoryPage = () => {
        const dateCells = document.querySelectorAll('[data-date]');
        dateCells.forEach((cell) => {
            const raw = cell.getAttribute('data-date');
            if (!raw) return;
            const parsed = new Date(raw);
            if (!isNaN(parsed.getTime())) {
                cell.textContent = new Intl.DateTimeFormat(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                }).format(parsed);
            }
        });
    };

    /* ==========================================================================
       Resume Upload & File Management
       ========================================================================== */
    const form = document.getElementById('resume-form');
    const fileInput = document.getElementById('resume');
    const uploadBox = document.getElementById('upload-box');
    const selectedChip = document.getElementById('selected-file-chip');
    const chipFilename = document.getElementById('chip-filename');
    const chipFilesize = document.getElementById('chip-filesize');
    const chipRemoveBtn = document.getElementById('chip-remove-btn');
    const jobDescriptionInput = document.getElementById('job_description');
    const submitBtn = document.getElementById('submit-btn');
    const loader = document.getElementById('loader');
    const resultSection = document.getElementById('result');

    let currentFile = null;

    const setFile = (file) => {
        if (!file) {
            clearFile();
            return;
        }

        if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
            renderError('Please select a valid PDF file. Other formats are not supported.');
            clearFile();
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            renderError('File size exceeds the 5MB limit. Please upload a smaller PDF resume.');
            clearFile();
            return;
        }

        currentFile = file;
        if (chipFilename) chipFilename.textContent = file.name;
        if (chipFilesize) chipFilesize.textContent = formatBytes(file.size);

        if (uploadBox) uploadBox.classList.add('hidden');
        if (selectedChip) selectedChip.classList.remove('hidden');

        // Clear previous error in result if it was a file validation error
        if (resultSection && !resultSection.classList.contains('hidden')) {
            const isUploadError = resultSection.querySelector('.alert-card');
            if (isUploadError) {
                resultSection.classList.add('hidden');
                resultSection.innerHTML = '';
            }
        }
    };

    const clearFile = () => {
        currentFile = null;
        if (fileInput) fileInput.value = '';
        if (selectedChip) selectedChip.classList.add('hidden');
        if (uploadBox) uploadBox.classList.remove('hidden');
    };

    const initUploadControls = () => {
        if (!uploadBox || !fileInput) return;

        // Click on dropzone opens native file picker
        uploadBox.addEventListener('click', () => fileInput.click());

        // Keyboard navigation (Enter / Space)
        uploadBox.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInput.click();
            }
        });

        // Native file picker change
        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files[0]) {
                setFile(fileInput.files[0]);
            }
        });

        // Drag & Drop events
        ['dragenter', 'dragover'].forEach((eventName) => {
            uploadBox.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadBox.classList.add('is-dragover');
            });
        });

        ['dragleave', 'drop'].forEach((eventName) => {
            uploadBox.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadBox.classList.remove('is-dragover');
            });
        });

        uploadBox.addEventListener('drop', (e) => {
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
                const dropped = e.dataTransfer.files[0];
                fileInput.files = e.dataTransfer.files;
                setFile(dropped);
            }
        });

        // Chip Remove button
        if (chipRemoveBtn) {
            chipRemoveBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                clearFile();
            });
        }

        // Job description drop support
        if (jobDescriptionInput) {
            jobDescriptionInput.addEventListener('dragover', (e) => e.preventDefault());
            jobDescriptionInput.addEventListener('drop', (e) => {
                e.preventDefault();
                const file = e.dataTransfer?.files?.[0];
                if (file && (file.type.startsWith('text/') || file.name.endsWith('.txt'))) {
                    const reader = new FileReader();
                    reader.onload = (re) => {
                        jobDescriptionInput.value = re.target.result;
                    };
                    reader.readAsText(file);
                }
            });
        }
    };

    /* ==========================================================================
       Error & Result Rendering
       ========================================================================== */
    const renderError = (message, isAuthError = false) => {
        if (!resultSection) return;
        resultSection.classList.remove('hidden');

        const authAction = isAuthError
            ? `<a href="/login" class="alert-link">Log in to your account &rarr;</a>`
            : '';

        resultSection.innerHTML = `
            <div class="alert-card" role="alert">
                <div class="alert-icon" aria-hidden="true">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                </div>
                <div class="alert-body">
                    <h3 class="alert-title">${isAuthError ? 'Authentication Required' : 'Unable to complete analysis'}</h3>
                    <p class="alert-message">${escapeHtml(message)}</p>
                    ${authAction}
                </div>
            </div>
        `;

        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const getScoreCategory = (score) => {
        if (score >= 75) return { label: 'Strong Fit', class: 'high' };
        if (score >= 50) return { label: 'Moderate Fit', class: 'mid' };
        return { label: 'Needs Improvement', class: 'low' };
    };

    const renderResult = (data) => {
        if (!resultSection) return;

        const score = Math.max(0, Math.min(100, Math.round(Number(data.score || 0))));
        const scoreCategory = getScoreCategory(score);
        const scoreAngle = Math.round(score * 3.6);

        const isJobMatch = data.mode === 'job_match';
        const title = isJobMatch ? 'ATS Job Match Analysis' : 'ATS Resume Analysis';

        // Assessment details
        const assessment = data.overall_assessment || {};
        const assessmentTitle = assessment.title || (isJobMatch ? 'Job Description Alignment' : 'Resume Completeness');
        const assessmentMessage = assessment.message || (isJobMatch
            ? 'Skills and requirements have been cross-checked against your resume.'
            : 'Your resume sections and technical skill keywords have been extracted.');

        // Skills lists
        const matchedSkills = Array.isArray(data.matched_skills)
            ? data.matched_skills
            : Array.isArray(data.resume_skills)
                ? data.resume_skills
                : [];
        const missingSkills = Array.isArray(data.missing_skills) ? data.missing_skills : [];

        // Recommendations
        const recommendations = Array.isArray(data.recommendations)
            ? data.recommendations
            : Array.isArray(data.feedback)
                ? data.feedback
                : [];

        // Contact details
        const contact = data.contact_details || {};

        // Build HTML
        let html = `
            <div class="results-header-card">
                <div class="score-ring-wrap">
                    <div class="score-ring" style="--score-angle: ${scoreAngle}deg;" role="img" aria-label="ATS Score: ${score}%">
                        <div class="score-ring-inner">
                            <span class="score-ring-value">${score}%</span>
                            <span class="score-ring-label">ATS SCORE</span>
                        </div>
                    </div>
                </div>

                <div class="results-heading-group">
                    <span class="results-mode-badge ${isJobMatch ? 'is-job' : 'is-resume'}">
                        ${isJobMatch ? 'Job Match Scan' : 'Resume Scan'}
                    </span>
                    <h2 class="results-main-title">${escapeHtml(title)}</h2>
                    <div class="assessment-box">
                        <h4 class="assessment-title">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                            ${escapeHtml(assessmentTitle)}
                        </h4>
                        <p class="assessment-message">${escapeHtml(assessmentMessage)}</p>
                    </div>
                </div>
            </div>

            <!-- 4-Card Metric Grid -->
            <div class="metrics-grid">
                ${data.skill_score !== undefined ? `
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Skill Match</span>
                        <span class="metric-value">${Math.round(data.skill_score)}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${getScoreCategory(data.skill_score).class}" style="width: ${Math.round(data.skill_score)}%"></div>
                    </div>
                </div>` : ''}

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Section Structure</span>
                        <span class="metric-value">${Math.round(data.section_score || 0)}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${getScoreCategory(data.section_score).class}" style="width: ${Math.round(data.section_score || 0)}%"></div>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Contact Details</span>
                        <span class="metric-value">${Math.round(data.contact_score || 0)}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${getScoreCategory(data.contact_score).class}" style="width: ${Math.round(data.contact_score || 0)}%"></div>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Overall Completeness</span>
                        <span class="metric-value">${Math.round(data.completeness_score || 0)}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${getScoreCategory(data.completeness_score).class}" style="width: ${Math.round(data.completeness_score || 0)}%"></div>
                    </div>
                </div>
            </div>
        `;

        // Section availability checklist (for resume_analysis)
        if (!isJobMatch && data.sections && typeof data.sections === 'object') {
            const standardSections = ['Summary', 'Skills', 'Projects', 'Education', 'Experience'];
            html += `
                <div class="sections-card">
                    <h3 class="card-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        Essential Resume Sections
                    </h3>
                    <div class="sections-status-grid">
                        ${standardSections.map((sec) => {
                            const found = Boolean(data.sections[sec]);
                            return `
                                <div class="section-status-pill ${found ? 'is-found' : 'is-missing'}">
                                    <span>${found ? '✓' : '✗'}</span>
                                    <span>${sec}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }

        // Contact info detection checklist
        html += `
            <div class="contact-card">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                    </svg>
                    Contact &amp; Profile Links
                </h3>
                <div class="contact-grid">
                    <span class="contact-pill ${contact.email ? 'is-active' : ''}">
                        ${contact.email ? '✓ Email' : '✗ Email'}
                    </span>
                    <span class="contact-pill ${contact.phone ? 'is-active' : ''}">
                        ${contact.phone ? '✓ Phone' : '✗ Phone'}
                    </span>
                    <span class="contact-pill ${contact.linkedin ? 'is-active' : ''}">
                        ${contact.linkedin ? '✓ LinkedIn' : '✗ LinkedIn'}
                    </span>
                    <span class="contact-pill ${contact.github ? 'is-active' : ''}">
                        ${contact.github ? '✓ GitHub' : '✗ GitHub'}
                    </span>
                    <span class="contact-pill ${contact.portfolio ? 'is-active' : ''}">
                        ${contact.portfolio ? '✓ Portfolio' : '✗ Portfolio'}
                    </span>
                </div>
            </div>
        `;

        // Skills Breakdown Grid
        html += `
            <div class="skills-grid">
                <div class="skills-column">
                    <h3 class="card-title">
                        ${isJobMatch ? `Matched Skills (${matchedSkills.length})` : `Detected Skills (${matchedSkills.length})`}
                    </h3>
                    <div class="chips-container">
                        ${matchedSkills.length > 0
                            ? matchedSkills.map((s) => `<span class="skill-chip matched">${escapeHtml(s)}</span>`).join('')
                            : '<p class="empty-message">No technical skills detected yet.</p>'}
                    </div>
                </div>

                <div class="skills-column">
                    <h3 class="card-title">
                        Missing Skills (${missingSkills.length})
                    </h3>
                    <div class="chips-container">
                        ${missingSkills.length > 0
                            ? missingSkills.map((s) => `<span class="skill-chip missing">${escapeHtml(s)}</span>`).join('')
                            : `<p class="empty-message">${isJobMatch ? 'None! All job description keywords are present.' : 'Add a job description to detect missing skills.'}</p>`}
                    </div>
                </div>
            </div>
        `;

        // Actionable Recommendations
        if (recommendations.length > 0) {
            html += `
                <div class="feedback-card">
                    <h3 class="card-title">Actionable Recommendations</h3>
                    <div class="recommendations-list">
                        ${recommendations.map((rec) => `
                            <div class="recommendation-item">
                                <span class="rec-icon" aria-hidden="true">✓</span>
                                <span>${escapeHtml(rec)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Result Actions Toolbar
        html += `
            <div class="results-actions">
                <button type="button" class="btn btn-outline-dark" id="download-report-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    <span>Download ATS Report</span>
                </button>

                <button type="button" class="btn btn-primary" id="ai-improve-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                    <span>AI Improve Resume</span>
                </button>

                <button type="button" class="btn btn-ghost" id="analyze-again-btn">
                    <span>Analyze Another Resume</span>
                </button>
            </div>
        `;

        resultSection.innerHTML = html;
        resultSection.classList.remove('hidden');

        // Bind Action Listeners
        const reportBtn = document.getElementById('download-report-btn');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => {
                window.location.href = '/download-report';
            });
        }

        const aiBtn = document.getElementById('ai-improve-btn');
        if (aiBtn) {
            aiBtn.addEventListener('click', () => requestAiImprovement(aiBtn));
        }

        const resetBtn = document.getElementById('analyze-again-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                clearFile();
                if (jobDescriptionInput) jobDescriptionInput.value = '';
                resultSection.classList.add('hidden');
                document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' });
            });
        }

        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    /* ==========================================================================
       Form Submission & Analysis Request
       ========================================================================== */
    const handleFormSubmit = async (e) => {
        e.preventDefault();

        const file = currentFile || (fileInput && fileInput.files && fileInput.files[0]);

        if (!file) {
            renderError('Please upload a PDF resume before checking your score.');
            return;
        }

        if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
            renderError('Only PDF format is supported. Please choose a valid PDF file.');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            renderError('File size must be 5MB or less. Please upload a smaller PDF resume.');
            return;
        }

        // Prepare UI state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="button-spinner" aria-hidden="true"></span>
                <span>Analyzing Resume...</span>
            `;
        }

        if (resultSection) {
            resultSection.classList.add('hidden');
            resultSection.innerHTML = '';
        }

        if (loader) {
            loader.classList.remove('hidden');
            loader.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        const formData = new FormData();
        formData.append('resume', file);
        if (jobDescriptionInput && jobDescriptionInput.value.trim()) {
            formData.append('job_description', jobDescriptionInput.value.trim());
        }

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.status === 401) {
                renderError('You must be logged in to analyze resumes.', true);
                return;
            }

            const data = await response.json().catch(() => ({}));

            if (!response.ok || data.error) {
                renderError(data.error || 'An error occurred during resume evaluation. Please try again.');
                return;
            }

            renderResult(data);
        } catch (err) {
            renderError('Could not connect to the server. Please check your internet connection or verify the server is running.');
        } finally {
            if (loader) loader.classList.add('hidden');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <span>Check Your Score</span>
                `;
            }
        }
    };

    /* ==========================================================================
       AI Suggestions Modal & Generator
       ========================================================================== */
    const aiModal = document.getElementById('ai-improve-modal');
    const aiContent = document.getElementById('ai-improve-content');
    const copyBtn = document.getElementById('copy-suggestions-btn');
    const downloadPdfBtn = document.getElementById('download-suggestions-btn');
    let aiRawMarkdown = '';
    let previouslyFocusedElement = null;

    const openAiModal = () => {
        if (!aiModal) return;
        previouslyFocusedElement = document.activeElement;
        aiModal.classList.remove('hidden');
        document.body.classList.add('modal-open');
        const closeBtn = aiModal.querySelector('.modal-close-btn');
        if (closeBtn) closeBtn.focus();
    };

    const closeAiModal = () => {
        if (!aiModal) return;
        aiModal.classList.add('hidden');
        document.body.classList.remove('modal-open');
        if (previouslyFocusedElement) previouslyFocusedElement.focus();
    };

    const initAiModal = () => {
        if (!aiModal) return;

        aiModal.querySelectorAll('[data-modal-close]').forEach((el) => {
            el.addEventListener('click', closeAiModal);
        });

        // Close when clicking overlay backdrop outside dialog
        aiModal.addEventListener('click', (e) => {
            if (e.target === aiModal) {
                closeAiModal();
            }
        });

        // ESC key close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !aiModal.classList.contains('hidden')) {
                closeAiModal();
            }
        });

        // Copy button
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                const textToCopy = aiContent?.innerText.trim() || aiRawMarkdown;
                if (!textToCopy) return;

                try {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        await navigator.clipboard.writeText(textToCopy);
                    } else {
                        const fallbackInput = document.createElement('textarea');
                        fallbackInput.value = textToCopy;
                        document.body.appendChild(fallbackInput);
                        fallbackInput.select();
                        document.execCommand('copy');
                        fallbackInput.remove();
                    }
                    showToast('AI suggestions copied to clipboard!');
                } catch {
                    showToast('Unable to copy. Please select and copy manually.');
                }
            });
        }

        // Download PDF button (html2canvas + jsPDF)
        if (downloadPdfBtn) {
            downloadPdfBtn.addEventListener('click', async () => {
                if (!aiRawMarkdown || !window.html2canvas || !window.jspdf) {
                    showToast('PDF tools are still loading. Please try again.');
                    return;
                }

                const originalBtnText = downloadPdfBtn.innerHTML;
                downloadPdfBtn.disabled = true;
                downloadPdfBtn.textContent = 'Generating PDF...';

                const exportContainer = document.createElement('div');
                exportContainer.style.position = 'fixed';
                exportContainer.style.top = '-9999px';
                exportContainer.style.left = '0';
                exportContainer.style.width = '750px';
                exportContainer.style.padding = '32px';
                exportContainer.style.background = '#ffffff';
                exportContainer.style.color = '#0f172a';
                exportContainer.style.fontFamily = 'Inter, sans-serif';
                exportContainer.innerHTML = `
                    <div style="border-bottom: 2px solid #0d9488; padding-bottom: 12px; margin-bottom: 20px;">
                        <h1 style="font-size: 20px; font-weight: 700; color: #0a192f; margin: 0;">ResumePilot AI · Improvement Suggestions</h1>
                        <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Generated ${new Date().toLocaleDateString()}</p>
                    </div>
                    <div>${aiContent.innerHTML}</div>
                `;
                document.body.appendChild(exportContainer);

                try {
                    const canvas = await window.html2canvas(exportContainer, {
                        scale: 2,
                        backgroundColor: '#ffffff',
                        useCORS: true
                    });
                    const { jsPDF } = window.jspdf;
                    const pdf = new jsPDF('p', 'mm', 'a4');
                    const imgWidth = 190;
                    const pageHeight = 277;
                    const imgHeight = (canvas.height * imgWidth) / canvas.width;
                    const imgData = canvas.toDataURL('image/png');

                    let heightLeft = imgHeight;
                    let position = 10;

                    pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
                    heightLeft -= pageHeight;

                    while (heightLeft >= 0) {
                        position = heightLeft - imgHeight + 10;
                        pdf.addPage();
                        pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
                        heightLeft -= pageHeight;
                    }

                    pdf.save('ResumePilot_AI_Suggestions.pdf');
                    showToast('PDF download complete!');
                } catch {
                    showToast('Failed to generate PDF. Please try again.');
                } finally {
                    exportContainer.remove();
                    downloadPdfBtn.disabled = false;
                    downloadPdfBtn.innerHTML = originalBtnText;
                }
            });
        }
    };

    const decorateAiContent = () => {
        if (!aiContent) return;

        aiContent.querySelectorAll('h3').forEach((h3) => {
            const text = h3.textContent.trim().toLowerCase();
            if (text === 'current') {
                h3.classList.add('ai-comparison-label', 'is-current');
            } else if (text === 'improved') {
                h3.classList.add('ai-comparison-label', 'is-improved');
            }
        });

        aiContent.querySelectorAll('p').forEach((p) => {
            if (p.textContent.trim() === '↓') {
                p.classList.add('ai-improvement-arrow');
            }
        });
    };

    const requestAiImprovement = async (triggerBtn) => {
        const file = currentFile || (fileInput && fileInput.files && fileInput.files[0]);

        if (!file) {
            showToast('Please upload a resume first.');
            return;
        }

        triggerBtn.disabled = true;
        const originalText = triggerBtn.innerHTML;
        triggerBtn.innerHTML = `
            <span class="button-spinner" aria-hidden="true"></span>
            <span>Requesting AI Suggestions...</span>
        `;

        if (aiContent) {
            aiContent.innerHTML = `
                <div class="loader-card" style="margin: 32px auto; box-shadow: none; border: none;">
                    <div class="loader-spinner" aria-hidden="true"></div>
                    <h3 class="loader-title" style="font-size: 1.125rem;">Groq AI is analyzing your resume...</h3>
                    <p class="loader-desc">Reviewing content structure, action verbs, and ATS compatibility.</p>
                </div>
            `;
        }
        if (copyBtn) copyBtn.classList.add('hidden');
        if (downloadPdfBtn) downloadPdfBtn.classList.add('hidden');
        openAiModal();

        const formData = new FormData();
        formData.append('resume', file);

        try {
            const response = await fetch('/ai-improve', {
                method: 'POST',
                body: formData
            });

            if (response.status === 401) {
                if (aiContent) {
                    aiContent.innerHTML = `
                        <div class="alert-card">
                            <div class="alert-body">
                                <h3 class="alert-title">Authentication Required</h3>
                                <p class="alert-message">Please log in to your account to use the AI Resume Coach.</p>
                                <a href="/login" class="alert-link">Go to Log In &rarr;</a>
                            </div>
                        </div>
                    `;
                }
                return;
            }

            const data = await response.json().catch(() => ({}));

            if (!response.ok || data.error) {
                if (aiContent) {
                    aiContent.innerHTML = `
                        <div class="alert-card">
                            <div class="alert-body">
                                <h3 class="alert-title">AI Suggestion Error</h3>
                                <p class="alert-message">${escapeHtml(data.error || 'Failed to generate suggestions.')}</p>
                            </div>
                        </div>
                    `;
                }
                return;
            }

            aiRawMarkdown = data.response || '';
            const rawHtml = data.html || '';

            // MUST sanitize HTML with DOMPurify
            const cleanHtml = typeof window.DOMPurify !== 'undefined'
                ? window.DOMPurify.sanitize(rawHtml)
                : rawHtml;

            if (aiContent) {
                aiContent.innerHTML = cleanHtml;
                decorateAiContent();
            }

            if (copyBtn) copyBtn.classList.remove('hidden');
            if (downloadPdfBtn) downloadPdfBtn.classList.remove('hidden');
        } catch {
            if (aiContent) {
                aiContent.innerHTML = `
                    <div class="alert-card">
                        <div class="alert-body">
                            <h3 class="alert-title">Network Timeout</h3>
                            <p class="alert-message">Could not connect to the AI service. Please verify your internet connection and try again.</p>
                        </div>
                    </div>
                `;
            }
        } finally {
            triggerBtn.disabled = false;
            triggerBtn.innerHTML = originalText;
        }
    };

    /* ==========================================================================
       Initialization
       ========================================================================== */
    document.addEventListener('DOMContentLoaded', () => {
        initMobileNav();
        initFormProtection();
        initHistoryPage();
        initUploadControls();
        initAiModal();

        if (form) {
            form.addEventListener('submit', handleFormSubmit);
        }
    });
})();
