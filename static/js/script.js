const form = document.getElementById("resume-form");
const fileInput = document.getElementById("resume");
const uploadBox = document.getElementById("upload-box");
const fileHelp = document.getElementById("file-help");
const textarea = document.getElementById("job_description");
const submitBtn = document.getElementById("submit-btn");
const loader = document.getElementById("loader");
const result = document.getElementById("result");
const aiImproveModal = document.getElementById("ai-improve-modal");
const aiImproveContent = document.getElementById("ai-improve-content");
const copySuggestionsBtn = document.getElementById("copy-suggestions-btn");
const downloadSuggestionsBtn = document.getElementById("download-suggestions-btn");
const toast = document.getElementById("toast");
let aiSuggestions = "";
let lastFocusedElement = null;
let toastTimeout;

const escapeHtml = (value = "") =>
    String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

const formatScore = (score) => Number(score || 0).toFixed(1);

const chipList = (items = [], missing = false) => {
    if (!items.length) {
        return '<p class="empty-state">Nothing to show yet.</p>';
    }

    return `
        <div class="chips">
            ${items.map((item) => `<span class="chip ${missing ? "missing" : ""}">${escapeHtml(item)}</span>`).join("")}
        </div>
    `;
};

const metricCard = (label, value) => {
    const score = Math.max(0, Math.min(100, Number(value || 0)));

    return `
        <article class="metric-card">
            <span>${escapeHtml(label)}</span>
            <strong>${formatScore(score)}%</strong>
            <div class="bar"><span style="width: ${score}%"></span></div>
        </article>
    `;
};

// Render resume-section availability from the new `sections` response object.
const resumeSectionsCard = (sections) => {
    const sectionNames = ["Summary", "Skills", "Projects", "Education", "Experience"];

    if (!sections || typeof sections !== "object") {
        return "";
    }

    return `
        <article class="feedback-card resume-sections-card">
            <h3>Resume Sections</h3>
            <div class="resume-sections-grid">
                ${sectionNames.map((section) => {
                    const isPresent = sections[section];

                    if (isPresent === undefined) {
                        return `<div class="empty-state">— ${section} (Not provided)</div>`;
                    }

                    return `
                        <div class="resume-section ${isPresent ? "is-present" : "is-missing"}">
                            ${isPresent ? "✓" : "✗"} ${section}
                        </div>
                    `;
                }).join("")}
            </div>
        </article>
    `;
};

// Replace the old ordered feedback list with recommendation cards.
const recommendationsCard = (recommendations) => {
    if (!recommendations.length) {
        return `
            <article class="feedback-card">
                <h3>Recommendations</h3>
                <p class="empty-state">No extra recommendations returned.</p>
            </article>
        `;
    }

    return `
        <article class="feedback-card">
            <h3>Recommendations</h3>
            ${recommendations.map((item) => `
                <div class="recommendation-item">
                    <strong style="color: #087d75;">✓</strong>
                    <span>${escapeHtml(item)}</span>
                </div>
            `).join("")}
        </article>
    `;
};

const setFileName = () => {
    const file = fileInput.files[0];
    fileHelp.textContent = file ? `${file.name} selected` : "PDF only. Max 5MB file size.";
};

const setLoading = (isLoading) => {
    submitBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? "Checking..." : "Check Your Score";
    loader.classList.toggle("hidden", !isLoading);
};

const openAiModal = () => {
    lastFocusedElement = document.activeElement;
    aiImproveModal.classList.remove("hidden");
    document.body.classList.add("modal-open");
    aiImproveModal.querySelector(".ai-modal__close").focus();
};

const closeAiModal = () => {
    aiImproveModal.classList.add("hidden");
    document.body.classList.remove("modal-open");
    lastFocusedElement?.focus();
};

const showToast = (message) => {
    toast.textContent = message;
    toast.classList.remove("hidden");
    window.clearTimeout(toastTimeout);
    toastTimeout = window.setTimeout(() => toast.classList.add("hidden"), 2200);
};

