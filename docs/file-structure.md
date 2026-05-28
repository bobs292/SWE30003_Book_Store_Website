# File Structure

## Project Tree

```
SWE30003_Book_Store_Website/
├── pyproject.toml
├── README.md
├── .gitignore
│
├── docs/
│   ├── file-structure.md
│   └── architecture-style.md
│
├── tests/
│   ├── conftest.py
│   ├── domain/
│   │   ├── models/
│   │   │   ├── test_user.py
│   │   │   ├── test_customer.py
│   │   │   ├── test_admin.py
│   │   │   ├── test_book_title.py
│   │   │   ├── test_physical_location.py
│   │   │   ├── test_cart.py
│   │   │   ├── test_order.py
│   │   │   ├── test_invoice.py
│   │   │   └── test_shipment.py
│   │   └── services/
│   │       ├── test_auth_service.py
│   │       ├── test_catalogue_service.py
│   │       ├── test_checkout_service.py
│   │       ├── test_inventory_service.py
│   │       └── test_search_service.py
│   ├── data/
│   │   └── repositories/
│   │       └── sqlite/
│   │           ├── test_customer_repository.py
│   │           ├── test_book_repository.py
│   │           └── test_order_repository.py
│   └── presentation/
│       └── routes/
│           ├── test_auth_routes.py
│           ├── test_catalogue_routes.py
│           ├── test_order_routes.py
│           └── api/
│               ├── test_auth_api.py
│               └── test_catalogue_api.py
│
└── src/
    ├── app.py
    ├── data/
    │   ├── __init__.py
    │   ├── database.py
    │   ├── store.db
    │   ├── seeds/
    │   │   └── data.json
    │   └── repositories/
    │       ├── __init__.py
    │       ├── abstract/
    │       │   ├── __init__.py
    │       │   ├── customer_repository.py
    │       │   ├── admin_repository.py
    │       │   ├── book_repository.py
    │       │   ├── order_repository.py
    │       │   └── payment_gateway.py
    │       └── sqlite/
    │           ├── __init__.py
    │           ├── customer_repository.py
    │           ├── admin_repository.py
    │           ├── book_repository.py
    │           └── order_repository.py
    ├── domain/
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── user.py
    │   │   ├── customer.py
    │   │   ├── admin.py
    │   │   ├── book_title.py
    │   │   ├── physical_location.py
    │   │   ├── cart.py
    │   │   ├── order.py
    │   │   ├── invoice.py
    │   │   └── shipment.py
    │   └── services/
    │       ├── __init__.py
    │       ├── auth_service.py
    │       ├── catalogue_service.py
    │       ├── checkout_service.py
    │       ├── inventory_service.py
    │       └── search_service.py
    └── presentation/
        ├── __init__.py
        ├── routes/
        │   ├── __init__.py
        │   ├── auth_routes.py
        │   ├── catalogue_routes.py
        │   ├── order_routes.py
        │   └── api/
        │       ├── __init__.py
        │       ├── auth_api.py
        │       └── catalogue_api.py
        ├── static/
        │   └── css/
        │       └── base.css
        └── templates/
            ├── base.html
            ├── cart.html
            ├── catalogue.html
            ├── checkout.html
            ├── home.html
            ├── login.html
            ├── order_confirmation.html
            └── register.html
```

---

## Architectural Foundation

This project implements the three-layer Enterprise Architecture pattern.
Each layer has a single, distinct responsibility:

- Presentation: responds to user events, renders views, handles HTTP
- Domain: enforces business rules entirely in plain Python (no Flask, no DB)
- Data: performs CRUD operations, owns all database/JSON access

The strict dependency rule is Presentation to Domain to Data Source.
No layer may import from a layer above it.

By structuring the filesystem this way it makes managing this separation a bit
easier. It also adds friction when moving between layers. If you find yourself
reaching across directories to import something from a layer above, the file
path alone signals that something is wrong.

The domain layer never receives or returns database objects. All data passed
upward to the presentation layer is serialised into plain dictionaries by the
domain service. This means the presentation layer has no knowledge of the
internal domain models and is unaffected by changes to them.

---

## src/

All application source code lives under src/. This is the standard src layout,
which means Python resolves imports from src/ as the package root. This
prevents import errors when running the project from different directories.

The Python Packaging User Guide describes this benefit directly:

"The src layout helps prevent accidental usage of the in-development copy of
the code. This is relevant since the Python interpreter includes the current
working directory as the first item on the import path."

Python Packaging User Guide, src layout vs flat layout.
https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/

---

## src/presentation/

The presentation layer. Owns all HTTP concerns including routes, templates,
and static assets. Nothing in this folder is imported by the domain or data
layers.

### src/presentation/routes/

Flask route handlers split by concern. This folder is divided into a general
folder for HTML responses and an api/ subfolder for JSON responses.

### src/presentation/routes/api/

Route handlers for JSON responses. Separated from the HTML routes to make
the distinction between browser and API consumers clear.

### src/presentation/templates/

Jinja2 HTML templates for the browser-facing pages of the application.

### src/presentation/static/

Static assets served directly to the browser.

---

## src/domain/

The domain layer. Contains all business logic and business entities. Nothing
in this folder imports from the presentation or data layers.

### src/domain/models/

The business entities of the system. Each file represents one concept from
the domain model defined in Assignment 2. user.py is abstract and is the
parent of customer.py and admin.py. This is an Is-Kind-Of relationship
enforced through the folder by keeping all three together as a family of
related types.

### src/domain/services/

One file per area of business logic. This folder maps directly to the
controller classes identified in Assignment 2.

---

## src/data/

The data layer. Owns all persistent data concerns. No other layer reads from
or writes to the database directly.

### src/data/seeds/

Seed data for populating the database in a development environment. Kept
separate from the database itself to make clear this data is for development
only.

### src/data/repositories/

The only way the domain layer accesses persistent data. This folder implements
the Repository Pattern from Domain-Driven Design. It is divided into two
subfolders to separate the contracts from the implementations.

### src/data/repositories/abstract/

Abstract base classes that define the contract each repository must fulfil.
The domain layer imports exclusively from this folder. Keeping contracts in
their own folder means the domain always has a stable target to import from
regardless of which concrete backend is in use.

If a new backend requires operations not present in the current contracts,
this folder would need to change. This would invalidate all existing concrete
implementations. In that case a team should fork this folder into a new
contract folder rather than modifying the shared one, preserving the stability
of existing implementations.

### src/data/repositories/sqlite/

Concrete SQLite implementations of the abstract contracts. If the project
migrated to a different database, a new folder would be added alongside
sqlite/ with its own implementations. The abstract folder and the domain
layer would require no changes.

---

## tests/

Tests mirror the src/ structure exactly. No __init__.py files are needed.
Pytest discovers tests by filename pattern and resolves imports from src/
via pythonpath = ["src"] in pyproject.toml.

### tests/domain/

Tests for the domain layer.

### tests/domain/models/

Tests for each domain model.

### tests/domain/services/

Tests for each domain service.

### tests/data/

Tests for the data layer. Only the concrete sqlite/ folder has tests as the
abstract folder has no logic to test.

### tests/data/repositories/sqlite/

Tests for the concrete SQLite repository implementations.

### tests/presentation/

Tests for the presentation layer.

### tests/presentation/routes/

Tests for the HTML route handlers.

### tests/presentation/routes/api/

Tests for the JSON API route handlers.

---

## docs/

Project documentation. Kept separate from source code so documentation can
be read and updated independently of the application.