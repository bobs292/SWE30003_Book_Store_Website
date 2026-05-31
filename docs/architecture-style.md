# Architecture Style

This project follows a layered (Presentation → Domain → Data) architecture.
Each layer depends only on the layer directly below it. The presentation
layer handles HTTP and templates, the domain layer holds business rules and
service logic, and the data layer owns persistence details (SQLite).

For the cart feature, the cart state is stored in the presentation layer
using the Flask session, while product data comes from the data layer via
the repository/service pipeline.

Reference:
https://martinfowler.com/bliki/PresentationDomainDataLayering.html

---

## Book Cover Images

### Data layer

`data.json` seeds 12 real books with ISBNs. On first startup, `init_db` in `database.py` creates the `customers` and `books` tables, then `_seed_books` reads `data.json` and inserts the books into SQLite. After seeding, it calls `cache_covers` with the book list and the covers folder path. `cache_covers` in `cover_cache.py` constructs the Open Library URL
for each ISBN and downloads each image as `{isbn}.jpg` into
`src/presentation/static/images/covers/` via Python's `urllib`
(which is part of the standard library and works across all
operating systems, unlike `curl` which is not available on Windows
by default).
On subsequent startups the `books` table is already populated, so `_seed_books` returns immediately — no network requests are made.

### Domain layer

`BookRepository` in `src/domain/repositories/` defines the abstract contract (`list_books`, `get_by_id`). It contains no SQL and no knowledge of Open Library or the file system. `CatalogueService` in `src/domain/services/` calls the repository and passes results to the presentation layer.

### Data repository

`SqliteBookRepository` in `src/data/repositories/` implements the abstract contract. Its `_row_to_dict` method checks whether the cached cover exists on disk. If present, it sets `cover_url` to `/static/images/covers/{isbn}.jpg`; otherwise `cover_url` is `None`. The repository never contacts Open Library at query time.

### Presentation layer

`app.py` resolves the absolute path to the covers folder and passes it into `init_db`. It instantiates `CatalogueService` with `SqliteBookRepository` injected. The catalogue route calls `catalogue_service.list_books()` and passes the result to the template.

`catalogue.html` renders an `img` tag when `book.cover_url` is set, or a text fallback (title and author) when it is `None`. The browser never contacts Open Library — all images are served by Flask from the local static folder.

### What the browser sees

A request to `/catalogue` returns HTML with image tags like `/static/images/covers/9780307588371.jpg`. The browser requests each image from Flask, which serves it from the local file system. Open Library is contacted exactly once per book, at seed time, and never again.

### Architectural notes

The layered dependency rule is maintained: the data layer owns seeding and caching, the domain layer defines the contract, and the presentation layer renders what it receives. The one intentional compromise is that `cover_cache.py` writes into the presentation static folder — a cross-layer write. This is justified because Flask can only serve static files from a designated folder. The data layer never imports from the presentation layer; the path is injected from `app.py`, so the data layer has no hardcoded knowledge of the presentation folder structure.

---

## Known Architectural Simplification: Static Media Files

In production, media files are stored in object storage (S3, GCS, Azure Blob). The database holds a URL or storage key, the application never handles the file directly, and the browser fetches images from a CDN — keeping the server stateless.

Here, Flask's built-in static file server is used instead. Cover images are cached from Open Library at seed time using ISBNs and saved as `{isbn}.jpg` into `src/presentation/static/images/covers/`. Flask serves them at `/static/images/covers/{isbn}.jpg`. `SqliteBookRepository` checks for the cached file on disk and sets `cover_url` accordingly, or `None` if missing. The template renders an `img` tag or a text fallback.

This is a known simplification driven by framework and assignment constraints. The data layer owns all seeding and caching logic; the domain layer remains unaware of file system and network concerns. The only boundary blur is the cross-layer write during caching, mitigated by path injection from `app.py`.

In production this would be resolved by:

1. Storing a full URL or storage key in the database instead of a local path.
2. Uploading images to object storage during seeding.
3. Removing the static images folder from the application entirely.
