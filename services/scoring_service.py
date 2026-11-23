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
    skill_weights: dict[str, float] | None = None,
) -> float:
    """Score canonical JD requirements using the same per-skill weighted ledger as the API."""
    return build_skill_score_breakdown(
        jd_skills, matched_skills, semantic_matches, evidence_matches, skill_weights
    )["score"]


def build_skill_score_breakdown(
    jd_skills: set[str],
    matched_skills: set[str],
    semantic_matches: dict[str, float] | None = None,
    evidence_matches: dict[str, float] | None = None,
    skill_weights: dict[str, float] | None = None,
) -> dict[str, object]:
    """Return the weighted score and an exclusive per-canonical-skill status ledger."""
    semantic_matches = semantic_matches or {}
    evidence_matches = evidence_matches or {}
    weights = skill_weights or {}
    matches = matched_skills & jd_skills
    normalized_weights = {}
    for skill in jd_skills:
        try:
            weight = float(weights.get(skill, 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        normalized_weights[skill] = weight if math.isfinite(weight) and weight > 0 else 1.0
    denominator = sum(normalized_weights.values())
    ledger = []
    numerator = 0.0
    counts = {"matched": 0, "partial": 0, "missing": 0}
    for skill in sorted(jd_skills):
        weight = normalized_weights[skill]

        if skill in matches:
            status, credit, reason = "matched", 1.0, "Direct positive skill evidence"
        else:
            try:
                semantic_value = float(semantic_matches.get(skill, 0.0))
            except (TypeError, ValueError):
                semantic_value = 0.0
            try:
                evidence_value = float(evidence_matches.get(skill, 0.0))
            except (TypeError, ValueError):
                evidence_value = 0.0
            semantic_confidence = max(0.0, min(1.0, semantic_value)) if math.isfinite(semantic_value) else 0.0
            evidence_confidence = max(0.0, min(1.0, evidence_value)) if math.isfinite(evidence_value) else 0.0
            semantic_credit = SEMANTIC_SCORE_CREDIT if semantic_confidence >= SEMANTIC_CONFIDENCE_THRESHOLD else 0.0
            credit = max(semantic_credit, evidence_confidence)
            if credit > 0:
                status = "matched" if credit >= 1.0 else "partial"
                reason = (
                    f"Contextual implementation evidence ({evidence_confidence:.0%} confidence)"
                    if evidence_confidence >= semantic_credit and evidence_confidence > 0
                    else f"Semantic evidence ({semantic_confidence:.0%} confidence); partial credit capped at {SEMANTIC_SCORE_CREDIT:.0%}"
                )
            else:
                status, credit, reason = "missing", 0.0, "No sufficient resume evidence found"
        counts[status] += 1
        contribution = weight * credit
        numerator += contribution
        ledger.append({
            "canonical_skill": skill,
            "weight": weight,
            "status": status,
            "credit": round(credit, 4),
            "confidence": round(max(semantic_confidence, evidence_confidence), 4) if skill not in matches else 1.0,
            "contribution": round(contribution, 4),
            "contribution_percent": round(contribution / denominator * 100, 2) if denominator else 0.0,
            "reason": reason,
        })
    score = round(numerator / denominator * 100, ROUND_DECIMALS) if denominator else 0.0
    return {
        "score": score,
        "total_skills": len(ledger),
        "matched_count": counts["matched"],
        "partial_count": counts["partial"],
        "missing_count": counts["missing"],
        "total_weight": round(denominator, 4),
        "earned_weight": round(numerator, 4),
        "skills": ledger,
    }


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
