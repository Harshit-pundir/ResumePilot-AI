import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from services.scoring_service import (
    SEMANTIC_CONFIDENCE_THRESHOLD,
    calculate_skill_score,
)
from services.skills_service import (
    classify_skills,
    extract_jd_requirements,
    extract_jd_skills,
    extract_skills,
    load_skills,
)


JOB_DOMAINS = {
    "robotics_drone": (
        "Robotics and Drone Engineer. Required skills: ROS 2, C++, Python, OpenCV, "
        "path planning, Arduino, and drone flight control."
    ),
    "java_backend": (
        "Java Backend Developer. Required skills: Java, Spring Boot, REST APIs, "
        "PostgreSQL, Docker, and Kafka."
    ),
    "python_developer": (
        "Python Developer. Experience with Python, FastAPI, SQLAlchemy, "
        "PostgreSQL, and pytest."
    ),
    "ai_ml": (
        "AI/ML Engineer. Skills include Python, PyTorch, scikit-learn, machine "
        "learning, model evaluation, and feature engineering."
    ),
    "devops": (
        "DevOps Engineer. Experience with AWS, Kubernetes, Terraform, Docker, "
        "CI/CD, and Prometheus."
    ),
    "data_analyst": (
        "Data Analyst. Proficient in SQL, Tableau, Excel, data visualization, "
        "statistical analysis, and Python."
    ),
}

DOMAIN_RESUMES = {
    "robotics_drone": "Implemented ROS2 software in C++ and used path planning for drone flight control.",
    "java_backend": "Built Java services using Spring Boot and PostgreSQL with REST APIs.",
    "python_developer": "Developed Python APIs with FastAPI and SQLAlchemy, tested with pytest.",
    "ai_ml": "Built Python machine learning models using PyTorch, scikit-learn and feature engineering.",
    "devops": "Managed AWS infrastructure with Kubernetes, Terraform, Docker, CI/CD and Prometheus.",
    "data_analyst": "Analyzed data with SQL, Tableau, Excel, data visualization, statistical analysis and Python.",
}

S_VISHNU_OCR_SKILLS_TEXT = """\
PROFESSIONAL SUMMARY
Robotics Engineer with hands-on experience in ROS2-based autonomous systems, SLAM, and perception pipelines.
TECHNICAL SKILLS
Programming: C++, Python, MATLAB
Robotics Frameworks: ROS2 (Nav2, SLAM Toolbox, node/topic/service architecture, TF2 transforms), OpenCV, Extended Kalman Filter (EKF), MoveIt, URDF
Robotics Fundamentals: Coordinate frame transformations, forward/inverse kinematics, rigid-body dynamics, motion planning, feedback control, GNSS, A*, Dijkstra, RRT
Embedded & Hardware: ESP32, RaspberryPi, STM32, IMU, LiDAR, RGB-D Cameras, UART, I2C, SPI, BLE, TCP/IP, MQTT, DDS, ZMQ, PCB Design
Perception: Computer Vision, YOLO, CNNs, SIFT, Bag-of-Words
EDUCATION
Masters of Science in Robotics
INTERNSHIPS
Maruti Suzuki Private Limited
Assigned to the Engine Shop which works with 70% automation.
PROJECTS
Autonomous Color Object Retrieval Robot | ROS2, OpenCV, Python, Path Planning
Developed an autonomous mobile robot using ROS2, integrating SLAM and Nav2 for mapping, localization, and path planning.
Implemented a real-time perception pipeline using OpenCV and deep learning.
Cascaded PID Control for UAV (DJI Tello) | Python, Control Systems
Designed a cascaded PID control architecture for a DJI Tello drone with stable flight control.
CNN and Classical Vision for Robotic Perception | ResNet-18, PyTorch, SIFT, Bag-of-Words, SVM
Built and evaluated CNN and classical vision pipelines for object recognition.
ACHIEVEMENTS
Achieving 63 test accuracy; analysed robustness under domain shifts including lighting.
Published as: S. V. Rajeshwaran, R. Singh.
Control Systems April 2024; KiCAD February 2024.
"""

