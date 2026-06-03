import os

from smartystreets_python_sdk import BasicAuthCredentials, ClientBuilder
from smartystreets_python_sdk.international_street import Lookup as InternationalLookup

from src.domain.services.address_validator import AddressValidator


class SmartyStreetsAddressValidator(AddressValidator):
    def __init__(self, auth_id=None, auth_token=None):
        # Falls back to environment variables if credentials are not passed directly.
        auth_id = auth_id or os.environ.get("SMARTY_AUTH_ID")
        auth_token = auth_token or os.environ.get("SMARTY_AUTH_TOKEN")
        credentials = BasicAuthCredentials(auth_id, auth_token)
        self._client = ClientBuilder(
            credentials
        ).build_international_street_api_client()

    _STATUS_ERRORS = {
        "Partial": (
            "Address only partially matched — please check suburb, state and postcode."
        ),
        "Ambiguous": (
            "Address is ambiguous — please provide a more specific street address."
        ),
        "None": "Address could not be verified — please check all fields.",
    }

    def validate(self, street, suburb, state, postcode) -> str | None:
        lookup = InternationalLookup()
        lookup.country = "Australia"
        lookup.address1 = street or ""
        lookup.locality = suburb or ""
        lookup.administrative_area = state or ""
        lookup.postal_code = postcode or ""
        try:
            self._client.send(lookup)
            if not lookup.result:
                return "Address could not be verified."
            status = lookup.result[0].analysis.verification_status
            if status == "Verified":
                return None
            return self._STATUS_ERRORS.get(
                status, f"Address could not be verified (status: {status})."
            )
        except Exception as e:
            return f"Address verification failed: {e}"
