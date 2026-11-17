import unittest

from services.contact_service import extract_contact_details


class ContactExtractionTests(unittest.TestCase):
    def test_extracts_email_phone_profiles_and_portfolio(self):
        text = (
            "jane.doe@example.com +91 9876543210 "
            "https://www.linkedin.com/in/jane-doe "
            "https://github.com/janedoe https://jane.example"
        )
        self.assertEqual(
            extract_contact_details(text),
            {
                "email": "jane.doe@example.com",
                "phone": "+91 9876543210",
                "linkedin": "https://www.linkedin.com/in/jane-doe",
                "github": "https://github.com/janedoe",
                "portfolio": "https://jane.example",
            },
        )

    def test_returns_first_matching_contact_and_portfolio_url(self):
        text = (
            "first@example.com second@example.com "
            "9876543210 9123456789 "
            "https://example-first.test https://example-second.test"
        )
        contacts = extract_contact_details(text)
        self.assertEqual(contacts["email"], "first@example.com")
        self.assertEqual(contacts["phone"], "9876543210")
        self.assertEqual(contacts["portfolio"], "https://example-first.test")

    def test_missing_contacts_are_none(self):
        self.assertEqual(
            extract_contact_details("No contact details here."),
            {"email": None, "phone": None, "linkedin": None, "github": None, "portfolio": None},
        )


if __name__ == "__main__":
    unittest.main()
