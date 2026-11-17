import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from services.scoring_service import SEMANTIC_CONFIDENCE_THRESHOLD
from services.section_extractor import extract_resume_sections
from utils.constants import SKILLS_FILE_NAME
from utils.logger import get_logger

logger = get_logger(__name__)

# This is a small cross-domain spelling/abbreviation layer. It is not the set
# of skills the analyzer can recognize; requirements are extracted from each JD.
DEFAULT_ALIASES = {
    "c++": ["cpp", "c plus plus"],
    "c": ["c language"],
    "python": ["py", "python 3", "python3"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "postgresql": ["postgres", "postgre sql"],
    "kubernetes": ["k8s"],
    "machine learning": ["ml"],
    "artificial intelligence": ["ai"],
    "scikit-learn": ["scikit learn", "sklearn"],
    "node.js": ["nodejs", "node js"],
    ".net": ["dotnet", "dot net"],
    "ci/cd": ["continuous integration and continuous delivery", "continuous integration/continuous deployment"],
    "rest api": ["rest apis", "restful api", "restful apis"],
    "cnn": ["cnns", "convolutional neural network", "convolutional neural networks"],
}

GENERIC_TERMS = {
    "and", "or", "the", "a", "an", "with", "in", "of", "to", "for", "on",
    "experience", "proficiency", "proficient", "knowledge", "familiar", "familiarity",
    "strong", "excellent", "good", "working", "ability", "skills", "skill", "years",
    "year", "required", "preferred", "plus", "including", "such", "as", "using",
    "engineer", "engineering", "developer", "development", "analyst", "architect",
    "administrator", "scientist", "specialist", "manager", "intern", "candidate",
    "senior", "junior", "lead", "role", "position", "responsibilities", "responsibility",
    "drones", "drone", "robotics", "robotic", "robot", "robots", "ai-powered",
}

LIST_CUE = re.compile(
    r"\b(?:required|preferred|technical|core)?\s*(?:skills?|qualifications?|requirements?|"
    r"programming languages?|frameworks?|tools?|platforms?|databases?|technologies|tech stack)\s*[:\-]\s*",
    re.IGNORECASE,
)
SKILL_CUE = re.compile(
    r"\b(?:experience\s+(?:with|in)|proficien(?:t|cy)\s+(?:with|in)|knowledge\s+(?:of|in)|"
    r"familiar(?:ity)?\s+(?:with|in)|expertise\s+(?:with|in)|hands-on\s+(?:with|experience\s+in)|"
    r"tools?\s+(?:such as|like)|technologies\s+(?:such as|include)|skills?\s+(?:include|such as))\s*",
    re.IGNORECASE,
)


@dataclass
class SkillLexicon:
    aliases: dict[str, list[str]]
    semantic_evidence: dict[str, dict[str, object]] = field(default_factory=dict)
    jd_canonicalizations: dict[str, str] = field(default_factory=dict)
    technical_terms: list[str] = field(default_factory=list)


@dataclass
class RequirementGroup:
    original_text: str
    raw_skills: list[str]
    normalized_skills: list[str]


@dataclass
class JDRequirements:
    original_text: str
    groups: list[RequirementGroup]
    raw_skills: list[str]
    normalized_skills: set[str]
    unresolved_requirements: list[str]
    extraction_coverage: float


@dataclass
class SkillClassification:
    exact: set[str] = field(default_factory=set)
    semantic: dict[str, float] = field(default_factory=dict)
    related: set[str] = field(default_factory=set)
    missing: set[str] = field(default_factory=set)
    evidence: dict[str, str] = field(default_factory=dict)
    match_details: dict[str, dict[str, object]] = field(default_factory=dict)


def load_skills() -> SkillLexicon:
    """Load generic aliases and data-driven technical phrase metadata."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, SKILLS_FILE_NAME)
    aliases = {key: list(values) for key, values in DEFAULT_ALIASES.items()}
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        alias_data = data.get("aliases", data) if isinstance(data, dict) else None
        if not isinstance(alias_data, dict) or not all(
            isinstance(key, str) and isinstance(values, list)
            and all(isinstance(value, str) for value in values)
            for key, values in alias_data.items()
        ):
            raise ValueError("skills.json aliases must map canonical skills to alias lists")
        for canonical, values in alias_data.items():
            aliases.setdefault(canonical, []).extend(values)
        semantic = data.get("semantic_evidence", {}) if "aliases" in data else {}
        canonicalizations = data.get("jd_canonicalizations", {}) if "aliases" in data else {}
        technical_terms = data.get("technical_terms", []) if "aliases" in data else []
        if not isinstance(semantic, dict) or not isinstance(canonicalizations, dict) or not isinstance(technical_terms, list):
            raise ValueError("skills.json taxonomy sections have invalid formats")
        return SkillLexicon(aliases, semantic, canonicalizations, technical_terms)
    except FileNotFoundError:
        logger.warning("skills.json not found; using generic built-in aliases.")
    except (json.JSONDecodeError, ValueError):
        logger.exception("Invalid skills.json; using generic built-in aliases.")
    return SkillLexicon(aliases)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower().replace("＋", "+")
    text = text.replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def _alias_index(lexicon: SkillLexicon | dict[str, list[str]] | list[str] | None) -> dict[str, str]:
    aliases = lexicon.aliases if isinstance(lexicon, SkillLexicon) else lexicon
    result = {normalize_text(name): normalize_text(name) for name in DEFAULT_ALIASES}
    result.update({normalize_text(alias): normalize_text(name) for name, values in DEFAULT_ALIASES.items() for alias in values})
    if isinstance(aliases, dict):
        for name, values in aliases.items():
            canonical = normalize_text(name)
            result[canonical] = canonical
            result.update({normalize_text(alias): canonical for alias in values})
    elif isinstance(aliases, list):
        result.update({normalize_text(name): normalize_text(name) for name in aliases})
    return result


def _boundary_pattern(term: str) -> re.Pattern:
    escaped = re.escape(normalize_text(term))
    suffix = r"(?![\w+#])" if normalize_text(term) in {"c", "c++", "c#"} else r"(?![\w])"
    return re.compile(rf"(?<![\w]){escaped}{suffix}", re.IGNORECASE)


def _canonical_phrase(phrase: str, lexicon: SkillLexicon, aliases: dict[str, str]) -> str:
    candidate = normalize_text(phrase).strip(" \t.,;:!?()[]{}'\"")
    jd_map = {normalize_text(key): normalize_text(value) for key, value in lexicon.jd_canonicalizations.items()}
    return jd_map.get(candidate, aliases.get(candidate, candidate))


def _split_conjunctions(value: str) -> list[str]:
    """Split list syntax, preserving established slash compounds such as CI/CD."""
    return [
        piece.strip(" \t\r\n-*•:;,.()[]{}")
        for piece in re.split(r"[,;\n|]+|\s+\band/or\b\s+|\s+\band\b\s+|\s+\bor\b\s+", value, flags=re.IGNORECASE)
        if piece.strip(" \t\r\n-*•:;,.()[]{}")
    ]


def _split_technical_list(value: str) -> list[str]:
    """Split skill lists while retaining both sides of parenthetical names."""
    values = []
    for comma_item in re.split(r"[,;]+", value):
        item = comma_item.strip(" \t\r\n-*•:;,.()[]{}")
        if not item:
            continue
        outer = re.sub(r"\([^)]*\)|\([^)]*$", " ", item).strip(" \t()")
        outer = re.sub(r"\)[^)]*$", "", outer).strip()
        if outer:
            values.extend(_split_conjunctions(outer))
        for inner in re.findall(r"\(([^()]*)\)", comma_item):
            values.extend(_split_conjunctions(inner))
        open_paren = re.search(r"\(([^()]*)$", comma_item)
        if open_paren:
            values.extend(_split_conjunctions(open_paren.group(1)))
    return values


def _requirement_phrases(original: str, aliases: dict[str, str], lexicon: SkillLexicon) -> list[str]:
    cleaned = re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", original).strip()
    # Parenthetical technologies are retained as separate constituents unless
    # they normalize to the same canonical requirement as the surrounding phrase.
    parenthetical_terms = re.findall(r"\(([^()]*)\)", cleaned)
    outer = re.sub(r"\([^()]*\)", " ", cleaned)
    pieces = _split_conjunctions(outer)
    for parenthetical in parenthetical_terms:
        pieces.extend(_split_conjunctions(parenthetical))

    valid = []
    seen = set()
    for raw in pieces:
        phrase = re.sub(r"\b(?:using|powered by)\b.*$", "", raw, flags=re.IGNORECASE).strip()
        if not phrase or len(phrase) > 80 or len(phrase.split()) > 8:
            continue
        normalized = _canonical_phrase(phrase, lexicon, aliases)
        tokens = re.findall(r"[a-z0-9+#./-]+", normalized)
        if not tokens or all(token in GENERIC_TERMS for token in tokens):
            continue
        if normalized in {"drones", "drone", "robotics", "robot", "robots"}:
            continue
        raw_key = normalize_text(phrase)
        if raw_key not in seen:
            valid.append((phrase, normalized))
            seen.add(raw_key)
    return valid


def _jd_source_groups(text: str) -> list[str]:
    lines = [line.strip() for line in (text or "").replace("\r", "\n").split("\n") if line.strip()]
    bullets = [line for line in lines if re.match(r"^(?:[-*•]+|\d+[.)])\s*", line)]
    if bullets:
        return bullets

    groups = []
    for line in lines:
        label = LIST_CUE.search(line)
        if label:
            tail = line[label.end():].strip()
            # Retain the entire list line as its group; members are decomposed below.
            if tail:
                groups.append(tail)
            continue
        cue = SKILL_CUE.search(line)
        if cue:
            tail = line[cue.end():].strip()
            if tail:
                groups.append(tail)
    if groups:
        return groups

    # For inline JD text without explicit labels, sentence clauses with named
    # skill aliases remain independently extractable.
    return [line for line in lines if line]


def extract_jd_requirements(text: str, lexicon: SkillLexicon | None = None) -> JDRequirements:
    lexicon = lexicon or load_skills()
    aliases = _alias_index(lexicon)
    groups: list[RequirementGroup] = []
    raw_skills: list[str] = []
    normalized_skills: set[str] = set()
    unresolved: list[str] = []
    mapped_count = 0
    possible_count = 0
    seen_groups = set()

    for source in _jd_source_groups(text):
        group_key = normalize_text(source)
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)
        phrases = _requirement_phrases(source, aliases, lexicon)
        group_raw, group_normalized = [], []
        for raw, canonical in phrases:
            possible_count += 1
            mapped_count += 1
            group_raw.append(raw)
            raw_skills.append(raw)
            if canonical not in group_normalized:
                group_normalized.append(canonical)
            normalized_skills.add(canonical)
        if not group_normalized and not _is_generic_jd_line(source):
            unresolved.append(source)
        groups.append(RequirementGroup(source, group_raw, group_normalized))

    coverage = round((mapped_count / possible_count) * 100, 2) if possible_count else 0.0
    if unresolved and groups:
        coverage = round(coverage * (len(groups) - len(unresolved)) / len(groups), 2)
    return JDRequirements(text or "", groups, raw_skills, normalized_skills, unresolved, coverage)


def _is_generic_jd_line(text: str) -> bool:
    tokens = re.findall(r"[a-z]+", normalize_text(text))
    return not tokens or all(token in GENERIC_TERMS for token in tokens)


def extract_jd_skills(text: str, aliases: SkillLexicon | dict[str, list[str]] | list[str] | None = None) -> set[str]:
    """Compatibility wrapper returning the flattened, normalized JD requirement set."""
    lexicon = aliases if isinstance(aliases, SkillLexicon) else _lexicon_from_aliases(aliases)
    return extract_jd_requirements(text, lexicon).normalized_skills


def _lexicon_from_aliases(value) -> SkillLexicon:
    if isinstance(value, dict):
        return SkillLexicon(value)
    if isinstance(value, list):
        return SkillLexicon({name: [] for name in value})
    return load_skills()


def _skill_list_phrases(text: str) -> list[str]:
    phrases = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        groups = line.split("|")[1:] if "|" in line else [line]
        for group in groups:
            if ":" in group:
                group = group.split(":", 1)[1].strip()
            # Skills-section rows are authored as lists; unlike prose, a list
            # entry may be an unfamiliar multiword technical phrase.
            phrases.extend(_split_technical_list(group))
    return phrases


def _labeled_skill_list_phrases(text: str) -> list[str]:
    phrases = []
    excluded_labels = {
        "published as", "achievements", "achievement", "contact", "email", "phone",
        "percentage", "performance", "date", "location", "address", "references",
    }
    for line in (text or "").splitlines():
        if ":" not in line or line.count(",") < 1:
            continue
        label, value = line.split(":", 1)
        label = normalize_text(label).strip(" -•")
        if len(label) > 48 or label in excluded_labels or re.search(r"\b(?:achieved|achieving|analysed|analyzed|published|assigned|collaborated)\b", normalize_text(line)):
            continue
        phrases.extend(_split_technical_list(value))
    return phrases


def _resume_heading_lines(text: str):
    from services.section_extractor import SECTION_HEADINGS, _compact_heading

    headings = {}
    for section, names in SECTION_HEADINGS.items():
        for name in names:
            headings[_compact_heading(name)] = section
    headings.update({"internship": "internship", "internships": "internship", "leadershipextracurricular": "achievements"})
    current = "summary"
    for line in (text or "").splitlines():
        compact = _compact_heading(line.strip())
        next_section = headings.get(compact)
        if next_section:
            current = next_section
            continue
        yield line.strip(), current


def _valid_resume_list_phrase(phrase: str) -> bool:
    normalized = normalize_text(phrase).strip(" .,:;()[]{}")
    if not normalized or len(normalized) > 80 or len(normalized.split()) > 8:
        return False
    if re.search(r"\b(?:19|20)\d{2}\b|\d+\s*%|\baccuracy\b|\bovershoot\b|\bsettling time\b", normalized):
        return False
    if re.search(r"\b(?:achieved|achieving|analysed|analyzed|published|designed|implemented|contributed|improved)\b", normalized):
        return False
    if re.fullmatch(r"(?:[a-z]\.\s*){1,4}[a-z]+(?:\s+[a-z]+)?", normalized):
        return False
    if any(token in {"january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"} for token in normalized.split()):
        return False
    return True


def _mentioned_terms(text: str, lexicon: SkillLexicon, aliases: dict[str, str]) -> set[str]:
    found = set()
    for term, canonical in aliases.items():
        if term and _boundary_pattern(term).search(normalize_text(text)):
            found.add(canonical)
    for term in lexicon.technical_terms:
        canonical = _canonical_phrase(term, lexicon, aliases)
        if term and _boundary_pattern(term).search(normalize_text(text)):
            found.add(canonical)
    return found


def extract_skills(text: str, known_skills: SkillLexicon | dict[str, list[str]] | list[str] | None = None) -> set[str]:
    """Extract technical skills from skills lists, project tags, and known phrases.

    Ordinary prose is not treated as a comma-delimited skill list. Named aliases
    and the compact technical phrase taxonomy may still be found in prose.
    """
    lexicon = known_skills if isinstance(known_skills, SkillLexicon) else _lexicon_from_aliases(known_skills)
    aliases = _alias_index(lexicon)
    normalized_text = normalize_text(text)
    found = _mentioned_terms(text, lexicon, aliases)
    sections = extract_resume_sections(text or "")

    for phrase in _skill_list_phrases(sections.get("skills", "")):
        if _valid_resume_list_phrase(phrase):
            found.add(_canonical_phrase(phrase, lexicon, aliases))

    for phrase in _labeled_skill_list_phrases(text):
        if _valid_resume_list_phrase(phrase):
            found.add(_canonical_phrase(phrase, lexicon, aliases))

    # Project title tags are an authored, compact list. Ignore prose bullets and
    # dates/names elsewhere in project descriptions.
    for line, section in _resume_heading_lines(text):
        if section == "projects" and "|" in line:
            for phrase in _skill_list_phrases(line):
                if _valid_resume_list_phrase(phrase):
                    found.add(_canonical_phrase(phrase, lexicon, aliases))

    # Keep only nonempty normalized names and canonicalize aliases once more.
    return {
        _canonical_phrase(skill, lexicon, aliases)
        for skill in found
        if normalize_text(skill) and not _is_generic_jd_line(skill)
    }


def _sentences(text: str):
    for line in re.split(r"\n+", text or ""):
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip(" -*•\t")
            if sentence:
                yield sentence


def _source_for_sentence(text: str, sentence: str) -> str:
    from services.section_extractor import SECTION_HEADINGS, _compact_heading

    aliases = {}
    for section, names in SECTION_HEADINGS.items():
        for name in names:
            aliases[_compact_heading(name)] = section
    aliases.update({"internship": "internship", "internships": "internship", "leadershipextracurricular": "achievements"})
    current = "summary"
    target = normalize_text(sentence)
    for line in (text or "").splitlines():
        compact = _compact_heading(line.strip())
        if compact in aliases:
            current = aliases[compact]
        if target and target in normalize_text(line):
            return current
    sections = extract_resume_sections(text or "")
    for section, content in sections.items():
        if target and target in normalize_text(content):
            return "project" if section == "projects" else section
    return current if text else "resume"


def _find_phrase_evidence(text: str, phrase: str, aliases: dict[str, str], canonical: str | None = None):
    terms = [term for term, value in aliases.items() if value == normalize_text(canonical or phrase)]
    terms.append(phrase)
    for sentence in _sentences(text):
        for term in terms:
            match = _boundary_pattern(term).search(normalize_text(sentence))
            if not match:
                continue
            # A nearby denial describes missing experience, not evidence of a skill.
            # Keep this conservative and sentence-local so unrelated prose does not
            # turn an otherwise positive mention into a negative one.
            prefix = sentence[:match.start()]
            if re.search(r"\b(?:no|never|without|not)\b(?:\W+\w+){0,3}\W*$", prefix, re.IGNORECASE):
                continue
            return sentence, _source_for_sentence(text, sentence)
    return None, None


def _configured_semantic_evidence(text: str, skill: str, lexicon: SkillLexicon, aliases: dict[str, str]):
    entry = lexicon.semantic_evidence.get(normalize_text(skill), {})
    confidence = float(entry.get("confidence", 0.0)) if isinstance(entry, dict) else 0.0
    groups = entry.get("evidence_groups", []) if isinstance(entry, dict) else []
    for group in groups:
        if not isinstance(group, list) or not group:
            continue
        # All items in one evidence group must occur in one resume sentence.
        for sentence in _sentences(text):
            if all(_boundary_pattern(term).search(normalize_text(sentence)) for term in group):
                return confidence, sentence, _source_for_sentence(text, sentence)
    return 0.0, None, None


def _word_set(phrase: str) -> set[str]:
    stop = GENERIC_TERMS | {"software", "technology", "technical", "development", "developer", "engineering"}
    return {token for token in re.findall(r"[a-z0-9+#]+", normalize_text(phrase)) if token not in stop and len(token) > 1}


def _similarity(required: str, evidence: str) -> float:
    required_words, evidence_words = _word_set(required), _word_set(evidence)
    if not required_words or not evidence_words:
        return 0.0
    overlap = len(required_words & evidence_words) / len(required_words | evidence_words)
    requirement_coverage = len(required_words & evidence_words) / len(required_words)
    sequence = SequenceMatcher(None, re.sub(r"[^a-z0-9+#.]", "", normalize_text(required)), re.sub(r"[^a-z0-9+#.]", "", normalize_text(evidence))).ratio()
    return round(0.5 * overlap + 0.25 * requirement_coverage + 0.25 * sequence, 4)


def classify_skills(
    resume_skills: set[str] | str,
    jd_skills: set[str],
    aliases: SkillLexicon | dict[str, list[str]] | list[str] | None = None,
    semantic_threshold: float = SEMANTIC_CONFIDENCE_THRESHOLD,
) -> SkillClassification:
    lexicon = aliases if isinstance(aliases, SkillLexicon) else _lexicon_from_aliases(aliases)
    alias_index = _alias_index(lexicon)
    resume_text = resume_skills if isinstance(resume_skills, str) else "\n".join(sorted(resume_skills))
    result = SkillClassification()

    for requested in jd_skills:
        skill = _canonical_phrase(requested, lexicon, alias_index)
        sentence, source = _find_phrase_evidence(resume_text, skill, alias_index, skill)
        # The extracted skill set is keyword-based; exact matches must be backed
        # by a positive sentence occurrence so a negated mention cannot bypass
        # the evidence check through that set.
        if sentence:
            result.exact.add(requested)
            sentence = sentence or next((item for item in detected_resume_skills if _canonical_phrase(item, lexicon, alias_index) == skill), "")
            source = source or _source_for_sentence(resume_text, sentence)
            detail = {"canonical_skill": skill, "category": "exact", "confidence": 1.0, "evidence": sentence, "source_section": source}
        else:
            confidence, semantic_sentence, semantic_source = _configured_semantic_evidence(resume_text, skill, lexicon, alias_index)
            if semantic_sentence and confidence >= semantic_threshold:
                result.semantic[requested] = confidence
                sentence, source = semantic_sentence, semantic_source
                detail = {"canonical_skill": skill, "category": "semantic", "confidence": confidence, "evidence": sentence, "source_section": source}
            else:
                ranked = [(_similarity(skill, sentence_text), sentence_text) for sentence_text in _sentences(resume_text)]
                confidence, related_sentence = max(ranked, default=(0.0, ""))
                overlap = _word_set(skill) & _word_set(related_sentence)
                if overlap and confidence >= semantic_threshold:
                    result.semantic[requested] = confidence
                    sentence, source = related_sentence, _source_for_sentence(resume_text, related_sentence)
                    detail = {"canonical_skill": skill, "category": "semantic", "confidence": confidence, "evidence": sentence, "source_section": source}
                elif overlap and confidence >= 0.25:
                    result.related.add(requested)
                    sentence, source = related_sentence, _source_for_sentence(resume_text, related_sentence)
                    detail = {"canonical_skill": skill, "category": "related", "confidence": confidence, "evidence": sentence, "source_section": source}
                else:
                    result.missing.add(requested)
                    continue

        result.evidence[requested] = sentence
        result.match_details[requested] = detail
    return result


def match_skills(resume_skills: set[str], jd_skills: set[str]) -> tuple[set[str], set[str]]:
    """Backward-compatible exact-match and non-exact result."""
    result = classify_skills(resume_skills, jd_skills)
    return result.exact, result.missing | result.related | set(result.semantic)
