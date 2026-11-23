import difflib
import re
import unicodedata


SECTION_HEADINGS = {
    "summary": ("summary", "professional summary", "professional profile", "career summary", "profile", "career objective", "objective"),
    "skills": ("technical skills", "technical expertise", "core competencies", "areas of expertise", "skills", "core skills", "professional skills", "key skills"),
    "projects": ("projects", "project", "academic projects", "selected projects", "personal projects", "key projects"),
    "education": ("education", "educational background", "academic", "academic background", "qualifications", "qualification"),
    "experience": (
        "experience", "work experience", "professional experience", "employment history",
        "work history", "internship", "internships", "internship experience", "leadership",
        "leadership experience", "student leadership", "community leadership",
        "extracurricular leadership", "positions of responsibility",
    ),
    "certifications": ("certifications", "certificates", "licenses", "licenses and certifications"),
    "achievements": ("achievements", "awards", "honors", "honours", "honors and awards", "accomplishments"),
}


def _compact_heading(text: str) -> str:
    """Normalize case, accents, OCR punctuation, and spacing for heading checks."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", text.lower())


_HEADING_LOOKUP = {
    _compact_heading(alias): section
    for section, aliases in SECTION_HEADINGS.items()
    for alias in aliases
}
_ALIAS_TO_SECTION = {
    alias: section for section, aliases in SECTION_HEADINGS.items() for alias in aliases
}
HeadingRow = tuple[int, str, str, int]


def _identify_heading(line: str) -> tuple[str | None, str]:
    """Return (section key, same-line content) for a heading line."""
    stripped = re.sub(r"^[\s\W_]+|[\s\W_]+$", "", line).strip()
    compact = _compact_heading(stripped)
    if compact in _HEADING_LOOKUP:
        return _HEADING_LOOKUP[compact], ""

    # A fuzzy OCR heading may still have inline text after a heading separator.
    separated = re.match(r"^(.+?)\s*[:|–—-]\s*(.+)$", stripped)
    if separated:
        left = _compact_heading(separated.group(1))
        best = difflib.get_close_matches(left, _HEADING_LOOKUP.keys(), n=1, cutoff=0.88)
        if best:
            return _HEADING_LOOKUP[best[0]], separated.group(2).strip()

    # OCR may join a heading and body after a colon, dash, or column separator.
    for alias in sorted(_ALIAS_TO_SECTION, key=len, reverse=True):
        section = _ALIAS_TO_SECTION[alias]
        alias_pattern = re.escape(alias).replace(r"\ ", r"\s+")
        pattern = rf"^\s*{alias_pattern}\s*[:|–—-]\s*(.+)$"
        match = re.match(pattern, stripped, flags=re.IGNORECASE)
        if match:
            return section, match.group(1).strip()

    # OCR can confuse one character in a short heading (e.g. EDUCATION with
    # lowercase l substituted for I). Fuzzy matching is limited to short lines
    # so normal prose is not treated as a section label.
    if 5 <= len(compact) <= 28:
        best = difflib.get_close_matches(compact, _HEADING_LOOKUP.keys(), n=1, cutoff=0.88)
        if best:
            return _HEADING_LOOKUP[best[0]], ""
    return None, ""


def extract_section(text: str, headings: list[str]) -> str:
    """Extract one section, stopping at any recognized resume section heading."""
    requested = {_compact_heading(heading) for heading in headings}
    sections = extract_resume_sections(text)
    for key, aliases in SECTION_HEADINGS.items():
        if requested.intersection(_compact_heading(alias) for alias in aliases):
            return sections[key]
    return ""


def _normalize_resume_lines(text: str) -> list[str]:
    """Normalize line endings and spacing, returning nonempty resume lines."""
    # OCR engines vary between line feed, carriage return, and form-feed page
    # separators. Normalize them, then merge headings split across adjacent lines.
    text = (text or "").replace("\r", "\n").replace("\f", "\n")
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in text.split("\n")]
    return [line for line in lines if line]


def _find_heading_rows(lines: list[str]) -> list[HeadingRow]:
    """Find section headings, including headings split across adjacent lines."""
    heading_rows: list[HeadingRow] = []
    skip_next: set[int] = set()
    for index, line in enumerate(lines):
        if index in skip_next:
            continue
        heading_span = 1
        key, inline_content = _identify_heading(line)
        if not key and index + 1 < len(lines):
            combined_key, _ = _identify_heading(f"{line} {lines[index + 1]}")
            if combined_key:
                key, inline_content = combined_key, ""
                skip_next.add(index + 1)
                heading_span = 2
        if key:
            heading_rows.append((index, key, inline_content, index + heading_span))
    return heading_rows


def _collect_sections(lines: list[str], heading_rows: list[HeadingRow]) -> dict[str, str]:
    """Collect text between recognized heading rows into named sections."""
    extracted = {key: [] for key in SECTION_HEADINGS}
    for row_index, (line_index, key, inline_content, content_start) in enumerate(heading_rows):
        next_heading_line = (
            heading_rows[row_index + 1][0]
            if row_index + 1 < len(heading_rows)
            else len(lines)
        )
        content = ([inline_content] if inline_content else []) + lines[content_start:next_heading_line]
        extracted[key].extend(content)

    return {key: "\n".join(value).strip() for key, value in extracted.items()}


def extract_resume_sections(text: str) -> dict[str, str]:
    """Parse resume text into section-name to section-content values."""
    lines = _normalize_resume_lines(text)
    heading_rows = _find_heading_rows(lines)
    return _collect_sections(lines, heading_rows)
