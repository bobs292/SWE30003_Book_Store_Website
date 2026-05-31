import os
import time
import urllib.error
import urllib.request

# URL pattern for the Open Library Covers API.
# {isbn} is replaced with the book's ISBN-13. M is medium size.
# This is only called once per book, at seed time, and the result is cached
# locally.
_OPEN_LIBRARY_URL = "https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"

# Minimum file size in bytes to consider a cover valid.
# Open Library returns a 1x1 pixel blank image (around 43 bytes) when no cover
# exists. Any file smaller than this threshold is treated as a missing cover
# and discarded so the template can fall back gracefully to a placeholder.
# This threshold exists because the API serves a real JPEG for valid ISBNs and
# a tiny blank for missing ones, and we need to distinguish the two.
_MIN_COVER_BYTES = 1000

# urllib does not send a User-Agent by default which some servers reject.
# The User-Agent header identifies this application as a legitimate client
# rather than an anonymous script. Open Library and archive.org both serve the
# actual image data when a standard browser-like User-Agent is present, but may
# return HTTP 403 or block requests that lack one.
# We use urllib from the Python standard library instead of spawning a
# subprocess with curl because urllib requires no external dependencies, works
# identically across Windows, macOS and Linux, and eliminates shell-escaping
# and injection risks.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FavouriteBooks/1.0)"}


def cache_covers(books, cache_dir):
    """
    Fetches and saves cover images for a list of books into cache_dir.
    Each cover is saved as {isbn}.jpg. Covers that are already cached are
    skipped.
    Books with no isbn or a blank Open Library response are skipped silently.

    books     - list of dicts, each with at least an 'isbn' key
    cache_dir - absolute path to the folder where covers should be saved
    """
    os.makedirs(cache_dir, exist_ok=True)

    for book in books:
        isbn = book.get("isbn")
        if not isbn:
            # No ISBN means no cover can be fetched. Skip silently.
            continue

        dest = os.path.join(cache_dir, f"{isbn}.jpg")
        if os.path.exists(dest):
            # Already cached from a previous run. No need to fetch again.
            continue

        _fetch_and_save(isbn, dest)
        # Pause briefly between requests to avoid rate-limiting by Open Library
        # and archive.org.
        time.sleep(0.5)


def _fetch_and_save(isbn, dest):
    # Fetches the cover image for the given ISBN from Open Library and saves
    # it to dest. Open Library returns a 302 redirect to archive.org.
    # We build the request with a User-Agent header so both servers respond
    # with the image rather than rejecting the request.
    url = _OPEN_LIBRARY_URL.format(isbn=isbn)
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
    except (urllib.error.URLError, OSError):
        # Network error or timeout. Skip this cover silently.
        # The template will show a placeholder instead.
        return

    if len(data) < _MIN_COVER_BYTES:
        # Open Library returned a blank placeholder image.
        # Do not cache it so the template falls back gracefully.
        return

    with open(dest, "wb") as f:
        f.write(data)