const copyRenderedSuggestions = async () => {
    const plainText = aiImproveContent.innerText.trim() || aiSuggestions;
    const renderedHtml = aiImproveContent.innerHTML;

    if (navigator.clipboard?.write && window.ClipboardItem) {
        try {
            await navigator.clipboard.write([
                new ClipboardItem({
                    "text/plain": new Blob([plainText], { type: "text/plain" }),
                    "text/html": new Blob([renderedHtml], { type: "text/html" }),
                }),
            ]);
            return;
        } catch (error) {
            // Some browsers support text clipboard access but not rich HTML clipboard items.
        }
    }

    if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(plainText);
        return;
    }

    const fallback = document.createElement("textarea");
    fallback.value = plainText;
    fallback.setAttribute("readonly", "");
    fallback.style.position = "fixed";
    fallback.style.opacity = "0";
    document.body.appendChild(fallback);
    fallback.select();
    const copied = document.execCommand("copy");
    fallback.remove();
    if (!copied) throw new Error("Clipboard is unavailable");
};

const decorateAiSections = () => {
    const icons = { "Professional Summary": "✦", Projects: "⌘", Skills: "◈", Experience: "▣", Achievements: "★", "ATS Tips": "✓" };
    aiImproveContent.querySelectorAll("h2").forEach((heading) => {
        const label = heading.textContent.trim();
        heading.classList.add("ai-section-title");
        if (icons[label]) heading.innerHTML = `<span aria-hidden="true">${icons[label]}</span>${escapeHtml(label)}`;
    });
    aiImproveContent.querySelectorAll("h3").forEach((heading) => {
        const label = heading.textContent.trim().toLowerCase();
        if (label === "current" || label === "improved") heading.classList.add("ai-comparison-label", `is-${label}`);
    });
    aiImproveContent.querySelectorAll("p").forEach((paragraph) => {
        if (paragraph.textContent.trim() === "↓") paragraph.classList.add("ai-improvement-arrow");
    });
};

const renderAiLoading = () => {
    aiSuggestions = "";
    aiImproveContent.innerHTML = '<div class="ai-loading" role="status" aria-live="polite"><span class="ai-loading__spinner" aria-hidden="true"></span><div><strong>AI is analyzing your resume...</strong><p>Creating accurate, ATS-focused improvements from your existing content.</p></div></div>';
    copySuggestionsBtn.classList.add("hidden");
    downloadSuggestionsBtn.classList.add("hidden");
    openAiModal();
};

const renderAiError = (message) => {
    aiSuggestions = "";
    aiImproveContent.innerHTML = `<p class="ai-modal__error" role="alert">${escapeHtml(message)}</p>`;
    copySuggestionsBtn.classList.add("hidden");
    downloadSuggestionsBtn.classList.add("hidden");
    openAiModal();
};

const renderAiSuggestions = (suggestions, html) => {
    aiSuggestions = suggestions;
    // Markdown is converted server-side with Python-Markdown and sanitized before display.
    aiImproveContent.innerHTML = typeof DOMPurify !== "undefined"
        ? DOMPurify.sanitize(html)
        : html;
    decorateAiSections();
    copySuggestionsBtn.classList.remove("hidden");
    downloadSuggestionsBtn.classList.remove("hidden");
    copySuggestionsBtn.textContent = "Copy AI Suggestions";
    if (aiImproveModal.classList.contains("hidden")) openAiModal();
};

const improveResume = async (button) => {
    const file = fileInput.files[0];

    if (!file) {
        renderAiError("Please upload your resume before requesting AI suggestions.");
        return;
    }

    button.disabled = true;
    button.innerHTML = '<span class="button-spinner" aria-hidden="true"></span> AI is analyzing...';
    renderAiLoading();
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 50000);

    try {
        const formData = new FormData();
        formData.append("resume", file);
        const response = await fetch("/ai-improve", { method: "POST", body: formData, signal: controller.signal });
        const data = await response.json().catch(() => ({}));

        if (!response.ok || data.error || !data.response || !data.html) {
            renderAiError(data.error || "We could not generate suggestions right now. Please try again.");
            return;
        }

        renderAiSuggestions(data.response, data.html);
    } catch (error) {
        renderAiError(error.name === "AbortError"
            ? "The AI request took too long. Please try again in a moment."
            : "We could not reach the AI service. Please check your connection and try again.");
    } finally {
        window.clearTimeout(timeout);
        button.disabled = false;
        button.textContent = "✨ AI Improve Resume";
    }
};

