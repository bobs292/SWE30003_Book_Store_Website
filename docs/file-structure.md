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
│   │   ├── repositories/
│   │   │   ├── test_admin_repository.py
│   │   │   ├── test_book_repository.py
│   │   │   ├── test_customer_repository.py
│   │   │   ├── test_order_repository.py
│   │   │   └── test_payment_gateway.py
│   │   └── services/
│   │       ├── test_auth_service.py
│   │       ├── test_catalogue_service.py
│   │       ├── test_checkout_service.py
│   │       ├── test_inventory_service.py
│   │       └── test_search_service.py
│   ├── data/
│   │   └── repositories/
│   │       ├── test_customer_repository.py
│   │       ├── test_book_repository.py
│   │       └── test_order_repository.py
│   └── presentation/
│       └── routes/
│           ├── test_auth_routes.py
│           ├── test_catalogue_routes.py
│           └── test_order_routes.py
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
    │       ├── book_repository.py
    │       ├── customer_repository.py
    │       └── order_repository.py
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
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   ├── admin_repository.py
    │   │   ├── book_repository.py
    │   │   ├── customer_repository.py
    │   │   ├── order_repository.py
    │   │   └── payment_gateway.py
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
        │   └── order_routes.py
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

## Architectural Foundation

This project uses the layered architectural style, one of the Call-and-Return architectural styles. The system is decomposed into three layers. The presentation layer responds to HTTP requests, renders templates, and handles user interaction. The domain layer enforces business rules in plain Python, independent of any framework or database. The data layer performs all persistent storage operations and owns all database access.

The dependency rule is that presentation may call domain, and domain may call data. No layer may import from a layer above it. This constraint is what makes the style a true layered architecture rather than just a grouped folder structure.

The layered style was chosen because it directly addresses the quality attributes most critical to this system. It promotes modifiability, since the database backend can be replaced without touching business logic, and testability, since the domain layer can be tested in isolation without a running database or web server.

The filesystem mirrors this structure intentionally. If you find yourself importing across layer boundaries in the wrong direction, the file path itself signals the violation.

## src/

All application source code lives under `src/`. This separates runnable application code from project configuration, documentation, and tests.

## src/presentation/

The presentation layer. It is the externally visible interface of the system and the only layer that interacts with Flask and the browser. Nothing in this folder is imported by the domain or data layers.

This layer corresponds to the Process View in Kruchten's 4+1 model. It is the entry point for all runtime interactions initiated by a user.

### src/presentation/routes/

Flask route handlers separated by functional concern. Each file groups the routes for one area of the system.

### src/presentation/templates/

Jinja2 HTML templates for browser-facing pages.

### src/presentation/static/

Static assets served directly to the browser.

## src/domain/

The domain layer. It is the core abstraction of the system, existing independently of how data is stored or how users interact with it. Nothing here imports from the presentation or data layers.

In terms of software abstraction levels, this layer operates at the level of components and objects. It defines what the system does without specifying how it is implemented at a storage or interface level.

### src/domain/models/

The business entities of the system. Each file represents one concept from the domain model defined in Assignment 2.

`user.py` is an abstract class and is the parent of `customer.py` and `admin.py`. This is an Is-Kind-Of (inheritance) relationship. Keeping all three together makes the class hierarchy visible in the filesystem.

### src/domain/repositories/

The specifications that define what persistent storage operations the domain requires. Each file defines the contract a concrete implementation must fulfil, without specifying how data is stored. Placing these in the domain layer reflects that they express a requirement of the domain, not a detail of storage.

### src/domain/services/

One file per area of business logic. Each service encapsulates a cohesive set of responsibilities in the sense used by Responsibility-Driven Design, and collaborates with other services and the domain repository interfaces only.

This folder maps directly to the controller classes identified in Assignment 2.

## src/data/

The data layer. It owns all persistent storage concerns. No other layer reads from or writes to the database directly.

### src/data/seeds/

Initial data that populates the application on first run, including users, books, and other required records.

### src/data/repositories/

Concrete implementations of the repository contracts defined in `src/domain/repositories/`. If the project migrated to a different database, the files in this folder would be replaced. The domain layer would require no changes.

## tests/

Tests mirror the `src/` structure exactly. This makes it straightforward to identify which test file covers which source file and ensures each layer's tests remain independent of the others.

## docs/

Project documentation. Kept separate from source code so it can be read and updated independently of the application.
