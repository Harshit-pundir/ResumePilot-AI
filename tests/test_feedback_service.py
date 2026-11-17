import unittest

from services.feedback_service import (
    generate_feedback,
    generate_resume_feedback,
    generate_score_feedback,
    generate_skill_feedback,
)


class FeedbackCharacterizationTests(unittest.TestCase):
    def test_score_feedback_thresholds_for_job_match(self):
        self.assertEqual(generate_score_feedback(90, "job_match"), [
            "Excellent ATS score!",
            "Your resume is highly optimized for this job description.",
        ])
        self.assertEqual(generate_score_feedback(75, "job_match")[0], "Very good ATS score.")
        self.assertEqual(generate_score_feedback(60, "job_match")[0], "Good ATS score.")
        self.assertEqual(generate_score_feedback(40, "job_match")[0], "Average ATS score.")
        self.assertEqual(generate_score_feedback(39, "job_match")[0], "Low ATS score.")

    def test_resume_score_feedback_uses_resume_language(self):
        self.assertEqual(generate_score_feedback(90, "resume_analysis"), [
            "Excellent Resume score!",
            "Your resume follows most ATS best practices.",
        ])

    def test_skill_feedback_sorts_missing_skills(self):
        self.assertEqual(
            generate_skill_feedback({"python"}, {"SQL", "Java"}),
            [
                "You matched 1 required skill(s).",
                "Consider adding 'Java' if you have experience with it.",
                "Consider adding 'SQL' if you have experience with it.",
            ],
        )
        self.assertEqual(
            generate_skill_feedback({"python"}, set()),
            ["You matched 1 required skill(s).", "Excellent! You matched all the required technical skills."],
        )

    def test_resume_feedback_reports_missing_items_in_fixed_order(self):
        sections = {key: "" for key in ("summary", "skills", "projects", "education", "experience")}
        contacts = {key: None for key in ("email", "phone", "linkedin", "github", "portfolio")}
        self.assertEqual(
            generate_resume_feedback(sections, contacts),
            [
                "Add a professional summary.",
                "Add a Technical Skills section.",
                "Include at least one technical project.",
                "Add your education details.",
                "Include work experience or internships.",
                "Add your email address.",
                "Add your phone number.",
                "Include your LinkedIn profile.",
                "Add your GitHub profile.",
                "Add your portfolio website.",
            ],
        )

    def test_complete_resume_feedback_returns_single_praise(self):
        sections = {key: "present" for key in ("summary", "skills", "projects", "education", "experience")}
        contacts = {key: "present" for key in ("email", "phone", "linkedin", "github", "portfolio")}
        self.assertEqual(
            generate_resume_feedback(sections, contacts),
            ["Excellent! Your resume has all the important sections and contact details."],
        )


if __name__ == "__main__":
    unittest.main()