const renderError = (message) => {
    result.classList.remove("hidden");
    result.innerHTML = `
        <div class="feedback-card">
            <h3>Upload issue</h3>
            <p class="empty-state">${escapeHtml(message)}</p>
        </div>
    `;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
};

const renderResult = (data) => {
    const score = Math.max(0, Math.min(100, Number(data.score || 0)));
    const matched = Array.isArray(data.matched_skills)
        ? data.matched_skills
        : Array.isArray(data.resume_skills)
            ? data.resume_skills
            : [];
    const missing = Array.isArray(data.missing_skills) ? data.missing_skills : [];
    const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];
    const title = data.mode === "job_match" ? "ATS Job Match Analysis" : "ATS Resume Analysis";

    // Use the new backend assessment field.
    const assessment = data.overall_assessment || {};

    const assessmentTitle = assessment.title || "Resume Analysis";
    const assessmentMessage =
        assessment.message || "Your resume analysis is ready.";

    result.classList.remove("hidden");
    result.innerHTML = `
        <div class="result-header">
            <div class="score-ring" style="--score-angle: ${score * 3.6}deg">
                <div class="score-ring-inner">
                    <strong>${Math.round(score)}%</strong>
                    <small>ATS SCORE</small>
                </div>
            </div>
            <div>
                <h2>${title}</h2>
                <div class="assessment-card">
                <div class="assessment-heading">
                        <span class="assessment-status" aria-hidden="true">&#10003;</span>
                        <span>Overall Assessment</span>
                    </div>

                    <h4>${escapeHtml(assessmentTitle)}</h4>
                    <p>${escapeHtml(assessmentMessage)}</p>
                </div>
            </div>
        </div>

        <div class="score-grid">
            ${data.skill_score !== undefined ? metricCard("Skill match", data.skill_score) : ""}
            ${metricCard("Sections", data.section_score)}
            ${metricCard("Contact", data.contact_score)}
            ${metricCard("Completeness", data.completeness_score)}
        </div>

        ${data.mode !== "job_match" ? resumeSectionsCard(data.sections) : ""}

        <div class="keyword-grid">
            <article class="keyword-card">
                <h3>${data.mode === "job_match" ? `Matched Skills (${matched.length})` : `Detected Skills (${matched.length})`}</h3>
                ${chipList(matched)}
            </article>
            <article class="keyword-card">
                <h3>Missing Skills (${missing.length})</h3>
                ${chipList(missing, true)}
            </article>
        </div>

        ${recommendationsCard(recommendations)}

        <div class="result-actions">
            <button type="button" class="report-button" id="download-report-btn">Download ATS Report</button>
            <button type="button" class="ai-improve-button" id="ai-improve-btn">✨ AI Improve Resume</button>
            <button type="button" class="analyze-again-button" id="analyze-again-btn">Analyze Another Resume</button>
        </div>
    `;

    const analyzeAgainBtn = document.getElementById("analyze-again-btn");

    if (analyzeAgainBtn) {
        analyzeAgainBtn.addEventListener("click", () => {
            document.getElementById("checker").scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        });
    }

    const downloadBtn = document.getElementById("download-report-btn");

    if (downloadBtn) {
        downloadBtn.addEventListener("click", () => {
            window.location.href = "/download-report";
        });
    }

    const aiImproveBtn = document.getElementById("ai-improve-btn");
    if (aiImproveBtn) {
        aiImproveBtn.addEventListener("click", () => improveResume(aiImproveBtn));
    }

    result.scrollIntoView({ behavior: "smooth", block: "start" });
};

