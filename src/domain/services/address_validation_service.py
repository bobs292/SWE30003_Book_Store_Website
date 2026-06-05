import re


class AddressValidationService:
    """Validates Australian address fields."""

    def validate_address(self, street, suburb, state, postcode):
        """
        Validates address fields.

        Returns dict of validation errors (empty if valid).
        """
        errors = {}

        if not street:
            errors["street"] = "Street address is required."
        if not suburb:
            errors["suburb"] = "Suburb is required."
        if not state:
            errors["state"] = "State is required."
        elif not re.fullmatch(r"[A-Za-z]{2,3}", state):
            errors["state"] = "State must be 2 or 3 letters (e.g. VIC, NSW)."
        if not postcode:
            errors["postcode"] = "Postcode is required."
        elif not re.fullmatch(r"\d{4}", postcode):
            errors["postcode"] = "Postcode must be exactly 4 digits (e.g. 3000)."

        return errors
