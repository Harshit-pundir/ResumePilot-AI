import math

from utils.constants import (
    CONTACT_WEIGHT, PERCENT_MULTIPLIER,
    RESUME_CONTACT_WEIGHT, RESUME_SECTION_WEIGHT,
    ROUND_DECIMALS, SECTION_WEIGHT, SKILL_WEIGHT,
    SEMANTIC_CONFIDENCE_THRESHOLD, SEMANTIC_SCORE_CREDIT,
    REQUIRED_CONTACT_FIELDS, REQUIRED_RESUME_SECTIONS, OPTIONAL_CONTACT_FIELDS,
    OPTIONAL_RESUME_SECTIONS,
)


def _percentage_score(available_count: int | float, total_count: int) -> float:
    """Convert an available-item count to a rounded percentage."""
    if not total_count or not math.isfinite(float(available_count)):
        return 0.0
    score = available_count / total_count * PERCENT_MULTIPLIER
    return round(max(0.0, min(100.0, score)), ROUND_DECIMALS)


def _bounded_score(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric):
        return 0.0
    return max(0.0, min(100.0, numeric))


def _section_present(sections: dict[str, str], key: str) -> bool:
    return bool(str(sections.get(key) or "").strip())


def _weighted_score(components: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in components)
    if total_weight <= 0:
        return 0.0
    weighted = sum(_bounded_score(score) * weight for score, weight in components) / total_weight
    return round(_bounded_score(weighted), ROUND_DECIMALS)


def calculate_skill_score(
    matched_skills: set[str],
    jd_skills: set[str],
    semantic_matches: dict[str, float] | None = None,
    unresolved_requirements: int = 0,
    evidence_matches: dict[str, float] | None = None,
) -> float:
    """Score unique exact, semantic, and evidence-based JD matches."""
    # Unparsed prose is diagnostic data, not a skill requirement.
    denominator = len(jd_skills)
    if not denominator:
        return 0
    semantic_matches = semantic_matches or {}
    evidence_matches = evidence_matches or {}
    exact_count = len(matched_skills & jd_skills)
    earned_credit = float(exact_count)
    for skill in jd_skills - matched_skills:
        semantic_confidence = semantic_matches.get(skill, 0.0)
        try:
            semantic_confidence = float(semantic_confidence)
        except (TypeError, ValueError):
            semantic_confidence = 0.0
        semantic_credit = (
            SEMANTIC_SCORE_CREDIT
            if math.isfinite(semantic_confidence) and semantic_confidence >= SEMANTIC_CONFIDENCE_THRESHOLD
            else 0.0
        )
        evidence_confidence = evidence_matches.get(skill, 0.0)
        try:
            evidence_confidence = float(evidence_confidence)
        except (TypeError, ValueError):
            evidence_confidence = 0.0
        evidence_credit = max(0.0, min(1.0, evidence_confidence)) if math.isfinite(evidence_confidence) else 0.0
        # A requirement earns at most one match credit even if duplicated across
        # semantic/evidence channels; exact evidence takes precedence above.
        earned_credit += max(semantic_credit, evidence_credit)
    return _percentage_score(earned_credit, denominator)


def calculate_section_score(sections: dict[str, str]) -> float:
    """Score required student-friendly core sections; optional sections do not reduce it."""
    available_sections = sum(_section_present(sections, key) for key in REQUIRED_RESUME_SECTIONS)
    return _percentage_score(available_sections, len(REQUIRED_RESUME_SECTIONS))


def calculate_contact_score(contact_details: dict[str, str | None]) -> float:
    """Score required contact channels; portfolio links are optional."""
    available_contact_details = sum(bool(contact_details.get(key)) for key in REQUIRED_CONTACT_FIELDS)
    return _percentage_score(available_contact_details, len(REQUIRED_CONTACT_FIELDS))


def calculate_completeness_score(sections: dict[str, str], contact_details: dict[str, str | None]) -> float:
    """Return coverage of required resume sections and required contact channels."""
    total_items = len(REQUIRED_RESUME_SECTIONS) + len(REQUIRED_CONTACT_FIELDS)
    available_items = sum(_section_present(sections, key) for key in REQUIRED_RESUME_SECTIONS)
    available_items += sum(bool(contact_details.get(key)) for key in REQUIRED_CONTACT_FIELDS)
    return _percentage_score(available_items, total_items)


def calculate_resume_score(section_score: float, contact_score: float, completeness_score: float) -> float:
    """Combine non-overlapping section and contact scores in resume-only mode."""
    return _weighted_score([
        (section_score, RESUME_SECTION_WEIGHT),
        (contact_score, RESUME_CONTACT_WEIGHT),
    ])


def calculate_ats_score(skill_score: float, section_score: float, contact_score: float, completeness_score: float) -> float:
    """Combine skill, core-section, and required-contact scores for job matching.

    ``completeness_score`` remains in the signature for caller compatibility,
    but is diagnostic only because it aggregates the other two components.
    """
    return _weighted_score([
        (skill_score, SKILL_WEIGHT),
        (section_score, SECTION_WEIGHT),
        (contact_score, CONTACT_WEIGHT),
    ])


def build_score_breakdown(
    mode: str,
    sections: dict[str, str],
    contact_details: dict[str, str | None],
    skill_score: float | None = None,
) -> dict[str, object]:
    """Return the exact weights, contributions, and required-field coverage."""
    if mode == "job_match":
        definitions = [
            ("Skill Match", _bounded_score(skill_score or 0), SKILL_WEIGHT),
            ("Section Structure", calculate_section_score(sections), SECTION_WEIGHT),
            ("Contact Details", calculate_contact_score(contact_details), CONTACT_WEIGHT),
        ]
        formula = "Skill Match x 60% + Section Structure x 25% + Contact Details x 15%"
    else:
        definitions = [
            ("Section Structure", calculate_section_score(sections), RESUME_SECTION_WEIGHT),
            ("Contact Details", calculate_contact_score(contact_details), RESUME_CONTACT_WEIGHT),
        ]
        formula = "Section Structure x 70% + Contact Details x 30%"

    components = {
        name: {
            "score": score,
            "weight": weight,
            "contribution": round(score * weight / PERCENT_MULTIPLIER, ROUND_DECIMALS),
        }
        for name, score, weight in definitions
    }
    missing_sections = [key for key in REQUIRED_RESUME_SECTIONS if not _section_present(sections, key)]
    missing_contacts = [key for key in REQUIRED_CONTACT_FIELDS if not contact_details.get(key)]
    optional_sections_present = [key for key in OPTIONAL_RESUME_SECTIONS if _section_present(sections, key)]
    optional_contacts_present = [key for key in OPTIONAL_CONTACT_FIELDS if contact_details.get(key)]
    return {
        "formula": formula,
        "components": components,
        "required_sections": {
            "present": len(REQUIRED_RESUME_SECTIONS) - len(missing_sections),
            "total": len(REQUIRED_RESUME_SECTIONS),
            "missing": missing_sections,
            "optional_present": optional_sections_present,
        },
        "required_contacts": {
            "present": len(REQUIRED_CONTACT_FIELDS) - len(missing_contacts),
            "total": len(REQUIRED_CONTACT_FIELDS),
            "missing": missing_contacts,
            "optional_present": optional_contacts_present,
        },
        "completeness_note": "Experience/leadership, achievements, certifications, and portfolio are optional and do not reduce these scores. Completeness is a required-field diagnostic and is not added again to the overall score.",
    }
