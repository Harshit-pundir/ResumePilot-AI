import re
from typing import Pattern

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}")
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


def extract_contact_details(text: str) -> dict[str, str | None]:
    """Extract the first email, phone, profile links, and portfolio URL."""
    contacts = {
        "email": _first_match(EMAIL_PATTERN, text),
        "phone": _first_match(PHONE_PATTERN, text),
        "linkedin": _first_match(LINKEDIN_PATTERN, text),
        "github": _first_match(GITHUB_PATTERN, text),
        "portfolio": _first_portfolio_url(text),
    }
    return contacts
