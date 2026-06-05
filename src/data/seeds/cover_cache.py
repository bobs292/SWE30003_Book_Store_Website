import os
import ssl
import time
import urllib.error
import urllib.request

import certifi

_OPEN_LIBRARY_URL = "https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
_MIN_COVER_BYTES = 1000
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FavouriteBooks/1.0)"}

# On Windows, Python's urllib does not use the system certificate store.
# Pointing the SSL context at certifi's CA bundle replicates the behaviour
# Linux gets from its system store, so archive.org's certificate chain is
# trusted without disabling verification entirely.
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

def cache_covers(books, cache_dir):
    """
    Fetches and saves cover images for a list of books into cache_dir.
    Each cover is saved as {isbn}.jpg. Covers that are already cached are
    skipped, as are books whose Open Library response is blank.
    Since isbn is the books table's primary key, callers pass books that
    already have an isbn, so the no-isbn case is only a safety net here
    rather than an expected path.
    books     - list of dicts, each with an 'isbn' key
    cache_dir - absolute path to the folder where covers should be saved
    """
    os.makedirs(cache_dir, exist_ok=True)
    to_fetch = [
        b
        for b in books
        if b.get("isbn")
        and not os.path.exists(os.path.join(cache_dir, f"{b['isbn']}.jpg"))
    ]
    if not to_fetch:
        print("  [covers] All covers already cached.", flush=True)
        return
    total = len(to_fetch)
    print(f"  [covers] Fetching {total} new cover(s) from Open Library...", flush=True)
    for i, book in enumerate(to_fetch, 1):
        isbn = book["isbn"]
        title = book.get("title", isbn)
        dest = os.path.join(cache_dir, f"{isbn}.jpg")
        print(f"  [covers] [{i}/{total}] {title}", flush=True)
        _fetch_and_save(isbn, dest)
        if i < total:
            time.sleep(1.0)
    print("  [covers] Done.", flush=True)

def _fetch_and_save(isbn, dest):
    url = _OPEN_LIBRARY_URL.format(isbn=isbn)
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as response:
            data = response.read()
    except (urllib.error.URLError, OSError) as e:
        print(f"    [covers] FAILED {isbn}: {type(e).__name__}: {e}", flush=True)
        return

    if len(data) < _MIN_COVER_BYTES:
        print(f"    [covers] Blank image returned for {isbn}, skipping.", flush=True)
        return

    with open(dest, "wb") as f:
        f.write(data)
