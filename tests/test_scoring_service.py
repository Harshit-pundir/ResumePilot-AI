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
        self.assertEqual(calculate_ats_score(80, 60, 40, 100), 69.0)

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

    def test_duplicate_semantic_and_evidence_credit_does_not_exceed_one_skill(self):
        self.assertEqual(
            calculate_skill_score(
                {"python"},
                {"python"},
                {"python": 0.99},
                evidence_matches={"python": 0.8},
            ),
            100.0,
        )

    def test_weighted_totals_are_bounded_for_invalid_component_values(self):
        self.assertEqual(calculate_ats_score(150, -20, float("nan"), 100), 60.0)
        self.assertEqual(calculate_resume_score(float("inf"), 100, 0), 30.0)

    def test_optional_portfolio_and_sections_do_not_reduce_scores(self):
        sections = {"summary": "present", "skills": "present", "projects": "present", "education": "present"}
        contacts = {"email": "a@example.com", "phone": "+1 415-555-2671", "linkedin": "https://linkedin.com/in/a", "github": "https://github.com/a", "portfolio": None}
        self.assertEqual(calculate_section_score(sections), 100.0)
        self.assertEqual(calculate_contact_score(contacts), 100.0)
        self.assertEqual(calculate_completeness_score(sections, contacts), 100.0)
        contacts["portfolio"] = "https://portfolio.example"
        self.assertEqual(calculate_contact_score(contacts), 100.0)
        self.assertEqual(calculate_completeness_score(sections, contacts), 100.0)

    def test_strong_fresher_with_leadership_and_achievements_is_not_penalized(self):
        from services.section_extractor import extract_resume_sections

        resume = """Professional Summary
Computer science student focused on backend engineering.
Technical Expertise
Python, SQL, FastAPI
Selected Projects
Built a deployed API project.
Education
B.Tech Computer Science, 2027, CGPA 8.5
Leadership Experience
Core team member in a developer community.
Achievements
Hackathon finalist and 1400+ DSA problems solved."""
        sections = extract_resume_sections(resume)
        contacts = {"email": "student@example.com", "phone": "+91 98765 43210", "linkedin": "https://linkedin.com/in/student", "github": "https://github.com/student", "portfolio": None}
        self.assertTrue(all(sections[key] for key in ("summary", "skills", "projects", "education")))
        self.assertIn("Core team", sections["experience"])
        self.assertIn("Hackathon", sections["achievements"])
        section_score = calculate_section_score(sections)
        contact_score = calculate_contact_score(contacts)
        completeness = calculate_completeness_score(sections, contacts)
        self.assertEqual((section_score, contact_score, completeness), (100.0, 100.0, 100.0))
        self.assertEqual(calculate_ats_score(76, section_score, contact_score, completeness), 85.6)

    def test_experienced_developer_score_uses_unique_skill_credit_and_direct_weights(self):
        sections = {"summary": "present", "skills": "present", "projects": "present", "education": "present", "experience": "present"}
        contacts = {"email": "dev@example.com", "phone": "+44 20 7946 0958", "linkedin": "https://linkedin.com/in/dev", "github": None, "portfolio": "https://dev.example"}
        skill_score = calculate_skill_score({"python", "sql"}, {"python", "sql", "java"})
        self.assertEqual(skill_score, round(2 / 3 * 100, 2))
        self.assertEqual(calculate_section_score(sections), 100.0)
        self.assertEqual(calculate_contact_score(contacts), 75.0)
        self.assertEqual(calculate_ats_score(skill_score, 100, 75, 90), 76.25)

    def test_weak_resume_and_empty_extraction_scores_reflect_required_gaps(self):
        sections = {"summary": "Only a short summary", "skills": "", "projects": "", "education": ""}
        contacts = {"email": "weak@example.com", "phone": None, "linkedin": None, "github": None, "portfolio": None}
        self.assertEqual(calculate_section_score(sections), 25.0)
        self.assertEqual(calculate_contact_score(contacts), 25.0)
        self.assertEqual(calculate_completeness_score(sections, contacts), 25.0)
        self.assertEqual(calculate_ats_score(0, 25, 25, 25), 10.0)
        self.assertEqual(calculate_section_score({}), 0.0)
        self.assertEqual(calculate_contact_score({}), 0.0)

    def test_score_breakdown_explains_weights_optional_items_and_section_gaps(self):
        from services.scoring_service import build_score_breakdown

        breakdown = build_score_breakdown(
            "job_match",
            {"summary": "present", "skills": "present", "projects": "", "education": "present", "experience": "", "achievements": "present"},
            {"email": "a@example.com", "phone": "1234567890", "linkedin": None, "github": "https://github.com/a", "portfolio": None},
            76,
        )
        self.assertEqual(breakdown["formula"], "Skill Match x 60% + Section Structure x 25% + Contact Details x 15%")
        self.assertEqual(breakdown["required_sections"]["missing"], ["projects"])
        self.assertEqual(breakdown["required_sections"]["optional_present"], ["achievements"])
        self.assertEqual(breakdown["required_contacts"]["missing"], ["linkedin"])
        self.assertIn("not added again", breakdown["completeness_note"])


if __name__ == "__main__":
    unittest.main()
