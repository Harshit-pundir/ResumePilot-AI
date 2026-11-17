from utils.constants import (
    CONTACT_WEIGHT, COMPLETENESS_WEIGHT, PERCENT_MULTIPLIER,
    RESUME_COMPLETENESS_WEIGHT, RESUME_CONTACT_WEIGHT, RESUME_SECTION_WEIGHT,
    ROUND_DECIMALS, SECTION_WEIGHT, SKILL_WEIGHT,
    SEMANTIC_CONFIDENCE_THRESHOLD, SEMANTIC_SCORE_CREDIT,
)


def _percentage_score(available_count: int | float, total_count: int) -> float:
    """Convert an available-item count to a rounded percentage."""
    score = available_count / total_count * PERCENT_MULTIPLIER
    return round(score, ROUND_DECIMALS)


def calculate_skill_score(
    matched_skills: set[str],
    jd_skills: set[str],
    semantic_matches: dict[str, float] | None = None,
    unresolved_requirements: int = 0,
) -> float:
    """Score exact and qualifying semantic matches against JD requirements."""
    denominator = len(jd_skills) + max(0, unresolved_requirements)
    if not denominator:
        return 0
    semantic_matches = semantic_matches or {}
    exact_count = len(matched_skills & jd_skills)
    semantic_credit = 0.0
    for skill, confidence in semantic_matches.items():
        qualifies_for_credit = (
            skill in jd_skills
            and confidence >= SEMANTIC_CONFIDENCE_THRESHOLD
            and skill not in matched_skills
        )
        if qualifies_for_credit:
            semantic_credit += SEMANTIC_SCORE_CREDIT
    return _percentage_score(exact_count + semantic_credit, denominator)


def calculate_section_score(sections: dict[str, str]) -> float:
    """Return the percentage of resume sections that contain text."""
    available_sections = sum(1 for section in sections.values() if section.strip())
    return _percentage_score(available_sections, len(sections))


def calculate_contact_score(contact_details: dict[str, str | None]) -> float:
    """Return the percentage of supported contact fields that are present."""
    available_contact_details = sum(1 for contact in contact_details.values() if contact)
    return _percentage_score(available_contact_details, len(contact_details))


def calculate_completeness_score(sections: dict[str, str], contact_details: dict[str, str | None]) -> float:
    """Return the percentage of all section and contact fields that are present."""
    total_items = len(sections) + len(contact_details)
    available_items = sum(1 for section in sections.values() if section.strip())
    available_items += sum(1 for contact in contact_details.values() if contact)
    return _percentage_score(available_items, total_items)


def calculate_resume_score(section_score: float, contact_score: float, completeness_score: float) -> float:
    """Combine section, contact, and completeness scores for resume-only mode."""
    final_score = (
        section_score * RESUME_SECTION_WEIGHT
        + contact_score * RESUME_CONTACT_WEIGHT
        + completeness_score * RESUME_COMPLETENESS_WEIGHT
    ) / PERCENT_MULTIPLIER
    return round(final_score, ROUND_DECIMALS)


def calculate_ats_score(skill_score: float, section_score: float, contact_score: float, completeness_score: float) -> float:
    """Combine skill, section, contact, and completeness scores for job matching."""
    final_score = (
        skill_score * SKILL_WEIGHT
        + section_score * SECTION_WEIGHT
        + contact_score * CONTACT_WEIGHT
        + completeness_score * COMPLETENESS_WEIGHT
    ) / PERCENT_MULTIPLIER
    return round(final_score, ROUND_DECIMALS)
