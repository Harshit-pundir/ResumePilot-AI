import json
import os
import re

from utils.constants import SKILLS_FILE_NAME
from utils.logger import get_logger

logger = get_logger(__name__)


def load_skills() -> list[str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_file = os.path.join(base_dir, SKILLS_FILE_NAME)
    try:
        with open(skills_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.exception("skills.json file not found.")
        return []
    except json.JSONDecodeError:
        logger.exception("Invalid JSON format.")
        return []


def extract_skills(text: str, known_skills: list[str]) -> set[str]:
    text = text.lower()
    found_skills = set()
    for skill in known_skills:
        pattern = rf"\b{re.escape(skill.lower())}\b"
        if re.search(pattern, text):
            found_skills.add(skill)
    return found_skills


def match_skills(resume_skills: set[str], jd_skills: set[str]) -> tuple[set[str], set[str]]:
    return resume_skills & jd_skills, jd_skills - resume_skills
