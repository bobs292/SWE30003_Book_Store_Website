- **Presentation** — responds to user events, renders views, handles HTTP
- **Domain** — enforces business rules entirely in plain Python (no Flask, no DB)
- **Data Source** — performs CRUD operations, owns all database/JSON access

The strict dependency rule is: Presentation → Domain → Data Source.
No layer may import from a layer above it.

By structuring our filesystem this way it makes managing this separation a bit easier. It also adds friction when moving between layers. If you find yourself reaching across directories to import something from a layer above, the file path alone signals that something is wrong
