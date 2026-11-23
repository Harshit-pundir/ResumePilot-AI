import re
from typing import Pattern

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+\d{1,3}[\s().-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}(?!\w)")
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s]+")
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s]+")
URL_PATTERN = re.compile(r"https?://[^\s]+")


def _first_match(pattern: Pattern[str], text: str) -> str | None:
    """Return the first regex match in text, or None if there is no match."""
    match = pattern.search(text)
    if match is None:
        return None
    return match.group()


def _first_portfolio_url(text: str) -> str | None:
    """Return the first web URL that is not a LinkedIn or GitHub profile."""
    for match in URL_PATTERN.finditer(text):
        url = match.group()
        if "linkedin.com" not in url and "github.com" not in url:
            return url
    return None


def _first_phone(text: str) -> str | None:
    """Return the first phone-like number containing 10–15 digits."""
    for match in PHONE_PATTERN.finditer(text):
        value = match.group().strip(" .,-")
        digit_count = sum(character.isdigit() for character in value)
        if 10 <= digit_count <= 15:
            return value
    return None


def extract_contact_details(text: str) -> dict[str, str | None]:
    """Extract the first email, phone, profile links, and portfolio URL."""
    contacts = {
        "email": _first_match(EMAIL_PATTERN, text),
        "phone": _first_phone(text),
        "linkedin": _first_match(LINKEDIN_PATTERN, text),
        "github": _first_match(GITHUB_PATTERN, text),
        "portfolio": _first_portfolio_url(text),
    }
    return contacts