USER_SPECIFIED_ROBOTICS_REQUIREMENTS = """\
Robotics & Drone Programming Engineer
- Robotics software development
- Drone flight control and automation
- ROS 2 (Robot Operating System)
- Python and C++
- Arduino, Raspberry Pi, ESP32
- Computer Vision (OpenCV)
- Autonomous navigation and path planning
- AI-powered robotics and drones
"""


class DomainIndependentSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aliases = load_skills()

    def test_job_description_drives_requirements_across_six_domains(self):
        expected = {
            "robotics_drone": {"ros 2", "c++", "python", "opencv", "path planning", "arduino", "drone flight control"},
            "java_backend": {"java", "spring boot", "rest api", "postgresql", "docker", "kafka"},
            "python_developer": {"python", "fastapi", "sqlalchemy", "postgresql", "pytest"},
            "ai_ml": {"python", "pytorch", "scikit-learn", "machine learning", "model evaluation", "feature engineering"},
            "devops": {"aws", "kubernetes", "terraform", "docker", "ci/cd", "prometheus"},
            "data_analyst": {"sql", "tableau", "excel", "data visualization", "statistical analysis", "python"},
        }
        for domain, description in JOB_DOMAINS.items():
            with self.subTest(domain=domain):
                skills = extract_jd_skills(description, self.aliases)
                self.assertTrue(expected[domain].issubset(skills), (domain, skills))

    def test_changing_jd_changes_extracted_requirements_and_matches(self):
        java_skills = extract_jd_skills(JOB_DOMAINS["java_backend"], self.aliases)
        data_skills = extract_jd_skills(JOB_DOMAINS["data_analyst"], self.aliases)
        self.assertNotEqual(java_skills, data_skills)

        resume = "Built Java services with Spring Boot and PostgreSQL. Used Tableau for data visualization."
        java_result = classify_skills(resume, java_skills, self.aliases)
        data_result = classify_skills(resume, data_skills, self.aliases)
        self.assertIn("java", java_result.exact)
        self.assertIn("tableau", data_result.exact)
        self.assertNotEqual(java_result.exact, data_result.exact)

    def test_each_domain_matches_only_skills_evidenced_in_its_resume(self):
        for domain, description in JOB_DOMAINS.items():
            with self.subTest(domain=domain):
                requirements = extract_jd_skills(description, self.aliases)
                result = classify_skills(DOMAIN_RESUMES[domain], requirements, self.aliases)
                self.assertTrue(result.exact, (domain, requirements, result))
                self.assertTrue(result.evidence.keys() & result.exact, (domain, result.evidence))

    def test_uploaded_s_vishnu_resume_ocr_skill_regression(self):
        skills = extract_skills(S_VISHNU_OCR_SKILLS_TEXT, self.aliases)
        explicit_resume_skills = {
            "ros 2", "nav2", "python", "c++", "opencv", "esp32", "raspberry pi",
            "stm32", "computer vision", "deep learning", "cnn", "sift", "svm",
            "path planning", "uav",
        }
        self.assertTrue(explicit_resume_skills.issubset(skills), explicit_resume_skills - skills)
        self.assertNotIn("arduino", skills)

    def test_s_vishnu_against_user_listed_robotics_requirements(self):
        jd = extract_jd_requirements(USER_SPECIFIED_ROBOTICS_REQUIREMENTS, self.aliases)
        jd_requirements = jd.normalized_skills
        resume_skills = extract_skills(S_VISHNU_OCR_SKILLS_TEXT, self.aliases)
        classification = classify_skills(S_VISHNU_OCR_SKILLS_TEXT, jd_requirements, self.aliases)

        self.assertEqual(jd_requirements, {
            "robotics software development", "drone flight control", "automation", "ros 2",
            "python", "c++", "arduino", "raspberry pi", "esp32", "computer vision", "opencv",
            "autonomous navigation", "path planning", "artificial intelligence",
        })
        self.assertEqual(jd.extraction_coverage, 100.0)
        self.assertEqual(len(jd.groups), 8)
        ros_group = next(group for group in jd.groups if "ROS 2" in group.original_text)
        self.assertEqual(ros_group.normalized_skills, ["ros 2"])
        self.assertIn("Robot Operating System", ros_group.raw_skills)
        self.assertIn("ros 2", jd_requirements)
        self.assertIn("ros 2", resume_skills)
        self.assertIn("raspberry pi", resume_skills)
        self.assertTrue({"opencv", "raspberry pi", "path planning"}.issubset(classification.exact))
        self.assertTrue({"robotics software development", "drone flight control", "autonomous navigation", "artificial intelligence"}.issubset(classification.semantic))
        self.assertNotIn("arduino", resume_skills)
        self.assertIn("arduino", classification.missing)
        self.assertNotIn("artificial intelligence", classification.exact)
        self.assertIn("automation", classification.exact)
        self.assertEqual(classification.match_details["automation"]["source_section"], "internship")
        self.assertEqual(classification.match_details["ros 2"]["source_section"], "summary")
        self.assertEqual(classification.match_details["path planning"]["source_section"], "projects")
        for skill in classification.exact | set(classification.semantic) | classification.related:
            detail = classification.match_details[skill]
            self.assertTrue(detail["evidence"], skill)
            self.assertTrue(detail["source_section"], skill)

    def test_job_match_api_debug_contains_groups_evidence_and_coverage(self):
        from routes.upload import process_job_match

        resume_skills = extract_skills(S_VISHNU_OCR_SKILLS_TEXT, self.aliases)
        sections = {key: "present" for key in ("summary", "skills", "projects", "education", "experience", "certifications", "achievements")}
        contacts = {"email": "v@example.com", "phone": None, "linkedin": None, "github": None, "portfolio": None}
        with patch("routes.upload.save_resume_history"), patch("routes.upload.build_latest_report"):
            response = process_job_match(
                USER_SPECIFIED_ROBOTICS_REQUIREMENTS,
                self.aliases,
                resume_skills,
                S_VISHNU_OCR_SKILLS_TEXT,
                sections,
                contacts,
                SimpleNamespace(filename="SVishnu.pdf"),
                100,
                20,
                50,
                None,
                "regression-user",
            )
        payload = json.loads(response.body)
        debug = payload["debug"]
        self.assertEqual(debug["original_jd"], USER_SPECIFIED_ROBOTICS_REQUIREMENTS)
        self.assertEqual(len(debug["requirement_groups"]), 8)
        self.assertIn("Arduino", debug["raw_extracted_jd_skills"])
        self.assertIn("arduino", debug["normalized_jd_skills"])
        self.assertIn("arduino", debug["missing_skills"])
        self.assertEqual(debug["extraction_coverage_percent"], 100.0)
        self.assertTrue(all({"canonical_skill", "category", "confidence", "evidence", "source_section"} <= detail.keys()
                            for detail in debug["exact_matches"] + debug["semantic_matches"]))

    def test_noisy_resume_sentences_are_not_skill_items(self):
        skills = extract_skills(S_VISHNU_OCR_SKILLS_TEXT, self.aliases)
        for noise in (
            "achieving 63 test accuracy",
            "analysed robustness under domain shifts including lighting",
            "control systems april 2024",
            "kicad february 2024",
            "s. v. rajeshwaran",
            "r. singh",
        ):
            self.assertNotIn(noise, skills)
        self.assertTrue({"autonomous navigation", "computer vision", "motion planning", "feedback control"} & skills)

    def test_generic_aliases_normalize_case_abbreviations_and_variants(self):
        self.assertEqual(extract_jd_skills("Experience with JS, K8s, Postgres and sklearn", self.aliases), {
            "javascript", "kubernetes", "postgresql", "scikit-learn"
        })
        self.assertEqual(extract_skills("Built APIs in RESTful API services", self.aliases), {"rest api"})

    def test_exact_semantic_related_and_missing_are_distinct_and_evidence_backed(self):
        result = classify_skills(
            "Java services supporting backend platforms are deployed and maintained.",
            {"java", "java backend", "spring boot"},
            self.aliases,
        )
        self.assertIn("java", result.exact)
        self.assertIn("java backend", set(result.semantic) | result.related)
        self.assertIn("spring boot", result.missing)
        self.assertIn("java backend", result.evidence)
        self.assertNotIn("spring boot", result.evidence)

    def test_semantic_match_needs_strong_phrase_similarity_and_resume_evidence(self):
        result = classify_skills("Backend Java specialist.", {"java backend"}, self.aliases)
        self.assertEqual(result.exact, set())
        self.assertIn("java backend", result.semantic)
        self.assertGreaterEqual(result.semantic["java backend"], SEMANTIC_CONFIDENCE_THRESHOLD)
        self.assertIn("Backend Java", result.evidence["java backend"])

    def test_shared_industry_or_adjacent_tool_is_not_enough_for_related_match(self):
        result = classify_skills("Docker deployments in production.", {"kubernetes"}, self.aliases)
        self.assertEqual(result.related, set())
        self.assertEqual(result.missing, {"kubernetes"})

    def test_alias_registry_contains_equivalences_not_domain_related_rules(self):
        alias_data = json.loads(Path("skills.json").read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(values, list) for values in alias_data["aliases"].values()))
        self.assertNotIn("related", alias_data["aliases"])
        self.assertIn("semantic_evidence", alias_data)
        self.assertNotIn("RELATED_SKILLS", __import__("services.skills_service", fromlist=["RELATED_SKILLS"]).__dict__)
        self.assertEqual(extract_skills("ROS2 and RaspberryPi with OpenCV", self.aliases), {"ros 2", "raspberry pi", "opencv"})

    def test_robotics_jd_does_not_leak_into_unrelated_jd_or_resume(self):
        java_skills = extract_jd_skills(JOB_DOMAINS["java_backend"], self.aliases)
        java_resume_skills = extract_skills("Java developer with Spring Boot and PostgreSQL experience.", self.aliases)
        self.assertFalse({"ros 2", "opencv", "path planning", "drone flight control"} & java_skills)
        self.assertFalse({"ros 2", "opencv", "path planning", "drone flight control"} & java_resume_skills)
        result = classify_skills("Java developer with Spring Boot and PostgreSQL experience.", java_skills, self.aliases)
        self.assertFalse(result.related & {"ros 2", "opencv", "path planning", "drone flight control"})

    def test_c_and_cpp_remain_distinct(self):
        requirements = extract_jd_skills("Required skills: C and C++", self.aliases)
        self.assertTrue({"c", "c++"}.issubset(requirements))
        self.assertEqual(extract_skills("Firmware written in C++", self.aliases), {"c++"})

    def test_semantic_score_obeys_explicit_threshold_and_credit_policy(self):
        requirements = {"exact", "semantic", "related", "missing"}
        score_below = calculate_skill_score({"exact"}, requirements, {"semantic": SEMANTIC_CONFIDENCE_THRESHOLD - 0.01})
        score_above = calculate_skill_score({"exact"}, requirements, {"semantic": SEMANTIC_CONFIDENCE_THRESHOLD})
        self.assertEqual(score_below, 25.0)
        self.assertEqual(score_above, 37.5)
        self.assertEqual(calculate_skill_score({"exact"}, requirements, unresolved_requirements=1), 20.0)

    def test_negated_skill_mentions_are_not_exact_matches(self):
        for resume in (
            "I have no Java experience.",
            "I never used Java.",
            "The project was completed without Java.",
            "I am not familiar with Java.",
        ):
            with self.subTest(resume=resume):
                result = classify_skills(resume, {"java"}, self.aliases)
                self.assertNotIn("java", result.exact)

    def test_positive_skill_evidence_still_matches_exactly(self):
        result = classify_skills("Built a REST API in Java.", {"java"}, self.aliases)
        self.assertIn("java", result.exact)


if __name__ == "__main__":
    unittest.main()
