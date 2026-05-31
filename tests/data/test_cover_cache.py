import os
import urllib.error
from unittest.mock import patch, MagicMock

import pytest

from src.data.cover_cache import cache_covers


class TestCacheCovers:
    """Tests for the cover image caching utility."""

    def test_covers_folder_created_if_missing(self, tmp_path):
        # When cache_covers is called with a non-existent cache_dir,
        # the folder should be created automatically.
        cache_dir = tmp_path / "covers"
        assert not cache_dir.exists()

        cache_covers([], str(cache_dir))

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_valid_image_is_saved(self, tmp_path):
        # A response larger than _MIN_COVER_BYTES should be written to disk.
        cache_dir = tmp_path / "covers"
        isbn = "9780140449136"
        # Fake JPEG-like data well above the 1000 byte threshold.
        fake_image = b"\xff\xd8\xff\xe0" + b"x" * 2000

        with patch("src.data.cover_cache.urllib.request.urlopen") as mock_urlopen:
            response = MagicMock()
            response.read.return_value = fake_image
            mock_urlopen.return_value.__enter__.return_value = response

            cache_covers([{"isbn": isbn}], str(cache_dir))

        expected_path = cache_dir / f"{isbn}.jpg"
        assert expected_path.exists()
        assert expected_path.read_bytes() == fake_image

    def test_blank_placeholder_not_saved(self, tmp_path):
        # A response below _MIN_COVER_BYTES represents a blank placeholder.
        # It must not be written to disk so the template can fall back.
        cache_dir = tmp_path / "covers"
        isbn = "9780000000000"
        tiny_placeholder = b"\x00" * 50  # Far below the 1000 byte threshold.

        with patch("src.data.cover_cache.urllib.request.urlopen") as mock_urlopen:
            response = MagicMock()
            response.read.return_value = tiny_placeholder
            mock_urlopen.return_value.__enter__.return_value = response

            cache_covers([{"isbn": isbn}], str(cache_dir))

        expected_path = cache_dir / f"{isbn}.jpg"
        assert not expected_path.exists()

    def test_already_cached_file_not_refetched(self, tmp_path):
        # If the destination file already exists, _fetch_and_save should not
        # be called and the existing file must remain untouched.
        cache_dir = tmp_path / "covers"
        isbn = "9780140449136"
        cache_dir.mkdir()
        existing_file = cache_dir / f"{isbn}.jpg"
        existing_file.write_bytes(b"existing_data")

        with patch("src.data.cover_cache._fetch_and_save") as mock_fetch:
            cache_covers([{"isbn": isbn}], str(cache_dir))
            mock_fetch.assert_not_called()

        assert existing_file.read_bytes() == b"existing_data"

    def test_missing_isbn_skipped_silently(self, tmp_path):
        # Books without an ISBN cannot have covers fetched.
        # They should be skipped without raising or calling the fetcher.
        cache_dir = tmp_path / "covers"

        with patch("src.data.cover_cache._fetch_and_save") as mock_fetch:
            cache_covers([{"title": "No ISBN Book"}], str(cache_dir))
            mock_fetch.assert_not_called()

    def test_network_error_handled_gracefully(self, tmp_path):
        # Network failures during fetching must not propagate uncaught.
        # The cover is simply skipped and the application continues.
        cache_dir = tmp_path / "covers"
        isbn = "9780140449136"

        with patch("src.data.cover_cache.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection timeout")
            cache_covers([{"isbn": isbn}], str(cache_dir))

        expected_path = cache_dir / f"{isbn}.jpg"
        assert not expected_path.exists()
