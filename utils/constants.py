PERCENT_MULTIPLIER = 100
ROUND_DECIMALS = 2

# Job-match weights are percentages and are divided by PERCENT_MULTIPLIER.
# Completeness remains a diagnostic metric; it is excluded from the total because
# it summarizes the required section and contact fields already scored below.
SKILL_WEIGHT = 60
SECTION_WEIGHT = 25
CONTACT_WEIGHT = 15
COMPLETENESS_WEIGHT = 0

RESUME_SECTION_WEIGHT = 70
RESUME_CONTACT_WEIGHT = 30
RESUME_COMPLETENESS_WEIGHT = 0

REQUIRED_RESUME_SECTIONS = ("summary", "skills", "projects", "education")
OPTIONAL_RESUME_SECTIONS = ("experience", "certifications", "achievements")
REQUIRED_CONTACT_FIELDS = ("email", "phone", "linkedin", "github")
OPTIONAL_CONTACT_FIELDS = ("portfolio",)

# Semantic requirements receive partial skill credit only above this confidence.
SEMANTIC_CONFIDENCE_THRESHOLD = 0.82
SEMANTIC_SCORE_CREDIT = 0.5

EXCELLENT_SCORE_THRESHOLD = 90
VERY_GOOD_SCORE_THRESHOLD = 75
GOOD_SCORE_THRESHOLD = 60
AVERAGE_SCORE_THRESHOLD = 40
EXPIRE_MINUTES = 60 * 24
SKILLS_FILE_NAME = "skills.json"
