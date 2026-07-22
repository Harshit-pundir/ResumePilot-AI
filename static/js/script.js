const form = document.getElementById("resume-form");
const fileInput = document.getElementById("resume");
const uploadBox = document.getElementById("upload-box");
const fileHelp = document.getElementById("file-help");
const textarea = document.getElementById("job_description");
const submitBtn = document.getElementById("submit-btn");
const loader = document.getElementById("loader");
const result = document.getElementById("result");

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
            <button type="button" class="report-button">Download ATS Report</button>
            <button type="button" class="analyze-again-button" id="analyze-again-btn">Analyze Another Resume</button>
        </div>
    `;

    const analyzeAgainBtn = document.getElementById("analyze-again-btn");

    if (analyzeAgainBtn) {
        analyzeAgainBtn.addEventListener("click", () => {
            document.getElementById("checker").scrollIntoView({ behavior: "smooth", block: "start" });
        });
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
