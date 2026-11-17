import unittest

from services.scoring_service import (
    calculate_ats_score,
    calculate_completeness_score,
    calculate_contact_score,
    calculate_resume_score,
    calculate_section_score,
    calculate_skill_score,
)


class ScoringCharacterizationTests(unittest.TestCase):
    def test_section_contact_and_completeness_percentages(self):
        sections = {"summary": "present", "skills": "", "projects": "present", "education": ""}
        contacts = {"email": "a@example.com", "phone": None, "linkedin": "https://linkedin.test", "github": None}
        self.assertEqual(calculate_section_score(sections), 50.0)
        self.assertEqual(calculate_contact_score(contacts), 50.0)
        self.assertEqual(calculate_completeness_score(sections, contacts), 50.0)

    def test_resume_and_job_match_weighted_scores(self):
        self.assertEqual(calculate_resume_score(80, 50, 70), 71.0)
        self.assertEqual(calculate_ats_score(80, 60, 40, 100), 74.0)

    def test_skill_score_counts_only_exact_and_qualifying_semantic_matches(self):
        requirements = {"exact", "semantic", "related", "missing"}
        self.assertEqual(
            calculate_skill_score(
                {"exact"},
                requirements,
                {"semantic": 0.82, "related": 0.81, "unrequested": 1.0},
            ),
            37.5,
        )
        self.assertEqual(calculate_skill_score(set(), set()), 0)


if __name__ == "__main__":
    unittest.main()
