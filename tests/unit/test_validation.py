import unittest

from app.core.validation import (
    is_email,
    is_identifier,
    is_label,
    is_person_name,
    is_safe_free_text,
    is_technical_text,
    is_unit,
)


class InputValidationTests(unittest.TestCase):
    def test_person_names_accept_accents_and_reject_numbers(self):
        self.assertTrue(is_person_name("María-José O'Connor"))
        self.assertFalse(is_person_name("María 123"))
        self.assertFalse(is_person_name("<script>"))

    def test_labels_allow_equipment_numbers_but_reject_markup(self):
        self.assertTrue(is_label("Bomba centrífuga 2 (respaldo)"))
        self.assertFalse(is_label("Bomba <script>"))

    def test_identifiers_do_not_allow_spaces_or_shell_symbols(self):
        self.assertTrue(is_identifier("EQ-001/A"))
        self.assertFalse(is_identifier("EQ 001"))
        self.assertFalse(is_identifier("EQ-001;$"))

    def test_technical_fields_and_units_accept_common_notation(self):
        self.assertTrue(is_technical_text("ACS580-01 #2"))
        self.assertTrue(is_unit("mm/s²"))
        self.assertTrue(is_unit("°C"))

    def test_email_and_free_text_reject_invalid_shapes(self):
        self.assertTrue(is_email("persona@empresa.mx"))
        self.assertFalse(is_email("persona sin dominio"))
        self.assertTrue(is_safe_free_text("Revisión completada.\nSin novedades."))
        self.assertFalse(is_safe_free_text("Texto\x00oculto"))


if __name__ == "__main__":
    unittest.main()
