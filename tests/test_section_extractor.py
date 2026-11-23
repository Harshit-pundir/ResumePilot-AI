import unittest

from services.scoring_service import calculate_section_score
from services.section_extractor import extract_resume_sections, extract_section


class ResumeSectionExtractionTests(unittest.TestCase):
    def test_common_resume_headings_are_extracted(self):
        resume = """\
                PROFILE
                Robotics engineer with embedded software experience.
                TECHNICAL SKILLS
                Python, C++, ROS 2, OpenCV
                ACADEMIC PROJECTS
                Autonomous rover path planning project.
                WORK EXPERIENCE
                Robotics programming engineer, 2022 to 2025.
                EDUCATION
                BSc Computer Engineering
                CERTIFICATIONS
                UAV Safety Certificate
                ACHIEVEMENTS
                Robotics competition finalist
                """
        sections = extract_resume_sections(resume)
        self.assertIn("Robotics engineer", sections["summary"])
        self.assertIn("ROS 2", sections["skills"])
        self.assertIn("path planning", sections["projects"])
        self.assertIn("programming engineer", sections["experience"])
        self.assertIn("Computer Engineering", sections["education"])
        self.assertIn("UAV Safety", sections["certifications"])
        self.assertIn("competition finalist", sections["achievements"])
        self.assertEqual(calculate_section_score(sections), 100.0)

    def test_ocr_spacing_case_punctuation_and_split_headings(self):
        resume = """\
e D U C A T l O N: B.Tech Robotics
work   experience | Flight controls engineer
TECHNICAL
SKILLS
Python, C++
Academic-Projects
Drone navigation
Summary
Built autonomous systems
"""
        sections = extract_resume_sections(resume)
        self.assertIn("B.Tech Robotics", sections["education"])
        self.assertIn("Flight controls", sections["experience"])
        self.assertIn("Python", sections["skills"])
        self.assertIn("Drone navigation", sections["projects"])
        self.assertIn("autonomous systems", sections["summary"])

    def test_text_pdf_style_line_endings_and_page_breaks(self):
        resume = (
            "Skills\r\nC++ and Arduino\r\n\fProjects\r\nDrone controller"
            "\r\n\fEducation\r\nBEng Robotics"
        )
        sections = extract_resume_sections(resume)
        self.assertEqual(sections["skills"], "C++ and Arduino")
        self.assertEqual(sections["projects"], "Drone controller")
        self.assertEqual(sections["education"], "BEng Robotics")

    def test_extract_section_accepts_aliases_and_unknown_headings(self):
        resume = "Technical Skills\nPython, SQL\nProjects\nPortfolio dashboard"
        self.assertEqual(extract_section(resume, ["skills"]), "Python, SQL")
        self.assertEqual(extract_section(resume, ["unknown section"]), "")

    def test_inline_heading_content_and_repeated_sections_are_preserved(self):
        resume = "Summary: Candidate profile\nSkills\nPython\nProjects\nDashboard\nSkills\nSQL"
        sections = extract_resume_sections(resume)
        self.assertEqual(sections["summary"], "Candidate profile")
        self.assertEqual(sections["skills"], "Python\nSQL")


if __name__ == "__main__":
    unittest.main()
