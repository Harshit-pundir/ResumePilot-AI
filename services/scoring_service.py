from utils.constants import (
    CONTACT_WEIGHT, COMPLETENESS_WEIGHT, PERCENT_MULTIPLIER,
    RESUME_COMPLETENESS_WEIGHT, RESUME_CONTACT_WEIGHT, RESUME_SECTION_WEIGHT,
    ROUND_DECIMALS, SECTION_WEIGHT, SKILL_WEIGHT,
)


def calculate_skill_score(matched_skills: set[str], jd_skills: set[str]) -> float:
    if not jd_skills:
        return 0
    return round((len(matched_skills) / len(jd_skills)) * PERCENT_MULTIPLIER, ROUND_DECIMALS)


def calculate_section_score(sections: dict[str, str]) -> float:
    available_sections = sum(1 for section in sections.values() if section.strip())
    return round((available_sections / len(sections)) * PERCENT_MULTIPLIER, ROUND_DECIMALS)


def calculate_contact_score(contact_details: dict[str, str | None]) -> float:
    available_contact_details = sum(1 for contact in contact_details.values() if contact)
    return round((available_contact_details / len(contact_details)) * PERCENT_MULTIPLIER, ROUND_DECIMALS)


def calculate_completeness_score(sections: dict[str, str], contact_details: dict[str, str | None]) -> float:
    total_items = len(sections) + len(contact_details)
    available_items = sum(1 for section in sections.values() if section.strip())
    available_items += sum(1 for contact in contact_details.values() if contact)
    return round((available_items / total_items) * PERCENT_MULTIPLIER, ROUND_DECIMALS)


def calculate_resume_score(section_score: float, contact_score: float, completeness_score: float) -> float:
    final_score = (
        section_score * RESUME_SECTION_WEIGHT
        + contact_score * RESUME_CONTACT_WEIGHT
        + completeness_score * RESUME_COMPLETENESS_WEIGHT
    ) / PERCENT_MULTIPLIER
    return round(final_score, ROUND_DECIMALS)


def calculate_ats_score(skill_score: float, section_score: float, contact_score: float, completeness_score: float) -> float:
    final_score = (
        skill_score * SKILL_WEIGHT
        + section_score * SECTION_WEIGHT
        + contact_score * CONTACT_WEIGHT
        + completeness_score * COMPLETENESS_WEIGHT
    ) / PERCENT_MULTIPLIER
    return round(final_score, ROUND_DECIMALS)
