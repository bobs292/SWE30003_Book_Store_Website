import os
from unittest.mock import MagicMock, patch

import pytest

from src.data.services.address_validator import SmartyStreetsAddressValidator

_has_credentials = bool(
    os.environ.get("SMARTY_AUTH_ID") and os.environ.get("SMARTY_AUTH_TOKEN")
)
integration = pytest.mark.skipif(
    not _has_credentials,
    reason="SMARTY_AUTH_ID and SMARTY_AUTH_TOKEN not set",
)


def _make_validator():
    return SmartyStreetsAddressValidator(auth_id="fake-id", auth_token="fake-token")


def _mock_result(verification_status):
    """Return a fake lookup.result list with the given verification_status."""
    candidate = MagicMock()
    candidate.analysis.verification_status = verification_status
    return [candidate]


# ============================================================================
# Unit tests — no network, mock client.send()


def test_verified_status_returns_none():
    validator = _make_validator()
    with patch.object(validator._client, "send") as mock_send:
        mock_send.side_effect = lambda lookup: setattr(
            lookup, "result", _mock_result("Verified")
        )
        assert validator.validate("1 Main St", "Melbourne", "VIC", "3000") is None


def test_partial_status_returns_error():
    validator = _make_validator()
    with patch.object(validator._client, "send") as mock_send:
        mock_send.side_effect = lambda lookup: setattr(
            lookup, "result", _mock_result("Partial")
        )
        result = validator.validate("1 Main St", "Melbourne", "VIC", "3000")
    assert result is not None
    assert "partially" in result.lower()


def test_ambiguous_status_returns_error():
    validator = _make_validator()
    with patch.object(validator._client, "send") as mock_send:
        mock_send.side_effect = lambda lookup: setattr(
            lookup, "result", _mock_result("Ambiguous")
        )
        result = validator.validate("1 Main St", "Melbourne", "VIC", "3000")
    assert result is not None
    assert "ambiguous" in result.lower()


def test_none_status_returns_error():
    # verification_status "None" means the API found no match.
    validator = _make_validator()
    with patch.object(validator._client, "send") as mock_send:
        mock_send.side_effect = lambda lookup: setattr(
            lookup, "result", _mock_result("None")
        )
        result = validator.validate("99 Fake Street", "Fakeville", "VIC", "9999")
    assert result is not None
    assert "verified" in result.lower()


def test_empty_result_list_returns_error():
    # The API returned an empty array — no candidates at all.
    validator = _make_validator()
    with patch.object(validator._client, "send") as mock_send:
        mock_send.side_effect = lambda lookup: setattr(lookup, "result", [])
        result = validator.validate("1 Main St", "Melbourne", "VIC", "3000")
    assert result is not None


def test_api_exception_returns_error_string():
    validator = _make_validator()
    with patch.object(validator._client, "send", side_effect=Exception("timeout")):
        result = validator.validate("1 Main St", "Melbourne", "VIC", "3000")
    assert result is not None
    assert "timeout" in result


def test_constructor_reads_env_vars_when_no_credentials_passed(monkeypatch):
    monkeypatch.setenv("SMARTY_AUTH_ID", "env-id")
    monkeypatch.setenv("SMARTY_AUTH_TOKEN", "env-token")
    assert SmartyStreetsAddressValidator() is not None


# ============================================================================
# Integration tests — real SmartyStreets API
# Skipped automatically when credentials are absent.


@integration
def test_valid_address_returns_none():
    validator = SmartyStreetsAddressValidator()
    assert validator.validate("1 Martin Place", "Sydney", "NSW", "2000") is None


@integration
def test_second_valid_address_returns_none():
    validator = SmartyStreetsAddressValidator()
    assert validator.validate("1 Spring Street", "Melbourne", "VIC", "3000") is None


@integration
def test_fake_address_returns_error():
    # A made-up street in a made-up suburb with an invalid postcode must be
    # rejected now that we check verification_status rather than result list presence.
    validator = SmartyStreetsAddressValidator()
    result = validator.validate("99 Fake Street", "Fakeville", "VIC", "9999")
    assert result is not None


@integration
def test_all_empty_fields_returns_error():
    validator = SmartyStreetsAddressValidator()
    assert validator.validate("", "", "", "") is not None


@integration
def test_missing_street_returns_error():
    validator = SmartyStreetsAddressValidator()
    assert validator.validate("", "Melbourne", "VIC", "3000") is not None


@integration
def test_none_fields_returns_error():
    validator = SmartyStreetsAddressValidator()
    assert validator.validate(None, None, None, None) is not None