fileInput.addEventListener("change", setFileName);

["dragenter", "dragover"].forEach((eventName) => {
    uploadBox.addEventListener(eventName, (event) => {
        event.preventDefault();
        uploadBox.classList.add("is-dragging");
    });
});

aiImproveModal.querySelectorAll("[data-modal-close]").forEach((element) => {
    element.addEventListener("click", closeAiModal);
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !aiImproveModal.classList.contains("hidden")) {
        closeAiModal();
    }
});

copySuggestionsBtn.addEventListener("click", async () => {
    try {
        await copyRenderedSuggestions();
        copySuggestionsBtn.textContent = "Copied!";
        showToast("Copied AI suggestions to clipboard.");
        setTimeout(() => { copySuggestionsBtn.textContent = "Copy AI Suggestions"; }, 1800);
    } catch (error) {
        showToast("We could not access your clipboard. Please copy the text manually.");
    }
});

downloadSuggestionsBtn.addEventListener("click", async () => {
    if (!aiSuggestions || !window.html2canvas || !window.jspdf) return;
    const originalLabel = downloadSuggestionsBtn.textContent;
    downloadSuggestionsBtn.disabled = true;
    downloadSuggestionsBtn.textContent = "Preparing PDF...";
    const timestamp = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date());
    const exportCard = document.createElement("article");
    exportCard.className = "ai-pdf-export";
    exportCard.innerHTML = `<header><p>ATS ANALYZER · AI RESUME COACH</p><h1>AI Resume Suggestions</h1><time>Generated ${escapeHtml(timestamp)}</time></header><div>${aiImproveContent.innerHTML}</div>`;
    document.body.appendChild(exportCard);
    try {
        const canvas = await window.html2canvas(exportCard, { scale: 2, backgroundColor: "#ffffff", useCORS: true });
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF("p", "mm", "a4");
        const width = 190;
        const pageHeight = 277;
        const imageHeight = (canvas.height * width) / canvas.width;
        const image = canvas.toDataURL("image/png");
        for (let offset = 0; offset < imageHeight; offset += pageHeight) {
            pdf.addImage(image, "PNG", 10, 10 - offset, width, imageHeight);
            if (offset + pageHeight < imageHeight) pdf.addPage();
        }
        pdf.save("ai-resume-suggestions.pdf");
        showToast("AI suggestions PDF downloaded.");
    } catch (error) {
        showToast("We could not create the PDF. Please try again.");
    } finally {
        exportCard.remove();
        downloadSuggestionsBtn.disabled = false;
        downloadSuggestionsBtn.textContent = originalLabel;
    }
});

["dragleave", "drop"].forEach((eventName) => {
    uploadBox.addEventListener(eventName, (event) => {
        event.preventDefault();
        uploadBox.classList.remove("is-dragging");
    });
});

uploadBox.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];

    if (file) {
        fileInput.files = event.dataTransfer.files;
        setFileName();
    }
});

textarea.addEventListener("dragover", (event) => {
    event.preventDefault();
});

textarea.addEventListener("drop", (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];

    if (!file || !file.type.startsWith("text/")) {
        return;
    }

    const reader = new FileReader();
    reader.onload = (readerEvent) => {
        textarea.value = readerEvent.target.result;
    };
    reader.readAsText(file);
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = fileInput.files[0];

    if (!file) {
        renderError("Please choose a PDF resume before checking your score.");
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        renderError("Only PDF resumes are supported right now.");
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        renderError("Please upload a PDF smaller than 5MB.");
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_description", textarea.value.trim());

    result.classList.add("hidden");
    result.innerHTML = "";
    setLoading(true);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (!response.ok || data.error) {
            renderError(data.error || "Something went wrong while analyzing your resume.");
            return;
        }

        renderResult(data);
    } catch (error) {
        renderError("Could not connect to the analyzer. Please make sure the Flask server is running.");
    } finally {
        setLoading(false);
    }
});
