# SWE30003_Book_Store_Website
# Favourite Books

Online bookstore for SWE30003 Software Architectures and Design.

See `docs/file-structure.md` for the full project structure and architectural
decisions.

---

## How to Install

Clone the repository and create a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the package and its dependencies.

```bash
pip install -e .
```

---

## Running the Web Application

```bash
cd src
flask run
```

---

## Running in a Container

The app ships with a `Dockerfile`, so it can be built and run with either
Docker or Podman. On first start the container creates its SQLite database
and fetches book covers from Open Library, so the initial launch needs
network access and takes a few seconds longer. Data lives inside the
container and resets when it stops (it re-seeds on the next run).

### Docker

```bash
docker build -t favourite-books .
docker run --rm -p 8000:8000 favourite-books
```

### Podman

Podman's CLI is a drop-in replacement for Docker and uses the same
`Dockerfile`, so the commands are identical apart from the name:

```bash
podman build -t favourite-books .
podman run --rm -p 8000:8000 favourite-books
```

Either way, open http://localhost:8000 once it starts.

---

## Running Tests

The test suite includes unit tests, integration tests, and code style checks.

```bash
hatch run pytest
```

This runs:

- All unit and integration tests
- Code style checks via flake8 (formatting, linting, and pytest-specific style)
- Architectural import contract verification

To run tests without code style checks:

```bash
hatch run pytest -p no:flake8
```

---

## Setting Up for Development

The `pip install -e .` command installs the project and all development
dependencies including pytest, import-linter, pre-commit, pytest-flake8,
flake8, black, and isort. It also makes all imports resolve from `src/` so
you never need to modify your Python path manually.

Next, install the pre-commit hooks.

```bash
hatch run pre-commit install
```

This registers a git hook that runs automatically every time you run
`git commit`. You only need to do this once after cloning.

---

## How the Architecture is Enforced

This project uses import-linter to enforce the three-layer dependency rule.
The rule is: Presentation can import from Domain. Domain can import from Data.
Nothing can import upward.

import-linter checks this by scanning every import statement in the codebase
and verifying none of them cross a layer boundary in the wrong direction. If
they do, it prints exactly which file made the illegal import and which
contract it broke.

The check runs automatically when you commit. If a layer boundary is broken
the commit is blocked and you will see output explaining the violation.

To explore the dependency graphs run:

```bash
hatch run import-linter explore src
```

Or to explore a specific layer (replace `domain` with your target layer):

```bash
hatch run import-linter explore src.domain
```
