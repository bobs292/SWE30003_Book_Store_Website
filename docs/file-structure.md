# File Structure

## Project Tree

```
SWE30003_Book_Store_Website/
├── pyproject.toml
├── README.md
├── Dockerfile
├── .env
├── .gitignore
├── .pre-commit-config.yaml
│
├── docs/
│   ├── architecture-style.md
│   ├── database-decision.md
│   ├── file-structure.md
│   ├── patterns.md
│   └── where-to-put-what.md
│
├── tests/
│   ├── test_architecture.py
│   ├── data/
│   │   ├── gateways/
│   │   │   └── test_address_validator.py
│   │   ├── repositories/
│   │   │   ├── test_book_repository.py
│   │   │   ├── test_customer_repository.py
│   │   │   ├── test_invoice_repository.py
│   │   │   └── test_order_repository.py
│   │   ├── test_cover_cache.py
│   │   └── test_database.py
│   ├── domain/
│   │   ├── models/
│   │   │   ├── test_admin.py
│   │   │   ├── test_book_title.py
│   │   │   ├── test_cart.py
│   │   │   ├── test_customer.py
│   │   │   ├── test_invoice.py
│   │   │   ├── test_order.py
│   │   │   ├── test_physical_location.py
│   │   │   ├── test_shipment.py
│   │   │   └── test_user.py
│   │   ├── repositories/
│   │   │   ├── test_admin_repository.py
│   │   │   ├── test_book_repository.py
│   │   │   ├── test_customer_repository.py
│   │   │   ├── test_order_repository.py
│   │   │   └── test_payment_gateway.py
│   │   └── services/
│   │       ├── test_auth_service.py
│   │       ├── test_cart_service.py
│   │       ├── test_catalogue_service.py
│   │       ├── test_checkout_service.py
│   │       ├── test_inventory_service.py
│   │       ├── test_phone_service.py
│   │       └── test_search_service.py
│   └── presentation/
│       ├── test_templates.py
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
    │   ├── payment_gateway.py
    │   ├── gateways/
    │   │   ├── __init__.py
    │   │   └── address_validator.py
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   ├── book_repository.py
    │   │   ├── customer_repository.py
    │   │   ├── invoice_repository.py
    │   │   └── order_repository.py
    │   └── seeds/
    │       ├── __init__.py
    │       ├── cover_cache.py
    │       └── data.json
    ├── domain/
    │   ├── __init__.py
    │   ├── gateways/
    │   │   ├── __init__.py
    │   │   ├── address_gateway.py
    │   │   └── payment_gateway.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── book_title.py
    │   │   ├── cart.py
    │   │   ├── customer.py
    │   │   ├── invoice.py
    │   │   ├── order.py
    │   │   └── user.py
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   ├── book_repository.py
    │   │   ├── customer_repository.py
    │   │   ├── invoice_repository.py
    │   │   └── order_repository.py
    │   └── services/
    │       ├── __init__.py
    │       ├── auth_service.py
    │       ├── cart_service.py
    │       ├── catalogue_service.py
    │       ├── checkout_service.py
    │       ├── phone_service.py
    │       └── search_service.py
    └── presentation/
        ├── __init__.py
        ├── routes/
        │   ├── __init__.py
        │   ├── auth_routes.py
        │   ├── catalogue_routes.py
        │   └── order_routes.py
        ├── static/
        │   ├── css/
        │   │   └── base.css
        │   └── images/
        │       ├── bookstore.jpg
        │       └── covers/          # cover images cached from Open Library at startup
        └── templates/
            ├── base.html
            ├── book_detail.html
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

Static assets served directly to the browser. Cover images are cached here from Open Library at startup — see `docs/architecture-style.md` for the full explanation of this design decision.

## src/domain/

The domain layer. It is the core abstraction of the system, existing independently of how data is stored or how users interact with it. Nothing here imports from the presentation or data layers.

In terms of software abstraction levels, this layer operates at the level of components and objects. It defines what the system does without specifying how it is implemented at a storage or interface level.

### src/domain/models/

The business entities of the system. Each file represents one concept from the domain model defined in Assignment 2.

`user.py` is an abstract class and is the parent of `customer.py`. This is an Is-Kind-Of (inheritance) relationship.

### src/domain/gateways/

Abstract contracts for external services the domain depends on. Each file defines an interface — what the gateway must do — without any knowledge of HTTP, APIs, or third-party SDKs. Concrete implementations live in `src/data/gateways/`.

### src/domain/repositories/

The specifications that define what persistent storage operations the domain requires. Each file defines the contract a concrete implementation must fulfil, without specifying how data is stored. Placing these in the domain layer reflects that they express a requirement of the domain, not a detail of storage.

### src/domain/services/

One file per area of business logic. Each service encapsulates a cohesive set of responsibilities in the sense used by Responsibility-Driven Design, and collaborates with other services and the domain repository interfaces only.

## src/data/

The data layer. It owns all persistent storage concerns. No other layer reads from or writes to the database directly.

### src/data/gateways/

Concrete implementations of the gateway contracts defined in `src/domain/gateways/`. Each file owns the HTTP calls, SDK usage, and external API details for one external service. If the provider changed, only this folder would change.

### src/data/repositories/

Concrete implementations of the repository contracts defined in `src/domain/repositories/`. If the project migrated to a different database, the files in this folder would be replaced. The domain layer would require no changes.

### src/data/seeds/

Initial data and utilities that populate the application on first run. `data.json` seeds the books catalogue (78 books) and demo user accounts. `cover_cache.py` fetches and caches cover images from Open Library at seed time so the presentation layer can serve them statically.

## tests/

Tests mirror the `src/` structure exactly. This makes it straightforward to identify which test file covers which source file and ensures each layer's tests remain independent of the others.

## docs/

Project documentation. Kept separate from source code so it can be read and updated independently of the application.
