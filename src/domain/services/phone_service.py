import re


class PhoneService:
    """Handles Australian phone number validation and normalization."""

    @staticmethod
    def normalize_australian_phone(phone):
        """
        Normalize various Australian phone formats to domestic 04XXXXXXXX.

        Converts +61 and 61 international formats to 0 format.
        Returns original phone if not a recognized format.
        """
        if not phone:
            return phone

        normalized = phone.replace(" ", "")

        if normalized.startswith("+61"):
            normalized = "0" + normalized[3:]
        elif normalized.startswith("61") and len(normalized) == 11:
            normalized = "0" + normalized[2:]

        return normalized

    @staticmethod
    def is_valid_australian_mobile(phone):
        """Validates if phone is a valid Australian mobile number (04XXXXXXXX)."""
        normalized = PhoneService.normalize_australian_phone(phone)
        return bool(re.fullmatch(r"04\d{8}", normalized))
