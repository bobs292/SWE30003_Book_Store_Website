# Where to Put What

## The One Rule

Before adding any file, ask: what layer does this belong to?

- Does it handle an HTTP request or render a page? -> `src/presentation/`
- Does it enforce a business rule or represent a business concept? ->
`src/domain/`
- Does it read from or write to the database? -> `src/data/`

No layer may import from a layer above it.

---

## src/presentation/

### src/presentation/routes/

Put a file here when it maps a URL to a response.

Examples:
- A user submits the login form -> `auth_routes.py`
- A user views the catalogue page -> `catalogue_routes.py`
- A user views or places an order -> `order_routes.py`

One file per functional area. Each file contains one or more Flask route
functions for that area.

### src/presentation/templates/

Put a file here when it is an HTML page rendered by Flask.

Examples:
- The login page -> `login.html`
- The catalogue page -> `catalogue.html`
- The checkout confirmation page -> `order_confirmation.html`

### src/presentation/static/

Put a file here when it is served directly to the browser without processing.

Examples:
- Stylesheets -> `css/base.css`
- Book cover images -> `images/covers/9780307588371.jpg`
- JavaScript files, fonts

**Note on images:** Cover images live here as a framework constraint, not a
design choice. Flask can only serve static files from this folder. Images
are cached from Open Library at seed time using ISBNs and saved as
`{isbn}.jpg` into `images/covers/`. The repository sets `cover_url` to
`/static/images/covers/{isbn}.jpg` if the file exists on disk, or `None`
if it doesn't. The template renders an `img` tag or a text fallback. In a
production deployment, images would be stored in object storage (S3 etc.)
and the database would store a full URL instead. See
`docs/architecture-style.md` for the full explanation.

---

## src/domain/

### src/domain/models/

Put a file here when it represents a business concept from the domain model.

Examples:
- A user of the system -> `user.py`
- A customer who places orders -> `customer.py`
- An admin who manages the catalogue -> `admin.py`
- A book available for sale -> `book_title.py`
- A confirmed purchase -> `order.py`
- A financial record of a transaction -> `invoice.py`
- A dispatch record -> `shipment.py`
- A customer's in-progress selection -> `cart.py`
- A physical shelf location in the store -> `physical_location.py`

Do not put anything here that knows about Flask, SQLite, or any database.

### src/domain/repositories/

Put a file here when it defines what storage operations the domain needs,
without specifying how they are performed.

Examples:
- What operations can be done on a customer record -> `customer_repository.py`
- What operations can be done on a book record -> `book_repository.py`
- What operations can be done on an order record -> `order_repository.py`
- What operations can be done on an admin record -> `admin_repository.py`
- The interface for processing a payment -> `payment_gateway.py`

These files contain abstract base classes only. No SQL, no database imports.

### src/domain/services/

Put a file here when it contains business logic that coordinates between models
and repositories.

Examples:
- Logging in and registering a user -> `auth_service.py`
- Searching and browsing the catalogue -> `catalogue_service.py` /
`search_service.py`
- Processing a checkout and payment -> `checkout_service.py`
- Checking and updating stock levels -> `inventory_service.py`

A service may import from `src/domain/models/` and `src/domain/repositories/`.
It must not import from `src/presentation/` or `src/data/`.

---

## src/data/

### src/data/repositories/

Put a file here when it is a concrete implementation of a repository contract
defined in `src/domain/repositories/`.

Examples:
- SQLite implementation for customer storage -> `customer_repository.py`
- SQLite implementation for book storage -> `book_repository.py`
- SQLite implementation for order storage -> `order_repository.py`

Each file here imports from `src/domain/repositories/` and contains SQL queries
or database calls.

### src/data/seeds/

Put a file here when it contains initial data loaded into the database on first
run.

Examples:
- Book records, user accounts, shelf locations -> `data.json`
- Cover image caching from Open Library -> `cover_cache.py`

### src/data/database.py

Connection setup and database initialisation logic lives here. Nothing else.

---

## tests/

Tests mirror `src/` exactly. If the source file is at
`src/domain/models/order.py`, the test file goes at
`tests/domain/models/test_order.py`.

| Source file | Test file |
|---|---|
| `src/domain/models/order.py` | `tests/domain/models/test_order.py` |
| `src/domain/services/checkout_service.py` |
`tests/domain/services/test_checkout_service.py` |
| `src/domain/repositories/order_repository.py` |
`tests/domain/repositories/test_order_repository.py` |
| `src/data/repositories/order_repository.py` |
`tests/data/repositories/test_order_repository.py` |
| `src/presentation/routes/order_routes.py` |
`tests/presentation/routes/test_order_routes.py` |

---

## Quick Reference

| I am writing... | It goes in... |
|---|---|
| A Flask route function | `src/presentation/routes/` |
| An HTML page | `src/presentation/templates/` |
| A CSS file | `src/presentation/static/` |
| A cover image (framework constraint, see architecture-style.md) | `src/presentation/static/images/covers/` |
| A business entity (model) | `src/domain/models/` |
| A storage contract (abstract) | `src/domain/repositories/` |
| Business logic | `src/domain/services/` |
| A database query | `src/data/repositories/` |
| Example data | `src/data/seeds/` |
| Database connection setup | `src/data/database.py` |
