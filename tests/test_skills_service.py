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

    def test_sde_intern_jd_filters_metadata_fragments_and_uses_resume_wide_evidence(self):
        jd = """SDE Internship
Duration: 3–6 months
Job type: Internship
Responsibilities: Integrate intelligent functionalities into applications using LLM-based applications and NLP & Generative AI.
Required skills: Java, Python, SQL, DSA, OOP, Backend Development, REST APIs, Flask, FastAPI, Git, GitHub, Database Management, Machine Learning, NLP, Generative AI/LLM, RAG, Docker, PostgreSQL, Spring Boot.
Debug and test reliability."""
        resume = """SUMMARY
Software developer with problem solving skills through data structures and algorithms.
TECHNICAL SKILLS
Java, Python, SQL, OOP, FastAPI, Flask, REST APIs, SQLAlchemy, MySQL, Supabase, Git, GitHub
PROJECTS
Built and deployed multiple backend applications with REST APIs using FastAPI and Flask.
Created an NLP pipeline using spaCy and integrated Groq LLM recommendations.
Applied machine learning, deep learning and computer vision.
ACHIEVEMENTS
Solved 1400+ algorithm problems on coding platforms."""
        jd_result = extract_jd_requirements(jd, self.aliases)
        expected = {
            "java", "python", "sql", "data structures and algorithms", "oop",
            "backend development", "rest api", "flask", "fastapi", "git", "github",
            "database management", "machine learning", "natural language processing",
            "generative ai", "large language models", "retrieval-augmented generation",
            "docker", "postgresql", "spring boot",
        }
        self.assertEqual(jd_result.normalized_skills, expected)
        self.assertFalse({"debug", "test", "reliability", "duration", "job type", "internship"} & jd_result.normalized_skills)

        classification = classify_skills(resume, jd_result.normalized_skills, self.aliases)
        matched = classification.exact | set(classification.semantic) | set(classification.evidence_based)
        expected_matched = {
            "java", "python", "sql", "data structures and algorithms", "oop",
            "backend development", "rest api", "flask", "fastapi", "git", "github",
            "database management", "machine learning", "natural language processing",
            "generative ai", "large language models",
        }
        self.assertTrue(expected_matched <= matched, expected_matched - matched)
        self.assertTrue({"retrieval-augmented generation", "docker", "postgresql", "spring boot"} <= classification.missing)
        self.assertFalse(matched & classification.missing)

    def test_sde_intern_noise_is_excluded_and_supported_skills_are_normalized(self):
        jd = """Software Development Engineer Intern
Work mode: Hybrid
Responsibilities: Improve existing codebases and participate in technical discussions.
Benefits: Mentorship and potential PPO consideration.
Required skills: analytical thinking, ML model integration, PostgreSQL.
Other: scalability, generic integration."""
        requirements = extract_jd_requirements(jd, self.aliases)
        self.assertEqual(requirements.normalized_skills, {
            "problem solving", "ml model integration", "postgresql",
        })
        self.assertEqual(extract_jd_skills("Integrate third-party APIs and integrate AI/ML models", self.aliases), {
            "api integration", "ml model integration",
        })
        # The API/report contract is an array of separate labels; no phrase is
        # reconstructed by concatenating adjacent requirement text.
        self.assertTrue(all(isinstance(skill, str) and "hybrid" not in skill for skill in requirements.normalized_skills))

    def test_sde_intern_missing_skills_are_separate_and_resume_context_matches(self):
        jd = "Required skills: Analytical Thinking, ML Model Integration, PostgreSQL"
        requirements = extract_jd_requirements(jd, self.aliases)
        resume = """TECHNICAL SKILLS
Python, PostgreSQL
PROJECTS
Built an inference pipeline and integrated trained ML models into a web application."""
        result = classify_skills(resume, requirements.normalized_skills, self.aliases)
        self.assertIn("postgresql", result.exact)
        self.assertIn("ml model integration", result.evidence_based)
        self.assertIn("problem solving", result.missing)
        self.assertEqual(result.missing, {"problem solving"})

        from routes.upload import process_job_match
        sections = {key: "present" for key in ("summary", "skills", "projects", "education", "experience")}
        contacts = {"email": "dev@example.com", "phone": None, "linkedin": None, "github": None, "portfolio": None}
        with patch("routes.upload.save_resume_history"), patch("routes.upload.build_latest_report"):
            response = process_job_match(
                jd, self.aliases, extract_skills(resume, self.aliases), resume, sections, contacts,
                SimpleNamespace(filename="resume.pdf"), 100, 50, 80, None, "sde-regression",
            )
        payload = json.loads(response.body)
        self.assertEqual(payload["missing_skills"], ["problem solving"])
        self.assertEqual(payload["matched_skills"], ["postgresql"])
        self.assertEqual(payload["partial_skills"], ["ml model integration"])
        self.assertEqual(payload["total_jd_skills"], 3)
        self.assertEqual(payload["matched_skill_count"] + payload["partial_skill_count"] + payload["missing_skill_count"], 3)
        self.assertTrue(all(isinstance(skill, str) for skill in payload["missing_skills"]))
        ledger = payload["skill_matches"]
        self.assertEqual(len({item["canonical_skill"] for item in ledger}), payload["total_jd_skills"])
        self.assertEqual({item["status"] for item in ledger}, {"matched", "partial", "missing"})
        self.assertEqual(
            round(sum(item["contribution"] for item in ledger) / payload["skill_summary"]["total_weight"] * 100, 2),
            payload["skill_score"],
        )

    def test_skill_phrase_normalization_collapses_overlapping_jd_requirements(self):
        requirements = extract_jd_requirements(
            "Required skills: Object-Oriented Programming, SQL, SQL-based systems, "
            "Data Structures and Algorithms, Algorithms, Data Structures, "
            "solve problems involving data structures, AI/ML models, "
            "backend-focused projects, database fundamentals, competitive programming",
            self.aliases,
        )
        self.assertEqual(requirements.normalized_skills, {
            "oop", "sql", "data structures and algorithms", "machine learning",
            "backend development", "database management", "competitive programming",
        })
        self.assertEqual(len(requirements.normalized_skills), len(set(requirements.normalized_skills)))

    def test_contextual_skill_evidence_respects_distinct_technologies_and_api_use(self):
        resume = """TECHNICAL SKILLS
Java, OOP, SQL, FastAPI, Flask
PROJECTS
Built backend services using FastAPI and Flask.
Integrated the Groq API to provide model recommendations.
Implemented an ML model to classify resume content."""
        required = extract_jd_requirements(
            "Required skills: Object-Oriented Programming, Backend-Focused Projects, "
            "API Integration, AI/ML Models, PostgreSQL", self.aliases,
        ).normalized_skills
        result = classify_skills(resume, required, self.aliases)
        self.assertIn("oop", result.exact)
        self.assertIn("machine learning", result.exact)
        self.assertIn("backend development", set(result.semantic) | set(result.evidence_based))
        self.assertIn("api integration", result.evidence_based)
        self.assertIn("postgresql", result.missing)

        rest_only = classify_skills("Built and deployed REST APIs using FastAPI.", {"api integration"}, self.aliases)
        self.assertEqual(rest_only.evidence_based, {})
        self.assertEqual(rest_only.missing, {"api integration"})

        sql_does_not_imply_postgresql = classify_skills("Used SQL with Supabase.", {"postgresql"}, self.aliases)
        self.assertEqual(sql_does_not_imply_postgresql.missing, {"postgresql"})

    def test_compound_data_structure_requirement_matches_project_evidence(self):
        jd = extract_jd_requirements(
            "Required skills: Data Structures, Algorithms, "
            "solve problems involving data structures", self.aliases,
        )
        self.assertEqual(jd.normalized_skills, {"data structures and algorithms"})
        result = classify_skills(
            "PROJECTS\nSolved algorithm problems using data structures and algorithms.",
            jd.normalized_skills,
            self.aliases,
        )
        self.assertTrue(
            {"data structures and algorithms"} & (result.exact | set(result.semantic) | set(result.evidence_based))
        )

    def test_generic_duties_are_not_extracted_and_evidence_is_clean_and_local(self):
        duties = extract_jd_skills(
            "Responsibilities: work with the team; build solutions to user problems; "
            "good communication; work in a hybrid environment", self.aliases,
        )
        self.assertEqual(duties, set())

        from services.skills_service import _clean_evidence
        evidence = _clean_evidence(
            "\x7f"
            "Integrated ML-powered recommendations into the analyzer â€” with reliable results.\x01 "
            "Unrelated project paragraph should not be appended."
        )
        self.assertIn("Integrated ML-powered recommendations", evidence)
        self.assertNotIn("â", evidence)
        self.assertNotIn("\ufffd", evidence)
        self.assertNotIn("\x01", evidence)
        self.assertNotIn("\x7f", evidence)
        self.assertNotIn("Unrelated project", evidence)
        self.assertLessEqual(len(evidence), 200)
        self.assertNotIn(chr(0x00e2), evidence)
        unicode_text = "\u0063af\u00e9 r\u00e9sum\u00e9"
        self.assertEqual(_clean_evidence(unicode_text, None), unicode_text)
        from services.skills_service import _sentences
        malformed_bullet = chr(0x00e2) + chr(0x20ac) + chr(0x00a2) + " Built an ML model."
        self.assertEqual(list(_sentences(malformed_bullet)), ["Built an ML model."])
        long_evidence = _clean_evidence("Implemented an ML model with " + "technical details " * 30)
        self.assertLessEqual(len(long_evidence), 200)
        self.assertTrue(long_evidence.endswith(chr(0x2026)))

    def test_exact_skill_wins_and_multiple_sentences_produce_one_evidence_record(self):
        resume = """TECHNICAL SKILLS
Problem Solving
PROJECTS
Solved 1400 problems using data structures and algorithms. Applied problem solving to optimize a search workflow."""
        result = classify_skills(resume, {"problem solving"}, self.aliases)
        self.assertEqual(result.exact, {"problem solving"})
        self.assertEqual(result.semantic, {})
        self.assertEqual(result.evidence_based, {})
        self.assertEqual(len(result.match_details), 1)
        self.assertEqual(result.match_details["problem solving"]["category"], "exact")
        self.assertLessEqual(len(result.match_details["problem solving"]["evidence"]), 200)

    def test_ai_ml_capabilities_match_project_implementation_without_inferencing_rag(self):
        resume = """PROJECTS
Developed an AI-powered resume analyzer with an NLP pipeline and integrated LLM recommendations.
Built a face recognition system using facial embeddings and an AI recognition pipeline.
Implemented neural style transfer with a deep learning framework and model-based feature extraction."""
        requirements = {"ml integration", "ml-based features", "retrieval-augmented generation"}
        result = classify_skills(resume, requirements, self.aliases)

        for skill in ("ml integration", "ml-based features"):
            with self.subTest(skill=skill):
                self.assertIn(skill, result.evidence_based)
                self.assertEqual(result.match_details[skill]["category"], "evidence")
                self.assertTrue(result.match_details[skill]["evidence"])
                self.assertEqual(result.match_details[skill]["source_section"], "projects")
        self.assertIn("retrieval-augmented generation", result.missing)
        self.assertFalse((result.exact | set(result.semantic) | set(result.evidence_based)) & result.missing)

    def test_cybersecurity_evidence_does_not_match_ai_ml_capabilities(self):
        resume = """EXPERIENCE
Monitored network traffic, investigated security alerts, and hardened Linux systems.
Configured SIEM correlation rules and documented incident response procedures."""
        result = classify_skills(resume, {"ml integration", "ml-based features"}, self.aliases)
        self.assertEqual(result.evidence_based, {})
        self.assertEqual(result.missing, {"ml integration", "ml-based features"})

    def test_jd_filters_prose_and_normalizes_alias_duplicates(self):
        requirements = extract_jd_requirements("""\
Software Engineer Intern — India
- Ability to learn new technologies
- Collaborate with frontend developers
- NLP and Natural Language Processing
- LLMs, Large Language Models, RAG, Retrieval-Augmented Generation
- Problem-Solving Ability
- Implement Efficient Algorithms
- Use Git
- Write clean, reusable code
""", self.aliases)
        self.assertEqual(requirements.normalized_skills, {
            "natural language processing", "large language models",
            "retrieval-augmented generation", "problem solving", "algorithms", "git",
        })
        self.assertEqual(len(requirements.normalized_skills), 6)
        for noise in ("ability to learn", "collaborate with", "write clean", "software engineer intern", "india"):
            self.assertFalse(any(noise in skill for skill in requirements.normalized_skills))

    def test_cross_domain_jds_retain_unknown_skills_and_filter_duty_fragments(self):
        jds = {
            "web": "Required skills: TypeScript, Vue.js, VitePress and Foo-Bar. Build clean interfaces and collaborate across teams.",
            "data": "Experience with DuckDB, Polars and dbt. Maintain reliable workflows for analysts.",
            "ai": "Technical skills: JAX, Hydra, model evaluation. Work in a collaborative environment.",
            "security": "Required tools: Zeek, Sigma and Suricata. Follow security procedures.",
            "devops": "Tech stack: OpenTofu, Argo CD and Buildkite. Deploy scalable services.",
        }
        extracted = {domain: extract_jd_skills(text, self.aliases) for domain, text in jds.items()}
        for domain, skills in extracted.items():
            with self.subTest(domain=domain):
                self.assertTrue(skills, domain)
                self.assertFalse(any("collaborative" in skill or "workflows for" in skill or "clean interfaces" in skill for skill in skills))
        self.assertIn("vitepress", extracted["web"])
        self.assertIn("duckdb", extracted["data"])
        self.assertIn("jax", extracted["ai"])
        self.assertIn("zeek", extracted["security"])
        self.assertIn("opentofu", extracted["devops"])
        self.assertEqual(extract_jd_skills("Required skills: Postgre-SQL and Retrieval Augmented Generation", self.aliases), {
            "postgresql", "retrieval-augmented generation",
        })

    def test_generic_contextual_evidence_matches_project_skills_without_dictionary_entries(self):
        required = extract_jd_skills("Required skills: Data Pipelines, Model Evaluation, Foo-Bar", self.aliases)
        resume = """TECHNICAL SKILLS
Foo-Bar
PROJECTS
Built data pipeline jobs for an analytics warehouse.\nEvaluated model quality using held-out datasets.
"""
        result = classify_skills(resume, required, self.aliases)
        self.assertEqual(result.exact, {"foo-bar"})
        self.assertTrue({"data pipelines", "model evaluation"} <= set(result.evidence_based))
        self.assertEqual(result.missing, set())

        absent = classify_skills("PROJECTS\nBuilt a portfolio website with Vue.js.", required, self.aliases)
        self.assertIn("data pipelines", absent.missing)
        self.assertIn("model evaluation", absent.missing)

    def test_aliases_deduplicate_classification_and_empty_scores_are_safe(self):
        result = classify_skills("Built with NLP and Git.", {"NLP", "Natural Language Processing", "Use Git", "Git"}, self.aliases)
        self.assertEqual(result.exact, {"natural language processing", "git"})
        self.assertEqual(calculate_skill_score(set(), set()), 0.0)
        self.assertEqual(calculate_skill_score({"git"}, {"git"}, {"git": float("nan")}), 100.0)
        self.assertEqual(calculate_skill_score(set(), {"git"}, {"git": float("nan")}), 0.0)

    def test_problem_solving_uses_contextual_resume_evidence(self):
        cases = (
            ("ACHIEVEMENTS\nSolved 1400+ problems across LeetCode, GFG and Codeforces.", "evidence"),
            ("SUMMARY\nStrong foundation in Data Structures and Algorithms.", "semantic"),
            ("ACTIVITIES\nCompetitive programming experience.", "semantic"),
            ("ACHIEVEMENTS\nParticipated in coding challenges.", "evidence"),
        )
        for resume, expected_category in cases:
            with self.subTest(resume=resume):
                result = classify_skills(resume, {"problem solving"}, self.aliases)
                self.assertEqual(result.exact, set())
                self.assertEqual(result.related, set())
                self.assertEqual(result.missing, set())
                self.assertEqual(result.match_details["problem solving"]["category"], expected_category)
                self.assertTrue(result.evidence["problem solving"])

    def test_problem_solving_platform_name_without_context_is_not_evidence(self):
        result = classify_skills("LeetCode profile: https://leetcode.com/example", {"problem solving"}, self.aliases)
        self.assertEqual(result.evidence_based, {})
        self.assertEqual(result.missing, {"problem solving"})

    def test_evidence_match_is_counted_once_and_exposed_in_job_match_report(self):
        confidence = {"problem solving": 1.0}
        self.assertEqual(calculate_skill_score({"problem solving"}, {"problem solving"}, evidence_matches=confidence), 100.0)
        self.assertEqual(calculate_skill_score(set(), {"problem solving"}, evidence_matches={"problem solving": 0.65}), 65.0)

        from routes.upload import process_job_match
        resume = "ACHIEVEMENTS\nSolved 1400+ problems across LeetCode, GFG and Codeforces."
        aliases = self.aliases
        sections = {key: "present" for key in ("summary", "skills", "projects", "education", "experience")}
        contacts = {"email": "dev@example.com", "phone": None, "linkedin": None, "github": None, "portfolio": None}
        with patch("routes.upload.save_resume_history"), patch("routes.upload.build_latest_report"):
            response = process_job_match(
                "Required skills: Problem Solving", aliases, set(), resume, sections, contacts,
                SimpleNamespace(filename="resume.pdf"), 100, 50, 80, None, "evidence-user",
            )
        payload = json.loads(response.body)
        self.assertEqual(payload["matched_skills"], [])
        self.assertEqual(payload["partial_skills"], ["problem solving"])
        self.assertEqual(payload["missing_skills"], [])
        self.assertIn("problem solving", payload["evidence_skills"])
        self.assertEqual(payload["debug"]["evidence_matches"][0]["category"], "partial")

    def test_exact_semantic_related_and_missing_are_distinct_and_evidence_backed(self):
        result = classify_skills(
            "Java services supporting backend platforms are deployed and maintained.",
            {"java", "java backend", "spring boot"},
            self.aliases,
        )
        self.assertIn("java", result.exact)
        self.assertIn("java backend", set(result.semantic) | set(result.evidence_based) | result.related)
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
        self.assertEqual(calculate_skill_score({"exact"}, requirements, unresolved_requirements=1), 25.0)

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
