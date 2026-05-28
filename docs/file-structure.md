## Architectural Foundation

This project implements the three-layer Enterprise Architecture pattern.
Each layer has a single, distinct responsibility:

- **Presentation** — responds to user events, renders views, handles HTTP
- **Domain** — enforces business rules entirely in plain Python (no Flask, no DB)
- **Data** — performs CRUD operations, owns all database/JSON access

The strict dependency rule is: Presentation → Domain → Data Source.
No layer may import from a layer above it.

By structuring our filesystem this way it makes managing this separation a bit
easier. It also adds friction when moving between layers. If you find yourself
reaching across directories to import something from a layer above, the file
path alone signals that something is wrong.

---

## Data Layer

### `/repositories`
Repositories are the only way the domain layer accesses persistent data.
From the domain's perspective they behave like a simple in-memory collection —
`save()`, `find_by_id()`, `find_by_username()` — with no knowledge of what is
happening underneath. This is the Repository Pattern from Domain-Driven Design.

### `/repositories/abstract`
Contains the contracts (abstract base classes) that define what operations a
repository must exist without implementing them. The domain layer imports
exclusively from here — it knows the interface but never the implementation.
Swapping storage backends requires no changes to the domain logic or its
imports, as the domain always references `/abstract` regardless of which
concrete implementation is injected. Only the import in `app.py` changes,
as it is the only place in the project where a concrete repository is named.

### `/repositories/sqlite`
The concrete SQLite implementation of each abstract repository. This is the
only place in the project where SQL is written. If the project were to migrate
to Postgres or any other database, a new folder would be added (e.g.
`/repositories/postgres`) with its own concrete implementation. The abstract
contracts and the domain layer would require no changes at all.