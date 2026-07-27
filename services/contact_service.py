import re


def extract_contact_details(text: str) -> dict[str, str | None]:
    contacts = {"email": None, "phone": None, "linkedin": None, "github": None, "portfolio": None}
    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email:
        contacts["email"] = email.group()
    phone = re.search(r"(?:\+91[\-\s]?)?[6-9]\d{9}", text)
    if phone:
        contacts["phone"] = phone.group()
    linkedin = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s]+", text)
    if linkedin:
        contacts["linkedin"] = linkedin.group()
    github = re.search(r"(?:https?://)?(?:www\.)?github\.com/[^\s]+", text)
    if github:
        contacts["github"] = github.group()
    for url in re.findall(r"https?://[^\s]+", text):
        if "linkedin.com" not in url and "github.com" not in url:
            contacts["portfolio"] = url
            break
    return contacts
