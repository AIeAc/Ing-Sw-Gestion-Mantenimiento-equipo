import re
import unicodedata


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

NAME_PUNCTUATION = {" ", "-", "'", "’", "."}
LABEL_PUNCTUATION = NAME_PUNCTUATION | {",", "(", ")", "/", "&", "+", "_"}
TECHNICAL_PUNCTUATION = LABEL_PUNCTUATION | {"#", ":", "%", "°", "·", "²", "³"}
UNIT_PUNCTUATION = {" ", "/", "%", "°", "·", "²", "³", "-", "^", ".", "_"}


def _matches_unicode_text(value, punctuation, allow_digits, require_letter=True):
    has_letter = False
    has_digit = False
    for character in value:
        category = unicodedata.category(character)
        if category.startswith(("L", "M")):
            has_letter = True
            continue
        if allow_digits and category == "Nd":
            has_digit = True
            continue
        if character in punctuation:
            continue
        return False
    return has_letter if require_letter else has_letter or has_digit


def is_person_name(value):
    return _matches_unicode_text(value, NAME_PUNCTUATION, allow_digits=False)


def is_label(value):
    return _matches_unicode_text(value, LABEL_PUNCTUATION, allow_digits=True)


def is_technical_text(value):
    return _matches_unicode_text(
        value, TECHNICAL_PUNCTUATION, allow_digits=True, require_letter=False
    )


def is_unit(value):
    return _matches_unicode_text(
        value, UNIT_PUNCTUATION, allow_digits=True, require_letter=False
    )


def is_identifier(value):
    return bool(IDENTIFIER_PATTERN.fullmatch(value))


def is_email(value):
    return len(value) <= 254 and bool(EMAIL_PATTERN.fullmatch(value))


def is_safe_free_text(value):
    """Allow normal prose and line breaks, but reject hidden control characters."""
    return all(
        character in "\n\r\t" or not unicodedata.category(character).startswith("C")
        for character in value
    )
